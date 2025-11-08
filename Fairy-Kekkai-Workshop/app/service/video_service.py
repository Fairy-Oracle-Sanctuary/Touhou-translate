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

        # 框选坐标显示
        self.coords_layout = QHBoxLayout()
        self.coords_label = CaptionLabel("框选区域坐标: 未选择")
        self.coords_layout.addWidget(self.coords_label)
        self.coords_layout.addStretch()

        self.vBoxLayout.addWidget(self.previewLabel)
        self.vBoxLayout.addLayout(self.control_layout)
        self.vBoxLayout.addLayout(self.coords_layout)
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

        # 更新坐标显示
        self.coords_label.setText("框选区域坐标: 未选择")

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
            self._redraw_canvas_and_boxes()

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

    def _redraw_canvas_and_boxes(self):
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

    def _update_coords_display(self):
        """更新坐标显示"""
        if not self.crop_boxes:
            self.coords_label.setText("框选区域坐标: 未选择")
            return

        coords_texts = []
        for i, box in enumerate(self.crop_boxes):
            coords = box["coords"]
            coords_texts.append(
                f"区域{i + 1}: x={coords['crop_x']}, y={coords['crop_y']}, w={coords['crop_width']}, h={coords['crop_height']}"
            )

        self.coords_label.setText(" | ".join(coords_texts))

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
