import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout
from qfluentwidgets import (
    ComboBox,
    LineEdit,
    MessageBoxBase,
    PillPushButton,
    PlainTextEdit,
    ProgressBar,
    ProgressRing,
    StrongBodyLabel,
    SubtitleLabel,
)

from ..common.event_bus import event_bus


class BaseInputDialog(MessageBoxBase):
    """基础输入对话框，提供通用功能"""

    def __init__(self, title, min_width=400, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(title)
        self.viewLayout.addWidget(self.titleLabel)

        # 设置按钮文本
        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")

        # 设置最小宽度
        self.widget.setMinimumWidth(min_width)

    def validate_non_empty(self, fields):
        """验证字段是否非空"""
        errors = []
        for field_name, field_value, error_msg in fields:
            if not field_value.strip():
                errors.append(error_msg)
        return errors

    def accept(self):
        """重写接受方法，停止定时器"""
        if hasattr(self, "timer"):
            self.timer.stop()
        super().accept()


class AddProject(BaseInputDialog):
    """添加新项目"""

    def __init__(self, parent=None):
        super().__init__("添加新项目", min_width=450, parent=parent)
        self.setup_ui()

    def setup_ui(self):
        grid_layout = QGridLayout()
        self.viewLayout.addLayout(grid_layout)

        self.nameInput = LineEdit(self)
        self.nameInput.setPlaceholderText("输入项目的名字")

        self.numInput = LineEdit(self)
        self.numInput.setPlaceholderText("输入这个系列一共几集")

        self.titleInput = LineEdit(self)
        self.titleInput.setPlaceholderText("输入这个系列的原标题")

        fields = [
            ("项目名称:", self.nameInput),
            ("总集数:", self.numInput),
            ("原标题:", self.titleInput),
        ]

        for row, (label_text, widget) in enumerate(fields):
            label = StrongBodyLabel(label_text, self)
            grid_layout.addWidget(label, row, 0)
            grid_layout.addWidget(widget, row, 1)

        # 设置列拉伸，使输入框能够扩展
        grid_layout.setColumnStretch(1, 1)

    def validateInput(self):
        errors = []
        base_path = ""
        project_name = self.nameInput.text()
        subfolder_count = self.numInput.text()
        title = self.titleInput.text()

        # 验证非空字段
        non_empty_checks = [
            ("项目名称", project_name, "请输入项目名称"),
            ("总集数", subfolder_count, "请输入总集数"),
            ("原标题", title, "请输入原标题"),
        ]
        errors.extend(self.validate_non_empty(non_empty_checks))

        # 检查项目是否已存在
        if project_name.strip() and os.path.exists(base_path + project_name):
            errors.append(f"错误：'{project_name}' 文件夹已存在！")

        # 验证集数格式
        if subfolder_count.strip():
            try:
                subfolder_count_int = int(subfolder_count)
                if subfolder_count_int <= 0:
                    errors.append("总集数必须大于0")
                elif subfolder_count_int >= 128:
                    errors.append("总集数必须小于128")
            except ValueError:
                errors.append("总集数必须是有效的数字")

        return errors


class AddProjectFromPlaylist(BaseInputDialog):
    """添加新项目"""

    def __init__(self, parent=None):
        super().__init__("根据播放列表添加新项目", min_width=450, parent=parent)
        self.setup_ui()

    def setup_ui(self):
        grid_layout = QGridLayout()
        self.viewLayout.addLayout(grid_layout)

        self.urlInput = LineEdit(self)
        self.urlInput.setPlaceholderText("输入播放列表url")

        self.nameInput = LineEdit(self)
        self.nameInput.setPlaceholderText("输入项目的名字")

        self.titleInput = LineEdit(self)
        self.titleInput.setPlaceholderText("输入这个系列的原标题")

        fields = [
            ("视频列表url:", self.urlInput),
            ("项目名称:", self.nameInput),
            ("原标题:", self.titleInput),
        ]

        for row, (label_text, widget) in enumerate(fields):
            label = StrongBodyLabel(label_text, self)
            grid_layout.addWidget(label, row, 0)
            grid_layout.addWidget(widget, row, 1)

        # 设置列拉伸，使输入框能够扩展
        grid_layout.setColumnStretch(1, 1)

    def validateInput(self):
        errors = []
        base_path = ""
        list_url = self.urlInput.text()
        project_name = self.nameInput.text()
        title = self.titleInput.text()

        # 验证非空字段
        non_empty_checks = [
            ("视频列表url", list_url, "请输入播放列表url"),
            ("项目名称", project_name, "请输入项目名称"),
            ("原标题", title, "请输入原标题"),
        ]
        errors.extend(self.validate_non_empty(non_empty_checks))

        # 检查项目是否已存在
        if project_name.strip() and os.path.exists(base_path + project_name):
            errors.append(f"错误：'{project_name}' 文件夹已存在！")

        return errors


class CustomMessageBox(BaseInputDialog):
    """单输入对话框"""

    def __init__(self, title, text, min_width=350, parent=None):
        super().__init__(title, min_width, parent)

        self.LineEdit = LineEdit()
        self.LineEdit.setPlaceholderText(text)
        self.LineEdit.setClearButtonEnabled(True)

        # 将组件添加到布局中
        self.viewLayout.addWidget(self.LineEdit)

    def validateInput(self):
        return self.validate_non_empty(
            [("输入内容", self.LineEdit.text().strip(), "请输入内容")]
        )


class CustomDoubleMessageBox(BaseInputDialog):
    """双输入对话框"""

    def __init__(
        self,
        title,
        input1,
        input2,
        text1,
        text2,
        error1,
        error2,
        min_width=400,
        parent=None,
    ):
        super().__init__(title, min_width, parent)
        self.error1 = error1
        self.error2 = error2
        self.setup_ui(input1, input2, text1, text2)

    def setup_ui(self, input1, input2, text1, text2):
        grid_layout = QGridLayout()
        self.viewLayout.addLayout(grid_layout)

        self.input_label_1 = StrongBodyLabel(input1, self)
        self.input_label_2 = StrongBodyLabel(input2, self)

        self.LineEdit_1 = LineEdit()
        self.LineEdit_2 = LineEdit()

        self.LineEdit_1.setPlaceholderText(text1)
        self.LineEdit_1.setClearButtonEnabled(True)

        self.LineEdit_2.setPlaceholderText(text2)
        self.LineEdit_2.setClearButtonEnabled(True)

        # 将输入框组件添加到网格布局中
        grid_layout.addWidget(self.input_label_1, 0, 0)
        grid_layout.addWidget(self.LineEdit_1, 0, 1)
        grid_layout.addWidget(self.input_label_2, 1, 0)
        grid_layout.addWidget(self.LineEdit_2, 1, 1)

        # 设置列拉伸，使输入框能够扩展
        grid_layout.setColumnStretch(1, 1)

        # 左对齐
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def validateInput(self):
        return self.validate_non_empty(
            [
                ("第一个输入", self.LineEdit_1.text().strip(), self.error1),
                ("第二个输入", self.LineEdit_2.text().strip(), self.error2),
            ]
        )


class CustomTripleMessageBox(BaseInputDialog):
    """三输入对话框"""

    def __init__(
        self,
        title,
        input1,
        input2,
        input3,
        text1,
        text2,
        text3,
        error1,
        error2,
        error3,
        min_width=450,
        parent=None,
    ):
        super().__init__(title, min_width, parent)
        self.error1 = error1
        self.error2 = error2
        self.error3 = error3
        self.setup_ui(input1, input2, input3, text1, text2, text3)

    def setup_ui(self, input1, input2, input3, text1, text2, text3):
        grid_layout = QGridLayout()
        self.viewLayout.addLayout(grid_layout)

        # 创建标签和输入框
        self.input_label_1 = StrongBodyLabel(input1, self)
        self.input_label_2 = StrongBodyLabel(input2, self)
        self.input_label_3 = StrongBodyLabel(input3, self)

        self.LineEdit_1 = LineEdit()
        self.LineEdit_2 = LineEdit()
        self.LineEdit_3 = LineEdit()

        # 设置占位符文本和清除按钮
        inputs = [
            (self.LineEdit_1, text1),
            (self.LineEdit_2, text2),
            (self.LineEdit_3, text3),
        ]

        for line_edit, placeholder in inputs:
            line_edit.setPlaceholderText(placeholder)
            line_edit.setClearButtonEnabled(True)

        # 将组件添加到网格布局
        grid_layout.addWidget(self.input_label_1, 0, 0)
        grid_layout.addWidget(self.LineEdit_1, 0, 1)
        grid_layout.addWidget(self.input_label_2, 1, 0)
        grid_layout.addWidget(self.LineEdit_2, 1, 1)
        grid_layout.addWidget(self.input_label_3, 2, 0)
        grid_layout.addWidget(self.LineEdit_3, 2, 1)

        # 设置列拉伸，使输入框能够扩展
        grid_layout.setColumnStretch(1, 1)

        # 左对齐
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def validateInput(self):
        return self.validate_non_empty(
            [
                ("第一个输入", self.LineEdit_1.text().strip(), self.error1),
                ("第二个输入", self.LineEdit_2.text().strip(), self.error2),
                ("第三个输入", self.LineEdit_3.text().strip(), self.error3),
            ]
        )


class EditProjectDialog(BaseInputDialog):
    """编辑项目对话框（包含图标选择）"""

    def __init__(self, current_name, current_title, current_icon, parent=None):
        super().__init__("修改项目", min_width=500, parent=parent)
        self.current_name = current_name
        self.current_title = current_title
        self.current_icon = current_icon
        self.setup_ui()

    def setup_ui(self):
        grid_layout = QGridLayout()
        self.viewLayout.addLayout(grid_layout)

        # 文件夹名
        self.nameLabel = StrongBodyLabel("文件夹名:", self)
        self.nameInput = LineEdit(self)
        self.nameInput.setText(self.current_name)
        self.nameInput.setClearButtonEnabled(True)

        # 原标题
        self.titleLabel = StrongBodyLabel("原标题:", self)
        self.titleInput = LineEdit(self)
        self.titleInput.setText(self.current_title)
        self.titleInput.setClearButtonEnabled(True)

        # 图标选择
        self.iconLabel = StrongBodyLabel("图标:", self)
        self.iconComboBox = ComboBox(self)

        # 添加图标选项
        icon_display_names = {
            ":/app/images/icons/牛排.svg": "牛排",
            ":/app/images/icons/牛油果.svg": "牛油果",
            ":/app/images/icons/番茄.svg": "番茄",
            ":/app/images/icons/豆腐.svg": "豆腐",
            ":/app/images/icons/紫薯.svg": "紫薯",
            ":/app/images/icons/生菜.svg": "生菜",
            ":/app/images/logo.ico": "默认",
        }

        self.iconComboBox.addItems(list(icon_display_names.values()))
        self.iconComboBox.setCurrentIndex(
            list(icon_display_names.keys()).index(self.current_icon)
            if self.current_icon in icon_display_names
            else 0
        )

        # 添加到布局
        grid_layout.addWidget(self.nameLabel, 0, 0)
        grid_layout.addWidget(self.nameInput, 0, 1)
        grid_layout.addWidget(self.titleLabel, 1, 0)
        grid_layout.addWidget(self.titleInput, 1, 1)
        grid_layout.addWidget(self.iconLabel, 2, 0)
        grid_layout.addWidget(self.iconComboBox, 2, 1)

        # 设置列拉伸
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def validateInput(self):
        errors = []
        if not self.nameInput.text().strip():
            errors.append("请输入文件夹名")
        if not self.titleInput.text().strip():
            errors.append("请输入原标题")
        return errors

    def get_selected_icon(self):
        """获取选中的图标路径"""
        icon_display_names = {
            "牛排": ":/app/images/icons/牛排.svg",
            "牛油果": ":/app/images/icons/牛油果.svg",
            "番茄": ":/app/images/icons/番茄.svg",
            "豆腐": ":/app/images/icons/豆腐.svg",
            "紫薯": ":/app/images/icons/紫薯.svg",
            "生菜": ":/app/images/icons/生菜.svg",
            "默认": ":/app/images/logo.ico",
        }
        return icon_display_names[self.iconComboBox.currentText()]


class ProjectProgressDialog(MessageBoxBase):
    """项目进度对话框"""

    def __init__(self, progress, title, parent=None):
        super().__init__(parent)
        self.progress = progress
        self.title = title
        self.setup_ui()

    def setup_ui(self):
        self.yesButton.setText("我知道了")
        self.cancelButton.setVisible(False)

        progress_all = sum(self.progress) / 5

        progress_view = QHBoxLayout()
        self.viewLayout.addLayout(progress_view)

        self.titleLabel = SubtitleLabel(self.title)
        self.progress_pill = PillPushButton(self)
        self.progress_pill.setText(f"{progress_all:.2f}%")
        self.progress_pill.setEnabled(False)
        progress_view.addWidget(self.titleLabel)
        progress_view.addStretch(1)
        progress_view.addWidget(self.progress_pill)

        grid_layout = QGridLayout()
        self.viewLayout.addLayout(grid_layout)

        # 一个项目的每一集都有一个封面, 一个原视频，一个翻译后的视频，一个原字幕，一个翻译后的字幕，对应五个ring
        self.ring_cover = ProgressRing(self)
        self.ring_video = ProgressRing(self)
        self.ring_translated_video = ProgressRing(self)
        self.ring_subtitle = ProgressRing(self)
        self.ring_translated_subtitle = ProgressRing(self)

        self.label_cover = StrongBodyLabel("封面", self)
        self.label_video = StrongBodyLabel("原视频", self)
        self.label_translated_video = StrongBodyLabel("翻译后的视频", self)
        self.label_subtitle = StrongBodyLabel("原字幕", self)
        self.label_translated_subtitle = StrongBodyLabel("翻译后的字幕", self)

        rings = [
            self.ring_cover,
            self.ring_video,
            self.ring_translated_video,
            self.ring_subtitle,
            self.ring_translated_subtitle,
        ]
        for ring, p in zip(rings, self.progress):
            ring.setMinimum(0)
            ring.setMaximum(100)
            ring.setValue(int(p))
            ring.setTextVisible(True)

        # 设置所有标签文字居中
        labels = [
            self.label_cover,
            self.label_video,
            self.label_translated_video,
            self.label_subtitle,
            self.label_translated_subtitle,
        ]

        for label in labels:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        grid_layout.addWidget(self.ring_cover, 0, 0)
        grid_layout.addWidget(self.ring_video, 0, 1)
        grid_layout.addWidget(self.ring_translated_video, 0, 2)
        grid_layout.addWidget(self.ring_subtitle, 0, 3)
        grid_layout.addWidget(self.ring_translated_subtitle, 0, 4)

        grid_layout.addWidget(self.label_cover, 1, 0)
        grid_layout.addWidget(self.label_video, 1, 1)
        grid_layout.addWidget(self.label_translated_video, 1, 2)
        grid_layout.addWidget(self.label_subtitle, 1, 3)
        grid_layout.addWidget(self.label_translated_subtitle, 1, 4)

        self.progress_bar = ProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(int(progress_all))
        self.viewLayout.addWidget(self.progress_bar)


class TranslateProgressDialog(MessageBoxBase):
    """翻译进度对话框"""

    def __init__(self, task=None, parent=None):
        super().__init__(parent)
        self.task = task
        self.current_content = ""  # 存储当前翻译内容
        self.setup_ui()
        if task:
            self.connect_signals()
            # 优先使用output_history，如果为空则从文件读取
            if hasattr(task, "output_history") and task.output_history:
                self.current_content = task.output_history
                self.textEdit.setPlainText(self.current_content)
            elif self.task.output_file and os.path.exists(self.task.output_file):
                try:
                    with open(self.task.output_file, "r", encoding="utf-8") as f:
                        self.current_content = f.read()
                        self.textEdit.setPlainText(self.current_content)
                except Exception as e:
                    print(f"读取翻译文件失败: {e}")

    def setup_ui(self):
        self.titleLabel = SubtitleLabel("翻译进度")
        self.viewLayout.addWidget(self.titleLabel)

        self.textEdit = PlainTextEdit(self)
        self.textEdit.setReadOnly(True)
        self.textEdit.setPlaceholderText("翻译文本将在这里显示...")
        self.viewLayout.addWidget(self.textEdit)

        self.yesButton.setText("关闭")
        self.cancelButton.setVisible(False)

        # 设置对话框大小
        self.widget.setMinimumWidth(600)
        self.widget.setMinimumHeight(500)

    def connect_signals(self):
        """连接实时翻译信号"""
        event_bus.translate_update_signal.connect(self.on_translate_update)

    def on_translate_update(self, task_id, content_chunk):
        """处理实时翻译更新"""
        # 只处理当前任务的更新
        if self.task and str(self.task.id) == task_id:
            self.current_content += content_chunk
            self.textEdit.setPlainText(self.current_content)
            scrollbar = self.textEdit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def accept(self):
        """重写接受方法，断开信号连接"""
        event_bus.translate_update_signal.disconnect(self.on_translate_update)
        super().accept()


class FFmpegProgressDialog(MessageBoxBase):
    """FFmpeg压制视频进度对话框"""

    def __init__(self, task=None, parent=None):
        super().__init__(parent)
        self.task = task
        self.current_content = ""  # 存储当前输出内容
        self.setup_ui()
        if task:
            # 加载已有的输出历史
            if hasattr(task, "output_history"):
                self.current_content = task.output_history
                self.textEdit.setPlainText(self.current_content)
            self.connect_signals()

    def setup_ui(self):
        self.titleLabel = SubtitleLabel("压制视频进度")
        self.viewLayout.addWidget(self.titleLabel)

        self.textEdit = PlainTextEdit(self)
        self.textEdit.setReadOnly(True)
        self.textEdit.setPlaceholderText("输出将在这里显示...")
        self.viewLayout.addWidget(self.textEdit)

        self.yesButton.setText("关闭")
        self.cancelButton.setVisible(False)

        # 设置对话框大小
        self.widget.setMinimumWidth(600)
        self.widget.setMinimumHeight(500)

    def connect_signals(self):
        """连接实时ffmpeg输出信号"""
        event_bus.ffmpeg_update_signal.connect(self.on_ffmpeg_update)

    def on_ffmpeg_update(self, task_id, output_chunk):
        """处理实时ffmpeg输出更新"""
        # 只处理当前任务的更新
        if self.task and str(self.task.id) == task_id:
            self.current_content += output_chunk
            self.textEdit.setPlainText(self.current_content)
            scrollbar = self.textEdit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def accept(self):
        """重写接受方法，断开信号连接"""
        event_bus.ffmpeg_update_signal.disconnect(self.on_ffmpeg_update)
        super().accept()


class ReleaseProgressDialog(MessageBoxBase):
    """B站上传进度对话框"""

    def __init__(self, task=None, parent=None):
        super().__init__(parent)
        self.task = task
        self.current_content = ""  # 存储当前输出内容
        self.setup_ui()
        if task:
            # 加载已有的输出历史
            if hasattr(task, "output_history"):
                self.current_content = task.output_history
                self.textEdit.setPlainText(self.current_content)
            self.connect_signals()

    def setup_ui(self):
        self.titleLabel = SubtitleLabel("上传视频进度")
        self.viewLayout.addWidget(self.titleLabel)

        self.textEdit = PlainTextEdit(self)
        self.textEdit.setReadOnly(True)
        self.textEdit.setPlaceholderText("输出将在这里显示...")
        self.viewLayout.addWidget(self.textEdit)

        self.yesButton.setText("关闭")
        self.cancelButton.setVisible(False)

        # 设置对话框大小
        self.widget.setMinimumWidth(600)
        self.widget.setMinimumHeight(500)

    def connect_signals(self):
        """连接实时上传输出信号"""
        event_bus.release_update_signal.connect(self.on_release_update)

    def on_release_update(self, task_id, output_chunk):
        """处理实时上传输出更新"""
        # 只处理当前任务的更新
        if self.task and str(self.task.id) == task_id:
            self.current_content += output_chunk
            self.textEdit.setPlainText(self.current_content)
            scrollbar = self.textEdit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def accept(self):
        """重写接受方法，断开信号连接"""
        event_bus.release_update_signal.disconnect(self.on_release_update)
        super().accept()


class WhisperProgressDialog(MessageBoxBase):
    """Whisper语音识别进度对话框"""

    def __init__(self, task=None, parent=None):
        super().__init__(parent)
        self.task = task
        self.current_content = ""
        self.setup_ui()
        if task:
            # 加载已有的输出历史
            if hasattr(task, "output_history"):
                self.current_content = task.output_history
                self.textEdit.setPlainText(self.current_content)
            self.connect_signals()

    def setup_ui(self):
        self.titleLabel = SubtitleLabel("语音识别进度")
        self.viewLayout.addWidget(self.titleLabel)

        self.textEdit = PlainTextEdit(self)
        self.textEdit.setReadOnly(True)
        self.textEdit.setPlaceholderText("输出将在这里显示...")
        self.viewLayout.addWidget(self.textEdit)

        self.yesButton.setText("关闭")
        self.cancelButton.setVisible(False)

        # 设置对话框大小
        self.widget.setMinimumWidth(600)
        self.widget.setMinimumHeight(500)

    def connect_signals(self):
        """连接实时Whisper输出信号"""
        event_bus.whisper_update_signal.connect(self.on_whisper_update)

    def on_whisper_update(self, task_id, output_chunk):
        """处理实时Whisper输出更新"""
        # 只处理当前任务的更新
        if self.task and str(self.task.id) == task_id:
            self.current_content += output_chunk
            self.textEdit.setPlainText(self.current_content)
            scrollbar = self.textEdit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def accept(self):
        """重写接受方法，断开信号连接"""
        event_bus.whisper_update_signal.disconnect(self.on_whisper_update)
        super().accept()
