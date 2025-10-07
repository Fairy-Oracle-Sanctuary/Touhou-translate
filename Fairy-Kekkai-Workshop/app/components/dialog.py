import os
from PySide6.QtWidgets import QGridLayout, QWidget, QApplication
from PySide6.QtCore import Qt

from qfluentwidgets import MessageBoxBase, LineEdit, StrongBodyLabel, InfoBar, SubtitleLabel, MessageBox, PrimaryPushButton

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
        """重写接受方法，添加验证逻辑"""
        if hasattr(self, 'validateInput'):
            errors = self.validateInput()
            if errors:
                error_message = "\n".join(errors)
                event_bus.notification_service.show_error("输入错误", error_message)
                return
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
        base_path = ''
        project_name = self.nameInput.text()
        subfolder_count = self.numInput.text()
        title = self.titleInput.text()

        # 验证非空字段
        non_empty_checks = [
            ("项目名称", project_name, "请输入项目名称"),
            ("总集数", subfolder_count, "请输入总集数"),
            ("原标题", title, "请输入原标题")
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
        return self.validate_non_empty([
            ("输入内容", self.LineEdit.text().strip(), "请输入内容")
        ])


class CustomDoubleMessageBox(BaseInputDialog):
    """双输入对话框"""

    def __init__(self, title, input1, input2, text1, text2, error1, error2, min_width=400, parent=None):
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
        return self.validate_non_empty([
            ("第一个输入", self.LineEdit_1.text().strip(), self.error1),
            ("第二个输入", self.LineEdit_2.text().strip(), self.error2)
        ])


class CustomTripleMessageBox(BaseInputDialog):
    """三输入对话框"""

    def __init__(self, title, input1, input2, input3, text1, text2, text3, 
                 error1, error2, error3, min_width=450, parent=None):
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
            (self.LineEdit_3, text3)
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
        return self.validate_non_empty([
            ("第一个输入", self.LineEdit_1.text().strip(), self.error1),
            ("第二个输入", self.LineEdit_2.text().strip(), self.error2),
            ("第三个输入", self.LineEdit_3.text().strip(), self.error3)
        ])

    def getInputs(self):
        """获取三个输入框的值"""
        return (
            self.LineEdit_1.text().strip(),
            self.LineEdit_2.text().strip(),
            self.LineEdit_3.text().strip()
        )