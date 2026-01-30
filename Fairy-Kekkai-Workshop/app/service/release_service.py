# coding:utf-8

import os

from PySide6.QtCore import QObject, QProcess, Signal

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

    def build_api_command(self):
        """构建命令"""
        cmd = [cfg.get(cfg.apiPath)]

        # 视频路径
        cmd.extend(["--video_path", self.task.video_path])

        # 封面路径
        cmd.extend(["--cover", self.task.cover])

        # Cookie
        cmd.extend(["--SESSDATA", cfg.get(cfg.bilibiliBuvid3)])
        cmd.extend(["--BILI_JCT", cfg.get(cfg.bilibiliBiliJct)])
        cmd.extend(["--BUVID3", cfg.get(cfg.bilibiliBuvid3)])

        # 其他参数
        cmd.extend(["--tid", self.task.tid])
        cmd.extend(["--title", self.task.title])
        cmd.extend(["--desc", self.task.desc])
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
            print(f"执行上传命令: {' '.join(cmd)}")

            # 创建QProcess
            self.process = QProcess()

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
            print(e)

    def handle_stdout(self):
        """处理标准输出"""

    def handle_stderr(self):
        """处理标准错误输出"""
        pass

    def handle_finished(self, exit_code, exit_status):
        """处理上传完成"""

    def handle_error(self, error):
        """处理错误"""

    def cancel(self):
        """取消上传"""
        self.is_cancelled = True
        self.task.status = "已取消"
        self.finished_signal.emit(False, "上传已取消")
        self.cancelled_signal.emit()
        self.logger.info(f"上传已取消 -{self.task.video_path}-")
