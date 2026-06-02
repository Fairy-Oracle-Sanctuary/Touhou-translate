# Fairy-Kekkai-Workshop 开发文档

## 项目概述

**Fairy-Kekkai-Workshop** 是一个功能完整的视频字幕处理和管理工具，支持视频下载、字幕提取、多语言翻译、视频压制以及 B 站直播内容上传等功能。该项目采用 PySide6 + QFluentWidgets 构建现代化桌面应用。

### 核心特性
- 📥 **视频下载**：基于 yt-dlp，支持 YouTube 等多个视频平台
- 🔤 **字幕提取**：集成 paddleocr，支持自定义 OCR 参数和模型路径
- �️ **语音识别**：基于 [Const-me/Whisper](https://github.com/Const-me/Whisper)，支持多语言语音转字幕，带实时进度显示
- �🌐 **智能翻译**：支持多个 AI 模型（OpenAI、Deepseek、腾讯混元、ERNIE、Gemini、书生等）
- 🎬 **视频压制**：基于 FFmpeg，支持自定义编码参数
- 💾 **项目管理**：完整的项目文件系统管理，支持导入/链接外部项目
- 🎨 **主题切换**：标题栏快捷主题切换按钮，支持深色/浅色模式
- 🚀 **启动页**：带进度条和状态文字的启动页面

---

## 项目结构

```
Fairy-Kekkai-Workshop/
├── Fairy-Kekkai-Workshop.py       # 主入口文件
├── DEVELOPMENT.md                 # 本文件
├── requirements.txt               # 依赖列表
├── deploy.py                      # 打包脚本
├── app/
│   ├── common/                    # 公共模块
│   │   ├── config.py              # 配置管理（QConfig）
│   │   ├── event_bus.py           # 全局事件总线
│   │   ├── events.py              # 事件数据类
│   │   ├── logger.py              # 日志模块
│   │   ├── setting.py             # 应用常量和默认配置
│   │   └── style_sheet.py         # QSS 样式表管理
│   │
│   ├── components/                # UI 组件
│   │   ├── dialog.py              # 自定义对话框
│   │   ├── config_card.py         # 配置卡片组件
│   │   ├── project_card.py        # 项目卡片组件
│   │   ├── task_card.py           # 任务卡片组件
│   │   ├── infobar.py             # 通知栏组件
│   │   ├── system_tray.py         # 系统托盘
│   │   └── *.py                   # 其他 UI 组件
│   │
│   ├── service/                   # 业务逻辑服务
│   │   ├── project_service.py     # 项目管理服务
│   │   ├── translate_service.py   # 翻译服务（支持多个 AI 模型）
│   │   ├── download_service.py    # 视频下载服务
│   │   ├── ffmpeg_service.py      # 视频压制服务
│   │   ├── ocr_service.py         # OCR 字幕提取服务
│   │   ├── srt_service.py         # 字幕文件处理
│   │   ├── version_service.py     # 版本更新检查
│   │   └── CLI/                   # CLI 工具模块
│   │       ├── videocr/           # videocr 核心模块
│   │       │   ├── videocr_cli.py # videocr CLI 入口
│   │       │   ├── deploy.py      # CLI 打包脚本
│   │       │   ├── api.py         # OCR API
│   │       │   ├── video.py       # 视频处理
│   │       │   ├── models.py      # 数据模型
│   │       │   └── utils.py       # 工具函数
│   │       ├── whispernet/         # WhisperNet CLI (C#)
│   │       │   ├── Program.cs     # CLI 入口，支持进度输出
│   │       │   └── WhisperNetCLI.csproj
│   │       └── paddleocr/         # paddleocr 源码
│   │           └── main.cpp       # C++ CLI 实现
│   │
│   ├── view/                      # UI 视图层
│   │   ├── main_window.py         # 主窗口（含启动页、主题切换按钮）
│   │   ├── home_interface.py      # 主页（含关于卡片、清空日志/重置设置按钮）
│   │   ├── project_interface.py   # 项目管理页
│   │   ├── download_interface.py  # 下载页
│   │   ├── translate_interface.py # 翻译页
│   │   ├── ffmpeg_interface.py    # 压制页
│   │   ├── videocr_interface.py   # OCR 页
│   │   ├── whisper_interface.py   # 语音识别页
│   │   ├── setting_interface.py   # 设置页（含 Whisper CLI/模型路径配置）
│   │   └── *_task_interface.py    # 任务进度页
│   │
│   └── resource/                  # 资源文件
│       ├── resource_rc.py         # Qt 资源编译文件
│       ├── resource.qrc           # Qt 资源描述
│       ├── images/                # 图片资源
│       └── qss/                   # 样式表
│
├── tools/                         # 外部工具目录
│   ├── OCR.model/                 # OCR 模型文件
│   ├── PaddleOCR/                 # paddleocr 可执行文件
│   │   ├── paddleocr.exe
│   │   ├── CVUtils.dll
│   │   ├── onnxruntime.dll
│   │   └── ...
│   ├── Whisper.model/             # Whisper 模型文件（ggml 格式）
│   ├── Whisper/                   # WhisperNet CLI 及依赖
│   │   ├── WhisperNetCLI.exe
│   │   ├── Whisper.dll
│   │   ├── WhisperNet.dll
│   │   ├── ComLight.dll
│   │   └── ...
│   ├── videocr-cli.exe            # videocr CLI 可执行文件
│   ├── yt-dlp.exe                 # 视频下载工具
│   └── ffmpeg.exe                 # 视频处理工具
│
└── AppData/                       # 应用数据目录
    ├── config.json                # 用户配置
    ├── project.json               # 项目记录
    └── database.db                # 应用数据库
```

---

## 环境搭建

### 系统要求
- Python 3.9+
- Windows/macOS/Linux
- 硬件加速器（可选）：用于视频压制加速

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate.git
   cd Touhou-translate/Fairy-Kekkai-Workshop
   ```

2. **创建虚拟环境**（推荐使用 uv）
   ```bash
   uv venv
   source .venv/bin/activate  # Unix/macOS
   .venv\Scripts\activate     # Windows
   ```

3. **安装依赖**
   ```bash
   uv pip install -r requirements.txt
   ```

4. **准备 OCR 工具**
   - 下载 paddleocr 放到 `tools/PaddleOCR/` 目录
   - 下载 OCR 模型文件放到 `tools/OCR.model/` 目录
   - 编译 videocr CLI: `cd app/service/CLI && python deploy.py`

5. **准备 Whisper 工具**（仅 Windows）
   - 下载 Whisper 模型文件（ggml 格式）放到 `tools/Whisper.model/` 目录
   - 编译 WhisperNet CLI: `cd app/service/CLI/whispernet && dotnet publish -c Release -r win-x64 --self-contained`
   - 复制发布文件夹内容到 `tools/Whisper/` 目录

5. **运行应用**
   ```bash
   python Fairy-Kekkai-Workshop.py
   ```

### 依赖说明

| 包名 | 版本 | 用途 |
|------|------|------|
| PySide6-Fluent-Widgets | 最新 | GUI 框架 |
| opencv-python | 最新 | 图像处理 |
| openai | 最新 | OpenAI/兼容 API |
| numpy | 最新 | 数值计算 |
| Pillow | 最新 | 图像处理 |
| requests | 最新 | HTTP 请求 |
| av | 最新 | 视频处理 |
| fast_ssim | 最新 | 图像相似度计算 |


**外部工具**（需手动准备）：
```bash
# paddleocr（字幕提取）
# 下载 paddleocr.exe 放到 tools/PaddleOCR/ 目录
# 下载 OCR 模型文件放到 tools/OCR.model/ 目录

# FFmpeg（视频压制）
# Windows: 下载编译版本或通过 scoop/chocolatey
# macOS: brew install ffmpeg
# Linux: sudo apt-get install ffmpeg

# yt-dlp（视频下载）
uv pip install yt-dlp
```

---

## 核心模块说明

### 1. 配置管理（`app/common/config.py`）

配置系统基于 `QConfig`，支持持久化存储。

```python
from app.common.config import cfg

# 读取配置
theme = cfg.get(cfg.themeMode)  # 获取主题模式

# 设置配置
cfg.set(cfg.dpiScale, 1.5)
```

**主要配置项**：
- `dpiScale`：DPI 缩放倍数
- `themeMode`：主题（深色/浅色）
- `downloadFormat`：视频格式
- `downloadQuality`：视频质量
- `promptTemplate`：翻译提示词模板
- `whisperCliPath`：WhisperNetCLI.exe 路径
- `whisperModelPath`：Whisper 模型路径
- AI 模型的 API Key（OpenAI、Deepseek、腾讯混元等）

### 2. 事件总线（`app/common/event_bus.py`）

全局事件分发机制，用于组件间通信。

```python
from app.common.event_bus import event_bus

# 发送事件
event_bus.notification_service.show_success("标题", "消息内容")

# 监听事件
event_bus.download_requested.connect(on_download_started)
```

### 3. 项目管理（`app/service/project_service.py`）

管理本地项目文件结构，支持多格式字幕和视频。

```python
from app.service.project_service import project

# 创建项目
project.creat_files("项目名", 12, "原标题")

# 删除项目
project.delete_project("/path/to/project")

# 获取项目信息
progress = project.get_project_progress(project_id)
```

**项目文件结构**：
```
项目名/
├── 标题.txt          # 集中存储所有元数据
├── 原标题.txt        # 原标题文件
└── 1-12/             # 分集目录
    ├── 原视频.mp4
    ├── 翻译后的视频.mp4
    ├── 原文.srt
    ├── 译文.srt
    ├── 生肉.srt
    └── 封面.jpg
```

### 4. 翻译服务（`app/service/translate_service.py`）

支持多个 AI 模型的流式翻译。

```python
from app.service.translate_service import TranslateThread, TranslateTask

# 创建翻译任务
task = TranslateTask(args={
    "srt_path": "/path/to/subtitle.srt",
    "output_path": "/path/to/output.srt",
    "origin_lang": "Japanese",
    "target_lang": "Chinese",
    "AI": "deepseek",
    "temperature": 0.7,
})

# 执行翻译
thread = TranslateThread(task)
thread.finished_signal.connect(on_finished)
thread.start()
```

**支持的 AI 模型**：
- ✅ Deepseek（最推荐）
- ✅ 腾讯混元（HunyuanTurbos）
- ✅ 百度 ERNIE Speed 128K
- ✅ 书生（InternLM）
- ✅ Google Gemini 3 Flash
- ✅ 讯飞 Spark Lite（SDK 不兼容）
- ✅ GLM-4.5 Flash（SDK 不兼容）
- ✅ 自定义模型（兼容 OpenAI API 格式）

### 5. OCR 服务（`app/service/ocr_service.py`）

基于 paddleocr 的字幕提取服务。

```python
from app.service.ocr_service import OCRProcess, OCRTask

# 创建 OCR 任务
task = OCRTask(args={
    "video_path": "/path/to/video.mp4",
    "file_path": "/path/to/output.srt",
    "temp_dir": "/path/to/temp",
    "lang": "ja",
    "paddleocr_path": "tools/PaddleOCR/paddleocr.exe",
    "supportFilesPath": "tools/OCR.model",
})

# 执行 OCR
process = OCRProcess(task)
process.finished_signal.connect(on_finished)
process.start()
```

**OCR 流程**：
1. 视频帧提取和 SSIM 过滤
2. 文本检测（Text-Detection-Only pass）
3. 文本识别（OCR）
4. 字幕生成和合并

### 6. Whisper 语音识别服务（`app/service/whisper_service.py`）

基于 [Const-me/Whisper](https://github.com/Const-me/Whisper) 的语音转字幕服务，支持实时进度显示。

```python
from app.service.whisper_service import WhisperProcess, WhisperTask

# 创建 Whisper 任务
task = WhisperTask(args={
    "video_path": "/path/to/video.mp4",
    "output_path": "/path/to/output.srt",
    "model": "tools/Whisper.model/ggml-model-whisper-large.bin",
    "language": "auto",  # auto 表示自动检测，或指定 zh/ja/en
    "format": "srt",
    "gpu": "自动检测",
})

# 执行识别
process = WhisperProcess(task)
process.finished_signal.connect(on_finished)
process.start()
```

**Whisper CLI 进度输出格式**：
- CLI 输出 `PROGRESS:XX` 表示识别进度（XX 为百分比）
- 服务层解析进度并更新 UI 进度条
- 语言为 `auto` 时不传 `--language` 参数，让 Whisper 自动检测

### 7. 日志系统（`app/common/logger.py`）

结构化日志，自动保存到 AppData。支持在主页「关于」卡片中清空日志。

```python
from app.common.logger import Logger

logger = Logger("ModuleName", "category")
logger.info("消息")
logger.warning("警告")
logger.error("错误信息")
```

**日志位置**：`AppData/Log/`

### 8. 启动页（`app/view/main_window.py`）

带进度条和状态文字的启动页面，在应用初始化时显示。

```python
class LoadingSplashScreen(SplashScreen):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        self.progressBar = ProgressBar(self, useAni=False)  # 禁用动画以支持同步进度
        self.statusLabel = BodyLabel("正在启动...", self)

    def setProgress(self, value: int, text: str = None):
        self.progressBar.setValue(value)
        if text:
            self.statusLabel.setText(text)
        QApplication.processEvents()
```

**加载阶段**：
- 10%: 初始化服务
- 30%: 读取设置
- 50%: 加载界面
- 80%: 初始化系统托盘
- 100%: 启动完成

### 9. 主题切换（`app/view/main_window.py`）

标题栏最小化按钮左侧的主题切换按钮。

```python
def _initThemeButton(self):
    self.themeButton = TransparentToolButton(self.titleBar)
    self.themeButton.setFixedSize(self.titleBar.minBtn.size())
    self._updateThemeButtonIcon()
    self.themeButton.clicked.connect(self._toggleTheme)
    self.titleBar.buttonLayout.insertWidget(0, self.themeButton, 0, Qt.AlignTop)

def _toggleTheme(self):
    theme = Theme.LIGHT if isDarkTheme() else Theme.DARK
    cfg.set(cfg.themeMode, theme)
    setTheme(theme)
    self._updateThemeButtonIcon()
```

**图标逻辑**：
- 深色模式：显示太阳图标（切到浅色）
- 浅色模式：显示月亮图标（切到深色）

---

## 开发指南

### 添加新的 AI 翻译模型

1. **在 `app/service/translate_service.py` 中添加服务类**：

```python
class MyNewModelService(BaseTranslateService):
    def get_client(self):
        return OpenAI(
            api_key=cfg.get(cfg.myNewModelApiKey),
            base_url="https://api.example.com/v1",
        )

    def get_model_name(self) -> str:
        return "my-new-model"
```

2. **在 `SERVICES` 字典中注册**：

```python
SERVICES = {
    # ... 其他模型
    "my-new-model": MyNewModelService,
}
```

3. **在 `app/common/config.py` 中添加配置项**：

```python
myNewModelApiKey = ConfigItem(
    "MyNewModel", "ApiKey", "", restart=False
)
```

4. **在设置页面中添加 UI**（`app/view/setting_interface.py`）

### 添加新的项目功能

1. **在 `app/service/` 中创建服务类**
2. **在 `app/view/` 中创建对应的 UI 界面**
3. **通过 `event_bus` 连接服务与 UI**

### 跨平台注意事项

- ✅ 使用 `pathlib.Path` 处理路径（自动适配 Windows/Unix）
- ✅ 使用 `subprocess` 执行外部工具时注意平台差异
- ❌ 避免硬编码路径分隔符（如 `\` 或 `/`）
- ❌ 避免 Windows 特定的 API（如 `os.environ["QT_SCALE_FACTOR"]`）

---

## 常见问题

### Q: 应用启动时显示 Shiboken 警告

**A**: 这是 PySide6 的正常警告，不影响功能。可以安全忽略。

### Q: 字幕提取失败

**A**:
1. 确保 `paddleocr.exe` 存在于 `tools/PaddleOCR/` 目录
2. 确保 OCR 模型文件存在于 `tools/OCR.model/` 目录
3. 检查 VC++ 运行时是否已安装（需要 MSVCP140.dll 和 VCRUNTIME140.dll）
4. 检查 GPU 驱动是否支持 DirectML（如使用 GPU）

### Q: 翻译功能不可用

**A**:
- 确保已配置相应 AI 服务的 API Key（在设置页面）
- 部分 AI 模型（Spark、GLM）因 SDK 不兼容已禁用
- 推荐使用 Deepseek 或腾讯混元（支持较好）

### Q: Whisper 语音识别失败

**A**:
1. 确保 WhisperNetCLI.exe 存在于 `tools/Whisper/` 目录
2. 确保所有依赖 DLL（Whisper.dll、WhisperNet.dll、ComLight.dll）在同一目录
3. 确保 Whisper 模型文件存在于 `tools/Whisper.model/` 目录
4. 语言设置为 `auto` 时，CLI 会自动检测语言
5. 检查 GPU 驱动是否支持 DirectML（如使用 GPU）

### Q: 视频压制很慢

**A**:
1. 使用硬件加速（需 FFmpeg 支持）：配置 `-hwaccel cuda` 或 `-hwaccel videotoolbox`
2. 降低视频质量或分辨率
3. 使用更快的编码器（`libx264` → `libx265` 或 `av1`）

### Q: B 站上传失败

**A**:
1. 检查登录 Cookie 是否有效（每 3 个月需要更新）
2. 确保视频符合 B 站审核要求
3. 检查网络连接和代理设置

---

## 已知限制

| 功能 | 状态 | 备注 |
|------|------|------|
| 视频下载 | ✅ | 基于 yt-dlp，支持大多数平台 |
| 字幕提取 | ✅ | PaddleOCR，需手动安装模型 |
| 语音识别 | ✅ | [Const-me/Whisper](https://github.com/Const-me/Whisper)，仅 Windows，支持实时进度 |
| 翻译 | ⚠️ | 部分 AI 模型 SDK 不兼容 |
| 视频压制 | ✅ | 基于 FFmpeg，支持多种编码器 |
| 实时预览 | ❌ | 当前不支持 |
| 批量处理 | ⚠️ | 需要后台优化 |

---

## 性能优化建议

1. **减少 UI 更新频率**：使用定时器而非直接更新
2. **缓存配置**：避免频繁读写 `config.json`
3. **异步处理**：所有长时间操作使用 QThread
4. **内存管理**：及时释放大对象引用

---

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 使用 4 空格缩进
- 遵循 PEP 8
- 为公共 API 编写文档字符串
- 添加类型提示（Python 3.10+）

---

## 许可证

详见仓库根目录的 LICENSE 文件。

---

## 技术栈

- **UI 框架**：PySide6 + QFluentWidgets (Modern UI)
- **视频处理**：FFmpeg + yt-dlp
- **字幕识别**：paddleocr
- **语音识别**：[Const-me/Whisper](https://github.com/Const-me/Whisper)
- **翻译**：多个云 API（OpenAI、Deepseek、腾讯混元等）
- **B 站上传**：Bilibili API
- **配置存储**：JSON + SQLite
- **日志**：内置 Logger
- **包管理**：uv（推荐）

---

**最后更新**：2026 年 6 月 1 日  
**维护者**：`Baby2016` `镀铬酸钾`
