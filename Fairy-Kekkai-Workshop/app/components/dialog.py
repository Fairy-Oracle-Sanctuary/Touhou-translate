import os
from PySide6.QtWidgets import QGridLayout, QWidget, QApplication
from PySide6.QtCore import Qt

from qfluentwidgets import MessageBoxBase, LineEdit, StrongBodyLabel, InfoBar, SubtitleLabel, MessageBox, PrimaryPushButton

from ..common.event_bus import event_bus

class AddProject(MessageBoxBase):
    """添加新项目"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        grid_layout = QGridLayout()
        self.viewLayout.addLayout(grid_layout)

        self.nameInput = LineEdit(self)
        self.nameInput.setPlaceholderText("输入项目的名字")

        self.numInput= LineEdit(self)
        self.numInput.setPlaceholderText("输入这个系列一共几集")

        self.titleInput = LineEdit(self)
        self.titleInput.setPlaceholderText("输入这个系列的原标题")

        fields = [
            ("项目名称: ", self.nameInput),
            ("总集数: ", self.numInput),
            ("原标题: ", self.titleInput),
        ]

        for row, (label_text, widget) in enumerate(fields):
            label = StrongBodyLabel(label_text, self)
            grid_layout.addWidget(label, row, 0)
            grid_layout.addWidget(widget, row, 1)

        #按钮文本设置
        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")

        self.widget.setMinimumWidth(450)

    def validateInput(self):
        errors = []
        base_path = ''
        project_name = self.nameInput.text()
        subfolder_count = self.numInput.text()
        title = self.titleInput.text()

        if not project_name.strip():
            errors.append("请输入项目名称")
        if not subfolder_count.strip():
            errors.append("请输入总集数")
        if not title.strip():
            errors.append("请输入原标题")

        #判断
        if os.path.exists(base_path + project_name):
            errors.append(f"错误：'{project_name}' 文件夹已存在！")

        try:
            subfolder_count = int(subfolder_count)
            if subfolder_count <= 0:
                errors.append("总集数必须大于0")
            elif subfolder_count >= 128:
                errors.append("总集数必须小于128")
        except Exception:
            errors.append("总集数输入有误")

        #返回所有错误
        return errors

    def accept(self):
        errors = self.validateInput()
        if errors:
            error_message = "\n".join(errors)
            event_bus.notification_service.show_error("输入错误", error_message)
            return
        super().accept()

class CustomMessageBox(MessageBoxBase):
    """ Custom message box """

    def __init__(self, title, text, minwidth=350, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(title)
        self.LineEdit = LineEdit()

        self.LineEdit.setPlaceholderText(text)
        self.LineEdit.setClearButtonEnabled(True)

        # 将组件添加到布局中
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.LineEdit)

        # 设置对话框的最小宽度
        self.widget.setMinimumWidth(minwidth)

        # 按钮文本设置
        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")

    def accept(self):
        errors = self.LineEdit.text().strip()
        if not errors:
            event_bus.notification_service.show_error("输入错误", "请输入内容")
            return
        super().accept()

class CustomDoubleMessageBox(MessageBoxBase):
    """ Custom message box """

    def __init__(self, title, input1, input2, text1, text2, error1, error2, minwidth=400, parent=None):
        super().__init__(parent)
        self.error1 = error1
        self.error2 = error2

        grid_layout = QGridLayout()
        
        self.titleLabel = SubtitleLabel(title)

        self.input_label_1 = StrongBodyLabel(input1, self)
        self.input_label_2 = StrongBodyLabel(input2, self)

        self.LineEdit_1 = LineEdit()
        self.LineEdit_2 = LineEdit()

        self.LineEdit_1.setPlaceholderText(text1)
        self.LineEdit_1.setClearButtonEnabled(True)

        self.LineEdit_2.setPlaceholderText(text2)
        self.LineEdit_2.setClearButtonEnabled(True)

        # 调整组件添加顺序：先添加标题，再添加网格布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addLayout(grid_layout)

        # 将输入框组件添加到网格布局中
        grid_layout.addWidget(self.input_label_1, 0, 0, 1, 1)
        grid_layout.addWidget(self.LineEdit_1, 0, 1, 1, 1)
        grid_layout.addWidget(self.input_label_2, 1, 0, 1, 1)
        grid_layout.addWidget(self.LineEdit_2, 1, 1, 1, 1)

        # 按钮文本设置
        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")

        # 设置最小宽度
        self.widget.setMinimumWidth(minwidth)

        # 设置列拉伸，使输入框能够扩展
        grid_layout.setColumnStretch(1, 1)

        # 左对齐
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

    def validateInput(self):
        errors = []
        text1 = self.LineEdit_1.text().strip()
        text2 = self.LineEdit_2.text().strip()

        if not text1:
            errors.append(self.error1)
        if not text2:
            errors.append(self.error2)

        return errors

    def accept(self):
        errors = self.validateInput()
        if errors:
            error_message = "\n".join(errors)
            event_bus.notification_service.show_error("输入错误", error_message)
            return
        super().accept()

