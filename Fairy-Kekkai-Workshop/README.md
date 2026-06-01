# Fairy Kekkai Workshop

一个功能完整的视频字幕处理和管理工具，支持视频下载、字幕提取、语音识别、多语言翻译、视频压制等功能。

## 功能特性

- 📥 **视频下载**：基于 yt-dlp，支持 YouTube 等多个视频平台
- 🔤 **字幕提取**：集成 paddleocr，支持自定义 OCR 参数和模型路径
- 🎙️ **语音识别**：基于 WhisperNet，支持多语言语音转字幕，带实时进度显示（仅 Windows）
- 🌐 **智能翻译**：支持多个 AI 模型（OpenAI、Deepseek、腾讯混元、ERNIE、Gemini、书生等）
- 🎬 **视频压制**：基于 FFmpeg，支持自定义编码参数
- 💾 **项目管理**：完整的项目文件系统管理，支持导入/链接外部项目
- 🎨 **主题切换**：标题栏快捷主题切换按钮，支持深色/浅色模式
- 🚀 **启动页**：带进度条和状态文字的启动页面

## 系统要求

- Python 3.9+
- Windows/macOS/Linux
  - OCR 和语音识别功能仅支持 Windows
- 硬件加速器（可选）：用于视频压制加速

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate.git
cd Touhou-translate/Fairy-Kekkai-Workshop
```

### 2. 创建虚拟环境（推荐使用 uv）

```bash
uv venv
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
uv pip install -r requirements.txt
```

### 4. 准备外部工具

#### OCR 工具（仅 Windows）
- 下载 paddleocr 放到 `tools/PaddleOCR/` 目录
- 下载 OCR 模型文件放到 `tools/OCR.model/` 目录
- 编译 videocr CLI: `cd app/service/CLI && python deploy.py`

#### Whisper 工具（仅 Windows）
- 下载 Whisper 模型文件（ggml 格式）放到 `tools/Whisper.model/` 目录
- 编译 WhisperNet CLI: `cd app/service/CLI/whispernet && dotnet publish -c Release -r win-x64 --self-contained`
- 复制发布文件夹内容到 `tools/Whisper/` 目录

#### 其他工具
- **FFmpeg**：视频压制工具
  - Windows: 下载编译版本或通过 scoop/chocolatey 安装
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt-get install ffmpeg`
- **yt-dlp**：视频下载工具
  ```bash
  uv pip install yt-dlp
  ```

### 5. 运行应用

```bash
python Fairy-Kekkai-Workshop.py
```

## 使用说明

### 首次运行

首次运行时会显示新手引导，介绍软件的主要功能和使用方法。

### 主页功能

- **关于卡片**：显示应用版本信息，包含清空日志和重置设置按钮
- **项目管理**：创建和管理视频字幕项目
- **下载**：从 YouTube 等平台下载视频
- **OCR**：从视频中提取硬字幕（仅 Windows）
- **语音识别**：从视频中提取语音转字幕（仅 Windows）
- **翻译**：使用 AI 模型翻译字幕
- **压制**：使用 FFmpeg 压制视频
- **设置**：配置应用参数和外部工具路径

### 主题切换

点击标题栏最小化按钮左侧的主题切换按钮，可在深色/浅色模式之间快速切换。

### 日志管理

- 日志自动保存到 `AppData/Log/` 目录
- 在主页「关于」卡片中点击清空日志按钮可清空所有日志

### 重置设置

- 在主页「关于」卡片中点击重置设置按钮可恢复默认配置
- 重置后会自动重启应用

## 配置说明

主要配置项可在设置页面修改：

- **个性化**：主题、主题色、界面缩放、背景图片
- **项目**：项目详情页数量
- **下载**：yt-dlp、FFmpeg 路径
- **Whisper**（仅 Windows）：CLI 路径、模型路径、语言选择
- **AI 翻译**：各 AI 模型的 API Key 配置

## 开发文档

详细的开发文档请参阅 [DEVELOPMENT.md](DEVELOPMENT.md)

## 常见问题

### Q: 应用启动时显示 Shiboken 警告

A: 这是 PySide6 的正常警告，不影响功能。可以安全忽略。

### Q: 字幕提取失败

A:
1. 确保 `paddleocr.exe` 存在于 `tools/PaddleOCR/` 目录
2. 确保 OCR 模型文件存在于 `tools/OCR.model/` 目录
3. 检查 VC++ 运行时是否已安装（需要 MSVCP140.dll 和 VCRUNTIME140.dll）
4. 检查 GPU 驱动是否支持 DirectML（如使用 GPU）

### Q: Whisper 语音识别失败

A:
1. 确保 WhisperNetCLI.exe 存在于 `tools/Whisper/` 目录
2. 确保所有依赖 DLL（Whisper.dll、WhisperNet.dll、ComLight.dll）在同一目录
3. 确保 Whisper 模型文件存在于 `tools/Whisper.model/` 目录
4. 语言设置为 `auto` 时，CLI 会自动检测语言
5. 检查 GPU 驱动是否支持 DirectML（如使用 GPU）

### Q: 翻译功能不可用

A:
- 确保已配置相应 AI 服务的 API Key（在设置页面）
- 部分 AI 模型（Spark、GLM）因 SDK 不兼容已禁用
- 推荐使用 Deepseek 或腾讯混元（支持较好）

### Q: 视频压制很慢

A:
1. 使用硬件加速（需 FFmpeg 支持）：配置 `-hwaccel cuda` 或 `-hwaccel videotoolbox`
2. 降低视频质量或分辨率
3. 使用更快的编码器（`libx264` → `libx265` 或 `av1`）

## 已知限制

| 功能 | 状态 | 备注 |
|------|------|------|
| 视频下载 | ✅ | 基于 yt-dlp，支持大多数平台 |
| 字幕提取 | ✅ | PaddleOCR，需手动安装模型，仅 Windows |
| 语音识别 | ✅ | WhisperNet，仅 Windows，支持实时进度 |
| 翻译 | ⚠️ | 部分 AI 模型 SDK 不兼容 |
| 视频压制 | ✅ | 基于 FFmpeg，支持多种编码器 |
| 实时预览 | ❌ | 当前不支持 |
| 批量处理 | ⚠️ | 需要后台优化 |

## 技术栈

- **UI 框架**：PySide6 + QFluentWidgets (Modern UI)
- **视频处理**：FFmpeg + yt-dlp
- **字幕识别**：paddleocr
- **语音识别**：WhisperNet (C# .NET 6)
- **翻译**：多个云 API（OpenAI、Deepseek、腾讯混元等）
- **配置存储**：JSON + SQLite
- **日志**：内置 Logger
- **包管理**：uv（推荐）

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

详见仓库根目录的 LICENSE 文件。

---

**最后更新**：2026 年 6 月 1 日  
**维护者**：`Baby2016` `镀铬酸钾`
