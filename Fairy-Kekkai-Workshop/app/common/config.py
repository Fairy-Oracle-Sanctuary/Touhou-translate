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

from .setting import CONFIG_FILE, CONFIG_FOLDER, EXE_SUFFIX, PIC_SUFFIX


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

    # download
    ytdlpPath = ConfigItem(
        "Download", "YTDLPPath", str(Path(f"tools/yt-dlp{EXE_SUFFIX}").absolute())
    )
    ffmpegPath = ConfigItem(
        "Download", "FFmpegPath", str(Path(f"tools/ffmpeg{EXE_SUFFIX}").absolute())
    )

    # ytdlp parameters
    # 下载格式选择：mp4(确保mp4格式), best(最佳质量), worst(最差质量), bestvideo(最佳视频), bestaudio(最佳音频)
    # 命令行使用：-f mp4 或 --format mp4
    downloadFormat = OptionsConfigItem(
        "YTDLP",
        "DownloadFormat",
        "mp4",
        # OptionsValidator(["mp4", "best", "worst", "bestvideo", "bestaudio"]),
        OptionsValidator(["mp4"]),
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
        "h264",
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


cfg = Config()
cfg.themeMode.value = Theme.LIGHT
qconfig.load(str(CONFIG_FILE.absolute()), cfg)
