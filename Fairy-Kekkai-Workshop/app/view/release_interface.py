# coding:utf-8

from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    FluentStyleSheet,
    LineEdit,
    RadioButton,
    isDarkTheme,
    setFont,
)
from qfluentwidgets import FluentIcon as FIF

from ..common.event_bus import event_bus  # noqa
from ..common.logger import Logger
from ..common.setting import tid_data
from ..components.base_function_interface import BaseFunctionInterface
from ..components.base_stacked_interface import BaseStackedInterfaces
from ..components.config_card import ReleaseSettingInterface
from ..view.release_task_interface import ReleaseTaskInterface


class ReleaseStackedInterfaces(BaseStackedInterfaces):
    """上传堆叠界面"""

    def __init__(self, parent=None):
        super().__init__(
            parent=parent,
            main_interface_class=ReleaseInterface,
            task_interface_class=ReleaseTaskInterface,
            setting_interface_class=ReleaseSettingInterface,
            interface_name="视频上传",
        )

        # 连接专用信号
        self.mainInterface.addTask.connect(self.taskInterface.addReleaseTask)
        self.taskInterface.returnTask.connect(self.mainInterface.updateTask)


class ReleaseInterface(BaseFunctionInterface):
    """B站视频上传界面"""

    def __init__(self, parent=None):
        self.file_video = None
        super().__init__(parent, "上传")

        self.file_extension = "*.mp4;*.flv;*.avi;*.wmv;*.mov;*.webm;*.mpeg4;*.ts;*.mpg;*.rm;*.rmvb;*.mkv;*.m4v;*.vob;*.swf;*.3gp;*.mts;*.m2v;*.mts;*.f4v;*.mt;*.3g2;*.asf"
        self.cover_extension = "*.png;*.pjp;*.jfif;*.jpe;*.pjpeg;*.jpeg;*.jpg"
        self.default_output_suffix = ""

        self.logger = Logger("ReleaseInterface", "release")

        self.inputFileCard.titleLabel.setText("视频文件")
        self.outputFileCard.iconLabel.setIcon(FIF.PHOTO)
        self.outputFileCard.titleLabel.setText("封面文件")
        self.outputFileCard.contentLabel.setText("请选择你的封面")
        self.outputFileCard.lineEdit.setPlaceholderText("选择文件...")
        self.outputFileCard.browseBtn.clicked.disconnect(self._browse_output_file)
        self.outputFileCard.browseBtn.clicked.connect(self._browse_cover_file)

    def _browse_cover_file(self):
        """浏览输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存文件",
            self.outputFileCard.lineEdit.text(),
            f"文件 ({self.cover_extension});;所有文件 (*.*)",
        )

        if file_path:
            self.outputFileCard.lineEdit.setText(file_path)

    def get_input_icon(self):
        return FIF.VIDEO

    def _create_settings_cards(self):
        """创建基础设置卡片"""
        titleLabel = QLabel("基本设置", self)
        self.main_layout.addWidget(titleLabel)
        setFont(titleLabel, 20)
        titleLabel.adjustSize()
        self.main_layout.addSpacing(12)

        self.main_layout.addWidget(ReleaseBaseSettingInterface(self))

    def _init_tid_combo(self):
        """初始化分区选择下拉框"""
        for category, subcategories in tid_data.items():
            for subcategory, tid in subcategories.items():
                self.tid_combo.addItem(f"{category} - {subcategory}", tid)


class ReleaseBaseSettingInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QVBoxLayout(self)
        self._initWidget()

    def _initWidget(self):
        FluentStyleSheet.SETTING_CARD.apply(self)
        self.setFixedHeight(500)

        # 标题
        self.view.addSpacing(12)
        titleLayout = QHBoxLayout()

        titleLabel = BodyLabel("* 标题", self)

        titleEdit = LineEdit(self)
        titleEdit.setPlaceholderText("请输入稿件标题")
        titleEdit.textChanged.connect(
            lambda: titleLength.setText(f"{len(titleEdit.text())}/80")
        )

        titleLength = BodyLabel("0/80", self)

        titleLayout.addSpacing(12)
        titleLayout.addWidget(titleLabel)
        titleLayout.addSpacing(12)
        titleLayout.addWidget(titleEdit)
        titleLayout.addWidget(titleLength)
        titleLayout.addSpacing(12)
        self.view.addLayout(titleLayout)

        # 类型
        self.view.addSpacing(12)
        typeLayout = QHBoxLayout()

        typeLabel = BodyLabel("  类型", self)

        typeButton1 = RadioButton("自制")
        typeButton2 = RadioButton("转载")
        typeButtonGroup = QButtonGroup(self)
        typeButtonGroup.addButton(typeButton1)
        typeButtonGroup.addButton(typeButton2)
        typeButton1.setChecked(True)

        typeLayout.addSpacing(12)
        typeLayout.addWidget(typeLabel)
        typeLayout.addSpacing(12)
        typeLayout.addWidget(typeButton1)
        typeLayout.addSpacing(24)
        typeLayout.addWidget(typeButton2)
        typeLayout.addStretch(1)

        self.view.addLayout(typeLayout)

        self.view.addStretch(1)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        if isDarkTheme():
            painter.setBrush(QColor(255, 255, 255, 13))
            painter.setPen(QColor(0, 0, 0, 50))
        else:
            painter.setBrush(QColor(255, 255, 255, 170))
            painter.setPen(QColor(0, 0, 0, 19))

        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)
