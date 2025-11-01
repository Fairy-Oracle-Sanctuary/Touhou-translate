# coding:utf-8

from pathlib import Path

import cv2
from PySide6.QtCore import Qt, QTime, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CaptionLabel,
    CardWidget,
    ComboBox,
    ExpandSettingCard,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    Pivot,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    SettingCardGroup,
    Slider,
    StrongBodyLabel,
    TextEdit,
)
from qfluentwidgets import FluentIcon as FIF

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.setting import subtitle_positions_list, videocr_languages_dict
from ..components.config_card import OCRSettingInterface
from ..service.project_service import Project
from ..service.video_service import VideoPreview
from .videocr_task_interface import OcrTaskInterface


class VideocrStackedInterfaces(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 创建堆叠窗口
        self.pivot = Pivot(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.videocrInterface = VideocrInterface()
        self.taskInterface = OcrTaskInterface()
        self.settingInterface = OCRSettingInterface()

        # 添加标签页
        self.addSubInterface(self.videocrInterface, "videocrInterface", "字幕提取")
        self.addSubInterface(self.taskInterface, "taskInterface", "提取任务")
        self.addSubInterface(self.settingInterface, "settingInterface", "高级设置")

        # 连接信号并初始化当前标签页
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.videocrInterface)
        self.pivot.setCurrentItem(self.videocrInterface.objectName())

        self.settingInterface.changeSelectionSignal.connect(self.changeSelection)
        self.videocrInterface.addOcrTask.connect(self.taskInterface.addOcrTask)
        self.taskInterface.log_signal.connect(self.videocrInterface._log_message)
        self.taskInterface.returnOcrTask.connect(self.videocrInterface.updateOcrTask)

        self.vBoxLayout.setContentsMargins(30, 0, 30, 30)
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignHCenter)
        self.vBoxLayout.addWidget(self.stackedWidget)

        self.resize(780, 800)
        self.setObjectName("VideocrStackedInterfaces")

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
        self.videocrInterface._auto_start_btn_set()

    def changeSelection(self, isUseDualZone):
        if isUseDualZone:
            self.videocrInterface.video_preview.set_max_crop_boxes(2)
        else:
            self.videocrInterface.video_preview.set_max_crop_boxes(1)


