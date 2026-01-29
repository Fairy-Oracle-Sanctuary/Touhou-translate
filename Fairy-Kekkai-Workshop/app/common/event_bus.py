# core/event_bus.py
from PySide6.QtCore import QObject, Signal


class GlobalEventBus(QObject):
    """全局事件总线，负责组件间通信"""

    # 从主页切换页面
    switchToSampleCard = Signal(str, int)

    # 打开URL
    openUrl = Signal(str)

    # 检查更新
    checkUpdateSig = Signal()

    # 通知服务
    notification_service = None

    # 窗口
    project_interface = None
    project_detail_interface = None

    # 下载相关事件
    download_requested = Signal(
        dict
    )  # {"type": "video", "url": "...", "path": "...", "quality": "..."}
    download_progress = Signal(
        dict
    )  # {"task_id": 1, "progress": 50, "status": "downloading"}
    download_finished_signal = Signal(bool, str)
    download_list_finished_signal = Signal(bool, str)
    # OCR相关事件
    ocr_finished_signal = Signal(bool, str)
    add_video_signal = Signal(str)

    # 翻译相关事件
    translate_finished_signal = Signal(bool, list)
    translate_requested = Signal(str, str)
    translate_update_signal = Signal(
        str, str
    )  # 实时翻译更新信号 (task_id, content_chunk)

    # 压制相关事件
    ffmpeg_finished_signal = Signal(bool, str)
    ffmpeg_requested = Signal(str, str)
    ffmpeg_update_signal = Signal(
        str, str
    )  # 实时ffmpeg输出更新信号 (task_id, output_chunk)

    # B站上传相关事件
    release_finished_signal = Signal(bool, str)
    release_requested = Signal(str)

    # 项目相关事件
    project_created = Signal(dict)  # {"name": "...", "path": "..."}
    project_deleted = Signal(dict)  # {"path": "..."}
    project_updated = Signal(dict)  # {"path": "...", "changes": {...}}

    # 文件操作事件
    fileDeletedSignal = Signal()
    file_operation = Signal(
        dict
    )  # {"action": "delete", "path": "...", "success": True}

    # 界面导航事件
    navigation_requested = Signal(dict)  # {"target": "download", "data": {...}}

    # 日志窗口事件
    log_window_closed = Signal()
    log_message = Signal(str, str)  # (log_name, message)

    # 错误和消息事件
    notification = Signal(dict)  # {"type": "success", "title": "...", "message": "..."}


# 创建全局单例
event_bus = GlobalEventBus()
