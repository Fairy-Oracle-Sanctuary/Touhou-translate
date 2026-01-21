from PySide6.QtWidgets import (
    QHBoxLayout,
    QTableWidgetItem,
    QVBoxLayout,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBoxSettingCard,
    TableWidget,
)
from qfluentwidgets import FluentIcon as FIF

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.setting import AI_model_dict, translate_language_dict
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
        self.origin_languageCard = ComboBoxSettingCard(
            configItem=cfg.origin_lang,
            icon=FIF.GLOBE,
            title="原文语言",
            content="选择字幕文本的语言",
            texts=translate_language_dict.keys(),
        )
        self.settingsGroup.addSettingCard(self.origin_languageCard)

        # 翻译语言设置卡片
        self.target_languageCard = ComboBoxSettingCard(
            configItem=cfg.target_lang,
            icon=FIF.LANGUAGE,
            title="翻译语言",
            content="选择翻译后的语言",
            texts=translate_language_dict.keys(),
        )
        self.settingsGroup.addSettingCard(self.target_languageCard)

        self.AI_modelCard = ComboBoxSettingCard(
            configItem=cfg.ai_model,
            icon=FIF.BOOK_SHELF,
            title="AI模型",
            content="选择AI模型",
            texts=AI_model_dict.keys(),
        )
        self.settingsGroup.addSettingCard(self.AI_modelCard)

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
        if cfg.get(cfg.ai_model) == "Deepseek" and not cfg.get(cfg.deepseekApiKey):
            self.show_error_message("请先填写您的DeepSeek API Key")
            return

        elif cfg.get(cfg.ai_model) == "GLM-4.5-FLASH" and not cfg.get(cfg.glmApiKey):
            self.show_error_message("请先填写您的GLM-4.5-FLASH API Key")
            return

        elif cfg.get(cfg.ai_model) == "Spark-Lite" and not cfg.get(cfg.sparkApiKey):
            self.show_error_message("请先填写您的Spark-Lite API Key")
            return

        elif cfg.get(cfg.ai_model) == "Spark-Lite" and not cfg.get(cfg.sparkAppId):
            self.show_error_message("请先填写您的Spark-Lite App ID")
            return

        elif cfg.get(cfg.ai_model) == "Spark-Lite" and not cfg.get(cfg.sparkApiSecret):
            self.show_error_message("请先填写您的Spark-Lite API Secret")
            return

        elif cfg.get(cfg.ai_model) == "腾讯混元" and not cfg.get(cfg.hunyuanApiKey):
            self.show_error_message("请先填写您的腾讯混元 API Key")
            return

        elif cfg.get(cfg.ai_model) == "书生" and not cfg.get(cfg.internApiKey):
            self.show_error_message("请先填写您的书生 API Key")
            return

        elif cfg.get(cfg.ai_model) == "百度ERNIE-Speed-128K" and not cfg.get(
            cfg.ernieSpeedApiKey
        ):
            self.show_error_message("请先填写您的百度ERNIE-Speed-128K API Key")
            return

        elif cfg.get(cfg.ai_model) == "Gemini 3 Flash" and not cfg.get(
            cfg.geminiApiKey
        ):
            self.show_error_message("请先填写您的Gemini 3 Flash API Key")
            return

        if cfg.get(cfg.origin_lang) == cfg.get(cfg.target_lang):
            self.show_error_message("原语言和目标语言相同")
            return

        args = self._get_args()
        self.addTask.emit(args)

    def _get_args(self):
        """获取翻译参数"""
        args = {}
        args["srt_path"] = str(self.file_srt.file_path)
        args["output_path"] = self.output_path_edit.text()
        args["origin_lang"] = cfg.get(cfg.origin_lang)
        args["target_lang"] = cfg.get(cfg.target_lang)
        args["raw_content"] = self.file_srt.raw_content
        args["AI"] = AI_model_dict.get(cfg.get(cfg.ai_model), "glm-4.5-flash")
        args["temperature"] = cfg.get(cfg.aiTemperature)

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
