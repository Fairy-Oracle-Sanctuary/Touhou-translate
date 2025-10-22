# coding:utf-8

from pathlib import Path

import cv2
from PySide6.QtCore import QPoint, QRect, Qt, QTime
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    CheckBox,
    ComboBox,
    ExpandSettingCard,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    Pivot,
    PrimaryPushButton,
    ProgressBar,
    PushButton,
    ScrollArea,
    SettingCardGroup,
    Slider,
    StrongBodyLabel,
    TextEdit,
)


class VideocrStackedInterfaces(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 创建堆叠窗口
        self.pivot = Pivot(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.videocrInterface = VideocrInterface()
        # 这里假设YTDLPSettingInterface已经定义
        from ..components.config_card import YTDLPSettingInterface

        self.settingInterface = YTDLPSettingInterface()

        # 添加标签页
        self.addSubInterface(self.videocrInterface, "downloadInterface", "字幕提取")
        self.addSubInterface(self.settingInterface, "settingInterface", "设置")

        # 连接信号并初始化当前标签页
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.stackedWidget.setCurrentWidget(self.videocrInterface)
        self.pivot.setCurrentItem(self.videocrInterface.objectName())

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


class VideoPreviewWidget(CardWidget):
    """视频预览组件，支持框选功能"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.previewLabel = BodyLabel()
        self.previewLabel.setAlignment(Qt.AlignCenter)
        self.previewLabel.setMinimumSize(640, 360)
        # self.previewLabel.setStyleSheet("""
        #     BodyLabel {
        #         border: 2px solid #cccccc;
        #         border-radius: 8px;
        #         background: #1e1e1e;
        #         color: white;
        #         padding: 20px;
        #     }
        # """)
        self.previewLabel.setText("视频预览区域\n\n点击浏览按钮选择视频文件")

        # 框选相关变量
        self.selection_rect = None
        self.is_selecting = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.current_frame = None
        self.current_pixmap = None

        # 框选控制按钮
        self.control_layout = QHBoxLayout()
        self.select_btn = PushButton(FluentIcon.MOVE, "框选区域")
        self.clear_selection_btn = PushButton(FluentIcon.CANCEL, "清除框选")
        self.clear_selection_btn.setEnabled(False)

        self.control_layout.addWidget(self.select_btn)
        self.control_layout.addWidget(self.clear_selection_btn)
        self.control_layout.addStretch()

        self.vBoxLayout.addWidget(self.previewLabel)
        self.vBoxLayout.addLayout(self.control_layout)
        self.vBoxLayout.setContentsMargins(20, 20, 20, 20)

        # 连接信号
        self.select_btn.clicked.connect(self._start_selection)
        self.clear_selection_btn.clicked.connect(self._clear_selection)

        # 安装事件过滤器来捕获鼠标事件
        self.previewLabel.setMouseTracking(True)

        # 始终使用自定义事件处理器，但根据状态决定是否处理
        self.previewLabel.mousePressEvent = self._on_mouse_press
        self.previewLabel.mouseMoveEvent = self._on_mouse_move
        self.previewLabel.mouseReleaseEvent = self._on_mouse_release

    def _start_selection(self):
        """开始框选模式"""
        if self.current_frame is None:
            return

        self.is_selecting = True
        self.select_btn.setEnabled(False)
        self.previewLabel.setCursor(Qt.CrossCursor)
        # 清除提示文字但保留视频帧
        if self.previewLabel.text():
            self.previewLabel.setText("")

    def _clear_selection(self):
        """清除框选区域"""
        self.selection_rect = None
        self.is_selecting = False
        self.clear_selection_btn.setEnabled(False)
        self.select_btn.setEnabled(True)
        self.previewLabel.setCursor(Qt.ArrowCursor)
        self._update_preview()

    def _on_mouse_press(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.start_point = event.pos()
            self.end_point = event.pos()
            event.accept()
        else:
            # 调用父类的鼠标按下事件处理
            super().mousePressEvent(event)

    def _on_mouse_move(self, event):
        """处理鼠标移动事件"""
        if self.is_selecting:
            self.end_point = event.pos()
            self._update_preview()
            event.accept()
        else:
            # 调用父类的鼠标移动事件处理
            super().mouseMoveEvent(event)

    def _on_mouse_release(self, event):
        """处理鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.end_point = event.pos()
            self._finalize_selection()
            event.accept()
        else:
            # 调用父类的鼠标释放事件处理
            super().mouseReleaseEvent(event)

    def _finalize_selection(self):
        """完成框选"""
        # 确保矩形是有效的（宽度和高度为正）
        x1, y1 = self.start_point.x(), self.start_point.y()
        x2, y2 = self.end_point.x(), self.end_point.y()

        self.selection_rect = QRect(
            min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)
        )

        # 如果矩形太小，忽略它
        if self.selection_rect.width() < 10 or self.selection_rect.height() < 10:
            self.selection_rect = None
            self._update_preview()
            self._clear_selection()
            return

        self.clear_selection_btn.setEnabled(True)
        self.previewLabel.setCursor(Qt.ArrowCursor)
        self.is_selecting = False
        self._update_preview()

    def _update_preview(self):
        """更新预览图像，绘制框选区域"""
        if self.current_pixmap is None:
            return

        try:
            # 创建一个副本进行绘制
            display_pixmap = self.current_pixmap.copy()

            # 创建绘制器
            painter = QPainter(display_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # 如果有框选区域，绘制它
            if self.selection_rect and not self.is_selecting:
                pen = QPen(QColor(255, 0, 0), 2)
                painter.setPen(pen)
                painter.drawRect(self.selection_rect)

                # 绘制半透明填充
                fill_color = QColor(255, 0, 0, 50)
                painter.fillRect(self.selection_rect, fill_color)

            # 如果在绘制过程中，显示临时矩形
            elif self.is_selecting:
                temp_rect = QRect(
                    min(self.start_point.x(), self.end_point.x()),
                    min(self.start_point.y(), self.end_point.y()),
                    abs(self.end_point.x() - self.start_point.x()),
                    abs(self.end_point.y() - self.start_point.y()),
                )

                pen = QPen(QColor(255, 255, 0), 2, Qt.DashLine)
                painter.setPen(pen)
                painter.drawRect(temp_rect)

            painter.end()

            self.previewLabel.setPixmap(display_pixmap)
        except Exception as e:
            print(f"更新预览失败: {e}")

    def set_frame(self, frame_data):
        """设置视频帧"""
        if frame_data is not None:
            try:
                # 将OpenCV图像转换为QPixmap
                rgb_image = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(
                    rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888
                )

                # 创建Pixmap并缩放以适应预览区域
                pixmap = QPixmap.fromImage(qt_image)
                self.current_pixmap = pixmap.scaled(
                    self.previewLabel.width(),
                    self.previewLabel.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )

                self.current_frame = frame_data
                self._update_preview()
            except Exception as e:
                print(f"设置视频帧失败: {e}")
                self.current_frame = None
                self.current_pixmap = None
                self.previewLabel.clear()
                self.previewLabel.setText("无法加载视频帧")
        else:
            self.current_frame = None
            self.current_pixmap = None
            self.previewLabel.clear()
            self.previewLabel.setText("无法加载视频帧")

    def get_selection_rect(self):
        """获取框选区域（相对于原始图像的坐标）"""
        if not self.selection_rect or self.current_frame is None:
            return None

        try:
            # 计算缩放比例
            original_height, original_width = self.current_frame.shape[:2]

            if not self.current_pixmap:
                return None

            preview_width = self.current_pixmap.width()
            preview_height = self.current_pixmap.height()

            # 计算实际显示区域（保持宽高比）
            scale_x = original_width / preview_width
            scale_y = original_height / preview_height

            # 获取框选区域在原始图像中的坐标
            original_rect = QRect(
                int(self.selection_rect.x() * scale_x),
                int(self.selection_rect.y() * scale_y),
                int(self.selection_rect.width() * scale_x),
                int(self.selection_rect.height() * scale_y),
            )

            return original_rect
        except Exception as e:
            print(f"获取选择区域失败: {e}")
            return None

    def resizeEvent(self, event):
        """处理窗口大小改变事件"""
        super().resizeEvent(event)
        # 当窗口大小改变时，重新设置当前帧以更新显示
        if self.current_frame is not None:
            self.set_frame(self.current_frame)


class VideocrInterface(ScrollArea):
    """视频OCR字幕提取界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.video_path = None
        self.ocr_thread = None
        self.video_capture = None
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 0

        self._initWidget()
        self._connect_signals()

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
            FluentIcon.VIDEO,
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
            FluentIcon.SAVE, "输出文件", "设置字幕文件保存路径", self.fileSelectionGroup
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
            FluentIcon.LANGUAGE, "识别语言", "选择字幕文本的语言", self.settingsGroup
        )

        self.language_combo = ComboBox()
        self.language_combo.addItems(["中文", "英文", "日文", "韩文", "法文", "德文"])
        self.language_combo.setCurrentText("中文")
        self.languageCard.viewLayout.addWidget(self.language_combo)
        self.settingsGroup.addSettingCard(self.languageCard)

        # 位置设置卡片
        self.positionCard = ExpandSettingCard(
            FluentIcon.LAYOUT, "字幕位置", "指定字幕在视频中的位置", self.settingsGroup
        )

        self.position_combo = ComboBox()
        self.position_combo.addItems(["自动检测", "底部", "顶部", "全屏", "自定义区域"])
        self.position_combo.setCurrentText("自动检测")
        self.positionCard.viewLayout.addWidget(self.position_combo)
        self.settingsGroup.addSettingCard(self.positionCard)

        # 高级设置卡片
        self.advancedCard = ExpandSettingCard(
            FluentIcon.SETTING, "高级设置", "配置OCR处理参数", self.settingsGroup
        )

        self.use_gpu_check = CheckBox("使用GPU加速")
        self.use_gpu_check.setChecked(True)
        self.advanced_check = CheckBox("启用高级识别模式")

        self.advancedCard.viewLayout.addWidget(self.use_gpu_check)
        self.advancedCard.viewLayout.addWidget(self.advanced_check)
        self.settingsGroup.addSettingCard(self.advancedCard)

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
        self.video_preview = VideoPreviewWidget()
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
        title_label = StrongBodyLabel("处理进度")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        self.progress_bar = ProgressBar()
        self.progress_bar.setVisible(False)

        self.log_text = TextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("处理日志将显示在这里...")

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log_text)

    def _create_button_layout(self, main_layout):
        """创建操作按钮区域"""
        button_layout = QHBoxLayout()

        self.start_btn = PrimaryPushButton(FluentIcon.PLAY, "开始提取")
        self.start_btn.setEnabled(False)

        self.cancel_btn = PushButton(FluentIcon.CANCEL, "取消")
        self.cancel_btn.setEnabled(False)

        self.clear_btn = PushButton(FluentIcon.DELETE, "清空日志")

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.clear_btn)

        main_layout.addLayout(button_layout)

    def _connect_signals(self):
        """连接信号槽"""
        self.browse_video_btn.clicked.connect(self._browse_video_file)
        self.browse_output_btn.clicked.connect(self._browse_output_file)
        self.start_btn.clicked.connect(self._start_ocr)
        self.cancel_btn.clicked.connect(self._cancel_ocr)
        self.clear_btn.clicked.connect(self._clear_log)
        self.progress_slider.valueChanged.connect(self._seek_video)
        self.advanced_check.stateChanged.connect(self._toggle_advanced_settings)
        self.position_combo.currentTextChanged.connect(self._on_position_changed)

    def _browse_video_file(self):
        """浏览视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            str(Path.home()),
            "视频文件 (*.mp4 *.avi *.mkv *.mov *.webm *.flv *.wmv);;所有文件 (*.*)",
        )

        if file_path:
            self.video_path = file_path
            self.video_path_edit.setText(file_path)

            # 自动生成输出文件路径
            output_path = Path(file_path).with_suffix(".srt")
            self.output_path_edit.setText(str(output_path))

            # 加载视频
            self._load_video(file_path)

            self.start_btn.setEnabled(True)

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
            "字幕文件 (*.srt *.ass *.vtt);;所有文件 (*.*)",
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

            self._log_message(f"成功加载视频: {Path(video_path).name}")
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

        # 更新UI状态
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 开始OCR线程
        # 这里开始提取

    def _cancel_ocr(self):
        """取消OCR处理"""
        if self.ocr_thread and self.ocr_thread.isRunning():
            self.ocr_thread.stop()
            self.ocr_thread.wait()
            self._log_message("处理已取消")

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
        lang_map = {
            "中文": "ch",
            "英文": "en",
            "日文": "ja",
            "韩文": "ko",
            "法文": "fr",
            "德文": "de",
        }
        return lang_map.get(self.language_combo.currentText(), "ch")

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

    def _show_error(self, message):
        """显示错误信息"""
        InfoBar.error(
            title="错误",
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )

    def _show_success(self, message):
        """显示成功信息"""
        InfoBar.success(
            title="成功",
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )

    def _on_ocr_finished(self, success):
        """OCR处理完成"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

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
