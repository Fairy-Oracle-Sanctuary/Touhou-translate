# ocr_service.py
import os
import shutil
import tempfile
from datetime import datetime

from app.common.config import cfg
from PySide6.QtCore import QThread, Signal

from ...CLI.videocr.api import save_subtitles_to_file


class OCRTask:
    """OCR任务类"""

    _id_counter = 0

    def __init__(self, video_path, output_path="", project_name="", episode_num=0):
        self.video_path = video_path
        self.output_path = output_path or self._generate_default_output(video_path)
        self.project_name = project_name
        self.episode_num = episode_num
        self.status = "等待中"  # 等待中, 处理中, 已完成, 失败
        self.progress = 0
        self.current_frame = 0
        self.total_frames = 0
        self.start_time = None
        self.end_time = None
        self.error_message = ""

        OCRTask._id_counter += 1
        self.id = OCRTask._id_counter

    def _generate_default_output(self, video_path):
        """生成默认输出路径"""
        base_name = os.path.splitext(video_path)[0]
        return f"{base_name}.srt"


class OCRThread(QThread):
    """OCR处理线程"""

    progress_signal = Signal(int, int, int)  # 进度百分比, 当前帧, 总帧数
    finished_signal = Signal(bool, str)  # 成功/失败, 消息
    log_signal = Signal(str)  # 日志信息

    def __init__(self, task):
        super().__init__()
        self.task = task
        self.is_cancelled = False

    def make_path_safe(self, path):
        """确保路径不包含中文"""
        if not path or not any(ord(c) > 127 for c in path):
            return path

        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="ocr_safe_")

        if os.path.isfile(path):
            # 处理文件
            ext = os.path.splitext(path)[1]
            import uuid

            temp_file = os.path.join(temp_dir, f"temp_{uuid.uuid4().hex}{ext}")
            shutil.copy2(path, temp_file)
            self.log_signal.emit(f"已将文件复制到临时位置: {temp_file}")
            return temp_file
        else:
            return path

    def get_crop_zones(self):
        """根据配置获取裁剪区域"""
        crop_zones = []

        # 从配置中获取裁剪参数
        crop_x = cfg.get("OCR", "CropX", None)
        crop_y = cfg.get("OCR", "CropY", None)
        crop_width = cfg.get("OCR", "CropWidth", None)
        crop_height = cfg.get("OCR", "CropHeight", None)

        # 检查第一个区域是否定义
        zone1_defined = all(
            v is not None for v in [crop_x, crop_y, crop_width, crop_height]
        )

        if zone1_defined:
            crop_zones.append(
                {
                    "x": crop_x,
                    "y": crop_y,
                    "width": crop_width,
                    "height": crop_height,
                }
            )

            # 检查是否启用双区域
            if cfg.useDualZone.value:
                crop_x2 = cfg.get("OCR", "CropX2", None)
                crop_y2 = cfg.get("OCR", "CropY2", None)
                crop_width2 = cfg.get("OCR", "CropWidth2", None)
                crop_height2 = cfg.get("OCR", "CropHeight2", None)

                zone2_defined = all(
                    v is not None for v in [crop_x2, crop_y2, crop_width2, crop_height2]
                )

                if zone2_defined:
                    crop_zones.append(
                        {
                            "x": crop_x2,
                            "y": crop_y2,
                            "width": crop_width2,
                            "height": crop_height2,
                        }
                    )
                else:
                    self.log_signal.emit("警告：启用了双区域OCR但第二区域参数不完整")

        return crop_zones

    def run(self):
        """执行OCR处理"""
        self.task.status = "处理中"
        self.task.start_time = datetime.now()

        try:
            # 确保路径安全（处理中文路径）
            safe_video_path = self.make_path_safe(self.task.video_path)
            safe_output_path = self.make_path_safe(self.task.output_path)

            self.log_signal.emit(
                f"开始处理视频: {os.path.basename(self.task.video_path)}"
            )
            self.log_signal.emit(f"输出路径: {self.task.output_path}")

            # 获取裁剪区域配置
            crop_zones = self.get_crop_zones()
            if crop_zones:
                self.log_signal.emit(f"使用裁剪区域: {len(crop_zones)} 个区域")

            # 从配置中获取所有OCR参数
            ocr_params = {
                "video_path": safe_video_path,
                "file_path": safe_output_path,
                "lang": "japan",
                "time_start": cfg.timeStart.value,
                "time_end": cfg.timeEnd.value if cfg.timeEnd.value else "",
                "conf_threshold": cfg.confThreshold.value,
                "sim_threshold": cfg.simThreshold.value,
                "max_merge_gap_sec": cfg.maxMergeGap.value,
                "use_fullframe": False,
                "use_gpu": cfg.useGpu.value,
                "use_angle_cls": cfg.useAngleCls.value,
                "use_server_model": cfg.useServerModel.value,
                "brightness_threshold": cfg.brightnessThreshold.value
                if cfg.brightnessThreshold.value > 0
                else None,
                "ssim_threshold": cfg.ssimThreshold.value,
                "subtitle_position": "center",  # 可以根据需要配置化
                "frames_to_skip": cfg.framesToSkip.value,
                "crop_zones": crop_zones,
                "post_processing": cfg.postProcessing.value,
                "min_subtitle_duration_sec": cfg.minSubtitleDuration.value,
                "ocr_image_max_width": cfg.ocrImageMaxWidth.value,
            }

            # 调用videocr API
            self.log_signal.emit("开始OCR处理...")
            save_subtitles_to_file(**ocr_params)

            # 清理临时文件
            if safe_video_path != self.task.video_path and os.path.exists(
                safe_video_path
            ):
                os.remove(safe_video_path)
                os.rmdir(os.path.dirname(safe_video_path))

            self.task.status = "已完成"
            self.task.progress = 100
            self.task.end_time = datetime.now()

            self.log_signal.emit("OCR处理完成")
            self.finished_signal.emit(True, "OCR处理完成")

        except Exception as e:
            error_msg = f"OCR处理失败: {str(e)}"
            self.task.status = "失败"
            self.task.error_message = error_msg
            self.task.end_time = datetime.now()

            self.log_signal.emit(f"错误: {error_msg}")
            self.finished_signal.emit(False, error_msg)

    def cancel(self):
        """取消OCR处理"""
        self.is_cancelled = True
        self.task.status = "已取消"
        self.log_signal.emit("OCR处理已取消")


class OCRService:
    """OCR服务管理类"""

    def __init__(self):
        self.tasks = []
        self.current_thread = None

    def create_task(self, video_path, output_path="", project_name="", episode_num=0):
        """创建OCR任务"""
        task = OCRTask(video_path, output_path, project_name, episode_num)
        self.tasks.append(task)
        return task

    def start_ocr(
        self, task, progress_callback=None, finished_callback=None, log_callback=None
    ):
        """开始OCR处理"""
        if self.current_thread and self.current_thread.isRunning():
            return False, "已有任务正在运行"

        self.current_thread = OCRThread(task)

        if progress_callback:
            self.current_thread.progress_signal.connect(progress_callback)

        if finished_callback:
            self.current_thread.finished_signal.connect(finished_callback)

        if log_callback:
            self.current_thread.log_signal.connect(log_callback)

        self.current_thread.start()
        return True, "任务已开始"

    def cancel_current(self):
        """取消当前任务"""
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.cancel()
            return True
        return False

    def get_task_by_id(self, task_id):
        """根据ID获取任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_all_tasks(self):
        """获取所有任务"""
        return self.tasks.copy()
