# coding:utf-8
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from bilibili_api import Credential, sync, video_uploader

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.logger import Logger


class ReleaseTask:
    """B站视频上传任务类"""

    _id_counter = 0

    def __init__(self, args):
        self.args = args
        self.video_path = args["video_path"]
        self.cover_path = args.get("cover_path", "")
        self.title = args["title"]
        self.description = args["description"]
        self.tags = args["tags"]
        self.tid = args["tid"]
        self.status = "等待中"  # 等待中, 上传中, 已完成, 失败
        self.progress = 0
        self.error_message = ""
        self.bvid = ""
        self.aid = ""

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
        self.task = task
        self.is_cancelled = False

    async def upload_video(self):
        """异步上传视频"""
        try:
            # 获取 B 站凭证
            sessdata = cfg.get(cfg.bilibiliSessdata)
            bili_jct = cfg.get(cfg.bilibiliBiliJct)
            buvid3 = cfg.get(cfg.bilibiliBuvid3)

            if not all([sessdata, bili_jct, buvid3]):
                error_msg = "B站凭证未配置，请在设置中填写"
                self.finished_signal.emit(False, error_msg)
                return

            credential = Credential(
                sessdata=sessdata,
                bili_jct=bili_jct,
                buvid3=buvid3
            )

            # 创建视频元数据
            vu_meta = video_uploader.VideoMeta(
                tid=self.task.tid,
                title=self.task.title,
                tags=self.task.tags.split(","),
                desc=self.task.description,
                cover=self.task.cover_path if self.task.cover_path else None,
                original=True,
                no_reprint=True
            )

            # 验证元数据
            try:
                await vu_meta.verify(credential=credential)
            except Exception as e:
                error_msg = f"元数据验证失败: {str(e)}"
                self.finished_signal.emit(False, error_msg)
                return

            # 创建视频页面
            page = video_uploader.VideoUploaderPage(
                path=self.task.video_path,
                title=self.task.title
            )

            # 创建上传器
            uploader = video_uploader.VideoUploader(
                [page], vu_meta, credential
            )

            # 注册事件回调
            @uploader.on("__ALL__")
            async def ev(data):
                if self.is_cancelled:
                    return

                # 解析事件数据
                if isinstance(data, dict):
                    event = data.get("event")
                    progress = data.get("progress", 0)
                    message = data.get("message", "")

                    # 更新任务状态
                    if event == "UPLOAD_INIT":
                        self.task.status = "上传中"
                        self.task.progress = 0
                        self.progress_signal.emit(0, "", "初始化上传...")
                    elif event == "UPLOAD_PROGRESS":
                        self.task.progress = progress
                        self.progress_signal.emit(progress, "", f"上传中: {progress}%")
                    elif event == "UPLOAD_FINISH":
                        self.task.progress = 100
                        self.progress_signal.emit(100, "", "上传完成，处理中...")
                    elif event == "SUBMITTING":
                        self.task.status = "提交中"
                        self.progress_signal.emit(100, "", "提交审核中...")
                    elif event == "COMPLETED":
                        self.task.status = "已完成"
                        self.task.bvid = data.get("bvid", "")
                        self.task.aid = data.get("aid", "")
                        success_msg = f"上传成功！BVID: {self.task.bvid}"
                        self.finished_signal.emit(True, success_msg)
                        event_bus.release_finished_signal.emit(True, success_msg)
                        return
                    elif event == "FAILED":
                        error_msg = f"上传失败: {message}"
                        self.task.status = "失败"
                        self.task.error_message = error_msg
                        self.finished_signal.emit(False, error_msg)
                        event_bus.release_finished_signal.emit(False, error_msg)
                        return

            # 开始上传
            self.task.status = "上传中"
            self.task.start_time = datetime.now()
            self.logger.info(f"开始上传视频: -{self.task.video_path}-")

            await uploader.start()

        except Exception as e:
            if not self.is_cancelled:
                error_msg = f"上传失败: {str(e)}"
                self.task.status = "失败"
                self.task.error_message = error_msg
                self.task.end_time = datetime.now()
                self.finished_signal.emit(False, error_msg)
                event_bus.release_finished_signal.emit(False, error_msg)

    def start(self):
        """开始上传"""
        sync(self.upload_video())

    def cancel(self):
        """取消上传"""
        self.is_cancelled = True
        self.task.status = "已取消"
        self.finished_signal.emit(False, "上传已取消")
        self.cancelled_signal.emit()
        self.logger.info(f"上传已取消 -{self.task.video_path}-")
