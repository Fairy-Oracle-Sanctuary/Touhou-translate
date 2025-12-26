from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import Pivot


class BaseStackedInterfaces(QWidget):
    """基础堆叠界面"""

    def __init__(
        self,
        parent=None,
        main_interface_class=None,
        task_interface_class=None,
        setting_interface_class=None,
        interface_name=None,
    ):
        super().__init__(parent)
        self.main_interface_class = main_interface_class
        self.task_interface_class = task_interface_class
        self.setting_interface_class = setting_interface_class
        self.interface_name = interface_name

        self.pivot = Pivot(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        self._init_interfaces()
        self._setup_layout()
        self._connect_signals()

        self.resize(780, 800)
        self.setObjectName(f"{interface_name}StackedInterfaces")

    def _init_interfaces(self):
        """初始化界面"""
        self.mainInterface = self.main_interface_class()

        # 添加标签页
        self.addSubInterface(
            self.mainInterface, "mainInterface", f"{self.interface_name}"
        )

        # 只有当任务界面类存在时才创建并添加
        if self.task_interface_class:
            self.taskInterface = self.task_interface_class()
            self.addSubInterface(
                self.taskInterface, "taskInterface", f"{self.interface_name}任务"
            )

        # 只有当设置界面类存在时才创建并添加
        if self.setting_interface_class:
            self.settingInterface = self.setting_interface_class()
            self.addSubInterface(self.settingInterface, "settingInterface", "高级设置")

    def _setup_layout(self):
        """设置布局"""
        self.vBoxLayout.setContentsMargins(30, 0, 30, 30)
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignHCenter)
        self.vBoxLayout.addWidget(self.stackedWidget)

    def _connect_signals(self):
        """连接信号"""
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.mainInterface)
        self.pivot.setCurrentItem(self.mainInterface.objectName())

    def addSubInterface(self, widget: QWidget, objectName: str, text: str):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
