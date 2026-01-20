# coding:utf-8
import os
import re
from datetime import datetime

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from ..common.config import cfg
from ..common.event_bus import event_bus


class FFmpegTask:
    """FFmpeg压制任务类"""

    _id_counter = 0

    def __init__(self, args):
        self.args = args
        self.input_file = args["video_path"]
        self.output_file = args["output_path"]
        self.status = "等待中"  # 等待中, 压制中, 已完成, 失败
        self.progress = 0
        self.error_message = ""
        self.duration = 0  # 视频总时长（秒）
        self.current_time = 0  # 当前处理时间（秒）

        FFmpegTask._id_counter += 1
        self.id = FFmpegTask._id_counter


class FFmpegProcess(QObject):
    """FFmpeg压制进程"""

    progress_signal = Signal(int, str, str)  # 进度百分比, 速度, 状态信息
    finished_signal = Signal(bool, str)  # 成功/失败, 消息
    cancelled_signal = Signal()  # 取消完成信号

    def __init__(self, task):
        super().__init__()
        self.task = task
        self.is_cancelled = False
        self.process = None
        self.output_lines = []  # 存储输出用于错误诊断
        self._cancellation_timer = None

    def build_ffmpeg_command(self):
        """根据配置构建 FFmpeg 命令"""
        cmd = [cfg.get(cfg.ffmpegPath)]

        # 硬件加速
        if cfg.ffmpegUseHardwareAcceleration.value:
            accelerator = cfg.ffmpegHardwareAccelerator.value
            if accelerator != "auto":
                cmd.extend(["-hwaccel", accelerator])

        # 输入视频
        cmd.extend(["-i", self.task.input_file])

        # 视频编码参数
        cmd.extend(
            [
                "-c:v",
                cfg.ffmpegVideoCodec.value,
                "-crf",
                str(cfg.ffmpegCrf.value),
                "-preset",
                cfg.ffmpegPreset.value,
            ]
        )

        # x264高级参数（如果启用）
        if cfg.ffmpegUseAdvanced.value:
            x264_params = [
                f"ref={cfg.ffmpegRefFrames.value}",
                f"bframes={cfg.ffmpegBFrames.value}",
                f"keyint={cfg.ffmpegKeyint.value}",
                f"minkeyint={cfg.ffmpegMinkeyint.value}",
                f"scenecut={cfg.ffmpegScenecut.value}",
                f"qcomp={cfg.ffmpegQcomp.value}",
                f"psy-rd={cfg.ffmpegPsyRd.value}",
                f"aq-mode={cfg.ffmpegAqMode.value}",
                f"aq-strength={cfg.ffmpegAqStrength.value}",
            ]
            cmd.extend(["-x264-params", ":".join(x264_params)])

        # 音频处理
        audio_mode = cfg.ffmpegAudioMode.value
        if audio_mode == "none":
            cmd.extend(["-an"])  # 无音频
        elif audio_mode == "copy":
            cmd.extend(["-c:a", "copy"])  # 直接复制
        elif audio_mode == "encode" or audio_mode == "auto":
            # 自动检测：如果输入文件没有音频流，则跳过音频编码
            if self._has_audio_stream():
                cmd.extend(
                    [
                        "-c:a",
                        cfg.ffmpegAudioCodec.value,
                        "-b:a",
                        cfg.ffmpegAudioBitrate.value,
                    ]
                )
            else:
                cmd.extend(["-an"])  # 无音频流，不编码音频

        # 视频缩放
        scale_option = cfg.ffmpegScale.value
        if scale_option != "none":
            if scale_option == "custom":
                if cfg.ffmpegCustomScale.value:
                    cmd.extend(["-vf", f"scale={cfg.ffmpegCustomScale.value}"])
            else:
                resolution_map = {
                    "720p": "1280:720",
                    "1080p": "1920:1080",
                    "1440p": "2560:1440",
                    "2160p": "3840:2160",
                }
                if scale_option in resolution_map:
                    cmd.extend(["-vf", f"scale={resolution_map[scale_option]}"])

        # 帧率设置
        fps_option = cfg.ffmpegFps.value
        if fps_option != "source":
            cmd.extend(["-r", fps_option])

        # 视频码率限制
        if cfg.ffmpegVideoBitrate.value:
            cmd.extend(["-b:v", cfg.ffmpegVideoBitrate.value])

        # 输出格式
        output_format = cfg.ffmpegOutputFormat.value
        if output_format:
            # 确保输出文件扩展名匹配格式
            base_name = os.path.splitext(self.task.output_file)[0]
            self.task.output_file = f"{base_name}.{output_format}"

        # 覆盖输出文件
        if cfg.ffmpegOverwriteOutput.value:
            cmd.append("-y")
        else:
            cmd.append("-n")

        # 添加进度报告
        cmd.extend(["-progress", "pipe:1", "-stats_period", "0.5"])

        # 输出文件 - 去掉引号
        cmd.append(self.task.output_file)

        return cmd

    def _has_audio_stream(self):
        """检测输入文件是否有音频流"""
        try:
            ffmpeg_cmd = [cfg.get(cfg.ffmpegPath), "-i", self.task.input_file]

            process = QProcess()
            process.start(ffmpeg_cmd[0], ffmpeg_cmd[1:])
            process.waitForFinished(5000)  # 5秒超时

            stderr_output = (
                process.readAllStandardError().data().decode("utf-8", errors="ignore")
            )

            # 从FFmpeg输出中解析时长信息
            # 查找格式: Audio:
            if "Audio:" in stderr_output:
                return True
            else:
                return False

        except Exception as e:
            print(f"使用FFmpeg获取音频流失败: {str(e)}")
            return False

    def _get_video_duration(self):
        """获取视频总时长"""
        try:
            ffmpeg_cmd = [cfg.get(cfg.ffmpegPath), "-i", self.task.input_file]

            process = QProcess()
            process.start(ffmpeg_cmd[0], ffmpeg_cmd[1:])
            process.waitForFinished(5000)  # 5秒超时

            stderr_output = (
                process.readAllStandardError().data().decode("utf-8", errors="ignore")
            )

            # 从FFmpeg输出中解析时长信息
            # 查找格式: Duration: 00:00:05.03
            duration_match = re.search(
                r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr_output
            )
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = float(duration_match.group(3))
                total_seconds = hours * 3600 + minutes * 60 + seconds
                self.task.duration = total_seconds
                print(f"获取视频时长成功: {self.task.duration}秒")
                return [True, None]
            else:
                return [False, "在FFmpeg输出中未找到时长信息"]

        except Exception as e:
            print(f"使用FFmpeg获取时长失败: {str(e)}")
            return [False, str(e)]

    def start(self):
        self.task.status = "压制中"
        self.task.start_time = datetime.now()

        try:
            # 获取ffmpeg.exe路径
            ffmpeg_path = cfg.get(cfg.ffmpegPath)
            if not os.path.exists(ffmpeg_path):
                self.finished_signal.emit(False, f"ffmpeg.exe不存在: {ffmpeg_path}")
                return

            # 确保输出目录存在
            output_dir = os.path.dirname(self.task.output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # 先获取视频总时长
            duration = self._get_video_duration()
            if not duration[0]:
                self.finished_signal.emit(False, duration[1])
                return

            # 构建命令
            cmd = self.build_ffmpeg_command()
            print(f"执行FFmpeg命令: {' '.join(cmd)}")

            # 创建QProcess
            self.process = QProcess()

            # 连接信号
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(self.handle_finished)
            self.process.errorOccurred.connect(self.handle_error)

            # 设置程序和工作目录
            self.process.setProgram(ffmpeg_path)
            self.process.setArguments(cmd[1:])  # 去掉程序路径本身

            # 启动进程
            self.process.start()

        except Exception as e:
            if not self.is_cancelled:
                error_msg = f"视频压制失败: {str(e)}"
                if self.output_lines:
                    error_msg += "\n输出日志:\n" + "\n".join(self.output_lines[-10:])

                self.task.status = "失败"
                self.task.error_message = error_msg
                self.task.end_time = datetime.now()
                self.finished_signal.emit(False, error_msg)
                event_bus.ffmpeg_finished_signal.emit(False, error_msg)

    def handle_stdout(self):
        """处理标准输出（进度信息）"""
        if not self.process:
            return

        data = (
            self.process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        )
        # 这里把data合并为一行发送
        event_bus.ffmpeg_update_signal.emit(str(self.task.id), data.replace("\n", "-"))
        lines = data.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            self.output_lines.append(line)

            if self.is_cancelled:
                return

            # 解析进度信息
            progress_info = self.parse_progress_line(line)
            if progress_info:
                key, value = progress_info
                if key == "out_time_ms" and value != "N/A":
                    # 将微秒转换为秒
                    current_time = int(value) / 1000000
                    self.task.current_time = current_time

                    # 计算进度百分比
                    if self.task.duration > 0:
                        progress = min(
                            100, int((current_time / self.task.duration) * 100)
                        )
                        self.task.progress = progress

                        # 计算剩余时间
                        elapsed = (
                            datetime.now() - self.task.start_time
                        ).total_seconds()
                        if progress > 0:
                            total_time = elapsed / (progress / 100)
                            remaining = total_time - elapsed
                            speed_info = f"剩余时间: {int(remaining)}秒"
                        else:
                            speed_info = "计算中..."

                        self.progress_signal.emit(
                            progress, speed_info, f"处理中: {progress}%"
                        )

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

            # 错误输出可能包含有用信息
            if "frame=" in line and "fps=" in line:
                # 这是FFmpeg的统计信息，可以解析帧率和速度
                fps_match = re.search(r"fps= *(\d+)", line)
                speed_match = re.search(r"speed= *([\d.]+)x", line)

                if fps_match and speed_match:
                    fps = fps_match.group(1)
                    speed = speed_match.group(1)
                    status_info = f"帧率: {fps} fps, 速度: {speed}x"
                    self.progress_signal.emit(
                        self.task.progress,
                        f"剩余时间: {self._get_remaining_time()}秒",
                        status_info,
                    )

    def parse_progress_line(self, line):
        """解析进度信息行"""
        # FFmpeg进度信息格式: key=value
        match = re.match(r"(\w+)=(.+)", line)
        if match:
            return match.group(1), match.group(2)
        return None

    def _get_remaining_time(self):
        """计算剩余时间"""
        if self.task.progress <= 0 or self.task.progress >= 100:
            return 0

        elapsed = (datetime.now() - self.task.start_time).total_seconds()
        total_estimated = elapsed / (self.task.progress / 100)
        return int(total_estimated - elapsed)

    def handle_finished(self, exit_code, exit_status):
        """进程完成处理"""
        if self.is_cancelled:
            self.task.status = "已取消"
            self.finished_signal.emit(False, "压制已取消")
            self.cancelled_signal.emit()
        elif exit_code == 0:
            self.task.status = "已完成"
            self.task.progress = 100
            self.task.end_time = datetime.now()

            # 检查输出文件是否存在
            if os.path.exists(self.task.output_file):
                file_size = os.path.getsize(self.task.output_file) / (1024 * 1024)  # MB
                success_msg = f"压制完成 - 文件大小: {file_size:.2f}MB"
            else:
                success_msg = "压制完成"

            self.finished_signal.emit(True, success_msg)
            event_bus.ffmpeg_finished_signal.emit(True, str(self.task.output_file))
        else:
            error_message = f"压制失败，错误码: {exit_code}"

            # 添加最后几行输出作为调试信息
            if self.output_lines:
                last_lines = "\n".join(self.output_lines[-5:])
                error_message += f"\n最后输出:\n{last_lines}"

            self.task.status = "失败"
            self.task.error_message = error_message
            self.task.end_time = datetime.now()
            self.finished_signal.emit(False, error_message)
            event_bus.ffmpeg_finished_signal.emit(False, error_message)

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

    def cancel(self):
        """取消压制 - 异步非阻塞版本"""
        if self.is_cancelled:
            return

        self.is_cancelled = True

        print("正在取消视频压制...")

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
            print("强制终止压制进程...")
            self.process.kill()
            # 等待一小段时间让进程终止
            if self.process.waitForFinished(1000):
                print("压制进程已强制终止")
                self.cancelled_signal.emit()
            else:
                print("警告: 进程终止可能未完成")
                self.cancelled_signal.emit()
