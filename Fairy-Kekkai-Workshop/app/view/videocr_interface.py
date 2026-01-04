# videocr_task_interface.py
# coding:utf-8


import os
import re
import tempfile

import cv2
from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
)
from qfluentwidgets import (
    CaptionLabel,
    CardWidget,
    ComboBox,
    Dialog,
    ExpandSettingCard,
    PushButton,
    Slider,
    StrongBodyLabel,
    TextEdit,
)
from qfluentwidgets import FluentIcon as FIF

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.setting import subtitle_positions_list, videocr_languages_dict
from ..components.base_function_interface import BaseFunctionInterface
from ..components.base_stacked_interface import BaseStackedInterfaces
from ..components.config_card import OCRSettingInterface
from ..service.video_service import VideoPreview
from ..view.videocr_task_interface import OcrTaskInterface


class VideocrStackedInterfaces(BaseStackedInterfaces):
    """视频OCR堆叠界面"""

    def __init__(self, parent=None):
        super().__init__(
            parent=parent,
            main_interface_class=VideocrInterface,
            task_interface_class=OcrTaskInterface,
            setting_interface_class=OCRSettingInterface,
            interface_name="字幕提取",
        )

        # 连接专用信号
        self.mainInterface.addTask.connect(self.taskInterface.addOcrTask)
        self.taskInterface.log_signal.connect(self.mainInterface._log_message)
        self.taskInterface.returnTask.connect(self.mainInterface.updateTask)
        self.settingInterface.changeSelectionSignal.connect(self.changeSelection)

    def changeSelection(self, isUseDualZone):
        if isUseDualZone:
            self.mainInterface.video_preview.set_max_crop_boxes(2)
        else:
            self.mainInterface.video_preview.set_max_crop_boxes(1)

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        self.mainInterface.refresh_start_btn()


