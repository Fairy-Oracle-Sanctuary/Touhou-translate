import os
from PySide6.QtWidgets import QGridLayout

from qfluentwidgets import MessageBoxBase, LineEdit, StrongBodyLabel, InfoBar

class AddProject(MessageBoxBase):
    """
    添加新项目
    """

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
            InfoBar.error(
            title="输入错误",
            content=error_message,
            parent=self,
            duration=3000
            )
            return
        super().accept()

def showMessage(window):
    w = AddProject(window)
    if w.exec():
        print(w.urlLineEdit.text())
