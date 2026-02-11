# coding:utf-8
import json
import sys
from pathlib import Path

from qfluentwidgets import (
    BoolValidator,
    ConfigItem,
    OptionsConfigItem,
    OptionsValidator,
    QConfig,
    RangeConfigItem,
    RangeValidator,
    Theme,
    qconfig,
)

from .setting import (
    CONFIG_FILE,
    CONFIG_FOLDER,
    EXE_SUFFIX,
    PADDLEOCR_VERSION,
    PIC_SUFFIX,
    AI_model_dict,
    subtitle_positions_list,
    translate_language_dict,
    videocr_languages_dict,
)


def isWin11():
    return sys.platform == "win32" and sys.getwindowsversion().build >= 22000


class ProjectConfig:
    """项目配置"""

    def __init__(self, config_file=CONFIG_FOLDER):
        self.config_file = config_file / "project.json"
        self.config = {}
        self.load()

    def load(self):
        """读取配置文件"""
        if not self.config_file.exists():
            with open(self.config_file, "w", encoding="utf-8") as f:
                self.set("project_link", [])
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except json.JSONDecodeError:
            self.config = {}

    def save(self):
        """保存配置到文件"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)

    def set(self, key, value):
        """设置配置项"""
        self.config[key] = value
        self.save()

    def remove(self, key):
        """删除配置项"""
        if key in self.config:
            del self.config[key]
            self.save()

    def get_all(self):
        """获取所有配置"""
        return self.config.copy()


class Config(QConfig):
    """Config of application"""

    # main window
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())
    dpiScale = OptionsConfigItem(
        "MainWindow",
        "DpiScale",
        "Auto",
        OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]),
        restart=True,
    )
    accentColor = OptionsConfigItem(
        "MainWindow", "AccentColor", "#009faa", OptionsValidator(["#009faa", "Auto"])
    )
    closeDirectly = ConfigItem(
        "MainWindow", "CloseDirectly", False, BoolValidator(), restart=False
    )
    showBackground = ConfigItem(
        "MainWindow", "ShowBackground", False, BoolValidator(), restart=True
    )
    backgroundPath = ConfigItem(
        "MainWindow", "BackgroundPath", str(Path(f"background{PIC_SUFFIX}").absolute())
    )
    backgroundRect = RangeConfigItem(
        "MainWindow", "BackgroundRect", 0, RangeValidator(0, 200)
    )

    # project
    detailProjectItemNum = RangeConfigItem(
        "Project", "DetailProjectItemNum", 5, RangeValidator(1, 10)
    )
    linkProject = ProjectConfig()
    # 记录上一个选择的文件夹路径
    lastOpenPath = ConfigItem(
        "Project", "LastOpenPath", str(Path.home()), restart=False
    )

    # download
    ytdlpPath = ConfigItem(
        "Download", "YTDLPPath", str(Path(f"tools/yt-dlp{EXE_SUFFIX}").absolute())
    )

    # ytdlp parameters
    # 下载格式选择：mp4(确保mp4格式), best(最佳质量), worst(最差质量), bestvideo(最佳视频), bestaudio(最佳音频)
    # 命令行使用：-f mp4 或 --format mp4
    downloadFormat = OptionsConfigItem(
        "YTDLP",
        "DownloadFormat",
        "mp4",
        OptionsValidator(["mp4", "best", "worst", "bestvideo", "bestaudio"]),
        # OptionsValidator(["mp4"]),
        restart=False,
    )
    # 视频质量选择：分辨率选项和最佳/最差选项
    # 命令行使用：-S "res:1080" 或 --format-sort "res:1080"
    downloadQuality = OptionsConfigItem(
        "YTDLP",
        "DownloadQuality",
        "1080",
        OptionsValidator(
            ["2160", "1440", "1080", "720", "480", "360", "best", "worst"]
        ),
        restart=False,
    )
    # 是否启用系统代理
    systemProxy = ConfigItem(
        "YTDLP", "SystemProxy", True, BoolValidator(), restart=False
    )
    # 代理设置
    # 命令行使用: --proxy "http://127.0.0.1:1080"
    proxyUrl = ConfigItem("YTDLP", "ProxyUrl", "http://127.0.0.1:1080", restart=False)

    # 是否下载字幕文件
    # 命令行使用：--write-sub 或 --write-auto-sub (自动生成字幕)
    downloadSubtitles = ConfigItem(
        "YTDLP", "DownloadSubtitles", False, BoolValidator(), restart=False
    )
    # 字幕语言设置，多个语言用逗号分隔，如"en,zh,ja"
    # 命令行使用：--sub-langs "en,zh,zh-Hans"
    subtitleLanguages = ConfigItem(
        "YTDLP", "SubtitleLanguages", "en,zh,zh-Hans", restart=False
    )
    # 是否将字幕内嵌到视频文件中（需要ffmpeg支持）
    # 命令行使用：--embed-subs
    embedSubtitles = ConfigItem(
        "YTDLP", "EmbedSubtitles", False, BoolValidator(), restart=False
    )
    # 是否下载视频缩略图
    # 命令行使用：--write-thumbnail
    downloadThumbnail = ConfigItem(
        "YTDLP", "DownloadThumbnail", False, BoolValidator(), restart=False
    )
    # 是否将缩略图内嵌到视频文件中（需要ffmpeg支持）
    # 命令行使用：--embed-thumbnail
    embedThumbnail = ConfigItem(
        "YTDLP", "EmbedThumbnail", False, BoolValidator(), restart=False
    )
    # 是否下载视频元数据信息
    # 命令行使用：--write-info-json
    downloadMetadata = ConfigItem(
        "YTDLP", "DownloadMetadata", False, BoolValidator(), restart=False
    )
    # 并发下载数量，同时下载多个视频时的最大并行数
    # 命令行使用：-N 3 或 --concurrent-fragments 3
    concurrentDownloads = RangeConfigItem(
        "YTDLP", "ConcurrentDownloads", 3, RangeValidator(1, 10), restart=False
    )
    # 下载失败时的重试次数，0表示不重试
    # 命令行使用：-R 3 或 --retries 3
    retryAttempts = RangeConfigItem(
        "YTDLP", "RetryAttempts", 3, RangeValidator(0, 10), restart=False
    )
    # 下载超时时间（秒），超过此时间未完成下载将视为失败
    # 命令行使用：--socket-timeout 300
    downloadTimeout = RangeConfigItem(
        "YTDLP", "DownloadTimeout", 300, RangeValidator(60, 3600), restart=False
    )
    # 输出文件名模板，支持yt-dlp的模板变量如%(title)s, %(ext)s等
    # 命令行使用：-o "%(title)s.%(ext)s"
    outputTemplate = ConfigItem(
        "YTDLP", "OutputTemplate", "%(title)s.%(ext)s", restart=False
    )
    # 是否使用cookies文件进行下载（用于需要登录的视频）
    # 命令行使用：--cookies-from-browser BROWSER 或 --cookies cookies.txt
    useCookies = ConfigItem(
        "YTDLP", "UseCookies", False, BoolValidator(), restart=False
    )
    # cookies文件路径，通常是浏览器导出的cookies.txt文件
    # 命令行使用：--cookies "path/to/cookies.txt"
    cookiesFile = ConfigItem("YTDLP", "CookiesFile", "", restart=False)
    # 是否启用下载速率限制
    # 命令行使用：--limit-rate 10M
    limitDownloadRate = ConfigItem(
        "YTDLP", "LimitDownloadRate", False, BoolValidator(), restart=False
    )
    # 最大下载速率，如"10M"表示10MB/s, "1K"表示1KB/s
    # 命令行使用：--limit-rate 10M
    maxDownloadRate = ConfigItem("YTDLP", "MaxDownloadRate", "10M", restart=False)
    # 是否跳过已存在的文件，避免重复下载
    # 命令行使用：--no-overwrites 或 --skip-download
    skipExistingFiles = ConfigItem(
        "YTDLP", "SkipExistingFiles", True, BoolValidator(), restart=False
    )
    # 是否将视频描述写入单独的文件
    # 命令行使用：--write-description
    writeDescription = ConfigItem(
        "YTDLP", "WriteDescription", False, BoolValidator(), restart=False
    )
    # 是否将视频信息写入JSON文件
    # 命令行使用：--write-info-json
    writeInfoJson = ConfigItem(
        "YTDLP", "WriteInfoJson", False, BoolValidator(), restart=False
    )
    # 是否写入视频注释（部分平台支持）
    # 命令行使用：--write-annotations
    writeAnnotations = ConfigItem(
        "YTDLP", "WriteAnnotations", False, BoolValidator(), restart=False
    )
    # 音频格式选择（当下载纯音频时使用）
    # 命令行使用：--audio-format best
    audioFormat = OptionsConfigItem(
        "YTDLP",
        "AudioFormat",
        "best",
        OptionsValidator(
            ["best", "aac", "flac", "mp3", "m4a", "opus", "vorbis", "wav"]
        ),
        restart=False,
    )
    # 视频编码器选择
    # 命令行使用：--video-codec h264
    videoCodec = OptionsConfigItem(
        "YTDLP",
        "VideoCodec",
        "h265",
        OptionsValidator(["h264", "h265", "vp9", "av1", "mp4v"]),
        restart=False,
    )
    # 音频编码器选择
    # 命令行使用：--audio-codec aac
    audioCodec = OptionsConfigItem(
        "YTDLP",
        "AudioCodec",
        "aac",
        OptionsValidator(["aac", "flac", "mp3", "opus", "vorbis"]),
        restart=False,
    )

    """
    # 下载播放列表时的起始位置
    # 命令行使用：--playlist-start 1
    playlistStart = RangeConfigItem(
        "YTDLP", "PlaylistStart", 1, RangeValidator(1, 10000), restart=False
    )
    # 下载播放列表时的结束位置
    # 命令行使用：--playlist-end 0 (0表示无限制)
    playlistEnd = RangeConfigItem(
        "YTDLP", "PlaylistEnd", 0, RangeValidator(0, 10000), restart=False
    )
    # 下载播放列表时的最大项目数，0表示无限制
    # 命令行使用：--playlist-items 1-10 或 --max-downloads 10
    playlistItems = ConfigItem("YTDLP", "PlaylistItems", "", restart=False)
    # 是否只下载音频（转换为音频文件）
    # 命令行使用：-x 或 --extract-audio
    extractAudio = ConfigItem(
        "YTDLP", "ExtractAudio", False, BoolValidator(), restart=False
    )
    # 是否保持原始视频文件（当提取音频时）
    # 命令行使用：-k 或 --keep-video
    keepVideo = ConfigItem("YTDLP", "KeepVideo", False, BoolValidator(), restart=False)
    """

    # OCR Settings
    # videocr_cli 路径
    videocrCliPath = ConfigItem(
        "OCR",
        "VideocrCliPath",
        str(Path(f"tools/videocr-cli{EXE_SUFFIX}").absolute()),
    )

    # paddleocr exe路径
    paddleocrPath = ConfigItem(
        "OCR",
        "PaddleocrPath",
        str(
            Path(
                f"tools/PaddleOCR-{PADDLEOCR_VERSION}/paddleocr{EXE_SUFFIX}"
            ).absolute()
        ),
    )
    # tools/PaddleOCR-CPU-v1.3.2/paddleocr{EXE_SUFFIX}
    # tools/PaddleOCR-GPU-v1.3.2-CUDA-11.8/paddleocr{EXE_SUFFIX}
    # tools/PaddleOCR-GPU-v1.3.2-CUDA-12.9/paddleocr{EXE_SUFFIX}

    # support.files路径
    supportFilesPath = ConfigItem(
        "OCR",
        "supportFilesPath",
        str(Path("tools/PaddleOCR.PP-OCRv5.support.files/").absolute()),
    )

    tempDir = ConfigItem(
        "OCR",
        "TempDir",
        str(Path("temp/").absolute()),
    )

    # 开始时间（例如：0:00 或 1:23:45）
    # 命令行使用：--time_start
    timeStart = ConfigItem("OCR", "TimeStart", "0:00", restart=False)

    # 结束时间（例如：0:10 或 2:34:56）
    # 命令行使用：--time_end
    timeEnd = ConfigItem("OCR", "TimeEnd", "", restart=False)

    # 字幕语言
    # 命令行使用：--lang
    ocr_lang = OptionsConfigItem(
        "OCR",
        "Lang",
        "中文与英文",
        OptionsValidator(list(videocr_languages_dict.keys())),
        restart=False,
    )

    # 字幕位置
    # 命令行使用：--subtitle_position
    ocr_position = OptionsConfigItem(
        "OCR",
        "Position",
        "任意",
        OptionsValidator(list(subtitle_positions_list.keys())),
        restart=False,
    )

    # 置信度阈值 (0-100)
    # 命令行使用：--conf_threshold
    confThreshold = RangeConfigItem(
        "OCR", "ConfThreshold", 75, RangeValidator(0, 100), restart=False
    )

    # 相似度阈值 (0-100)
    # 命令行使用：--sim_threshold
    simThreshold = RangeConfigItem(
        "OCR", "SimThreshold", 80, RangeValidator(0, 100), restart=False
    )

    # 最大合并间隔（秒）
    # 命令行使用：--max_merge_gap
    maxMergeGap = RangeConfigItem(
        "OCR", "MaxMergeGap", 0.1, RangeValidator(0.1, 10.0), restart=False
    )

    # 亮度阈值 (0-255)
    # 命令行使用：--brightness_threshold
    brightnessThreshold = RangeConfigItem(
        "OCR", "BrightnessThreshold", 0, RangeValidator(0, 255), restart=False
    )

    # SSIM阈值 (0-100)
    # 命令行使用：--ssim_threshold
    ssimThreshold = RangeConfigItem(
        "OCR", "SsimThreshold", 92, RangeValidator(0, 100), restart=False
    )

    # 最大OCR图像宽度（像素）
    # 命令行使用：--ocr_image_max_width
    ocrImageMaxWidth = RangeConfigItem(
        "OCR", "OcrImageMaxWidth", 1280, RangeValidator(100, 4096), restart=False
    )

    # 跳过的帧数
    # 命令行使用：--frames_to_skip
    framesToSkip = RangeConfigItem(
        "OCR", "FramesToSkip", 1, RangeValidator(0, 100), restart=False
    )

    # 最小字幕持续时间（秒）
    # 命令行使用：--min_subtitle_duration
    minSubtitleDuration = RangeConfigItem(
        "OCR", "MinSubtitleDuration", 0.2, RangeValidator(0.1, 10.0), restart=False
    )

    # 是否启用GPU使用
    # 命令行使用：--use_gpu
    useGpu = ConfigItem("OCR", "UseGpu", True, BoolValidator(), restart=False)

    # GPU环境
    # PaddleOCR-GPU-v1.4.2-CUDA-11.8
    # PaddleOCR-GPU-v1.4.2-CUDA-12.9
    gpuEnv = OptionsConfigItem(
        "OCR",
        "GpuEnv",
        "CPU-v1.4.0",
        OptionsValidator(
            ["CPU-v1.4.0", "GPU-v1.4.0-CUDA-11.8", "GPU-v1.4.0-CUDA-12.9"]
        ),
        restart=False,
    )

    # 是否使用全帧OCR
    # 命令行使用：--use_fullframe
    # useFullframe = ConfigItem(
    #     "OCR", "UseFullframe", False, BoolValidator(), restart=False
    # )

    # 是否启用双区域OCR
    # 命令行使用：--use_dual_zone
    useDualZone = ConfigItem(
        "OCR", "UseDualZone", False, BoolValidator(), restart=False
    )

    # 是否启用角度分类
    # 命令行使用：--use_angle_cls
    useAngleCls = ConfigItem(
        "OCR", "UseAngleCls", False, BoolValidator(), restart=False
    )

    # 是否启用后处理
    # 命令行使用：--post_processing
    postProcessing = ConfigItem(
        "OCR", "PostProcessing", True, BoolValidator(), restart=False
    )

    # 是否使用服务器模型
    # 命令行使用：--use_server_model
    useServerModel = ConfigItem(
        "OCR", "UseServerModel", False, BoolValidator(), restart=False
    )

    # translate settings
    # 原语言
    origin_lang = OptionsConfigItem(
        "Translate",
        "OriginLang",
        "日语",
        OptionsValidator(list(translate_language_dict.keys())),
        restart=False,
    )

    # 目标语言
    target_lang = OptionsConfigItem(
        "Translate",
        "TargetLang",
        "中文",
        OptionsValidator(list(translate_language_dict.keys())),
        restart=False,
    )

    # prompt模板
    promptTemplate = ConfigItem(
        "Translate",
        "PromptTemplate",
        "将以下{origin_lang}文本翻译成{target_lang},\n人名优先匹配《东方Project》,保留原本srt格式,你只需要输出翻译后的结果，不需要输出多余内容\n{content}",
        restart=False,
    )

    # AI模型选择
    ai_model = OptionsConfigItem(
        "Translate",
        "AiModel",
        "腾讯混元",
        OptionsValidator(list(AI_model_dict.keys())),
        restart=False,
    )

    # Deepseek API Key (付费)
    deepseekApiKey = ConfigItem("Translate", "DeepseekApiKey", "", restart=False)
    # glm-4.5-flash API Key (免费)
    glmApiKey = ConfigItem("Translate", "GlmApiKey", "", restart=False)
    # Spark Lite API Key (免费)
    sparkApiKey = ConfigItem("Translate", "SparkApiKey", "", restart=False)
    # Spark Lite App ID (免费)
    sparkAppId = ConfigItem("Translate", "SparkAppId", "", restart=False)
    # Spark Lite API Secret (免费)
    sparkApiSecret = ConfigItem("Translate", "SparkApiSecret", "", restart=False)
    # 腾讯混元 API Key (免费)
    hunyuanApiKey = ConfigItem("Translate", "HunyuanApiKey", "", restart=False)
    # 书生 API Key (免费)
    internApiKey = ConfigItem("Translate", "InternApiKey", "", restart=False)
    # 百度ERNIE-Speed-128K API Key (免费)
    ernieSpeedApiKey = ConfigItem("Translate", "ErnieSpeedApiKey", "", restart=False)
    # Gemini 3 Flash API Key (免费)
    geminiApiKey = ConfigItem("Translate", "GeminiApiKey", "", restart=False)

    # 自定义模型配置
    customModelEnabled = ConfigItem(
        "Translate", "CustomModelEnabled", False, BoolValidator(), restart=False
    )
    customModelName = ConfigItem("Translate", "CustomModelName", "", restart=False)
    customModelApiKey = ConfigItem("Translate", "CustomModelApiKey", "", restart=False)
    customModelBaseUrl = ConfigItem(
        "Translate", "CustomModelBaseUrl", "", restart=False
    )
    customModelEndpoint = ConfigItem(
        "Translate", "CustomModelEndpoint", "", restart=False
    )

    # AI温度 (0-2)
    aiTemperature = ConfigItem("Translate", "AiTemperature", "0.7", restart=False)

    # ffmpeg settings
    ffmpegPath = ConfigItem(
        "FFmpeg", "FFmpegPath", str(Path(f"tools/ffmpeg{EXE_SUFFIX}").absolute())
    )

    # 并发数量，同时压制多个视频时的最大并行数
    concurrentEncodes = RangeConfigItem(
        "FFmpeg", "ConcurrentEncodes", 2, RangeValidator(1, 5), restart=False
    )

    # 视频编码器
    ffmpegVideoCodec = OptionsConfigItem(
        "FFmpeg",
        "VideoCodec",
        "libx264",
        OptionsValidator(["libx264", "libx265", "libvpx-vp9", "copy"]),
        restart=False,
    )

    # CRF质量参数 (0-51, 0为无损，18-28为常用范围)
    ffmpegCrf = RangeConfigItem(
        "FFmpeg", "Crf", 24, RangeValidator(0, 51), restart=False
    )

    # 编码速度预设
    ffmpegPreset = OptionsConfigItem(
        "FFmpeg",
        "Preset",
        "medium",
        OptionsValidator(
            [
                "ultrafast",
                "superfast",
                "veryfast",
                "faster",
                "fast",
                "medium",
                "slow",
                "slower",
                "veryslow",
            ]
        ),
        restart=False,
    )

    # 音频处理模式
    ffmpegAudioMode = OptionsConfigItem(
        "FFmpeg",
        "AudioMode",
        "auto",
        OptionsValidator(["auto", "encode", "none", "copy"]),
        restart=False,
    )

    # 音频编码器
    ffmpegAudioCodec = OptionsConfigItem(
        "FFmpeg",
        "AudioCodec",
        "aac",
        OptionsValidator(["aac", "libmp3lame", "opus", "copy"]),
        restart=False,
    )

    # 音频码率
    ffmpegAudioBitrate = OptionsConfigItem(
        "FFmpeg",
        "AudioBitrate",
        "128k",
        OptionsValidator(["64k", "96k", "128k", "192k", "256k", "320k"]),
        restart=False,
    )

    # x264高级参数 - 参考帧数量
    ffmpegRefFrames = RangeConfigItem(
        "FFmpeg", "RefFrames", 6, RangeValidator(1, 16), restart=False
    )

    # x264高级参数 - B帧数量
    ffmpegBFrames = RangeConfigItem(
        "FFmpeg", "BFrames", 6, RangeValidator(0, 16), restart=False
    )

    # x264高级参数 - 关键帧间隔
    ffmpegKeyint = RangeConfigItem(
        "FFmpeg", "Keyint", 250, RangeValidator(1, 1000), restart=False
    )

    # x264高级参数 - 最小关键帧间隔
    ffmpegMinkeyint = RangeConfigItem(
        "FFmpeg", "Minkeyint", 1, RangeValidator(1, 100), restart=False
    )

    # x264高级参数 - 场景切换阈值
    ffmpegScenecut = RangeConfigItem(
        "FFmpeg", "Scenecut", 60, RangeValidator(0, 100), restart=False
    )

    # x264高级参数 - 量化器曲线压缩因子
    ffmpegQcomp = RangeConfigItem(
        "FFmpeg", "Qcomp", 0.5, RangeValidator(0.0, 1.0), restart=False
    )

    # x264高级参数 - 心理视觉率失真
    ffmpegPsyRd = ConfigItem("FFmpeg", "PsyRd", "0.3,0", restart=False)

    # x264高级参数 - 自适应量化模式
    ffmpegAqMode = OptionsConfigItem(
        "FFmpeg", "AqMode", 2, OptionsValidator([0, 1, 2, 3]), restart=False
    )

    # x264高级参数 - 自适应量化强度
    ffmpegAqStrength = RangeConfigItem(
        "FFmpeg", "AqStrength", 0.8, RangeValidator(0.0, 2.0), restart=False
    )

    # 是否启用x264高级参数
    ffmpegUseAdvanced = ConfigItem(
        "FFmpeg", "UseAdvanced", False, BoolValidator(), restart=False
    )

    # 输出文件格式
    ffmpegOutputFormat = OptionsConfigItem(
        "FFmpeg",
        "OutputFormat",
        "mp4",
        OptionsValidator(["mp4", "mkv", "avi", "mov", "webm"]),
        restart=False,
    )

    # 是否覆盖输出文件
    ffmpegOverwriteOutput = ConfigItem(
        "FFmpeg", "OverwriteOutput", True, BoolValidator(), restart=False
    )

    # 视频缩放选项
    ffmpegScale = OptionsConfigItem(
        "FFmpeg",
        "Scale",
        "none",
        OptionsValidator(["none", "720p", "1080p", "1440p", "2160p", "custom"]),
        restart=False,
    )

    # 自定义视频尺寸 (例如: "1920:1080")
    ffmpegCustomScale = ConfigItem("FFmpeg", "CustomScale", "1920:1080", restart=False)

    # 帧率设置
    ffmpegFps = OptionsConfigItem(
        "FFmpeg",
        "Fps",
        "source",
        OptionsValidator(["source", "24", "25", "30", "50", "60"]),
        restart=False,
    )

    # 视频码率限制 (可选，为空表示不使用码率限制)
    ffmpegVideoBitrate = ConfigItem("FFmpeg", "VideoBitrate", "", restart=False)

    # 是否启用硬件加速
    ffmpegUseHardwareAcceleration = ConfigItem(
        "FFmpeg", "UseHardwareAcceleration", False, BoolValidator(), restart=False
    )

    # 硬件加速类型
    ffmpegHardwareAccelerator = OptionsConfigItem(
        "FFmpeg",
        "HardwareAccelerator",
        "auto",
        OptionsValidator(["auto", "cuda", "qsv", "dxva2", "videotoolbox"]),
        restart=False,
    )

    # B站上传配置
    apiPath = ConfigItem(
        "Bilibili", "ApiPath", str(Path(f"tools/upload-video{EXE_SUFFIX}").absolute())
    )
    bilibiliSessdata = ConfigItem("Bilibili", "Sessdata", "", restart=False)
    bilibiliBiliJct = ConfigItem("Bilibili", "BiliJct", "", restart=False)
    bilibiliBuvid3 = ConfigItem("Bilibili", "Buvid3", "", restart=False)


cfg = Config()
cfg.themeMode.value = Theme.LIGHT
qconfig.load(str(CONFIG_FILE.absolute()), cfg)
