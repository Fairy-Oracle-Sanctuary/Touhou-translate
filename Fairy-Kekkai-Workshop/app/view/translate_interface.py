from PySide6.QtWidgets import (
    QHBoxLayout,
    QTableWidgetItem,
    QVBoxLayout,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    ExpandSettingCard,
    TableWidget,
)
from qfluentwidgets import FluentIcon as FIF

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.setting import translate_deepseek_language_dict
from ..components.base_function_interface import BaseFunctionInterface
from ..components.base_stacked_interface import BaseStackedInterfaces
from ..components.config_card import TranslateSettingInterface
from ..service.srt_service import Srt


class TranslateStackedInterfaces(BaseStackedInterfaces):
    """翻译堆叠界面"""

    def __init__(self, parent=None):
        from ..view.translate_task_interface import TranslateTaskInterface

        super().__init__(
            parent=parent,
            main_interface_class=TranslationInterface,
            task_interface_class=TranslateTaskInterface,
            setting_interface_class=TranslateSettingInterface,
            interface_name="翻译字幕",
        )

        # 连接专用信号
        self.mainInterface.addTask.connect(self.taskInterface.addTranslateTask)
        self.taskInterface.returnTranslateTask.connect(self.mainInterface.updateTask)


class TranslationInterface(BaseFunctionInterface):
    """SRT文件翻译界面"""

    def __init__(self, parent=None):
        self.file_srt = None
        super().__init__(parent, "翻译")

        self.file_extension = "*.srt"
        self.default_output_suffix = "_translated.srt"
        self.special_filename_mapping = {"原文.srt": "译文.srt"}

    def get_input_icon(self):
        return FIF.CALENDAR

    def _create_settings_cards(self):
        """创建翻译设置卡片"""
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

        # 连接信号
        self.origin_language_combo.currentTextChanged.connect(
            lambda: cfg.set(cfg.origin_lang, self.origin_language_combo.currentText())
        )
        self.target_language_combo.currentTextChanged.connect(
            lambda: cfg.set(cfg.target_lang, self.target_language_combo.currentText())
        )

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

    def _connect_signals(self):
        """连接信号槽"""
        super()._connect_signals()
        event_bus.translate_requested.connect(self.addTranslateFromProject)

    def load_file_content(self, file_path):
        """加载SRT文件内容"""
        self.file_srt = Srt(file_path)
        self.update_preview_table(self.file_srt.subtitle_data)

    def _start_processing(self):
        """开始翻译"""
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
        self.addTask.emit(args)

    def _get_args(self):
        """获取翻译参数"""
        args = {}
        args["srt_path"] = str(self.file_srt.file_path)
        args["output_path"] = self.output_path_edit.text()
        args["origin_lang"] = self.origin_language_combo.currentText()
        args["target_lang"] = self.target_language_combo.currentText()
        args["raw_content"] = self.file_srt.raw_content
        return args

    def update_preview_table(self, subtitles_data):
        """更新预览表格内容"""
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

    def addTranslateFromProject(self, file_path, output_path):
        """从项目界面添加翻译任务"""
        srt_file = Srt(file_path)
        self.file_srt = srt_file

        args = {}
        args["srt_path"] = file_path
        args["output_path"] = output_path
        args["origin_lang"] = cfg.get(cfg.origin_lang)
        args["target_lang"] = cfg.get(cfg.target_lang)
        args["raw_content"] = srt_file.raw_content

        self.addTask.emit(args)
