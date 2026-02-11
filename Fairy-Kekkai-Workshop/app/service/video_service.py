# coding:utf-8

import math

import cv2
from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    FluentIcon,
    PushButton,
    SpinBox,
    LineEdit,
)

from ..common.config import cfg


class VideoPreview(CardWidget):
    """视频预览组件，支持框选功能"""

    isCropChoose = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.vBoxLayout = QVBoxLayout(self)
        self.previewLabel = BodyLabel()
        self.previewLabel.setAlignment(Qt.AlignCenter)
        self.previewLabel.setMinimumSize(640, 360)
        self.previewLabel.setText("视频预览区域\n\n点击浏览按钮选择视频文件")

        # 框选相关变量
        self.crop_boxes = []  # 存储框选区域
        self.drawn_rect_ids = []  # 存储绘制的矩形ID
        self.start_point_img = None  # 框选起点（预览图像坐标）
        self.end_point_img = None  # 框选终点（预览图像坐标）
        self.is_selecting = False  # 是否正在框选
        self.current_frame = None  # 当前视频帧
        self.current_pixmap = None  # 当前显示的Pixmap
        self.original_frame_size = None  # 原始视频帧尺寸
        self.max_crop_boxes = (
            2 if cfg.get(cfg.useDualZone) else 1
        )  # 可以修改这个值来控制最大框选数量

        # 框选控制按钮
        self.control_layout = QHBoxLayout()
        self.select_btn = PushButton(FluentIcon.MOVE, "框选区域")
        self.select_btn.setEnabled(False)
        self.clear_selection_btn = PushButton(FluentIcon.CANCEL, "清除框选")
        self.clear_selection_btn.setEnabled(False)

        self.control_layout.addWidget(self.select_btn)
        self.control_layout.addWidget(self.clear_selection_btn)
        self.control_layout.addStretch()

        # 框选坐标显示和编辑区域
        self.coords_layout = QHBoxLayout()
        self.coords_label = CaptionLabel("框选区域坐标: 未选择")
        self.coords_layout.addWidget(self.coords_label)
        self.coords_layout.addStretch()
        
        # 坐标编辑区域
        self.coord_edit_layout = QVBoxLayout()
        self.coord_inputs = []  # 存储每个区域的坐标输入框
        self.coord_edit_widgets = []  # 存储坐标编辑组件

        self.vBoxLayout.addWidget(self.previewLabel)
        self.vBoxLayout.addLayout(self.control_layout)
        self.vBoxLayout.addLayout(self.coords_layout)
        self.vBoxLayout.addLayout(self.coord_edit_layout)
        self.vBoxLayout.setContentsMargins(20, 20, 20, 20)

        # 连接信号
        self.select_btn.clicked.connect(self._start_selection)
        self.clear_selection_btn.clicked.connect(self._clear_selection)

        # 安装事件过滤器来捕获鼠标事件
        self.previewLabel.setMouseTracking(True)

        # 始终使用自定义事件处理器
        self.previewLabel.mousePressEvent = self._on_mouse_press
        self.previewLabel.mouseMoveEvent = self._on_mouse_move
        self.previewLabel.mouseReleaseEvent = self._on_mouse_release

    def refresh_select_btn(self):
        """刷新框选按钮状态"""
        if self.crop_boxes.__len__() >= self.max_crop_boxes:
            self.select_btn.setEnabled(False)
        else:
            self.select_btn.setEnabled(True)

    def _start_selection(self):
        """开始框选模式"""
        if self.current_frame is None:
            return

        self.is_selecting = True
        # self.select_btn.setEnabled(False)
        self.previewLabel.setCursor(Qt.CrossCursor)

        # 清除提示文字但保留视频帧
        if self.previewLabel.text():
            self.previewLabel.setText("")

        # 更新坐标显示
        self.coords_label.setText("框选区域坐标: 正在选择...")

    def _clear_selection(self):
        """清除框选区域"""
        self.crop_boxes.clear()
        self.drawn_rect_ids.clear()
        self.start_point_img = None
        self.end_point_img = None
        self.is_selecting = False
        self.clear_selection_btn.setEnabled(False)
        self.select_btn.setEnabled(True)
        self.previewLabel.setCursor(Qt.ArrowCursor)

        # 更新坐标显示（这会清除坐标编辑组件）
        self._update_coords_display()

        # 重绘画布
        self._redraw_canvas_and_boxes()

        # 发送信号
        self.isCropChoose.emit(False)

    def _on_mouse_press(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton and self.is_selecting:
            # 获取鼠标在预览图像中的位置
            mouse_pos = event.pos()
            preview_rect = self.previewLabel.rect()
            pixmap_rect = self.current_pixmap.rect() if self.current_pixmap else QRect()

            # 计算图像在预览区域中的偏移量（居中显示）
            image_offset_x = (preview_rect.width() - pixmap_rect.width()) // 2
            image_offset_y = (preview_rect.height() - pixmap_rect.height()) // 2

            # 计算鼠标在图像上的位置
            img_x = mouse_pos.x() - image_offset_x
            img_y = mouse_pos.y() - image_offset_y

            # 检查是否在图像范围内
            if 0 <= img_x < pixmap_rect.width() and 0 <= img_y < pixmap_rect.height():
                self.start_point_img = (img_x, img_y)
                event.accept()
                return

        event.ignore()

    def _on_mouse_move(self, event):
        """处理鼠标移动事件"""
        if self.is_selecting and self.start_point_img is not None:
            # 获取鼠标在预览图像中的位置
            mouse_pos = event.pos()
            preview_rect = self.previewLabel.rect()
            pixmap_rect = self.current_pixmap.rect() if self.current_pixmap else QRect()

            # 计算图像在预览区域中的偏移量（居中显示）
            image_offset_x = (preview_rect.width() - pixmap_rect.width()) // 2
            image_offset_y = (preview_rect.height() - pixmap_rect.height()) // 2

            # 计算鼠标在图像上的位置
            img_x = mouse_pos.x() - image_offset_x
            img_y = mouse_pos.y() - image_offset_y

            # 限制在图像范围内
            img_x = max(0, min(img_x, pixmap_rect.width() - 1))
            img_y = max(0, min(img_y, pixmap_rect.height() - 1))

            self.end_point_img = (img_x, img_y)

            # 重绘画布和临时矩形
            self._redraw_canvas_and_boxes(preview_mode=True)

            # 绘制临时矩形
            if self.start_point_img and self.end_point_img:
                self._draw_temp_rectangle()

            event.accept()
        else:
            event.ignore()

    def _on_mouse_release(self, event):
        """处理鼠标释放事件"""
        if (
            event.button() == Qt.LeftButton
            and self.is_selecting
            and self.start_point_img is not None
            and self.end_point_img is not None
        ):
            # 计算矩形坐标
            rect_x1_img = min(self.start_point_img[0], self.end_point_img[0])
            rect_y1_img = min(self.start_point_img[1], self.end_point_img[1])
            rect_x2_img = max(self.start_point_img[0], self.end_point_img[0])
            rect_y2_img = max(self.start_point_img[1], self.end_point_img[1])

            # 重置起点和终点
            self.start_point_img = None
            self.end_point_img = None

            # 检查矩形是否太小
            min_draw_size = 7
            if (rect_x2_img - rect_x1_img) < min_draw_size or (
                rect_y2_img - rect_y1_img
            ) < min_draw_size:
                self._redraw_canvas_and_boxes()
                return

            # 转换为原始图像坐标
            if self.original_frame_size and self.current_pixmap:
                original_width, original_height = self.original_frame_size

                # 关键修复：使用实际显示的缩放后图像尺寸，而不是预览标签的尺寸
                preview_width = self.current_pixmap.width()
                preview_height = self.current_pixmap.height()

                # 计算缩放比例
                scale_x = original_width / preview_width
                scale_y = original_height / preview_height

                crop_x = math.floor(rect_x1_img * scale_x)
                crop_y = math.floor(rect_y1_img * scale_y)
                crop_w = math.ceil((rect_x2_img - rect_x1_img) * scale_x)
                crop_h = math.ceil((rect_y2_img - rect_y1_img) * scale_y)

                # 确保坐标不超出原始图像范围
                crop_x = max(0, min(crop_x, original_width - 1))
                crop_y = max(0, min(crop_y, original_height - 1))
                crop_w = max(1, min(crop_w, original_width - crop_x))
                crop_h = max(1, min(crop_h, original_height - crop_y))

                # 创建新的框选区域
                new_box = {
                    "coords": {
                        "crop_x": crop_x,
                        "crop_y": crop_y,
                        "crop_width": crop_w,
                        "crop_height": crop_h,
                    },
                    "img_points": (
                        (rect_x1_img, rect_y1_img),
                        (rect_x2_img, rect_y2_img),
                    ),
                }

                # 根据最大框选数量管理框选区域
                if len(self.crop_boxes) >= self.max_crop_boxes:
                    # 如果已达到最大数量，移除最早的框选
                    self.crop_boxes.pop(0)

                # 添加新的框选区域
                self.crop_boxes.append(new_box)

                # 更新UI状态
                self.clear_selection_btn.setEnabled(True)
                self.previewLabel.setCursor(Qt.ArrowCursor)
                self.is_selecting = False

                # 更新坐标显示
                self._update_coords_display()

                # 重绘画布和框选框
                self._redraw_canvas_and_boxes()

                # 发送信号
                if len(self.crop_boxes) == self.max_crop_boxes:
                    self.isCropChoose.emit(True)
                else:
                    self.isCropChoose.emit(False)

            event.accept()
        else:
            event.ignore()

    def _redraw_canvas_and_boxes(self, preview_mode=False):
        """重绘画布和所有框选框"""
        if self.current_pixmap is None:
            return

        try:
            # 创建一个副本进行绘制
            display_pixmap = self.current_pixmap.copy()

            # 创建绘制器
            painter = QPainter(display_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # 定义颜色列表，用于区分不同的框选区域
            colors = [QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255)]

            # 绘制所有已确定的框选框
            for i, crop_box in enumerate(self.crop_boxes):
                # 在预览模式下，如果有临时预览坐标，使用临时坐标
                if preview_mode and "temp_img_points" in crop_box:
                    start_img, end_img = crop_box["temp_img_points"]
                else:
                    start_img, end_img = crop_box["img_points"]

                rect_x1_img = min(start_img[0], end_img[0])
                rect_y1_img = min(start_img[1], end_img[1])
                rect_x2_img = max(start_img[0], end_img[0])
                rect_y2_img = max(start_img[1], end_img[1])

                # 限制在图像范围内
                draw_x1 = max(0, rect_x1_img)
                draw_y1 = max(0, rect_y1_img)
                draw_x2 = min(self.current_pixmap.width() - 1, rect_x2_img)
                draw_y2 = min(self.current_pixmap.height() - 1, rect_y2_img)

                # 选择颜色
                color = colors[i % len(colors)]
                
                # 在预览模式下使用虚线
                if preview_mode and "temp_img_points" in crop_box:
                    pen = QPen(color, 2, Qt.DashLine)
                else:
                    pen = QPen(color, 2)
                painter.setPen(pen)
                
                painter.drawRect(
                    QRect(
                        int(draw_x1),
                        int(draw_y1),
                        int(draw_x2 - draw_x1),
                        int(draw_y2 - draw_y1),
                    )
                )

                # 添加区域编号
                painter.drawText(int(draw_x1) + 5, int(draw_y1) + 15, f"{i + 1}")

            painter.end()

            self.previewLabel.setPixmap(display_pixmap)
        except Exception as e:
            print(f"重绘画布失败: {e}")

    def _draw_temp_rectangle(self):
        """绘制临时矩形（框选过程中）"""
        if (
            self.current_pixmap is None
            or self.start_point_img is None
            or self.end_point_img is None
        ):
            return

        try:
            # 创建一个副本进行绘制
            display_pixmap = self.current_pixmap.copy()

            # 创建绘制器
            painter = QPainter(display_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # 绘制所有已确定的框选框
            colors = [QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255)]
            for i, crop_box in enumerate(self.crop_boxes):
                start_img, end_img = crop_box["img_points"]

                rect_x1_img = min(start_img[0], end_img[0])
                rect_y1_img = min(start_img[1], end_img[1])
                rect_x2_img = max(start_img[0], end_img[0])
                rect_y2_img = max(start_img[1], end_img[1])

                # 限制在图像范围内
                draw_x1 = max(0, rect_x1_img)
                draw_y1 = max(0, rect_y1_img)
                draw_x2 = min(self.current_pixmap.width() - 1, rect_x2_img)
                draw_y2 = min(self.current_pixmap.height() - 1, rect_y2_img)

                # 选择颜色
                color = colors[i % len(colors)]

                # 绘制矩形
                pen = QPen(color, 2)
                painter.setPen(pen)
                painter.drawRect(
                    QRect(
                        int(draw_x1),
                        int(draw_y1),
                        int(draw_x2 - draw_x1),
                        int(draw_y2 - draw_y1),
                    )
                )

                # 添加区域编号
                painter.drawText(int(draw_x1) + 5, int(draw_y1) + 15, f"{i + 1}")

            # 绘制临时矩形
            rect_x1_img = min(self.start_point_img[0], self.end_point_img[0])
            rect_y1_img = min(self.start_point_img[1], self.end_point_img[1])
            rect_x2_img = max(self.start_point_img[0], self.end_point_img[0])
            rect_y2_img = max(self.start_point_img[1], self.end_point_img[1])

            # 限制在图像范围内
            draw_x1 = max(0, rect_x1_img)
            draw_y1 = max(0, rect_y1_img)
            draw_x2 = min(self.current_pixmap.width() - 1, rect_x2_img)
            draw_y2 = min(self.current_pixmap.height() - 1, rect_y2_img)

            # 绘制临时矩形（虚线）
            pen = QPen(QColor(255, 255, 0), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(
                QRect(
                    int(draw_x1),
                    int(draw_y1),
                    int(draw_x2 - draw_x1),
                    int(draw_y2 - draw_y1),
                )
            )

            painter.end()

            self.previewLabel.setPixmap(display_pixmap)
        except Exception as e:
            print(f"绘制临时矩形失败: {e}")

    def set_frame(self, frame_data):
        """设置视频帧"""
        if frame_data is not None:
            try:
                # 保存原始帧尺寸
                if self.original_frame_size is None:
                    self.original_frame_size = (
                        frame_data.shape[1],
                        frame_data.shape[0],
                    )

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
                self._redraw_canvas_and_boxes()
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
        """获取第一个框选区域（相对于原始图像的坐标）"""
        if not self.crop_boxes:
            return None

        try:
            crop_box = self.crop_boxes[0]
            coords = crop_box["coords"]
            return QRect(
                coords["crop_x"],
                coords["crop_y"],
                coords["crop_width"],
                coords["crop_height"],
            )
        except Exception as e:
            print(f"获取选择区域失败: {e}")
            return None

    def get_all_selection_rects(self):
        """获取所有框选区域（相对于原始图像的坐标）"""
        rects = []
        for crop_box in self.crop_boxes:
            coords = crop_box["coords"]
            rects.append(
                QRect(
                    coords["crop_x"],
                    coords["crop_y"],
                    coords["crop_width"],
                    coords["crop_height"],
                )
            )
        return rects

    def resizeEvent(self, event):
        """处理窗口大小改变事件"""
        super().resizeEvent(event)
        # 当窗口大小改变时，重新设置当前帧以更新显示
        if self.current_frame is not None:
            self.set_frame(self.current_frame)

    def set_max_crop_boxes(self, max_boxes):
        """设置最大框选数量"""
        self.max_crop_boxes = max_boxes
        # 如果当前框选数量超过新的最大值，移除多余的框选
        while len(self.crop_boxes) > self.max_crop_boxes:
            self.crop_boxes.pop(0)
        self._redraw_canvas_and_boxes()
        self._update_coords_display()

    def _create_coord_edit_widget(self, zone_index):
        """创建坐标编辑组件"""
        widget = CardWidget()
        layout = QVBoxLayout(widget)
        
        # 标题
        title_layout = QHBoxLayout()
        title_label = CaptionLabel(f"区域 {zone_index + 1} 坐标")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 坐标输入框
        coords_input_layout = QHBoxLayout()
        
        # X坐标
        x_layout = QVBoxLayout()
        x_label = CaptionLabel("X:")
        x_input = SpinBox()
        x_input.setMinimum(0)
        x_input.setMaximum(9999)
        x_layout.addWidget(x_label)
        x_layout.addWidget(x_input)
        
        # Y坐标
        y_layout = QVBoxLayout()
        y_label = CaptionLabel("Y:")
        y_input = SpinBox()
        y_input.setMinimum(0)
        y_input.setMaximum(9999)
        y_layout.addWidget(y_label)
        y_layout.addWidget(y_input)
        
        # 宽度
        w_layout = QVBoxLayout()
        w_label = CaptionLabel("宽度:")
        w_input = SpinBox()
        w_input.setMinimum(1)
        w_input.setMaximum(9999)
        w_layout.addWidget(w_label)
        w_layout.addWidget(w_input)
        
        # 高度
        h_layout = QVBoxLayout()
        h_label = CaptionLabel("高度:")
        h_input = SpinBox()
        h_input.setMinimum(1)
        h_input.setMaximum(9999)
        h_layout.addWidget(h_label)
        h_layout.addWidget(h_input)
        
        coords_input_layout.addLayout(x_layout)
        coords_input_layout.addLayout(y_layout)
        coords_input_layout.addLayout(w_layout)
        coords_input_layout.addLayout(h_layout)
        coords_input_layout.addStretch()
        
        # 应用按钮
        apply_btn = PushButton(FluentIcon.ACCEPT, "应用")
        coords_input_layout.addWidget(apply_btn)
        coords_input_layout.addSpacing(12)
        
        layout.addLayout(title_layout)
        layout.addLayout(coords_input_layout)
        
        # 保存输入框引用
        coord_inputs = {
            'x': x_input,
            'y': y_input,
            'width': w_input,
            'height': h_input,
            'apply_btn': apply_btn
        }
        
        # 连接信号
        apply_btn.clicked.connect(lambda: self._apply_coord_changes(zone_index))
        
        # 当输入框值改变时实时更新
        x_input.valueChanged.connect(lambda: self._preview_coord_changes(zone_index))
        y_input.valueChanged.connect(lambda: self._preview_coord_changes(zone_index))
        w_input.valueChanged.connect(lambda: self._preview_coord_changes(zone_index))
        h_input.valueChanged.connect(lambda: self._preview_coord_changes(zone_index))
        
        return widget, coord_inputs

    def _update_coords_display(self):
        """更新坐标显示"""
        if not self.crop_boxes:
            self.coords_label.setText("框选区域坐标: 未选择")
            # 清除所有坐标编辑组件
            for widget in self.coord_edit_widgets:
                widget.setParent(None)
                widget.deleteLater()
            self.coord_edit_widgets.clear()
            self.coord_inputs.clear()
            return

        coords_texts = []
        for i, box in enumerate(self.crop_boxes):
            coords = box["coords"]
            coords_texts.append(
                f"区域{i + 1}: x={coords['crop_x']}, y={coords['crop_y']}, w={coords['crop_width']}, h={coords['crop_height']}"
            )

        self.coords_label.setText(" | ".join(coords_texts))
        
        # 更新或创建坐标编辑组件
        self._update_coord_edit_widgets()

    def _update_coord_edit_widgets(self):
        """更新坐标编辑组件"""
        # 清除现有组件
        for widget in self.coord_edit_widgets:
            widget.setParent(None)
            widget.deleteLater()
        self.coord_edit_widgets.clear()
        self.coord_inputs.clear()
        
        # 为每个框选区域创建编辑组件
        for i in range(len(self.crop_boxes)):
            widget, coord_inputs = self._create_coord_edit_widget(i)
            
            # 设置当前坐标值
            coords = self.crop_boxes[i]["coords"]
            coord_inputs['x'].setValue(coords['crop_x'])
            coord_inputs['y'].setValue(coords['crop_y'])
            coord_inputs['width'].setValue(coords['crop_width'])
            coord_inputs['height'].setValue(coords['crop_height'])
            
            # 设置最大值限制（基于原始图像尺寸）
            if self.original_frame_size:
                max_x, max_y = self.original_frame_size
                coord_inputs['x'].setMaximum(max_x - 1)
                coord_inputs['y'].setMaximum(max_y - 1)
                coord_inputs['width'].setMaximum(max_x)
                coord_inputs['height'].setMaximum(max_y)
            
            self.coord_edit_layout.addWidget(widget)
            self.coord_edit_widgets.append(widget)
            self.coord_inputs.append(coord_inputs)
    
    def _preview_coord_changes(self, zone_index):
        """预览坐标变化（实时更新显示但不保存）"""
        if zone_index >= len(self.coord_inputs) or zone_index >= len(self.crop_boxes):
            return
            
        coord_inputs = self.coord_inputs[zone_index]
        crop_box = self.crop_boxes[zone_index]
        
        # 获取新的坐标值
        new_x = coord_inputs['x'].value()
        new_y = coord_inputs['y'].value()
        new_w = coord_inputs['width'].value()
        new_h = coord_inputs['height'].value()
        
        # 验证坐标值
        if self.original_frame_size:
            max_x, max_y = self.original_frame_size
            new_x = max(0, min(new_x, max_x - 1))
            new_y = max(0, min(new_y, max_y - 1))
            new_w = max(1, min(new_w, max_x - new_x))
            new_h = max(1, min(new_h, max_y - new_y))
        
        # 转换为预览图像坐标
        if self.current_pixmap and self.original_frame_size:
            original_width, original_height = self.original_frame_size
            preview_width = self.current_pixmap.width()
            preview_height = self.current_pixmap.height()
            
            scale_x = preview_width / original_width
            scale_y = preview_height / original_height
            
            img_x1 = int(new_x * scale_x)
            img_y1 = int(new_y * scale_y)
            img_x2 = int((new_x + new_w) * scale_x)
            img_y2 = int((new_y + new_h) * scale_y)
            
            # 临时更新框选区域的预览坐标
            crop_box["temp_img_points"] = ((img_x1, img_y1), (img_x2, img_y2))
            
            # 重绘画布显示预览
            self._redraw_canvas_and_boxes(preview_mode=True)
    
    def _apply_coord_changes(self, zone_index):
        """应用坐标变化"""
        if zone_index >= len(self.coord_inputs) or zone_index >= len(self.crop_boxes):
            return
            
        coord_inputs = self.coord_inputs[zone_index]
        crop_box = self.crop_boxes[zone_index]
        
        # 获取新的坐标值
        new_x = coord_inputs['x'].value()
        new_y = coord_inputs['y'].value()
        new_w = coord_inputs['width'].value()
        new_h = coord_inputs['height'].value()
        
        # 验证坐标值
        if self.original_frame_size:
            max_x, max_y = self.original_frame_size
            new_x = max(0, min(new_x, max_x - 1))
            new_y = max(0, min(new_y, max_y - 1))
            new_w = max(1, min(new_w, max_x - new_x))
            new_h = max(1, min(new_h, max_y - new_y))
        
        # 更新框选区域的坐标
        crop_box["coords"] = {
            "crop_x": new_x,
            "crop_y": new_y,
            "crop_width": new_w,
            "crop_height": new_h,
        }
        
        # 转换为预览图像坐标
        if self.current_pixmap and self.original_frame_size:
            original_width, original_height = self.original_frame_size
            preview_width = self.current_pixmap.width()
            preview_height = self.current_pixmap.height()
            
            scale_x = preview_width / original_width
            scale_y = preview_height / original_height
            
            img_x1 = int(new_x * scale_x)
            img_y1 = int(new_y * scale_y)
            img_x2 = int((new_x + new_w) * scale_x)
            img_y2 = int((new_y + new_h) * scale_y)
            
            crop_box["img_points"] = ((img_x1, img_y1), (img_x2, img_y2))
        
        # 清除临时预览坐标
        if "temp_img_points" in crop_box:
            del crop_box["temp_img_points"]
        
        # 重绘画布
        self._redraw_canvas_and_boxes()
        
        # 更新坐标显示
        self._update_coords_display()

    def clear_selection(self, index=None):
        """清除指定索引的框选区域或所有区域"""
        if index is not None and 0 <= index < len(self.crop_boxes):
            self.crop_boxes.pop(index)
        else:
            self.crop_boxes.clear()

        if not self.crop_boxes:
            self.clear_selection_btn.setEnabled(False)

        self.isCropChoose.emit(False)

        self._redraw_canvas_and_boxes()
        self._update_coords_display()
