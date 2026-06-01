from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    PillPushButton,
    PopupTeachingTip,
    SimpleCardWidget,
    StrongBodyLabel,
    TransparentPushButton,
)

from ..common.config import cfg


class TeachingTipManager:
    """新手引导管理器"""

    def __init__(self, parent=None):
        self.parent = parent
        self.current_step = 0
        self.teaching_tip = None
        self.setup_tips()

    def setup_tips(self):
        """设置引导步骤

        不同平台的界面顺序不同：
        - Windows: 主页(0) 项目(1) 下载(2) 字幕(3) 识别(4) 翻译(5) 压制(6) 设置(-1)
        - macOS:   主页(0) 项目(1) 下载(2) 翻译(3) 压制(4) 设置(-1)
        macOS 不包含「字幕(OCR)」与「识别(Whisper)」功能，因此这两步会被跳过。
        """
        import sys

        is_win = sys.platform == "win32"

        self.tips_data = [
            {
                "title": "欢迎使用 Fairy Kekkai Workshop",
                "content": "这是一个专为东方Project视频翻译设计的工具，支持视频下载、OCR识别、语音识别、AI翻译、视频压制等功能。主页的「关于」卡片中还可以查看日志、一键清空日志或重置所有设置。",
                "interface_index": 0,  # 主页
            },
            {
                "title": "项目管理",
                "content": "点击「新建项目」创建新的翻译项目，或点击「导入项目」导入已有项目。每个项目对应一个视频系列。",
                "interface_index": 1,  # 项目界面
            },
            {
                "title": "下载视频",
                "content": "在下载界面输入视频URL，支持YouTube、Bilibili等平台。可选择清晰度和下载格式。",
                "interface_index": 2,  # 下载界面
            },
        ]

        # 字幕(OCR) 与 识别(Whisper) 仅 Windows 平台提供
        if is_win:
            self.tips_data.append(
                {
                    "title": "OCR识别",
                    "content": "在字幕界面选择视频文件，点击「开始OCR」进行字幕识别。需要配置PaddleOCR模型路径。",
                    "interface_index": 3,  # 字幕界面（仅Windows）
                }
            )
            self.tips_data.append(
                {
                    "title": "语音识别",
                    "content": "在识别界面选择视频或音频文件，使用 Whisper 模型将语音转写为字幕。可在设置中选择模型、语言、输出格式与 GPU 加速。",
                    "interface_index": 4,  # 识别界面（仅Windows）
                }
            )

        # 翻译界面：Windows 为索引5，macOS 为索引3
        self.tips_data.append(
            {
                "title": "AI翻译",
                "content": "在翻译界面选择SRT文件，配置AI模型和API Key，点击「开始翻译」进行翻译。支持多轮对话保持上下文。",
                "interface_index": 5 if is_win else 3,  # 翻译界面
            }
        )

        # 压制界面：Windows 为索引6，macOS 为索引4
        self.tips_data.append(
            {
                "title": "视频压制",
                "content": "在压制界面选择视频文件，将字幕烤制进视频并压制输出。可在设置中调整编码器、CRF、分辨率等参数。",
                "interface_index": 6 if is_win else 4,  # 压制界面
            }
        )

        self.tips_data.append(
            {
                "title": "设置配置",
                "content": "在设置界面配置各种API Key、模型路径、下载参数等。首次使用请先完成基础配置。",
                "interface_index": -1,  # 设置界面（最后一个）
            }
        )

    def show_teaching_tips(self):
        """显示新手引导"""
        if not self.tips_data:
            return

        self.current_step = 0
        self.show_current_tip()

    def show_current_tip(self):
        """显示当前步骤的引导"""
        if self.current_step >= len(self.tips_data):
            self.finish_tour()
            return

        tip_data = self.tips_data[self.current_step]
        self.create_teaching_tip(tip_data)

    def create_teaching_tip(self, tip_data):
        """创建单个引导提示"""
        # 切换到对应的界面
        if "interface_index" in tip_data and tip_data["interface_index"] is not None:
            interface_index = tip_data["interface_index"]
            if interface_index == -1:
                interface_index = len(self.parent.interface) - 1
            if hasattr(self.parent, "interface") and 0 <= interface_index < len(
                self.parent.interface
            ):
                self.parent.switchTo(self.parent.interface[interface_index])

        # 延迟显示，确保界面切换完成
        QTimer.singleShot(300, lambda: self._show_tip_delayed(tip_data))

    def _show_tip_delayed(self, tip_data):
        """延迟显示引导提示"""
        # 创建视图
        view = SimpleCardWidget()
        layout = QVBoxLayout(view)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title_label = StrongBodyLabel(tip_data["title"])
        content_label = BodyLabel(tip_data["content"])
        content_label.setWordWrap(True)

        # 进度
        progress_label = BodyLabel(f"{self.current_step + 1}/{len(self.tips_data)}")

        layout.addWidget(title_label)
        layout.addWidget(content_label)
        layout.addWidget(progress_label)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 上一步按钮
        if self.current_step > 0:
            previous_button = TransparentPushButton("上一步", view)
            previous_button.clicked.connect(self.previous_step)
            button_layout.addWidget(previous_button)

        # 跳过按钮
        skip_button = TransparentPushButton("跳过", view)
        skip_button.clicked.connect(self.finish_tour)
        button_layout.addWidget(skip_button)

        # 下一步/完成按钮
        if self.current_step < len(self.tips_data) - 1:
            next_button = PillPushButton("下一步", view)
            next_button.clicked.connect(self.next_step)
        else:
            next_button = PillPushButton("完成", view)
            next_button.clicked.connect(self.finish_tour)
        button_layout.addWidget(next_button)

        layout.addLayout(button_layout)

        self.teaching_tip = PopupTeachingTip(
            view=view,
            target=self.parent,
            duration=-1,  # 不自动关闭
        )
        self.teaching_tip.show()

    def next_step(self):
        """下一步"""
        if self.teaching_tip:
            try:
                self.teaching_tip.close()
            except Exception:
                pass
        self.current_step += 1
        self.show_current_tip()

    def previous_step(self):
        """上一步"""
        if self.teaching_tip:
            try:
                self.teaching_tip.close()
            except Exception:
                pass
        if self.current_step > 0:
            self.current_step -= 1
            self.show_current_tip()

    def finish_tour(self):
        """完成引导"""
        if self.teaching_tip:
            try:
                self.teaching_tip.close()
            except Exception:
                pass
        # 标记已完成首次运行
        cfg.set(cfg.isFirstRun, False)
        # 切换回主页
        if hasattr(self.parent, "interface") and len(self.parent.interface) > 0:
            self.parent.switchTo(self.parent.interface[0])

    def restart_tour(self):
        """重新开始引导"""
        try:
            if self.teaching_tip:
                self.teaching_tip.close()
        except Exception:
            pass
        self.current_step = 0
        self.teaching_tip = None
        self.show_teaching_tips()
