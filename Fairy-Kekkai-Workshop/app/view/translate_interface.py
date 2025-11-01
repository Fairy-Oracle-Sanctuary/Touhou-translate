from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QStackedWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    ExpandSettingCard,
    LineEdit,
    Pivot,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SettingCardGroup,
    TableWidget,
)
from qfluentwidgets import FluentIcon as FIF

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.setting import translate_deepseek_language_dict
from ..components.config_card import TranslateSettingInterface
from ..service.project_service import Project
from ..service.srt_service import Srt
from .translate_task_interface import TranslateTaskInterface


class TranslateStackedInterfaces(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 创建堆叠窗口
        self.pivot = Pivot(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.translateInterface = TranslationInterface()
        self.taskInterface = TranslateTaskInterface()
        self.settingInterface = TranslateSettingInterface()

        # 添加标签页
        self.addSubInterface(self.translateInterface, "translateInterface", "翻译字幕")
        self.addSubInterface(self.taskInterface, "taskInterface", "翻译任务")
        self.addSubInterface(self.settingInterface, "settingInterface", "高级设置")

        # 连接信号并初始化当前标签页
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.translateInterface.addTranslateTask.connect(
            self.taskInterface.addTranslateTask
        )
        self.taskInterface.returnTranslateTask.connect(
            self.translateInterface.updateTranslateTask
        )

        self.stackedWidget.setCurrentWidget(self.translateInterface)
        self.pivot.setCurrentItem(self.translateInterface.objectName())

        self.vBoxLayout.setContentsMargins(30, 0, 30, 30)
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignHCenter)
        self.vBoxLayout.addWidget(self.stackedWidget)

        self.resize(780, 800)
        self.setObjectName("TranslateStackedInterfaces")

    def addSubInterface(self, widget: QWidget, objectName: str, text: str):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)

        # 使用全局唯一的 objectName 作为路由键
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())