class VideocrInterface(ScrollArea):
    """视频OCR字幕提取界面"""

    addOcrTask = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.video_path = None
        self.ocr_thread = None
        self.video_capture = None
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0
        self.ocr_tasks = []

        self._initWidget()
        self._connect_signals()

        self.installEventFilter(self)

    def _initWidget(self):
        """初始化界面"""
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setObjectName("videocrInterface")
        self.enableTransparentBackground()

        # 主布局
        main_layout = QVBoxLayout(self.view)

        # 文件选择卡片组
        self.fileSelectionGroup = SettingCardGroup("文件选择", self.view)
        self._create_file_selection_cards()
        main_layout.addWidget(self.fileSelectionGroup)

        # OCR设置卡片组
        self.settingsGroup = SettingCardGroup("OCR设置", self.view)
        self._create_settings_cards()
        main_layout.addWidget(self.settingsGroup)

        # 视频预览卡片
        self.previewCard = CardWidget(self.view)
        self._create_preview_card()
        main_layout.addWidget(self.previewCard)

        # 进度显示卡片
        self.progressCard = CardWidget(self.view)
        self._create_progress_card()
        main_layout.addWidget(self.progressCard)

        # 操作按钮区域
        self._create_button_layout(main_layout)

        main_layout.addStretch()

    def _create_file_selection_cards(self):
        """创建文件选择卡片"""
        # 视频文件选择卡片
        self.videoFileCard = ExpandSettingCard(
            FIF.VIDEO,
            "视频文件",
            "选择要提取字幕的视频文件",
            self.fileSelectionGroup,
        )

        video_layout = QHBoxLayout()
        self.video_path_edit = LineEdit()
        self.video_path_edit.setPlaceholderText("选择视频文件...")
        self.video_path_edit.setReadOnly(True)
        self.browse_video_btn = PushButton("浏览文件")
        video_layout.addWidget(self.video_path_edit, 1)
        video_layout.addWidget(self.browse_video_btn)

        self.videoFileCard.viewLayout.addLayout(video_layout)
        self.fileSelectionGroup.addSettingCard(self.videoFileCard)

        # 输出文件选择卡片
        self.outputFileCard = ExpandSettingCard(
            FIF.SAVE, "输出文件", "设置字幕文件保存路径", self.fileSelectionGroup
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

    def _create_preview_card(self):
        """创建视频预览卡片"""
        layout = QVBoxLayout(self.previewCard)

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

        layout.addLayout(control_layout)

    def _create_progress_card(self):
        """创建进度显示卡片"""
        layout = QVBoxLayout(self.progressCard)

        # 标题
        title_layout = QHBoxLayout()
        title_label = StrongBodyLabel("处理日志")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        self.log_text = TextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("处理日志将显示在这里...")

        layout.addWidget(self.log_text)

    def _create_button_layout(self, main_layout):
        """创建操作按钮区域"""
        button_layout = QHBoxLayout()

        self.start_btn = PrimaryPushButton(FIF.PLAY, "添加任务")
        self.start_btn.setEnabled(False)

        self.previous_btn = PushButton(FIF.UP, "上一个")
        self.previous_btn.setEnabled(False)

        self.next_btn = PushButton(FIF.DOWN, "下一个")
        self.next_btn.setEnabled(False)

        self.clear_btn = PushButton(FIF.DELETE, "清空日志")

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.previous_btn)
        button_layout.addWidget(self.next_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.clear_btn)

        main_layout.addLayout(button_layout)

    def _connect_signals(self):
        """连接信号槽"""
        self.browse_video_btn.clicked.connect(self._browse_video_file)
        self.browse_output_btn.clicked.connect(self._browse_output_file)
        self.start_btn.clicked.connect(self._start_ocr)
        self.clear_btn.clicked.connect(self._clear_log)
        self.progress_slider.valueChanged.connect(self._seek_video)
        self.language_combo.currentTextChanged.connect(
            lambda: cfg.set(cfg.ocr_lang, self.language_combo.currentText())
        )
        self.position_combo.currentTextChanged.connect(self._on_position_changed)
        self.video_preview.isCropChoose.connect(self._start_btn_enabled)
        self.previous_btn.clicked.connect(self.switch_previous_file)
        self.next_btn.clicked.connect(self.switch_next_file)
        event_bus.add_video_signal.connect(self.loadVideoFromProject)

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

    def _start_btn_enabled(self, enabled):
        """设置开始按钮可用性"""
        self.start_btn.setEnabled(enabled)

    def _auto_start_btn_set(self):
        """自动设置开始按钮可用性"""
        if (
            self.video_preview.crop_boxes.__len__() == 2
            if cfg.get(cfg.useDualZone)
            else 1
        ):
            self.start_btn.setEnabled(True)
        else:
            self.start_btn.setEnabled(False)

    def _browse_video_file(self):
        """浏览视频文件"""
        video_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            str(Path.home()),
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv);;所有文件 (*.*)",
        )

        if video_path:
            self.video_path = video_path
            self.video_path_edit.setText(video_path)

            # 自动生成输出文件路径
            output_path = Path(video_path).with_suffix(".srt")
            self.output_path_edit.setText(str(output_path))

            # 加载视频
            self._load_video(video_path)

            # 更新上下按钮状态
            self.update_adjacent_button()

            self.video_preview.select_btn.setEnabled(True)

    def _browse_output_file(self):
        """浏览输出文件"""
        if not self.video_path:
            InfoBar.error(
                title="错误",
                content="请先选择视频文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存字幕文件",
            self.output_path_edit.text(),
            "字幕文件 (*.srt);;所有文件 (*.*)",
        )

        if file_path:
            self.output_path_edit.setText(file_path)

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
            else:
                self._log_message(f"读取帧 {frame_number} 失败", is_error=True)

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

    def _start_ocr(self):
        """开始OCR处理"""
        if not self.video_path:
            self._show_error("请先选择视频文件")
            return

        if not self.output_path_edit.text():
            self._show_error("请设置输出文件路径")
            return

        # 检查是否需要框选区域
        if self.position_combo.currentText() == "自定义区域":
            selection_rect = self.video_preview.get_selection_rect()
            if not selection_rect:
                self._show_error("请先框选字幕区域")
                return
            self._log_message(
                f"使用自定义区域: {selection_rect.x()}, {selection_rect.y()}, {selection_rect.width()}x{selection_rect.height()}"
            )

        # 组合参数发送信号
        args = self._get_args()
        self.addOcrTask.emit(args)

    def _get_args(self):
        """获取参数"""
        args = {}

        args["video_path"] = self.video_path
        args["file_path"] = self.output_path_edit.text()
        args["lang"] = self._get_language_code()
        args["time_start"] = "0:00"
        args["time_end"] = ""
        args["conf_threshold"] = cfg.get(cfg.confThreshold)
        args["sim_threshold"] = cfg.get(cfg.simThreshold)
        args["max_merge_gap_sec"] = cfg.get(cfg.maxMergeGap)
        args["use_fullframe"] = False
        args["use_gpu"] = cfg.get(cfg.useGpu)
        args["use_angle_cls"] = cfg.get(cfg.useAngleCls)
        args["use_server_model"] = cfg.get(cfg.useServerModel)
        args["brightness_threshold"] = cfg.get(cfg.brightnessThreshold)
        args["ssim_threshold"] = cfg.get(cfg.ssimThreshold)
        args["subtitle_position"] = self._get_subtitle_position()
        args["frames_to_skip"] = cfg.get(cfg.framesToSkip)
        args["crop_zones"] = self._get_crop_zones()
        args["ocr_image_max_width"] = cfg.get(cfg.ocrImageMaxWidth)
        args["post_processing"] = cfg.get(cfg.postProcessing)
        args["min_subtitle_duration_sec"] = cfg.get(cfg.minSubtitleDuration)
        args["gpu_env"] = cfg.get(cfg.gpuEnv)

        return args

    def _clear_log(self):
        """清空日志"""
        self.log_text.clear()

    def _toggle_advanced_settings(self):
        """切换高级设置显示"""
        # 这里可以添加高级设置的显示/隐藏逻辑
        pass

    def _on_position_changed(self, position):
        """字幕位置选项改变时的处理"""
        if position == "自定义区域":
            self._log_message("请使用框选工具在视频预览中选择字幕区域")
        elif position == "自动检测":
            self.video_preview._clear_selection()

    def _get_language_code(self):
        """获取语言代码"""
        return videocr_languages_dict.get(self.language_combo.currentText(), "ch")

    def _get_subtitle_position(self):
        """获取字幕对齐方式"""
        return subtitle_positions_list.get(self.position_combo.currentText(), "center")

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

    def _log_message(self, message, is_error=False):
        """添加日志消息"""
        timestamp = QTime.currentTime().toString("hh:mm:ss")
        if is_error:
            formatted_message = f'<font color="red">[{timestamp}] {message}</font>'
        else:
            formatted_message = f"[{timestamp}] {message}"

        self.log_text.append(formatted_message)

        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def switch_previous_file(self):
        """切换上一个文件"""
        previous_path = Project.get_previous_path(self.video_path)
        if previous_path:
            self.video_path = previous_path

            # 自动生成输出文件路径
            output_path = Path(self.video_path).with_suffix(".srt")

            # 更新界面
            self.video_path_edit.setText(str(self.video_path))
            self.output_path_edit.setText(str(output_path))
            self._load_video(self.video_path)
            self.update_adjacent_button()

    def switch_next_file(self):
        """切换上一个文件"""
        next_path = Project.get_next_path(self.video_path)
        if next_path:
            self.video_path = next_path

            # 自动生成输出文件路径
            output_path = Path(self.video_path).with_suffix(".srt")

            # 更新界面
            self.video_path_edit.setText(str(self.video_path))
            self.output_path_edit.setText(str(output_path))
            self._load_video(self.video_path)
            self.update_adjacent_button()

    def update_adjacent_button(self):
        """更新上一个/下一个按钮状态"""
        adjacent_file_exists = Project.isAdjacentFileExists(self.video_path)
        if adjacent_file_exists[0]:
            self.previous_btn.setEnabled(True)
        else:
            self.previous_btn.setEnabled(False)
        if adjacent_file_exists[1]:
            self.next_btn.setEnabled(True)
        else:
            self.next_btn.setEnabled(False)

    def _show_error(self, message):
        """显示错误信息"""
        event_bus.notification_service.show_error("错误", message)

    def _show_success(self, message):
        """显示成功信息"""
        event_bus.notification_service.show_success("成功", message)

    def _on_ocr_finished(self, success):
        """OCR处理完成"""
        self.start_btn.setEnabled(True)

        if success:
            self._show_success("字幕提取完成！")
        else:
            self._show_error("字幕提取失败")

    def _on_ocr_error(self, error_message):
        """OCR处理出错"""
        self._log_message(f"处理出错: {error_message}", is_error=True)
        self._on_ocr_finished(False)

    def closeEvent(self, event):
        """关闭事件处理"""
        if self.ocr_thread and self.ocr_thread.isRunning():
            self.ocr_thread.stop()
            self.ocr_thread.wait()

        if self.video_capture:
            self.video_capture.release()

        super().closeEvent(event)

    def updateOcrTask(self, isRepeat, ocr_tasks, isMessage):
        if isRepeat and isMessage:
            self._show_error("重复的任务")
        elif not isRepeat and isMessage:
            self._show_success(f"任务-{ocr_tasks[-1]}-添加成功！")
        self.ocr_tasks = ocr_tasks

    def loadVideoFromProject(self, video_path):
        if video_path:
            self.video_path = video_path
            self.video_path_edit.setText(video_path)

            # 自动生成输出文件路径
            output_path = Path(video_path).with_suffix(".srt")
            self.output_path_edit.setText(str(output_path))

            # 加载视频
            self._load_video(video_path)

            self.video_preview.select_btn.setEnabled(True)
