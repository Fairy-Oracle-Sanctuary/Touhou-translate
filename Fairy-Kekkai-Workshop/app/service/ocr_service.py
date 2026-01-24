# ocr_service.py

import os

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.logger import Logger


class OCRTask:
    """OCR任务类"""

    _id_counter = 0

    def __init__(self, args):
        self.args = args
        self.status = "等待中"  # 等待中, 处理中, 已完成, 失败
        self.progress = 0
        self.error_message = ""
        self.input_file = args.get("video_path")
        self.output_file = args.get("file_path")
        self.temp_dir = args.get("temp_dir")

        OCRTask._id_counter += 1
        self.id = OCRTask._id_counter


class OCRProcess(QObject):
    """OCR处理进程"""

    progress_signal = Signal(int, int, int)  # 进度百分比, 当前帧, 总帧数
    finished_signal = Signal(bool, str)  # 成功/失败, 消息
    log_signal = Signal(str, bool, bool)  # 日志信息
    print_signal = Signal(str)  # 捕获print输出
    cancelled_signal = Signal()  # 取消完成信号

    def __init__(self, task: OCRTask):
        super().__init__()
        self.logger = Logger("OCRProcess")
        self.task = task
        self.is_cancelled = False
        self.process = None
        self.output_lines = []  # 存储输出用于错误诊断
        self._cancellation_timer = None

    def build_ocr_command(self):
        """根据配置构建 ocr 命令"""
        args = self.task.args

        cmd_path = cfg.get(cfg.videocrCliPath)

        # 构建命令参数
        cmd_args = []

        # 添加参数
        cmd_args.extend(["--video_path", args["video_path"]])
        cmd_args.extend(["--output", args["file_path"]])
        cmd_args.extend(["--temp_dir", args["temp_dir"]])
        cmd_args.extend(["--lang", args["lang"]])
        cmd_args.extend(["--time_start", args["time_start"]])
        if args["time_end"]:
            cmd_args.extend(["--time_end", args["time_end"]])
        cmd_args.extend(["--conf_threshold", str(args["conf_threshold"])])
        cmd_args.extend(["--sim_threshold", str(args["sim_threshold"])])
        cmd_args.extend(["--max_merge_gap", str(args["max_merge_gap_sec"])])
        cmd_args.extend(["--use_fullframe", str(args["use_fullframe"]).lower()])
        cmd_args.extend(["--use_gpu", str(args["use_gpu"]).lower()])
        cmd_args.extend(["--use_angle_cls", str(args["use_angle_cls"]).lower()])
        cmd_args.extend(["--use_server_model", str(args["use_server_model"]).lower()])
        cmd_args.extend(["--subtitle_position", args["subtitle_position"]])
        cmd_args.extend(["--frames_to_skip", str(args["frames_to_skip"])])
        cmd_args.extend(["--ocr_image_max_width", str(args["ocr_image_max_width"])])
        cmd_args.extend(["--post_processing", str(args["post_processing"]).lower()])
        cmd_args.extend(
            ["--min_subtitle_duration", str(args["min_subtitle_duration_sec"])]
        )

        # 处理paddleocr_path参数
        if "paddleocr_path" in args and args["paddleocr_path"]:
            cmd_args.extend(["--paddleocr_path", args["paddleocr_path"]])

        # 处理supportFilesPath参数
        if "supportFilesPath" in args and args["supportFilesPath"]:
            cmd_args.extend(["--supportFilesPath", args["supportFilesPath"]])

        # 处理crop_zones参数
        if args["crop_zones"]:
            # 由于命令行无法直接传递复杂结构，这里暂时不处理crop_zones
            pass

        return cmd_path, cmd_args

    def start(self):
        """启动OCR处理进程"""
        self.task.status = "提取中"

        try:
            # 获取videocr-cli.exe路径
            cmd_path, cmd_args = self.build_ocr_command()

            if not os.path.exists(cmd_path):
                error_msg = f"videocr-cli.exe不存在: {cmd_path}"
                self.task.status = "失败"
                self.task.error_message = error_msg
                self.finished_signal.emit(False, error_msg)
                event_bus.ocr_finished_signal.emit(False, error_msg)
                return

            # 确保输出目录存在
            output_dir = os.path.dirname(self.task.output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            print(f"执行OCR命令: {cmd_path} {' '.join(cmd_args)}")

            # 创建QProcess
            self.process = QProcess()

            # 连接信号
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(self.handle_finished)
            self.process.errorOccurred.connect(self.handle_error)

            # 设置程序和参数
            self.process.setProgram(cmd_path)
            self.process.setArguments(cmd_args)

            # 启动进程
            self.process.start()

        except Exception as e:
            if not self.is_cancelled:
                error_msg = f"OCR处理失败: {str(e)}"
                print(error_msg)
                self.task.status = "失败"
                self.task.error_message = error_msg
                self.finished_signal.emit(False, error_msg)
                event_bus.ocr_finished_signal.emit(False, error_msg)
                self.logger.error(
                    f"OCR处理失败: -{self.task.input_file}- 错误信息: {str(e)}"
                )

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

            # 发射print信号，由videocr_task_interface.py中的onPrintOutput处理
            self.print_signal.emit(line)

    def handle_stderr(self):
        """处理标准错误"""
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

            # 发射print信号，由videocr_task_interface.py中的onPrintOutput处理
            self.print_signal.emit(line)

    def handle_finished(self, exit_code, exit_status):
        """进程完成处理"""
        if self.is_cancelled:
            self.task.status = "已取消"
            self.finished_signal.emit(False, "OCR处理已取消")
            self.cancelled_signal.emit()
            self.logger.info(f"OCR处理已取消: -{self.task.input_file}-")
        elif exit_code == 0:
            self.task.status = "已完成"
            self.task.progress = 100

            # 检查输出文件是否存在
            if os.path.exists(self.task.output_file):
                file_size = os.path.getsize(self.task.output_file) / (1024 * 1024)  # MB
                success_msg = f"OCR处理完成 - 文件大小: {file_size:.2f}MB"
            else:
                success_msg = "OCR处理完成"

            self.finished_signal.emit(True, success_msg)
            self.log_signal.emit("OCR处理完成\n", False, False)
            event_bus.ocr_finished_signal.emit(True, str(self.task.output_file))
            self.logger.info(
                f"OCR处理完成: -{self.task.input_file}- 输出文件: {self.task.output_file}"
            )
        else:
            error_message = f"OCR处理失败，错误码: {exit_code}"

            # 添加最后几行输出作为调试信息
            if self.output_lines:
                last_lines = "\n".join(self.output_lines[-5:])
                error_message += f"\n最后输出:\n{last_lines}"

            self.task.status = "失败"
            self.task.error_message = error_message
            self.finished_signal.emit(False, error_message)
            self.log_signal.emit(f"OCR处理失败:\n{error_message}\n", False, False)
            event_bus.ocr_finished_signal.emit(False, error_message)
            self.logger.error(
                f"OCR处理失败: -{self.task.input_file}- 错误信息: {error_message}"
            )

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
        """取消OCR处理 - 异步非阻塞版本"""
        if self.is_cancelled:
            return

        self.is_cancelled = True

        # 立即发送取消日志，不等待进程结束
        self.log_signal.emit("正在取消OCR处理...\n", False, False)

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
            self.log_signal.emit("强制终止OCR处理...", False, False)
            self.process.kill()
            # 等待一小段时间让进程终止
            if self.process.waitForFinished(1000):
                self.log_signal.emit("OCR处理已强制终止", False, False)
                self.cancelled_signal.emit()
            else:
                self.log_signal.emit("警告: 进程终止可能未完成", True, False)
                self.cancelled_signal.emit()
