# coding:utf-8
import os
import re
from datetime import datetime

import requests
from PySide6.QtCore import QProcess, QThread, QTimer, Signal

from ..common.config import cfg
from ..common.event_bus import event_bus


class DownloadTask:
    """下载任务类"""

    _id_counter = 0

    def __init__(
        self,
        url,
        download_path,
        file_name="",
        quality="best",
        project_name="",
        episode_num=0,
    ):
        self.url = url
        self.download_path = download_path
        self.file_name = file_name
        self.quality = quality
        self.project_name = project_name
        self.episode_num = episode_num
        self.status = "等待中"  # 等待中, 下载中, 已完成, 失败
        self.progress = 0
        self.speed = ""
        self.filename = ""
        self.start_time = None
        self.end_time = None
        self.error_message = ""

        DownloadTask._id_counter += 1
        self.id = DownloadTask._id_counter


class DownloadThread(QThread):
    """下载线程 - 使用QProcess版本"""

    progress_signal = Signal(int, str, str)  # 进度百分比, 速度, 文件名
    finished_signal = Signal(bool, str)  # 成功/失败, 消息
    cancelled_signal = Signal()  # 新增：取消完成信号

    def __init__(self, task: DownloadTask):
        super().__init__()
        self.task = task
        self.is_cancelled = False
        self.process = None
        self.output_lines = []  # 存储输出用于错误诊断
        self._cancellation_timer = None

    def build_ytdlp_command(self):
        """根据配置构建 yt-dlp 命令"""
        cmd = [cfg.ytdlpPath.value]

        # 输出路径和模板
        if self.task.file_name:
            output_path = os.path.join(self.task.download_path, self.task.file_name)
            cmd.extend(["-o", output_path])
        else:
            output_template = os.path.join(
                self.task.download_path, cfg.outputTemplate.value
            )
            cmd.extend(["-o", output_template])

        # 格式设置 - 强制 MP4 格式
        cmd.extend(["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"])

        # 质量筛选
        if cfg.downloadQuality.value not in ["best", "worst"]:
            cmd.extend(["-S", f"res:{cfg.downloadQuality.value}"])

        # 代理设置
        if not cfg.systemProxy.value and cfg.proxyUrl.value:
            cmd.extend(["--proxy", cfg.proxyUrl.value])

        # 字幕设置
        if cfg.downloadSubtitles.value:
            cmd.append("--write-sub")
            if cfg.subtitleLanguages.value:
                cmd.extend(["--sub-langs", cfg.subtitleLanguages.value])

        if cfg.embedSubtitles.value:
            cmd.append("--embed-subs")

        # 缩略图设置
        if cfg.downloadThumbnail.value:
            cmd.append("--write-thumbnail")

        if cfg.embedThumbnail.value:
            cmd.append("--embed-thumbnail")

        # 元数据设置
        if cfg.downloadMetadata.value:
            cmd.append("--write-info-json")

        if cfg.writeDescription.value:
            cmd.append("--write-description")

        if cfg.writeAnnotations.value:
            cmd.append("--write-annotations")

        # 下载控制
        cmd.extend(["-N", str(cfg.concurrentDownloads.value)])
        cmd.extend(["-R", str(cfg.retryAttempts.value)])
        cmd.extend(["--socket-timeout", str(cfg.downloadTimeout.value)])

        if cfg.limitDownloadRate.value and cfg.maxDownloadRate.value:
            cmd.extend(["--limit-rate", cfg.maxDownloadRate.value])

        if cfg.skipExistingFiles.value:
            cmd.append("--no-overwrites")

        # Cookies 设置
        if cfg.useCookies.value and cfg.cookiesFile.value:
            cmd.extend(["--cookies", cfg.cookiesFile.value])

        # 编码器设置
        # if cfg.videoCodec.value != "h264":
        #     cmd.extend(["--video-codec", cfg.videoCodec.value])

        # if cfg.audioCodec.value != "aac":
        #     cmd.extend(["--audio-codec", cfg.audioCodec.value])

        # ffmpeg 路径
        if cfg.ffmpegPath.value:
            cmd.extend(["--ffmpeg-location", cfg.ffmpegPath.value])

        # 添加通用参数
        cmd.extend(
            [
                "--newline",
                "--no-part",
                "--no-mtime",
                "--ignore-errors",
            ]
        )

        # 添加 URL
        cmd.append(self.task.url)

        return cmd

    def run(self):
        # 网络检查部分保持不变
        try:
            resp = requests.get("https://www.youtube.com", timeout=3)
            if resp.status_code != 200:
                self.finished_signal.emit(
                    False, f"无法访问YouTube，HTTP状态码: {resp.status_code}"
                )
                return
        except requests.exceptions.Timeout:
            self.finished_signal.emit(False, "连接YouTube超时，请检查网络连接")
            return
        except requests.exceptions.ConnectionError:
            self.finished_signal.emit(False, "无法连接到YouTube，请检查网络连接")
            return
        except requests.exceptions.RequestException as e:
            self.finished_signal.emit(False, f"网络错误: {str(e)}")
            return
        except Exception as e:
            self.finished_signal.emit(False, f"检测网络连接时发生未知错误: {str(e)}")
            return

        self.task.status = "下载中"
        self.task.start_time = datetime.now()

        try:
            # 获取yt-dlp.exe路径
            ytdlp_path = cfg.get(cfg.ytdlpPath)
            if not os.path.exists(ytdlp_path):
                self.finished_signal.emit(False, f"yt-dlp.exe不存在: {ytdlp_path}")
                return

            # 确保下载目录存在
            os.makedirs(self.task.download_path, exist_ok=True)

            # 构建命令
            cmd = self.build_ytdlp_command()
            print(f"执行yt-dlp命令: {' '.join(cmd)}")

            # 创建QProcess
            self.process = QProcess()

            # 连接信号
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(self.handle_finished)
            self.process.errorOccurred.connect(self.handle_error)

            # 设置程序和工作目录
            self.process.setProgram(ytdlp_path)
            self.process.setArguments(cmd[1:])  # 去掉程序路径本身

            # 启动进程
            self.process.start()

            # 等待进程完成（在事件循环中）
            self.exec()

            # 发送信号
            event_bus.download_finished_signal.emit(True, self.task.download_path)

        except Exception as e:
            if not self.is_cancelled:
                error_msg = f"下载失败: {str(e)}"
                if self.output_lines:
                    error_msg += "\n输出日志:\n" + "\n".join(self.output_lines[-10:])

                self.task.status = "失败"
                self.task.error_message = error_msg
                self.task.end_time = datetime.now()
                self.finished_signal.emit(False, error_msg)
                event_bus.download_finished_signal.emit(False, error_msg)

    def handle_stdout(self):
        """处理标准输出"""
        if not self.process:
            return

        data = (
            self.process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        )
        lines = data.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            self.output_lines.append(line)

            if self.is_cancelled:
                return

            # 解析进度信息
            progress_match = self.parse_progress_line(line)
            if progress_match:
                percent, speed = progress_match
                self.task.progress = percent
                self.task.speed = speed
                self.progress_signal.emit(percent, speed, self.task.filename)

            # 提取文件名
            if not hasattr(self, "filename_extracted") or not self.filename_extracted:
                if self.extract_filename(line):
                    self.filename_extracted = True

    def handle_stderr(self):
        """处理标准错误输出"""
        if not self.process:
            return

        data = (
            self.process.readAllStandardError().data().decode("utf-8", errors="ignore")
        )
        lines = data.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            self.output_lines.append(line)

            # 错误输出也可能包含进度信息，所以同样解析
            if self.is_cancelled:
                return

            progress_match = self.parse_progress_line(line)
            if progress_match:
                percent, speed = progress_match
                self.task.progress = percent
                self.task.speed = speed
                self.progress_signal.emit(percent, speed, self.task.filename)

            if not hasattr(self, "filename_extracted") or not self.filename_extracted:
                if self.extract_filename(line):
                    self.filename_extracted = True

    def handle_finished(self, exit_code, exit_status):
        """进程完成处理"""
        if self.is_cancelled:
            self.task.status = "已取消"
            self.finished_signal.emit(False, "下载已取消")
            self.cancelled_signal.emit()  # 发送取消完成信号
        elif exit_code == 0:
            self.task.status = "已完成"
            self.task.progress = 100
            self.task.end_time = datetime.now()
            self.finished_signal.emit(True, "下载完成")
        else:
            # 获取详细的错误信息
            error_detail = self.get_error_detail(exit_code)
            error_message = f"下载失败，错误码: {exit_code}\n{error_detail}"

            # 添加最后几行输出作为调试信息
            if self.output_lines:
                last_lines = "\n".join(self.output_lines[-5:])
                error_message += f"\n最后输出:\n{last_lines}"

            self.task.status = "失败"
            self.task.error_message = error_message
            self.task.end_time = datetime.now()
            self.finished_signal.emit(False, error_message)

        # 退出事件循环
        self.quit()

    def handle_error(self, error):
        """处理进程错误"""
        if self.is_cancelled:
            return

        error_map = {
            QProcess.FailedToStart: "进程启动失败",
            QProcess.Crashed: "进程崩溃",
            QProcess.Timedout: "进程超时",
            QProcess.WriteError: "写入错误",
            QProcess.ReadError: "读取错误",
            QProcess.UnknownError: "未知错误",
        }

        error_msg = error_map.get(error, f"进程错误: {error}")
        self.finished_signal.emit(False, error_msg)

    def parse_progress_line(self, line):
        """解析进度行"""
        # 多种进度格式匹配
        patterns = [
            r"\[download\]\s+(\d+\.?\d*)%.*?at\s+([\d.]+\s*[KMGT]?iB/s)",
            r"\[download\]\s+(\d+\.?\d*)%.*?at\s+([\d.]+\s*[KMGT]?B/s)",
            r"\[download\]\s+100%",
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                if pattern == patterns[2]:  # 100%完成
                    return 100, "完成"
                else:
                    percent = float(match.group(1))
                    speed = match.group(2)
                    return int(percent), speed

        # 检查下载完成
        if "100%" in line and "download" in line:
            return 100, "完成"

        return None

    def extract_filename(self, line):
        """从输出行提取文件名"""
        patterns = [
            r"\[download\] Destination: (.+)",
            r'\[Merger\] Merging formats into "(.+)"',
            r"\[info\] (.+): Downloading",
        ]

        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                filename = match.group(1)
                if filename and not self.task.filename:
                    # 提取纯文件名（去掉路径）
                    base_name = os.path.basename(filename)
                    self.task.filename = base_name
                    self.progress_signal.emit(0, "开始下载", self.task.filename)
                    return True
        return False

    def get_error_detail(self, return_code):
        """根据错误码返回详细的错误信息"""
        error_codes = {
            1: "一般错误 - 可能是网络问题、视频不可用或格式不支持",
            2: "命令行参数错误",
            3: "提取器错误 - 无法从该网站下载",
            4: "后处理错误 - 下载后处理失败",
            5: "网络错误 - 无法连接到网站",
            6: "认证错误 - 需要登录或会员",
            7: "提取错误 - 无法提取视频信息",
            8: "播放列表错误 - 播放列表处理失败",
            9: "地理限制 - 视频在您所在地区不可用",
            10: "会员限制 - 需要会员或订阅",
        }

        return error_codes.get(return_code, f"未知错误代码: {return_code}")

    def cancel(self):
        """取消下载 - 异步非阻塞版本"""
        if not self.isRunning() or self.is_cancelled:
            return

        self.is_cancelled = True

        # 立即发送取消日志，不等待进程结束
        print("正在取消下载...")

        if self.process and self.process.state() == QProcess.Running:
            # 先尝试优雅地终止
            self.process.terminate()

            # 使用定时器异步检查进程状态，避免阻塞
            self._cancellation_timer = QTimer()
            self._cancellation_timer.timeout.connect(self._checkCancellationStatus)
            self._cancellation_timer.start(100)  # 每100ms检查一次

            # 设置超时保护，5秒后强制终止
            QTimer.singleShot(5000, self._forceTerminateIfNeeded)
        else:
            # 如果没有进程在运行，直接发送取消完成信号
            self.cancelled_signal.emit()

    def _checkCancellationStatus(self):
        """检查取消状态"""
        if not self.process or self.process.state() != QProcess.Running:
            # 进程已结束
            if self._cancellation_timer:
                self._cancellation_timer.stop()
            self.cancelled_signal.emit()

    def _forceTerminateIfNeeded(self):
        """如果需要，强制终止进程"""
        if self.process and self.process.state() == QProcess.Running:
            print("强制终止下载进程...")
            self.process.kill()
            # 等待一小段时间让进程终止
            if self.process.waitForFinished(1000):
                print("下载进程已强制终止")
                self.cancelled_signal.emit()
            else:
                print("警告: 进程终止可能未完成")
                self.cancelled_signal.emit()
