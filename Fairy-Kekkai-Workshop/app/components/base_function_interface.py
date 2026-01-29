# coding:utf-8

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SettingCardGroup,
)

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..components.config_card import ChooseFileSettingCard
from ..service.project_service import Project


class BaseFunctionInterface(ScrollArea):
    """基础功能界面"""

    addTask = Signal(dict)

    def __init__(self, parent=None, function_type="function"):
        super().__init__(parent)
        self.view = QWidget(self)
        self.file_path = ""
        self.tasks = []

        self.function_type = function_type
        self.file_extension = ""
        self.default_output_suffix = ""
        self.special_filename_mapping = {}  # 特殊文件名映射

        self._initWidget()
        self._connect_signals()
        self.installEventFilter(self)
        self.setAcceptDrops(True)

    def _initWidget(self):
        """初始化界面"""
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName(f"{self.function_type}Interface")
        self.enableTransparentBackground()

        # 主布局
        self.main_layout = QVBoxLayout(self.view)

        # 文件选择卡片组
        self.fileSelectionGroup = SettingCardGroup("文件选择", self.view)
        self._create_file_selection_cards()
        self.main_layout.addWidget(self.fileSelectionGroup)

        # 设置卡片组
        self.settingsGroup = SettingCardGroup(f"{self.function_type}设置", self.view)
        self._create_settings_cards()
        self.main_layout.addWidget(self.settingsGroup)

        # 内容预览卡片
        self.preview_card = self.create_preview_card()
        if self.preview_card:
            self.main_layout.addWidget(self.preview_card)

        # 操作按钮
        self._create_button_layout(self.main_layout)
        self.main_layout.addStretch(1)

    def _create_file_selection_cards(self):
        """创建文件选择卡片"""
        # 输入文件卡片
        self.inputFileCard = ChooseFileSettingCard(
            self.get_input_icon(),
            f"{self.function_type}文件",
            f"选择要{self.function_type}的文件",
            "选择文件...",
            self.fileSelectionGroup,
        )
        self.fileSelectionGroup.addSettingCard(self.inputFileCard)

        # 输出文件选择卡片
        self.outputFileCard = ChooseFileSettingCard(
            FIF.SAVE,
            "输出文件",
            f"设置{self.function_type}后的文件保存路径",
            "输出文件路径...",
            self.fileSelectionGroup,
        )
        self.fileSelectionGroup.addSettingCard(self.outputFileCard)

    def _create_settings_cards(self):
        """创建设置卡片 - 子类实现"""
        raise NotImplementedError

    def create_preview_card(self):
        """创建内容预览卡片 - 子类实现"""
        return None

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
        self.inputFileCard.browseBtn.clicked.connect(self._browse_input_file)
        self.outputFileCard.browseBtn.clicked.connect(self._browse_output_file)
        self.start_btn.clicked.connect(self._start_processing)
        self.previous_btn.clicked.connect(self.switch_previous_file)
        self.next_btn.clicked.connect(self.switch_next_file)

    def dragEnterEvent(self, event):
        # 检查是否包含 URL 数据（文件或文件夹）
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """处理拖拽释放事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()

            # 检查文件数量
            if len(urls) > 1:
                self.show_error_message("只支持单个文件")
                event.ignore()
                return

            # 获取第一个文件的本地路径
            file_url = urls[0]
            if not file_url.isLocalFile():
                self.show_error_message("不支持网络文件")
                event.ignore()
                return

            file_path = Path(file_url.toLocalFile())

            # 检查是否为文件夹
            if file_path.is_dir():
                self.show_error_message("不支持文件夹")
                event.ignore()
                return

            # 检查文件扩展名
            allow_extensions = [ext.strip() for ext in self.file_extension.split(";")]
            # 移除通配符*，只保留扩展名部分
            allow_extensions = [ext.replace("*", "") for ext in allow_extensions]

            file_extension = file_path.suffix.lower()  # 包括点号，例如 ".mp4"

            # 检查扩展名是否在允许列表中
            if file_extension not in allow_extensions:
                self.show_error_message(f"不支持{file_extension}文件")
                event.ignore()
                return

            # 设置文件路径到输入框
            self.input_path_edit.setText(str(file_path))
            self.load_file_content(file_path)
            event.accept()
        else:
            event.ignore()

    def get_input_icon(self):
        """获取输入文件图标 - 子类实现"""
        raise NotImplementedError

    def _browse_input_file(self):
        """浏览输入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"选择{self.function_type}文件",
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
            self.outputFileCard.lineEdit.setText(str(output_path))

            # 启用按钮
            self.start_btn.setEnabled(True)

            # 更新上下按钮状态
            self.update_adjacent_button()

            # 加载文件内容预览
            self.load_file_content(file_path)

    def _generate_output_path(self, input_path):
        """生成输出文件路径"""
        input_path = Path(input_path)

        # 检查特殊文件名映射
        for special_name, output_name in self.special_filename_mapping.items():
            if input_path.name == special_name:
                return input_path.parent / output_name

        # 默认输出路径
        return input_path.parent / f"{input_path.stem}{self.default_output_suffix}"

    def _browse_output_file(self):
        """浏览输出文件"""
        if not self.file_path:
            self.show_error_message(f"请先选择原{self.file_extension}文件")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存文件",
            self.outputFileCard.lineEdit.text(),
            f"文件 ({self.file_extension});;所有文件 (*.*)",
        )

        if file_path:
            self.outputFileCard.lineEdit.setText(file_path)

    def _start_processing(self):
        """开始处理 - 子类实现"""
        raise NotImplementedError

    def _get_args(self):
        """获取参数 - 子类实现"""
        raise NotImplementedError

    def load_file_content(self, file_path):
        """加载文件内容 - 子类实现"""
        pass

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

    def switch_previous_file(self):
        """切换上一个文件"""
        previous_path = Project.get_previous_path(self.file_path)
        if previous_path:
            self._switch_to_file(previous_path)

    def switch_next_file(self):
        """切换下一个文件"""
        next_path = Project.get_next_path(self.file_path)
        if next_path:
            self._switch_to_file(next_path)

    def _switch_to_file(self, new_path):
        """切换到指定文件"""
        self.file_path = new_path

        # 生成输出路径
        output_path = self._generate_output_path(new_path)

        # 更新界面
        self.input_path_edit.setText(str(self.file_path))
        self.output_path_edit.setText(str(output_path))

        # 加载文件内容
        self.load_file_content(new_path)

        # 更新按钮状态
        self.update_adjacent_button()

    def update_adjacent_button(self):
        """更新上一个/下一个按钮状态"""
        adjacent_file_exists = Project.isAdjacentFileExists(self.file_path)
        if adjacent_file_exists[0]:
            self.previous_btn.setEnabled(True)
        else:
            self.previous_btn.setEnabled(False)
        if adjacent_file_exists[1]:
            self.next_btn.setEnabled(True)
        else:
            self.next_btn.setEnabled(False)

    def updateTask(self, isRepeat, tasks, isMessage):
        """更新任务状态"""
        if isRepeat and isMessage:
            self.show_error_message("重复的任务")
        elif not isRepeat and isMessage:
            self.show_success_message(f"任务-{tasks[-1]}-添加成功！")
        self.tasks = tasks

    def show_success_message(self, message):
        """显示成功消息"""
        event_bus.notification_service.show_success("成功", message)

    def show_error_message(self, message):
        """显示错误消息"""
        event_bus.notification_service.show_error("错误", message)

    def show_warning_message(self, message):
        """显示警告消息"""
        event_bus.notification_service.show_warning("警告", message)
