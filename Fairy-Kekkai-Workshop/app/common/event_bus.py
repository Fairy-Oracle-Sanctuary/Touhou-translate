# core/event_bus.py
from PySide6.QtCore import QObject, Signal
from typing import Any, Dict, Optional

class GlobalEventBus(QObject):
    """全局事件总线，负责组件间通信"""
    #检查更新
    checkUpdateSig = Signal()
    
    # 通知服务
    notification_service = None
    
    # 窗口
    project_interface = None
    project_detail_interface = None

    # 下载相关事件
    download_requested = Signal(dict)  # {"type": "video", "url": "...", "path": "...", "quality": "..."}
    download_progress = Signal(dict)   # {"task_id": 1, "progress": 50, "status": "downloading"}
    download_finished = Signal(dict)   # {"task_id": 1, "success": True, "file_path": "..."}
    
    # 项目相关事件
    project_created = Signal(dict)     # {"name": "...", "path": "..."}
    project_deleted = Signal(dict)     # {"path": "..."}
    project_updated = Signal(dict)     # {"path": "...", "changes": {...}}
    
    # 文件操作事件
    fileDeletedSignal = Signal()
    file_operation = Signal(dict)      # {"action": "delete", "path": "...", "success": True}
    
    # 界面导航事件
    navigation_requested = Signal(dict) # {"target": "download", "data": {...}}
    
    # 错误和消息事件
    notification = Signal(dict)        # {"type": "success", "title": "...", "message": "..."}

# 创建全局单例
event_bus = GlobalEventBus()