class VideocrInterface(BaseFunctionInterface):
    """视频OCR字幕提取界面"""

    def __init__(self, parent=None):
        self.video_capture = None
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0
        self.video_preview = None

        super().__init__(parent, "提取字幕")

        self.file_extension = "*.mp4"
        self.default_output_suffix = ".srt"
        self.special_filename_mapping = {"生肉.mp4": "原文.srt"}

    def get_input_icon(self):
        return FIF.VIDEO

    def _create_settings_cards(self):
        """创建OCR设置卡片"""
        # 语言设置卡片
        self.languageCard = ExpandSettingCard(
            FIF.LANGUAGE, "识别语言", "选择字幕文本的语言", self.settingsGroup
        )

        self.language_combo = ComboBox()
        self.language_combo.addItems(videocr_languages_dict.keys())
        self.language_combo.setCurrentText(cfg.get(cfg.ocr_lang))
        self.languageCard.viewLayout.addWidget(self.language_combo)
        self.settingsGroup.addSettingCard(self.languageCard)

        # 位置设置卡片
        self.positionCard = ExpandSettingCard(
            FIF.LAYOUT, "文本对齐", "指定字幕的对齐方式", self.settingsGroup
        )

        self.position_combo = ComboBox()
        self.position_combo.addItems(subtitle_positions_list.keys())
        self.position_combo.setCurrentText("居中")
        self.positionCard.viewLayout.addWidget(self.position_combo)
        self.settingsGroup.addSettingCard(self.positionCard)

        # 连接信号
        self.language_combo.currentTextChanged.connect(
            lambda: cfg.set(cfg.ocr_lang, self.language_combo.currentText())
        )
        self.position_combo.currentTextChanged.connect(self._on_position_changed)

    def create_preview_card(self):
        """创建视频预览卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)

        # 标题
        title_layout = QHBoxLayout()
        title_label = StrongBodyLabel("视频预览")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # 视频预览组件
        self.video_preview = VideoPreview()
        layout.addWidget(self.video_preview)

        # 进度条和控制
        control_layout = QHBoxLayout()
        self.progress_slider = Slider(Qt.Horizontal)
        self.progress_slider.setEnabled(False)

        self.frame_label = CaptionLabel("帧: -/-")
        self.time_label = CaptionLabel("时间: -/-")

        control_layout.addWidget(self.progress_slider, 4)
        control_layout.addWidget(self.frame_label, 1)
        control_layout.addWidget(self.time_label, 1)

        self.log_text = TextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("处理日志将显示在这里...")

        layout.addLayout(control_layout)
        layout.addWidget(self.log_text)

        # 连接信号
        self.progress_slider.valueChanged.connect(self._seek_video)
        self.video_preview.isCropChoose.connect(self._start_btn_enabled)

        return card

    def refresh_start_btn(self):
        """刷新开始按钮状态"""
        if self.video_preview.crop_boxes.__len__() >= self.video_preview.max_crop_boxes:
            self.start_btn.setEnabled(True)
        else:
            self.start_btn.setEnabled(False)

    def _create_button_layout(self, main_layout):
        """创建操作按钮区域"""
        super()._create_button_layout(main_layout)

        # 为OCR界面添加清空日志按钮
        self.clear_btn = PushButton(FIF.DELETE, "清空日志")
        main_layout.itemAt(main_layout.count() - 1).layout().addWidget(self.clear_btn)
        self.clear_btn.clicked.connect(self._clear_log)

    def _connect_signals(self):
        """连接信号槽"""
        super()._connect_signals()
        event_bus.add_video_signal.connect(self.loadVideoFromProject)

    def _start_btn_enabled(self, enabled):
        """设置开始按钮可用性"""
        self.start_btn.setEnabled(enabled)

    def _on_position_changed(self, position):
        """字幕位置选项改变时的处理"""
        if position == "自定义区域":
            self._log_message("请使用框选工具在视频预览中选择字幕区域")
        elif position == "自动检测":
            self.video_preview._clear_selection()

    def load_file_content(self, file_path):
        """加载视频文件"""
        self._load_video(file_path)

    def _load_video(self, video_path):
        """加载视频文件"""
        try:
            # 释放之前的视频捕获对象
            if self.video_capture:
                self.video_capture.release()

            self.video_capture = cv2.VideoCapture(video_path)
            if not self.video_capture.isOpened():
                raise Exception("无法打开视频文件")

            self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            self.current_frame = 0

            # 设置进度条
            self.progress_slider.setRange(0, self.total_frames - 1)
            self.progress_slider.setEnabled(True)

            # 显示第一帧
            self._update_video_frame(0)

            # 刷新按钮状态
            self.video_preview.refresh_select_btn()
            self.refresh_start_btn()

            self._log_message(f"成功加载视频: {video_path}")
            self._log_message(f"总帧数: {self.total_frames}, FPS: {self.fps:.2f}")

        except Exception as e:
            self._log_message(f"加载视频失败: {str(e)}", is_error=True)

    def _update_video_frame(self, frame_number):
        """更新视频帧显示"""
        if self.video_capture and 0 <= frame_number < self.total_frames:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = self.video_capture.read()

            if ret:
                self.video_preview.set_frame(frame)
                self.current_frame = frame_number

                # 更新帧和时间信息
                self.frame_label.setText(f"帧: {frame_number + 1}/{self.total_frames}")
                if self.fps > 0:
                    current_time = frame_number / self.fps
                    total_time = self.total_frames / self.fps
                    self.time_label.setText(
                        f"时间: {self._format_time(current_time)}/{self._format_time(total_time)}"
                    )

    def _format_time(self, seconds):
        """格式化时间显示"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def _seek_video(self, value):
        """跳转到指定帧"""
        if value != self.current_frame:
            self._update_video_frame(value)

    def _start_processing(self):
        """开始OCR处理"""
        # 检测paddleocr路径内是否有中文
        if re.search("[\u4e00-\u9fff\u3400-\u4dbf]", cfg.get(cfg.paddleocrPath)):
            dialog = Dialog(
                self.tr("警告"),
                self.tr(f"PaddleOCR路径 {cfg.get(cfg.paddleocrPath)} 不能包含中文字符"),
                self.window(),
            )
            dialog.yesButton.setText("确认")
            dialog.cancelButton.setVisible(False)
            dialog.exec()
            return

        # 检测supportFiles路径是否有中文
        if re.search("[\u4e00-\u9fff\u3400-\u4dbf]", cfg.get(cfg.supportFilesPath)):
            dialog = Dialog(
                self.tr("警告"),
                self.tr(
                    f"支持文件夹路径 {cfg.get(cfg.supportFilesPath)} 不能包含中文字符"
                ),
                self.window(),
            )
            dialog.yesButton.setText("确认")
            dialog.cancelButton.setVisible(False)
            dialog.exec()
            return

        # 检测临时文件夹路径是否有中文
        temp_path = tempfile.gettempdir()
        if re.search("[\u4e00-\u9fff\u3400-\u4dbf]", temp_path):
            dialog = Dialog(
                self.tr("警告"),
                self.tr(f"临时文件夹路径 {temp_path} 不能包含中文字符"),
                self.window(),
            )
            dialog.yesButton.setText("确认")
            dialog.cancelButton.setVisible(False)
            dialog.exec()
            return

        if not os.path.exists(cfg.get(cfg.paddleocrPath)):
            self.show_error_message(
                f"PaddleOCR路径不存在: {cfg.get(cfg.paddleocrPath)}"
            )
            return

        if not os.path.exists(cfg.get(cfg.supportFilesPath)):
            self.show_error_message(
                f"支持文件夹路径不存在: {cfg.get(cfg.supportFilesPath)}"
            )
            return

        if not self.file_path:
            self.show_error_message("请先选择视频文件")
            return

        if not self.output_path_edit.text():
            self.show_error_message("请设置输出文件路径")
            return

        # 检查是否需要框选区域
        if self.position_combo.currentText() == "自定义区域":
            selection_rect = self.video_preview.get_selection_rect()
            if not selection_rect:
                self.show_error_message("请先框选字幕区域")
                return
            self._log_message(
                f"使用自定义区域: {selection_rect.x()}, {selection_rect.y()}, {selection_rect.width()}x{selection_rect.height()}"
            )

        # 组合参数发送信号
        args = self._get_args()
        self.addTask.emit(args)

    def _get_args(self):
        """获取OCR参数"""
        args = {}
        args["video_path"] = self.file_path
        args["file_path"] = self.output_path_edit.text()
        args["lang"] = videocr_languages_dict.get(
            self.language_combo.currentText(), "ch"
        )
        args["time_start"] = "0:00"
        args["time_end"] = ""
        args["conf_threshold"] = cfg.get(cfg.confThreshold)
        args["sim_threshold"] = cfg.get(cfg.simThreshold)
        args["max_merge_gap_sec"] = cfg.get(cfg.maxMergeGap)
        args["use_fullframe"] = False
        args["use_gpu"] = cfg.get(cfg.useGpu)
        args["use_angle_cls"] = cfg.get(cfg.useAngleCls)
        args["use_server_model"] = cfg.get(cfg.useServerModel)
        # args["brightness_threshold"] = cfg.get(cfg.brightnessThreshold)
        args["ssim_threshold"] = cfg.get(cfg.ssimThreshold)
        args["subtitle_position"] = subtitle_positions_list.get(
            self.position_combo.currentText(), "center"
        )
        args["frames_to_skip"] = cfg.get(cfg.framesToSkip)
        args["crop_zones"] = self._get_crop_zones()
        args["ocr_image_max_width"] = cfg.get(cfg.ocrImageMaxWidth)
        args["post_processing"] = cfg.get(cfg.postProcessing)
        args["min_subtitle_duration_sec"] = cfg.get(cfg.minSubtitleDuration)
        args["gpu_env"] = cfg.get(cfg.gpuEnv)

        return args

    def _get_crop_zones(self):
        """获取框选区域"""
        crop_zones = []
        crop_boxes = self.video_preview.crop_boxes
        for zones in crop_boxes:
            zones = zones["coords"]
            crop_zones.append(
                {
                    "x": zones["crop_x"],
                    "y": zones["crop_y"],
                    "width": zones["crop_width"],
                    "height": zones["crop_height"],
                }
            )
        return crop_zones

    def _clear_log(self):
        """清空日志"""
        if hasattr(self, "log_text"):
            self.log_text.clear()

    def _log_message(self, message, is_error=False, is_flush=False):
        """添加日志消息"""
        if not hasattr(self, "log_text"):
            return

        timestamp = QTime.currentTime().toString("hh:mm:ss")
        if is_error:
            formatted_message = f'<font color="red">[{timestamp}] {message}</font>'
        else:
            formatted_message = f"[{timestamp}] {message}"

        if is_flush:
            current_text = self.log_text.toPlainText()
            lines = current_text.split("\n")
            if lines:
                lines.pop()
            self.log_text.setPlainText("\n".join(lines))

        self.log_text.append(formatted_message)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def loadVideoFromProject(self, video_path):
        """从项目加载视频"""
        if video_path:
            self.file_path = video_path
            self.input_path_edit.setText(video_path)
            output_path = self._generate_output_path(video_path)
            self.output_path_edit.setText(str(output_path))
            self.load_file_content(video_path)
            self.video_preview.select_btn.setEnabled(True)

    def closeEvent(self, event):
        """关闭事件处理"""
        if self.video_capture:
            self.video_capture.release()
        super().closeEvent(event)
