# services/notification_service.py
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets import InfoBar, InfoBarPosition


class NotificationService(QObject):
    """统一的通知服务"""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.default_parent = parent
        self.default_duration = 3000  # 默认显示3秒
        self.position = InfoBarPosition.TOP_RIGHT

    def show_success(
        self, title: str, content: str, parent: QWidget = None, duration: int = None
    ):
        """显示成功通知"""
        self._show_notification("success", title, content, parent, duration)

    def show_error(
        self, title: str, content: str, parent: QWidget = None, duration: int = None
    ):
        """显示错误通知"""
        self._show_notification(
            "error", title, content, parent, duration or 5000
        )  # 错误显示5秒

    def show_warning(
        self, title: str, content: str, parent: QWidget = None, duration: int = None
    ):
        """显示警告通知"""
        self._show_notification("warning", title, content, parent, duration)

    def show_info(
        self, title: str, content: str, parent: QWidget = None, duration: int = None
    ):
        """显示信息通知"""
        self._show_notification("info", title, content, parent, duration)

    def _show_notification(
        self,
        type: str,
        title: str,
        content: str,
        parent: QWidget = None,
        duration: int = None,
    ):
        """显示通知的内部方法"""
        parent_widget = parent or self.default_parent
        if not parent_widget:
            # 如果没有指定父组件，尝试查找可用的窗口
            parent_widget = self._find_parent_window()

        if not parent_widget:
            # 如果还是找不到父窗口，使用控制台输出作为后备
            print(f"[{type.upper()}] {title}: {content}")
            return

        # 显示 InfoBar
        if type == "success":
            InfoBar.success(
                title=title,
                content=content,
                parent=parent_widget,
                duration=duration or self.default_duration,
                position=self.position,
            )
        elif type == "error":
            InfoBar.error(
                title=title,
                content=content,
                parent=parent_widget,
                duration=duration or self.default_duration,
                position=self.position,
            )
        elif type == "warning":
            InfoBar.warning(
                title=title,
                content=content,
                parent=parent_widget,
                duration=duration or self.default_duration,
                position=self.position,
            )
        else:  # info
            InfoBar.info(
                title=title,
                content=content,
                parent=parent_widget,
                duration=duration or self.default_duration,
                position=self.position,
            )

    def _find_parent_window(self) -> QWidget:
        """查找可用的父窗口"""
        for widget in QApplication.topLevelWidgets():
            if widget.isWindow() and widget.isVisible():
                return widget
        return None

    def set_default_parent(self, parent: QWidget):
        """设置默认父组件"""
        self.default_parent = parent

    def set_default_duration(self, duration: int):
        """设置默认显示时间"""
        self.default_duration = duration

    def set_position(self, position: InfoBarPosition):
        """设置通知位置"""
        self.position = position
