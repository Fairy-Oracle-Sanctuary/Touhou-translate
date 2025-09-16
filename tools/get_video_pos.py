import cv2
import numpy as np
import os

class VideoCoordinateTool:
    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.paused = False
        self.current_frame = None
        self.mouse_x, self.mouse_y = 0, 0
        self.roi_start = None
        self.roi_end = None
        self.drawing_roi = False
        self.scale_factor = 0.5  # 默认缩放因子
        self.window_name = f"视频坐标工具 - {os.path.basename(video_path)}"
        
        # 获取视频基本信息
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 计算缩放后的窗口尺寸
        self.display_width = int(self.width * self.scale_factor)
        self.display_height = int(self.height * self.scale_factor)
        
        print(f"视频信息: {self.width}x{self.height}, {self.fps:.2f} FPS, 总帧数: {self.total_frames}")
        print(f"显示尺寸: {self.display_width}x{self.display_height} (缩放因子: {self.scale_factor})")
        
    def resize_frame(self, frame):
        """调整帧大小"""
        return cv2.resize(frame, (self.display_width, self.display_height))
    
    def map_coordinates(self, x, y):
        """将显示坐标映射回原始视频坐标"""
        orig_x = int(x / self.scale_factor)
        orig_y = int(y / self.scale_factor)
        return orig_x, orig_y
    
    def mouse_callback(self, event, x, y, flags, param):
        """鼠标回调函数，处理鼠标事件"""
        self.mouse_x, self.mouse_y = x, y
        
        # 映射坐标到原始视频尺寸
        orig_x, orig_y = self.map_coordinates(x, y)
        
        if event == cv2.EVENT_LBUTTONDOWN:
            self.roi_start = (orig_x, orig_y)
            self.drawing_roi = True
            
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing_roi:
            self.roi_end = (orig_x, orig_y)
            
        elif event == cv2.EVENT_LBUTTONUP:
            self.roi_end = (orig_x, orig_y)
            self.drawing_roi = False
            
            # 计算并显示ROI信息
            x1, y1 = self.roi_start
            x2, y2 = self.roi_end
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            # 确保左上角是起点
            x_start = min(x1, x2)
            y_start = min(y1, y2)
            
            print(f"\n选择的区域:")
            print(f"  --crop_x {x_start} --crop_y {y_start} --crop_width {width} --crop_height {height}")
            
    def run(self):
        """运行主程序"""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.display_width, self.display_height)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        print("\n使用说明:")
        print("  空格键: 暂停/播放")
        print("  → 键: 前进一帧")
        print("  ← 键: 后退一帧")
        print("  + 键: 放大窗口")
        print("  - 键: 缩小窗口")
        print("  R 键: 重置ROI选择")
        print("  C 键: 复制当前坐标到剪贴板")
        print("  Q 键或ESC: 退出")
        print("  鼠标左键拖动: 选择区域")
        print("  鼠标移动: 查看坐标和颜色信息")
        
        while True:
            if not self.paused:
                ret, self.current_frame = self.cap.read()
                if not ret:
                    print("视频播放完毕或读取失败")
                    break
            
            if self.current_frame is not None:
                # 调整帧大小
                display_frame = self.resize_frame(self.current_frame)
                
                # 获取当前显示尺寸
                h, w = display_frame.shape[:2]
                
                # 绘制十字准星
                cv2.line(display_frame, (self.mouse_x, 0), (self.mouse_x, h), (0, 255, 0), 1)
                cv2.line(display_frame, (0, self.mouse_y), (w, self.mouse_y), (0, 255, 0), 1)
                
                # 获取原始坐标和颜色
                orig_x, orig_y = self.map_coordinates(self.mouse_x, self.mouse_y)
                if 0 <= orig_x < self.width and 0 <= orig_y < self.height:
                    bgr = self.current_frame[orig_y, orig_x]
                else:
                    bgr = [0, 0, 0]
                
                # 绘制坐标信息
                info_text = f"pos: X:{self.mouse_x}, Y:{self.mouse_y}"
                cv2.putText(display_frame, info_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                orig_text = f"orig_pos: X:{orig_x}, Y:{orig_y}, BGR:{bgr}"
                cv2.putText(display_frame, orig_text, (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # 绘制当前帧信息
                frame_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                frame_info = f"frame: {frame_pos}/{self.total_frames} scale: {self.scale_factor:.2f}"
                cv2.putText(display_frame, frame_info, (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # 绘制ROI区域
                if self.roi_start and self.roi_end:
                    # 将原始坐标映射到显示坐标
                    x1, y1 = self.roi_start
                    x2, y2 = self.roi_end
                    disp_x1 = int(x1 * self.scale_factor)
                    disp_y1 = int(y1 * self.scale_factor)
                    disp_x2 = int(x2 * self.scale_factor)
                    disp_y2 = int(y2 * self.scale_factor)
                    
                    cv2.rectangle(display_frame, (disp_x1, disp_y1), (disp_x2, disp_y2), (0, 255, 255), 2)
                    
                    # 显示ROI尺寸
                    width = abs(x2 - x1)
                    height = abs(y2 - y1)
                    roi_text = f"ROI: {width}x{height}"
                    cv2.putText(display_frame, roi_text, (10, 120), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # 显示图像
                cv2.imshow(self.window_name, display_frame)
            
            # 键盘控制
            key = cv2.waitKey(1 if not self.paused else 0) & 0xFF
            
            if key == ord(' '):  # 空格键暂停/播放
                self.paused = not self.paused
                
            elif key == ord('q') or key == 27:  # Q或ESC退出
                break
                
            elif key == ord('r'):  # R键重置ROI
                self.roi_start = None
                self.roi_end = None
                
            elif key == ord('c'):  # C键复制坐标到剪贴板
                orig_x, orig_y = self.map_coordinates(self.mouse_x, self.mouse_y)
                try:
                    import pyperclip
                    pyperclip.copy(f"--crop_x {orig_x} --crop_y {orig_y}")
                    print(f"已复制坐标到剪贴板: --crop_x {orig_x} --crop_y {orig_y}")
                except ImportError:
                    print("请安装pyperclip库以使用复制功能: pip install pyperclip")
                
            elif key == 81:  # 左箭头键 - 后退一帧
                if self.paused:
                    prev_frame = max(0, int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)) - 2)
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, prev_frame)
                    ret, self.current_frame = self.cap.read()
                
            elif key == 83:  # 右箭头键 - 前进一帧
                if self.paused:
                    ret, self.current_frame = self.cap.read()
                    
            elif key == ord('+') or key == ord('='):  # 放大
                self.scale_factor = min(2.0, self.scale_factor + 0.1)
                self.display_width = int(self.width * self.scale_factor)
                self.display_height = int(self.height * self.scale_factor)
                cv2.resizeWindow(self.window_name, self.display_width, self.display_height)
                print(f"缩放因子: {self.scale_factor:.2f}, 显示尺寸: {self.display_width}x{self.display_height}")
                
            elif key == ord('-') or key == ord('_'):  # 缩小
                self.scale_factor = max(0.2, self.scale_factor - 0.1)
                self.display_width = int(self.width * self.scale_factor)
                self.display_height = int(self.height * self.scale_factor)
                cv2.resizeWindow(self.window_name, self.display_width, self.display_height)
                print(f"缩放因子: {self.scale_factor:.2f}, 显示尺寸: {self.display_width}x{self.display_height}")
        
        self.cap.release()
        cv2.destroyAllWindows()

# "D:\东方project\油库里茶番剧\被捡回来的管家我竟要和主人蕾米莉亚交往了\8\生肉.mp4"