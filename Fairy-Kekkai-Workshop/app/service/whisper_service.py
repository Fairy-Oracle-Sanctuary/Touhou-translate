# coding:utf-8
import os
import re
from datetime import datetime

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.logger import Logger


def get_whisper_cli_path():
    """获取 whisper main.exe 路径"""
    custom_path = cfg.get(cfg.whisperCliPath)
    if custom_path and os.path.exists(custom_path):
        return custom_path

    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "tools",
        "whisper",
        "main.exe",
    )


class WhisperTask:
    """Whisper转录任务类"""

    _id_counter = 0

    def __init__(self, args):
        self.args = args
        self.input_file = args["video_path"]
        self.output_file = args["output_path"]
        self.model_file = args.get("model", "")
        self.language = args.get("language", "")
        self.format = args.get("format", "srt")
        self.gpu = args.get("gpu", "")
        self.status = "等待中"  # 等待中, 转录中, 已完成, 失败
        self.progress = 0
        self.error_message = ""
        self.output_history = ""  # 存储完整输出历史

        WhisperTask._id_counter += 1
        self.id = WhisperTask._id_counter


class WhisperProcess(QObject):
    """Whisper转录进程"""

    progress_signal = Signal(int, str, str)  # 进度百分比, 速度, 状态信息
    finished_signal = Signal(bool, str)  # 成功/失败, 消息
    cancelled_signal = Signal()  # 取消完成信号
    log_signal = Signal(str, bool, bool)  # 日志消息, 是否错误, 是否刷新

    def __init__(self, task):
        super().__init__()
        self.logger = Logger("WhisperProcess", "whisper")
        self.task = task
        self.is_cancelled = False
        self.process = None
        self.output_lines = []  # 存储输出用于错误诊断
        self._cancellation_timer = None

    def __del__(self):
        """析构时确保子进程被终止"""
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
            self.process.waitForFinished(1000)

    @staticmethod
    def _activate_as_current(output_file: str):
        """将提取结果复制为 原文.srt（作为当前活动原文）"""
        import shutil

        parent_dir = os.path.dirname(output_file)
        current_file = os.path.join(parent_dir, "原文.srt")
        try:
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                shutil.copy2(output_file, current_file)
        except Exception:
            pass

    def build_whisper_command(self):
        """构建 Whisper main.exe 命令"""
        cli_path = get_whisper_cli_path()

        cmd = [cli_path]
        cmd.extend(["-f", self.task.input_file])

        # 仅当指定了具体语言时才传 -l；"auto"/空 时让 Whisper 自动检测
        if self.task.language and self.task.language != "auto":
            cmd.extend(["-l", self.task.language])

        # 输出格式
        if self.task.format == "srt":
            cmd.append("-osrt")
        elif self.task.format == "txt":
            cmd.append("-otxt")
        elif self.task.format == "vtt":
            cmd.append("-ovtt")

        # 当 GPU 不为空时添加 GPU 参数（包括"自动检测"）
        if self.task.gpu:
            cmd.append("-gpu")

        # 模型路径
        if self.task.model_file:
            cmd.extend(["-m", self.task.model_file])

        return cmd

    def _get_video_duration(self):
        """获取视频总时长（秒）"""
        try:
            ffmpeg_path = cfg.get(cfg.ffmpegPath)
            if not ffmpeg_path or not os.path.exists(ffmpeg_path):
                return 0

            process = QProcess()
            process.start(ffmpeg_path, ["-i", self.task.input_file])
            process.waitForFinished(5000)

            stderr_output = (
                process.readAllStandardError().data().decode("utf-8", errors="ignore")
            )

            # 从 FFmpeg 输出中解析时长信息: Duration: 00:00:05.03
            duration_match = re.search(
                r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr_output
            )
            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = float(duration_match.group(3))
                total_seconds = hours * 3600 + minutes * 60 + seconds
                self.logger.info(f"获取视频时长成功: {total_seconds}秒")
                return total_seconds

        except Exception as e:
            self.logger.error(f"获取视频时长失败: {str(e)}")
        return 0

    @staticmethod
    def _timestamp_to_seconds(timestamp_str):
        """将时间戳字符串转换为秒数
        格式: 00:00:01.480 或 00:01:30
        """
        try:
            parts = timestamp_str.strip().split(":")
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
        except (ValueError, IndexError):
            pass
        return 0

    def start(self):
        self.task.status = "识别中"
        self.task.start_time = datetime.now()

        try:
            cli_path = get_whisper_cli_path()

            if not os.path.exists(cli_path):
                self.finished_signal.emit(False, f"main.exe 不存在: {cli_path}")
                return

            if self.task.model_file and not os.path.exists(self.task.model_file):
                self.finished_signal.emit(
                    False, f"模型文件不存在: {self.task.model_file}"
                )
                return

            output_dir = os.path.dirname(self.task.output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # 获取视频总时长用于进度计算
            self.task.duration = self._get_video_duration()

            cmd = self.build_whisper_command()
            try:
                print(f"执行Whisper命令: {' '.join(cmd)}")
            except UnicodeEncodeError:
                pass

            self.process = QProcess()

            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(self.handle_finished)
            self.process.errorOccurred.connect(self.handle_error)

            self.process.setProgram(cli_path)
            self.process.setArguments(cmd[1:])

            # 设置工作目录为 whisper 目录，方便加载相对路径的模型
            work_dir = os.path.dirname(cli_path)
            self.process.setWorkingDirectory(work_dir)

            # 启动进程
            self.process.start()

        except Exception as e:
            if not self.is_cancelled:
                error_msg = f"语音转录失败: {str(e)}"
                if self.output_lines:
                    error_msg += "\n输出日志:\n" + "\n".join(self.output_lines[-10:])

                self.task.status = "失败"
                self.task.error_message = error_msg
                self.task.end_time = datetime.now()
                self.finished_signal.emit(False, error_msg)
                event_bus.whisper_finished_signal.emit(False, error_msg)

    def handle_stdout(self):
        """处理标准输出 - 解析时间戳计算进度"""
        if not self.process:
            return

        data = (
            self.process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        )
        # 存储到任务输出历史
        self.task.output_history += data
        event_bus.whisper_update_signal.emit(str(self.task.id), data.replace("\n", "-"))
        lines = data.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            self.output_lines.append(line)
            self.logger.info(f"Whisper输出: {line}")

            if self.is_cancelled:
                return

            # 解析时间戳行计算进度
            # 格式: [00:00:01.480 --> 00:00:03.200]  xxxx
            timestamp_match = re.search(
                r"\[(\d+:\d+:\d+\.\d+)\s*-->\s*(\d+:\d+:\d+\.\d+)\]", line
            )
            if timestamp_match:
                end_time_str = timestamp_match.group(2)
                current_seconds = self._timestamp_to_seconds(end_time_str)

                if self.task.duration > 0 and current_seconds > 0:
                    progress = min(
                        100, int((current_seconds / self.task.duration) * 100)
                    )
                    self.task.progress = progress

                    # 计算剩余时间
                    elapsed = (datetime.now() - self.task.start_time).total_seconds()
                    if progress > 0:
                        total_time = elapsed / (progress / 100)
                        remaining = int(total_time - elapsed)
                        speed_info = f"剩余时间: {remaining}秒"
                    else:
                        speed_info = "计算中..."

                    self.progress_signal.emit(
                        progress, speed_info, f"转录中: {progress}%"
                    )
                    self.logger.info(f"进度更新: {progress}% (时间: {end_time_str})")

            # 检测完成标志
            if "LoadModel" in line and "RunComplete" in line:
                self.task.progress = 100
                self.progress_signal.emit(100, "完成", "转录完成")

    def handle_stderr(self):
        """处理标准错误输出 - main.exe 使用 UseStandardError，大部分输出在此"""
        if not self.process:
            return

        data = (
            self.process.readAllStandardError().data().decode("utf-8", errors="ignore")
        )
        # 同样发送到实时更新信号，让对话框可以显示
        event_bus.whisper_update_signal.emit(str(self.task.id), data.replace("\n", "-"))
        lines = data.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            self.output_lines.append(line)
            self.logger.info(f"Whisper: {line}")

            # 检测错误关键词
            if "error" in line.lower() or "failed" in line.lower() or "错误" in line:
                self.logger.error(f"Whisper错误: {line}")

    def handle_finished(self, exit_code, exit_status):
        """进程完成处理"""
        if self.is_cancelled:
            self.task.status = "已取消"
            self.finished_signal.emit(False, "转录已取消")
            self.cancelled_signal.emit()
            self.logger.info(f"转录已取消 -{self.task.input_file}-")
        elif exit_code == 0:
            self.task.status = "已完成"
            self.task.progress = 100
            self.task.end_time = datetime.now()
            self.logger.info(f"转录完成 -{self.task.input_file}-")

            # Whisper CLI 没有 -o 参数，输出自动生成在输入文件旁，需要重命名
            input_dir = os.path.dirname(self.task.input_file)
            input_stem = os.path.splitext(os.path.basename(self.task.input_file))[0]
            possible_outputs = [
                os.path.join(input_dir, f"{input_stem}.mp4.srt"),
                os.path.join(input_dir, f"{input_stem}.srt"),
            ]
            for candidate in possible_outputs:
                if os.path.exists(candidate) and candidate != self.task.output_file:
                    try:
                        os.replace(candidate, self.task.output_file)
                        break
                    except Exception:
                        pass

            # 检查输出文件是否存在
            if os.path.exists(self.task.output_file):
                file_size = os.path.getsize(self.task.output_file) / 1024  # KB
                success_msg = f"转录完成 - 文件大小: {file_size:.2f}KB"
            else:
                success_msg = "转录完成"

            self.finished_signal.emit(True, success_msg)
            # 自动复制到 原文.srt（设为当前活动原文）
            WhisperProcess._activate_as_current(self.task.output_file)
            event_bus.whisper_finished_signal.emit(True, str(self.task.output_file))
        else:
            error_message = f"转录失败，错误码: {exit_code}"

            # 添加最后几行输出作为调试信息
            if self.output_lines:
                last_lines = "\n".join(self.output_lines[-5:])
                error_message += f"\n最后输出:\n{last_lines}"

            self.task.status = "失败"
            self.task.error_message = error_message
            self.task.end_time = datetime.now()
            self.finished_signal.emit(False, error_message)
            event_bus.whisper_finished_signal.emit(False, error_message)

    def handle_error(self, error):
        """处理进程错误"""
        if self.is_cancelled:
            return

        error_map = {
            QProcess.ProcessError.FailedToStart: "进程启动失败",
            QProcess.ProcessError.Crashed: "进程崩溃",
            QProcess.ProcessError.Timedout: "进程超时",
            QProcess.ProcessError.WriteError: "写入错误",
            QProcess.ProcessError.ReadError: "读取错误",
            QProcess.ProcessError.UnknownError: "未知错误",
        }

        error_msg = error_map.get(error, f"进程错误: {error}")
        self.finished_signal.emit(False, error_msg)

    def cancel(self):
        """取消转录"""
        if self.is_cancelled:
            return

        self.is_cancelled = True

        try:
            print("正在取消语音转录...")
        except UnicodeEncodeError:
            pass

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
            try:
                print("强制终止转录进程...")
            except UnicodeEncodeError:
                pass
            self.process.kill()
            # 等待一小段时间让进程终止
            if self.process.waitForFinished(1000):
                try:
                    print("转录进程已强制终止")
                except UnicodeEncodeError:
                    pass
                self.cancelled_signal.emit()
            else:
                try:
                    print("警告: 进程终止可能未完成")
                except UnicodeEncodeError:
                    pass
                self.cancelled_signal.emit()
