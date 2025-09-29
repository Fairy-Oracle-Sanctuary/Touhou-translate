# models/events.py
from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum

class DownloadType(Enum):
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"

class NotificationType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class DownloadRequest:
    type: DownloadType
    url: str
    save_path: str
    quality: str = "best"
    project_name: str = ""
    episode_num: int = 0
    metadata: Optional[Dict] = None

@dataclass
class Notification:
    type: NotificationType
    title: str
    message: str
    duration: int = 3000

# 事件构建工具函数
class EventBuilder:    
    @staticmethod
    def download_video(url: str, save_path: str, quality: str = "best", **kwargs) -> dict:
        return {
            "type": "video",
            "url": url,
            "save_path": save_path,
            "quality": quality,
            **kwargs
        }
    
    @staticmethod
    def download_image(url: str, save_path: str) -> dict:
        return {
            "type": "image", 
            "url": url,
            "save_path": save_path
        }
    
    @staticmethod
    def notification_success(title: str, message: str) -> dict:
        return {
            "type": "success",
            "title": title,
            "message": message
        }
    
    @staticmethod
    def navigation_to_download() -> dict:
        return {
            "target": "download",
            "data": {}
        }