# coding:utf-8

import os

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, Signal

from ..common.config import cfg  # noqa
from ..common.event_bus import event_bus  # noqa
from ..common.logger import Logger


class ReleaseTask:
    """B站视频上传任务类"""

    _id_counter = 0

    def __init__(self, args):
        self.args = args
        self.input_file = args.get("video_path")
        self.video_path = args.get("video_path")
        self.cover = args.get("cover")
        self.tid = args.get("tid")
        self.title = args.get("title")
        self.desc = args.get("desc")
        self.tags = args.get("tags")
        self.original = args.get("original")
        self.source = args.get("source")
        self.recreate = args.get("recreate")
        self.delay_time = args.get("delay_time")
        self.status = "等待中"  # 等待中, 上传中, 已完成, 失败
        self.progress = 0
        self.error_message = ""

        ReleaseTask._id_counter += 1
        self.id = ReleaseTask._id_counter


class ReleaseProcess(QObject):
    """B站视频上传进程"""

    progress_signal = Signal(int, str, str)  # 进度百分比, 速度, 状态信息
    finished_signal = Signal(bool, str)  # 成功/失败, 消息
    cancelled_signal = Signal()  # 取消完成信号

    def __init__(self, task):
        super().__init__()
        self.logger = Logger("ReleaseProcess", "release")
        self.task: ReleaseTask = task
        self.is_cancelled = False
        self.output_lines = []  # 存储输出用于错误诊断

    def build_api_command(self):
        """构建命令"""
        cmd = [cfg.get(cfg.apiPath)]

        # 视频路径
        cmd.extend(["--video_path", self.task.video_path])

        # 封面路径
        cmd.extend(["--cover", self.task.cover])

        # Cookie
        cmd.extend(["--SESSDATA", cfg.get(cfg.bilibiliSessdata)])
        cmd.extend(["--BILI_JCT", cfg.get(cfg.bilibiliBiliJct)])
        cmd.extend(["--BUVID3", cfg.get(cfg.bilibiliBuvid3)])

        # 其他参数
        cmd.extend(["--tid", str(self.task.tid)])
        cmd.extend(["--title", self.task.title])
        cmd.extend(["--desc", self.task.desc]) if self.task.desc else None
        cmd.extend(["--tags", self.task.tags])
        cmd.extend(["--original", str(self.task.original)])
        cmd.extend(["--source", self.task.source])
        cmd.extend(["--recreate", str(self.task.recreate)])
        cmd.extend(["--delay_time", str(self.task.delay_time)])

        return cmd

    def start(self):
        """开始上传"""
        self.task.status = "上传中"
        try:
            # 获取upload-video.exe路径
            api_path = cfg.get(cfg.apiPath)
            if not os.path.exists(api_path):
                self.finished_signal.emit(False, f"upload-video.exe不存在: {api_path}")
                return

            # 构建命令
            cmd = self.build_api_command()
            print(f"执行上传命令: {' '.join(map(str, cmd))}")

            # 创建QProcess
            self.process = QProcess()

            env = QProcessEnvironment.systemEnvironment()

            self.process.setProcessEnvironment(env)

            working_dir = os.path.dirname(api_path)
            self.process.setWorkingDirectory(working_dir)

            # 连接信号
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(self.handle_finished)
            self.process.errorOccurred.connect(self.handle_error)

            # 设置程序和工作目录
            self.process.setProgram(api_path)
            self.process.setArguments(cmd[1:])  # 去掉程序路径本身

            # 启动进程
            self.process.start()

        except Exception as e:
            if not self.is_cancelled:
                error_msg = f"视频上传失败: {str(e)}"
                if self.output_lines:
                    error_msg += "\n输出日志:\n" + "\n".join(self.output_lines[-10:])

                self.task.status = "失败"
                self.task.error_message = error_msg

                self.finished_signal.emit(False, error_msg)
                event_bus.release_finished_signal.emit(False, error_msg)

    def handle_stdout(self):
        """处理标准输出"""
        try:
            # 尝试 UTF-8 解码，如果失败则使用系统默认编码
            data_bytes = self.process.readAllStandardOutput().data()
            try:
                data = data_bytes.decode("utf-8", errors="replace")
            except UnicodeDecodeError:
                # 如果 UTF-8 解码失败，使用系统默认编码
                import sys

                data = data_bytes.decode(sys.getdefaultencoding(), errors="replace")

            event_bus.ffmpeg_update_signal.emit(str(self.task.id), data)
            lines = data.split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                self.output_lines.append(line)
                self.parse_upload_progress(line)
        except Exception as e:
            self.logger.error(f"处理标准输出时出错: {e}")

    def handle_stderr(self):
        """处理标准错误输出"""
        try:
            data_bytes = self.process.readAllStandardError().data()
            try:
                data = data_bytes.decode("utf-8", errors="replace")
            except UnicodeDecodeError:
                # 如果 UTF-8 解码失败，使用系统默认编码
                import sys

                data = data_bytes.decode(sys.getdefaultencoding(), errors="replace")

            if data.strip():
                self.output_lines.append(f"[ERROR] {data.strip()}")
                self.parse_error_info(data)
        except Exception as e:
            self.logger.error(f"处理标准错误输出时出错: {e}")

    def handle_finished(self, exit_code, exit_status):
        """处理上传完成"""
        if self.is_cancelled:
            self.task.status = "已取消"
            self.finished_signal.emit(False, "上传已取消")
            self.cancelled_signal.emit()
            self.logger.info(f"上传已取消 -{self.task.input_file}-")
        elif exit_code == 0:
            self.task.status = "已完成"
            self.task.progress = 100
            self.logger.info(f"上传完成 -{self.task.input_file}-")

            success_msg = "上传完成"

            self.finished_signal.emit(True, success_msg)
            event_bus.release_finished_signal.emit(True, self.task.input_file)
        else:
            error_message = f"上传失败，错误码: {exit_code}"

            # 添加最后几行输出作为调试信息
            if self.output_lines:
                last_lines = "\n".join(self.output_lines[-5:])
                error_message += f"\n最后输出:\n{last_lines}"

            self.task.status = "失败"
            self.task.error_message = error_message
            self.finished_signal.emit(False, error_message)
            event_bus.release_finished_signal.emit(False, error_message)

    def parse_upload_progress(self, line):
        """解析上传进度信息"""
        try:
            # 尝试解析 JSON 格式的事件数据
            import json

            data = json.loads(line)

            event_type = data.get("event", "")

            if event_type == "PREUPLOAD":
                self.progress_signal.emit(5, "正在准备上传...", "准备上传")
                self.task.progress = 5

            elif event_type == "PREUPLOAD_FAILED":
                error_msg = data.get("error", "预上传失败")
                self.task.error_message = error_msg
                self.progress_signal.emit(0, "预上传失败", error_msg)

            elif event_type == "UPLOAD_START":
                self.progress_signal.emit(10, "开始上传视频...", "开始上传")
                self.task.progress = 10

            elif event_type == "UPLOAD_PROGRESS":
                progress = data.get("progress", 0)
                # 将上传进度映射到 10-90% 范围
                mapped_progress = 10 + int(progress * 0.8)
                speed = data.get("speed", "未知")
                self.progress_signal.emit(
                    mapped_progress, f"上传速度: {speed}", f"上传中 {progress}%"
                )
                self.task.progress = mapped_progress

            elif event_type == "UPLOAD_FAILED":
                error_msg = data.get("error", "上传失败")
                self.task.error_message = error_msg
                self.progress_signal.emit(0, "上传失败", error_msg)

            elif event_type == "UPLOAD_COMPLETED":
                self.progress_signal.emit(90, "视频上传完成", "正在提交信息...")
                self.task.progress = 90

            elif event_type == "SUBMIT_START":
                self.progress_signal.emit(95, "提交视频信息...", "提交信息")
                self.task.progress = 95

            elif event_type == "SUBMIT_FAILED":
                error_msg = data.get("error", "提交失败")
                self.task.error_message = error_msg
                self.progress_signal.emit(0, "提交失败", error_msg)

            elif event_type == "SUBMIT_SUCCESS":
                self.progress_signal.emit(100, "上传完成", "上传成功")
                self.task.progress = 100

        except (json.JSONDecodeError, AttributeError):
            # 如果不是 JSON 格式，尝试解析其他格式的进度信息
            if "progress" in line.lower() or "%" in line:
                # 提取进度百分比
                import re

                progress_match = re.search(r"(\d+)%", line)
                if progress_match:
                    progress = int(progress_match.group(1))
                    self.progress_signal.emit(progress, "上传中", line)
                    self.task.progress = progress
            elif "error" in line.lower() or "fail" in line.lower():
                self.task.error_message = line
                self.progress_signal.emit(0, "错误", line)

    def parse_error_info(self, error_data):
        """解析错误信息"""
        if "cookie" in error_data.lower():
            self.task.error_message = "Cookie 配置错误或已过期"
        elif "网络" in error_data or "network" in error_data.lower():
            self.task.error_message = "网络连接错误"
        elif "文件" in error_data or "file" in error_data.lower():
            self.task.error_message = "视频文件不存在或格式错误"

    def handle_error(self, error):
        """处理错误"""
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

        print(f"上传进程错误: {error}")

    def cancel(self):
        """取消上传"""
        self.is_cancelled = True
        self.task.status = "已取消"
        self.finished_signal.emit(False, "上传已取消")
        self.cancelled_signal.emit()
        self.logger.info(f"上传已取消 -{self.task.video_path}-")
