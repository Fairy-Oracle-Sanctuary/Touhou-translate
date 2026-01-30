# coding:utf-8

import time
from pathlib import Path

from PySide6.QtCore import QDate, QTime
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
    CheckBox,
    ComboBox,
    FastCalendarPicker,
    FlowLayout,
    FluentStyleSheet,
    LineEdit,
    PlainTextEdit,
    PushButton,
    RadioButton,
    SwitchButton,
    TimePicker,
    ToolButton,
    isDarkTheme,
    setFont,
)
from qfluentwidgets import FluentIcon as FIF

from ..common.config import cfg
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
        self.special_filename_mapping = {
            "熟肉.mp4": "封面.jpg",
            "熟肉_压制.mp4": "封面.jpg",
        }

        self.logger = Logger("ReleaseInterface", "release")

        self.inputFileCard.titleLabel.setText("视频文件")
        self.outputFileCard.iconLabel.setIcon(FIF.PHOTO)
        self.outputFileCard.titleLabel.setText("封面文件")
        self.outputFileCard.contentLabel.setText("请选择你的封面")
        self.outputFileCard.lineEdit.setPlaceholderText("选择文件...")

        self.inputFileCard.browseBtn.clicked.disconnect(self._browse_input_file)
        self.inputFileCard.browseBtn.clicked.connect(self._browse_video_file)
        self.outputFileCard.browseBtn.clicked.disconnect(self._browse_output_file)
        self.outputFileCard.browseBtn.clicked.connect(self._browse_cover_file)

        self.start_btn.setEnabled(True)

    def _browse_video_file(self):
        """浏览输入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            cfg.get(cfg.lastOpenPath)
            if Path(cfg.get(cfg.lastOpenPath)).exists()
            else str(Path.home()),
            f"文件 ({self.file_extension});;所有文件 (*.*)",
        )

        if file_path:
            self.file_path = file_path
            self.inputFileCard.lineEdit.setText(file_path)
            cfg.set(cfg.lastOpenPath, str(Path(file_path).parent))

            # 自动生成输出文件路径
            output_path = self._generate_output_path(file_path)
            if Path(output_path).exists():
                self.outputFileCard.lineEdit.setText(str(output_path))
            else:
                return

            # 更新上下按钮状态
            self.update_adjacent_button()

            # 加载文件内容预览
            self.load_file_content(file_path)

    def _browse_cover_file(self):
        """浏览封面文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择封面文件",
            cfg.get(cfg.lastOpenPath)
            if Path(cfg.get(cfg.lastOpenPath)).exists()
            else str(Path.home()),
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

        self.settingCard = ReleaseBaseSettingInterface(self)
        self.main_layout.addWidget(self.settingCard)

    def _start_processing(self):
        """开始上传"""
        if not cfg.get(cfg.bilibiliSessdata):
            self.show_error_message("请先填写Cookie：Sessdata")
            return

        if not cfg.get(cfg.bilibiliBiliJct):
            self.show_error_message("请先填写Cookie：BiliJct")
            return

        if not cfg.get(cfg.bilibiliBuvid3):
            self.show_error_message("请先填写Cookie：Buvid3")
            return

        if not self.inputFileCard.lineEdit.text():
            self.show_error_message("请选择视频文件")
            return

        if not self.outputFileCard.lineEdit.text():
            self.show_error_message("请选择封面文件")
            return

        if not self.settingCard.titleEdit.text():
            self.show_error_message("请输入稿件标题")
            return

        if (
            self.settingCard.typeButtonGroup.checkedButton().text() == "转载"
            and not self.settingCard.repostEdit.text()
        ):
            self.show_error_message("请输入转载链接")
            return

        if not self.settingCard.tags:
            self.show_error_message("请输入标签")
            return

        # 检测时间
        if self.settingCard.scheduleBtn.isChecked():
            date = self.settingCard.calendarPicker.getDate()
            time = self.settingCard.timePicker.getTime()
            if date < QDate.currentDate() or (
                date == QDate.currentDate() and time < QTime.currentTime()
            ):
                self.show_error_message("选择的时间必须大于现在的时间")
                return

        args = self._get_args()
        self.logger.info(
            f"开始上传视频: -{self.inputFileCard.lineEdit.text()}- 参数: {args}"
        )
        self.addTask.emit(args)

    def _get_args(self):
        """获取翻译参数"""
        args = {}
        args["video_path"] = self.inputFileCard.lineEdit.text()
        args["cover"] = self.outputFileCard.lineEdit.text()
        args["tid"] = tid_data.get(self.settingCard.tid_combo.currentText(), 160)
        args["title"] = self.settingCard.titleEdit.text()
        args["desc"] = self.settingCard.descEdit.toPlainText()
        args["tags"] = self.settingCard.tags
        is_original = self.settingCard.typeButtonGroup.checkedButton().text() == "自制"
        args["original"] = is_original
        args["source"] = self.settingCard.repostEdit.text() if not is_original else ""
        args["recreate"] = self.settingCard.recreateCheckbox.isChecked()
        date = self.settingCard.calendarPicker.getDate().toString("yyyy-MM-dd")
        _time = self.settingCard.timePicker.getTime().toString("HH:mm")

        # 计算定时发布时间戳（秒）
        if self.settingCard.scheduleBtn.isChecked():
            # 将日期和时间转换为时间戳
            datetime_str = f"{date} {_time}"
            datetime_obj = time.strptime(datetime_str, "%Y-%m-%d %H:%M")
            delay_timestamp = int(time.mktime(datetime_obj))
            args["delay_time"] = delay_timestamp
        else:
            args["delay_time"] = None

        return args


class ReleaseBaseSettingInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QVBoxLayout(self)

        self.tags = []
        self.maxTags = 10

        self._initWidget()

    def _initWidget(self):
        FluentStyleSheet.SETTING_CARD.apply(self)
        self.setMaximumHeight(750)
        self.setMinimumHeight(650)

        # 标题
        self.view.addSpacing(12)
        titleLayout = QHBoxLayout()

        titleLabel = BodyLabel("* 标题", self)

        self.titleEdit = LineEdit(self)
        self.titleEdit.setPlaceholderText("请输入稿件标题")
        self.titleEdit.textChanged.connect(
            lambda: titleLength.setText(f"{len(self.titleEdit.text())}/80")
        )

        titleLength = BodyLabel("0/80", self)

        titleLayout.addSpacing(12)
        titleLayout.addWidget(titleLabel)
        titleLayout.addSpacing(42)
        titleLayout.addWidget(self.titleEdit)
        titleLayout.addWidget(titleLength)
        titleLayout.addSpacing(12)

        self.view.addLayout(titleLayout)

        # 类型
        self.view.addSpacing(12)
        typeLayout = QHBoxLayout()

        typeLabel = BodyLabel("  类型", self)

        typeButton1 = RadioButton("自制")
        typeButton2 = RadioButton("转载")
        self.typeButtonGroup = QButtonGroup(self)
        self.typeButtonGroup.addButton(typeButton1)
        self.typeButtonGroup.addButton(typeButton2)
        typeButton1.setChecked(True)

        typeLayout.addSpacing(12)
        typeLayout.addWidget(typeLabel)
        typeLayout.addSpacing(42)
        typeLayout.addWidget(typeButton1)
        typeLayout.addSpacing(24)
        typeLayout.addWidget(typeButton2)
        typeLayout.addStretch(1)

        self.view.addLayout(typeLayout)

        # 转载链接
        self.repostLayout = QHBoxLayout()

        self.repostEdit = LineEdit(self)
        self.repostEdit.setPlaceholderText(
            "转载视频请注明来源、时间、地点(例：转自https://www.xxxx.com/yyyy)，注明来源会更快地通过审核哦"
        )
        self.repostEdit.setVisible(False)

        self.repostLength = BodyLabel("0/200", self)
        self.repostLength.setVisible(False)

        self.repostLayout.addSpacing(98)
        self.repostLayout.addWidget(self.repostEdit)
        self.repostLayout.addWidget(self.repostLength)
        self.repostLayout.addSpacing(12)

        self.view.addLayout(self.repostLayout)

        # 分区
        self.view.addSpacing(12)
        tidLayout = QHBoxLayout()

        tidLabel = BodyLabel("* 分区", self)

        self.tid_combo = ComboBox(self)
        self.tid_combo.setMinimumWidth(200)
        self.tid_combo.addItems(tid_data.keys())

        tidLayout.addSpacing(12)
        tidLayout.addWidget(tidLabel)
        tidLayout.addSpacing(42)
        tidLayout.addWidget(self.tid_combo)
        tidLayout.addStretch(1)

        self.view.addLayout(tidLayout)

        # 标签
        self.view.addSpacing(12)
        self.tagLayout = QHBoxLayout()
        self.tagInputLayout = QHBoxLayout()
        self.tagContainLayout = QVBoxLayout()

        tagLabel = BodyLabel("* 标签", self)

        self.tagContainer = QWidget(self)
        self.tagContainer.setObjectName("tagContainer")

        self.tagsLayout = FlowLayout(needAni=False)
        self.tagsLayout.setContentsMargins(0, 0, 0, 0)
        self.tagsLayout.setSpacing(4)

        self.tagInputHint = LineEdit(self.tagContainer)
        self.tagInputHint.setPlaceholderText("按回车键Enter创建标签")
        self.tagInputHint.setMinimumWidth(200)

        self.tagCountLabel = BodyLabel("还可以添加10个标签", self.tagContainer)

        self.tagLayout.addSpacing(12)
        self.tagLayout.addWidget(tagLabel)
        self.tagLayout.addSpacing(42)
        self.tagInputLayout.addWidget(self.tagInputHint)
        self.tagInputLayout.addWidget(self.tagCountLabel)
        self.tagContainLayout.addLayout(self.tagInputLayout)
        self.tagContainLayout.addLayout(self.tagsLayout)
        self.tagLayout.addLayout(self.tagContainLayout)
        self.tagLayout.addSpacing(12)

        self.view.addLayout(self.tagLayout)

        self.tagInputHint.returnPressed.connect(self._addTag)
        self.tagInputHint.textChanged.connect(self._handleTagInputChange)

        # 简介
        self.view.addSpacing(12)
        self.descLayout = QHBoxLayout()
        self.descLabelLayout = QVBoxLayout()
        self.descLengthLayout = QVBoxLayout()

        descLabel = BodyLabel("  简介", self)

        self.descEdit = PlainTextEdit(self)
        self.descEdit.setPlaceholderText(
            "填写更全面的相关信息，让更多的人能找到你的视频吧"
        )
        self.descEdit.setMinimumHeight(150)
        self.descEdit.textChanged.connect(
            lambda: descLength.setText(f"{len(self.descEdit.toPlainText())}/2000")
        )

        descLength = BodyLabel("0/2000", self)

        self.descLayout.addSpacing(12)
        self.descLabelLayout.addWidget(descLabel)
        self.descLabelLayout.addStretch(1)
        self.descLayout.addLayout(self.descLabelLayout)
        self.descLayout.addSpacing(42)
        self.descLayout.addWidget(self.descEdit)
        self.descLengthLayout.addStretch(1)
        self.descLengthLayout.addWidget(descLength)
        self.descLayout.addLayout(self.descLengthLayout)
        self.descLayout.addSpacing(12)

        self.view.addLayout(self.descLayout)

        # 定时发布
        self.view.addSpacing(12)
        self.scheduleLayout = QHBoxLayout()

        scheduleLabel = BodyLabel("  定时发布", self)

        self.scheduleBtn = SwitchButton(self)
        self.scheduleBtn.setOnText("")
        self.scheduleBtn.setOffText("")
        self.scheduleBtn.setChecked(False)

        self.scheduleLayout.addSpacing(12)
        self.scheduleLayout.addWidget(scheduleLabel)
        self.scheduleLayout.addSpacing(12)
        self.scheduleLayout.addWidget(self.scheduleBtn)
        self.scheduleLayout.addWidget(
            BodyLabel(
                "(可选择距离当前最早≥2小时/最晚≤15天的时间，花火稿件或距发布不足5分钟时不可修改/取消)"
            )
        )
        self.scheduleLayout.addStretch(1)

        self.view.addLayout(self.scheduleLayout)

        # 日期时间选择
        self.calendarLayout = QHBoxLayout()
        self.calendarPicker = FastCalendarPicker()
        self.calendarPicker.setDate(QDate.currentDate())
        self.calendarPicker.setVisible(False)

        self.timePicker = TimePicker(self)
        self.timePicker.setTime(QTime.currentTime())
        self.timePicker.setVisible(False)

        self.dateLabel = QLabel(self)
        self.dateLabel.setText(time.strftime("%Y-%m-%d %H:%M", time.localtime()))
        self.dateLabel.setVisible(False)

        self.calendarLayout.addSpacing(92)
        self.calendarLayout.addWidget(self.calendarPicker)
        self.calendarLayout.addWidget(self.timePicker)
        self.calendarLayout.addWidget(self.dateLabel)
        self.calendarLayout.addStretch(1)

        self.view.addLayout(self.calendarLayout)

        # 二创设置
        self.view.addSpacing(12)
        self.recreateLayout = QHBoxLayout()
        self.recreateLabel = BodyLabel("  二创设置", self)

        self.recreateCheckbox = CheckBox(self)
        self.recreateCheckbox.setText("允许二创")

        self.recreateLayout.addSpacing(12)
        self.recreateLayout.addWidget(self.recreateLabel)
        self.recreateLayout.addSpacing(12)
        self.recreateLayout.addWidget(self.recreateCheckbox)
        self.recreateLayout.addStretch(1)

        self.view.addLayout(self.recreateLayout)

        # 必要拉伸
        self.view.addSpacing(24)

        self._connect_signals()

    def _connect_signals(self):
        """连接信号槽"""
        self.typeButtonGroup.buttonToggled.connect(
            lambda button: self._handle_type_change(True)
            if button.text() == "转载"
            else self._handle_type_change(False)
        )
        self.scheduleBtn.checkedChanged.connect(
            lambda checked: self._handle_schedule_change(checked)
        )
        self.calendarPicker.dateChanged.connect(self._handle_date_change)
        self.timePicker.timeChanged.connect(self._handle_date_change)

    def _handle_type_change(self, is_repost):
        """处理类型改变"""
        self.repostEdit.setVisible(is_repost)
        self.repostLength.setVisible(is_repost)

    def _handle_schedule_change(self, is_schedule):
        """处理定时发布改变"""
        self.calendarPicker.setVisible(is_schedule)
        self.timePicker.setVisible(is_schedule)
        self.dateLabel.setVisible(is_schedule)

    def _handle_date_change(self, d):
        """更新日期时间标签"""
        date = self.calendarPicker.getDate()
        time = self.timePicker.getTime()
        # 选择的时间必须大于现在的时间
        if date < QDate.currentDate() or (
            date == QDate.currentDate() and time < QTime.currentTime()
        ):
            self.dateLabel.setText(
                f"{date.toString('yyyy-MM-dd')} {time.toString('hh:mm')} 选择的时间必须大于现在的时间"
            )
            return

        self.dateLabel.setText(
            f"{date.toString('yyyy-MM-dd')} {time.toString('hh:mm')}"
        )

    def _addTag(self):
        """添加标签"""
        tag_text = self.tagInputHint.text().strip()
        if tag_text and len(self.tags) < self.maxTags and tag_text not in self.tags:
            tag_button = PushButton(tag_text)
            tag_button.setObjectName("tagButton")

            delete_button = ToolButton()
            delete_button.setIcon(FIF.CLOSE)
            delete_button.setObjectName("tagDeleteButton")

            tag_container = QWidget()
            tag_container_layout = QHBoxLayout(tag_container)
            tag_container_layout.setContentsMargins(0, 0, 0, 0)
            tag_container_layout.addWidget(tag_button)
            tag_container_layout.addWidget(delete_button)

            delete_button.clicked.connect(
                lambda: self._removeTag(tag_text, tag_container)
            )

            self.tagsLayout.addWidget(tag_container)

            self.tags.append(tag_text)

            self.tagInputHint.clear()

            self._updateTagCount()

    def _removeTag(self, tag_text, tag_container):
        """删除标签"""
        if tag_text in self.tags:
            self.tags.remove(tag_text)
            tag_container.deleteLater()
            self._updateTagCount()

    def _updateTagCount(self):
        """更新标签数量显示"""
        remaining = self.maxTags - len(self.tags)
        self.tagCountLabel.setText(f"还可以添加{remaining}个标签")

    def _handleTagInputChange(self):
        """处理标签输入变化"""
        # 当标签数量达到上限时，禁用输入
        if len(self.tags) >= self.maxTags:
            self.tagInputHint.clear()
            self.tagInputHint.setPlaceholderText("已达到标签上限")
        else:
            self.tagInputHint.setPlaceholderText("按回车键Enter创建标签")

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