class TranslationInterface(ScrollArea):
    """SRT文件翻译界面"""

    # 定义信号
    addTranslateTask = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.srt_path = ""
        self.translate_thread = None
        self.translate_tasks = []

        self._initWidget()
        self._connect_signals()

        self.installEventFilter(self)

    def _initWidget(self):
        """初始化界面"""
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName("TranslationInterface")
        self.enableTransparentBackground()

        # 主布局
        main_layout = QVBoxLayout(self.view)

        # 文件选择卡片组
        self.fileSelectionGroup = SettingCardGroup("文件选择", self.view)
        self._create_file_selection_cards()
        main_layout.addWidget(self.fileSelectionGroup)

        # 翻译设置卡片组
        self.settingsGroup = SettingCardGroup("翻译设置", self.view)
        self._create_settings_cards()
        main_layout.addWidget(self.settingsGroup)

        # 内容预览卡片
        self.preview_card = self.create_preview_card()
        main_layout.addWidget(self.preview_card)

        # 操作按钮
        self._create_button_layout(main_layout)

        main_layout.addStretch(1)

        # 添加信号
        event_bus.translate_requested.connect(self.addTranslateFromProject)

    def _create_file_selection_cards(self):
        """创建文件选择卡片"""
        self.videoFileCard = ExpandSettingCard(
            FIF.CALENDAR,
            "字幕文件",
            "选择要翻译字幕的srt文件",
            self.fileSelectionGroup,
        )

        video_layout = QHBoxLayout()
        self.srt_path_edit = LineEdit()
        self.srt_path_edit.setPlaceholderText("选择srt文件...")
        self.srt_path_edit.setReadOnly(True)
        self.browse_video_btn = PushButton("浏览文件")
        video_layout.addWidget(self.srt_path_edit, 1)
        video_layout.addWidget(self.browse_video_btn)

        self.videoFileCard.viewLayout.addLayout(video_layout)
        self.fileSelectionGroup.addSettingCard(self.videoFileCard)

        # 输出文件选择卡片
        self.outputFileCard = ExpandSettingCard(
            FIF.SAVE,
            "输出文件",
            "设置翻译后的字幕文件保存路径",
            self.fileSelectionGroup,
        )

        output_layout = QHBoxLayout()
        self.output_path_edit = LineEdit()
        self.output_path_edit.setPlaceholderText("输出字幕文件路径...")
        self.output_path_edit.setReadOnly(True)
        self.browse_output_btn = PushButton("浏览文件")
        output_layout.addWidget(self.output_path_edit, 1)
        output_layout.addWidget(self.browse_output_btn)

        self.outputFileCard.viewLayout.addLayout(output_layout)
        self.fileSelectionGroup.addSettingCard(self.outputFileCard)

    def _create_settings_cards(self):
        """创建OCR设置卡片"""
        # 原语言设置卡片
        self.origin_languageCard = ExpandSettingCard(
            FIF.GLOBE, "原文语言", "选择字幕文本的语言", self.settingsGroup
        )

        self.origin_language_combo = ComboBox()
        self.origin_language_combo.addItems(translate_deepseek_language_dict.keys())
        self.origin_language_combo.setCurrentText(cfg.get(cfg.origin_lang))
        self.origin_languageCard.viewLayout.addWidget(self.origin_language_combo)
        self.settingsGroup.addSettingCard(self.origin_languageCard)

        # 目标语言设置卡片
        self.target_languageCard = ExpandSettingCard(
            FIF.LANGUAGE, "翻译语言", "选择翻译后的语言", self.settingsGroup
        )

        self.target_language_combo = ComboBox()
        self.target_language_combo.addItems(translate_deepseek_language_dict.keys())
        self.target_language_combo.setCurrentText(cfg.get(cfg.target_lang))
        self.target_languageCard.viewLayout.addWidget(self.target_language_combo)
        self.settingsGroup.addSettingCard(self.target_languageCard)

    def create_preview_card(self):
        """创建内容预览卡片"""
        card = CardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(20, 20, 20, 20)

        # 标题和统计信息
        preview_header = QHBoxLayout()

        title = BodyLabel("SRT 内容预览")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.stats_label = BodyLabel("共 0 条字幕")
        self.stats_label.setStyleSheet("color: #666;")

        preview_header.addWidget(title)
        preview_header.addStretch(1)
        preview_header.addWidget(self.stats_label)

        card_layout.addLayout(preview_header)

        # 表格
        self.preview_table = TableWidget()
        self.preview_table.setColumnCount(3)
        self.preview_table.setHorizontalHeaderLabels(["序号", "时间轴", "内容"])
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.setEditTriggers(TableWidget.NoEditTriggers)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setMinimumHeight(300)

        card_layout.addWidget(self.preview_table)

        return card

    def _create_button_layout(self, main_layout):
        """创建操作按钮区域"""
        button_layout = QHBoxLayout()

        self.start_btn = PrimaryPushButton(FIF.PLAY, "添加任务")
        self.start_btn.setEnabled(False)

        self.previous_btn = PushButton(FIF.UP, "上一个")
        self.previous_btn.setEnabled(False)

        self.next_btn = PushButton(FIF.DOWN, "下一个")
        self.next_btn.setEnabled(False)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.previous_btn)
        button_layout.addWidget(self.next_btn)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)

    def _connect_signals(self):
        """连接信号槽"""
        self.browse_video_btn.clicked.connect(self._browse_video_file)
        self.browse_output_btn.clicked.connect(self._browse_output_file)
        self.origin_language_combo.currentTextChanged.connect(
            lambda: cfg.set(cfg.origin_lang, self.origin_language_combo.currentText())
        )
        self.target_language_combo.currentTextChanged.connect(
            lambda: cfg.set(cfg.target_lang, self.target_language_combo.currentText())
        )
        self.start_btn.clicked.connect(self._start_translation)
        self.previous_btn.clicked.connect(self.switch_previous_file)
        self.next_btn.clicked.connect(self.switch_next_file)

    def eventFilter(self, obj, event):
        """事件过滤器，用于监听键盘事件"""
        if event.type() == event.Type.KeyPress:
            key = event.key()

            # 检测左方向键
            if key == Qt.Key_Left:
                self.switch_previous_file()
                return True

            # 检测右方向键
            elif key == Qt.Key_Right:
                self.switch_next_file()
                return True

        return super().eventFilter(obj, event)

    def _browse_video_file(self):
        """浏览字幕文件"""
        srt_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择字幕文件",
            str(Path.home()),
            "视频文件 (*.srt);;所有文件 (*.*)",
        )

        if srt_path:
            self.srt_path = srt_path
            self.srt_path_edit.setText(srt_path)

            # 自动生成输出文件路径
            srt_path = Path(srt_path)
            if srt_path.name == "原文.srt":
                output_path = srt_path.parent / "译文.srt"
            else:
                output_path = srt_path.parent / f"{srt_path.stem}_translated.srt"
            self.output_path_edit.setText(str(output_path))

            # 启用按钮
            self.start_btn.setEnabled(True)

            # 更新上下按钮状态
            self.update_adjacent_button()

            self.file_srt = Srt(srt_path)
            self.update_preview_table(self.file_srt.subtitle_data)

    def _browse_output_file(self):
        """浏览输出文件"""
        if not self.srt_path:
            self.show_error_message("请先选择原srt文件")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存字幕文件",
            self.output_path_edit.text(),
            "字幕文件 (*.srt);;所有文件 (*.*)",
        )

        if file_path:
            self.output_path_edit.setText(file_path)

    def _start_translation(self):
        """开始翻译槽函数"""
        if not cfg.get(cfg.deepseekApiKey):
            self.show_error_message("请先填写您的DeepSeek API Key")
            return

        if (
            self.origin_language_combo.currentText()
            == self.target_language_combo.currentText()
        ):
            self.show_error_message("原语言和目标语言相同")
            return

        args = self._get_args()
        self.addTranslateTask.emit(args)

    def _get_args(self):
        """获取参数"""
        args = {}

        args["srt_path"] = str(self.file_srt.file_path)
        args["output_path"] = self.output_path_edit.text()
        args["origin_lang"] = self.origin_language_combo.currentText()
        args["target_lang"] = self.target_language_combo.currentText()
        args["raw_content"] = self.file_srt.raw_content

        print(args)
        return args

    def update_preview_table(self, subtitles_data):
        """更新预览表格内容

        Args:
            subtitles_data: 字幕数据列表，每个元素为 (index, timestamp, text)
        """
        self.preview_table.setRowCount(0)  # 清空表格

        for row, (index, timestamp, text) in enumerate(subtitles_data):
            self.preview_table.insertRow(row)
            self.preview_table.setItem(row, 0, QTableWidgetItem(str(index)))
            self.preview_table.setItem(row, 1, QTableWidgetItem(timestamp))
            self.preview_table.setItem(
                row, 2, QTableWidgetItem(text.replace("\n", "\\n"))
            )

        # 调整列宽
        self.preview_table.resizeColumnsToContents()
        self.stats_label.setText(f"共 {len(subtitles_data)} 条字幕")

    def switch_previous_file(self):
        """切换上一个文件"""
        previous_path = Project.get_previous_path(self.srt_path)
        if previous_path:
            self.srt_path = previous_path
            self.file_srt = Srt(previous_path)

            # 自动生成输出文件路径
            srt_path = Path(previous_path)
            if srt_path.name == "原文.srt":
                output_path = srt_path.parent / "译文.srt"
            else:
                output_path = srt_path.parent / f"{srt_path.stem}_translated.srt"
            self.output_path_edit.setText(str(output_path))

            # 更新界面
            self.srt_path_edit.setText(str(self.srt_path))
            self.output_path_edit.setText(str(output_path))
            self.update_preview_table(self.file_srt.subtitle_data)
            self.update_adjacent_button()

    def switch_next_file(self):
        """切换上一个文件"""
        next_path = Project.get_next_path(self.srt_path)
        if next_path:
            self.srt_path = next_path
            self.file_srt = Srt(next_path)

            # 自动生成输出文件路径
            srt_path = Path(next_path)
            if srt_path.name == "原文.srt":
                output_path = srt_path.parent / "译文.srt"
            else:
                output_path = srt_path.parent / f"{srt_path.stem}_translated.srt"
            self.output_path_edit.setText(str(output_path))

            # 更新界面
            self.srt_path_edit.setText(str(self.srt_path))
            self.output_path_edit.setText(str(output_path))
            self.update_preview_table(self.file_srt.subtitle_data)
            self.update_adjacent_button()

    def update_adjacent_button(self):
        """更新上一个/下一个按钮状态"""
        adjacent_file_exists = Project.isAdjacentFileExists(self.srt_path)
        if adjacent_file_exists[0]:
            self.previous_btn.setEnabled(True)
        else:
            self.previous_btn.setEnabled(False)
        if adjacent_file_exists[1]:
            self.next_btn.setEnabled(True)
        else:
            self.next_btn.setEnabled(False)

    def updateTranslateTask(self, isRepeat, translate_tasks, isMessage):
        if isRepeat and isMessage:
            self.show_error_message("重复的任务")
        elif not isRepeat and isMessage:
            self.show_success_message(f"任务-{translate_tasks[-1]}-添加成功！")
        self.translate_tasks = translate_tasks

    def show_success_message(self, message):
        """显示成功消息"""
        event_bus.notification_service.show_success("成功", message)

    def show_error_message(self, message):
        """显示错误消息"""
        event_bus.notification_service.show_error("错误", message)

    def show_warning_message(self, message):
        """显示警告消息"""
        event_bus.notification_service.show_warning("警告", message)

    def addTranslateFromProject(self, file_path, output_path):
        """从项目界面添加翻译任务"""
        srt_file = Srt(file_path)

        args = {}
        args["srt_path"] = file_path
        args["output_path"] = output_path
        args["origin_lang"] = cfg.get(cfg.origin_lang)
        args["target_lang"] = cfg.get(cfg.target_lang)
        args["raw_content"] = srt_file.raw_content
        print(args)

        self.addTranslateTask.emit(args)
