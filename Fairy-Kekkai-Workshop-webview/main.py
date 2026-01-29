import os

import webview


class Api:
    def __init__(self):
        pass

    def select_file(self, file_type="file"):
        """
        选择文件
        file_type: 'file' 或 'folder'
        """
        try:
            if file_type == "folder":
                result = webview.windows[0].create_file_dialog(
                    webview.FOLDER_DIALOG, directory=os.path.expanduser("~")
                )
            else:
                result = webview.windows[0].create_file_dialog(
                    webview.OPEN_DIALOG, directory=os.path.expanduser("~")
                )
            if result:
                return result[0] if isinstance(result, list) else result
            return None
        except Exception as e:
            return {"error": str(e)}

    def save_file(self, default_name="output.txt"):
        """
        保存文件对话框
        """
        try:
            result = webview.windows[0].create_file_dialog(
                webview.SAVE_DIALOG,
                directory=os.path.expanduser("~"),
                save_filename=default_name,
            )
            return result
        except Exception as e:
            return {"error": str(e)}

    def process_subtitle(self, params):
        """
        字幕提取处理
        params: 包含输入文件、输出路径、语言等参数
        """
        print(f"开始字幕提取: {params}")
        # 这里实现实际的字幕提取逻辑
        # 可以调用 PaddleOCR 或其他 OCR 工具

        # 模拟处理过程
        import time

        for i in range(0, 101, 20):
            webview.windows[0].evaluate_js(f"window.updateProgress({i})")
            time.sleep(0.5)

        return {"status": "success", "message": "字幕提取完成"}

    def process_translate(self, params):
        """
        字幕翻译处理
        params: 包含输入文件、模型、目标语言等参数
        """
        print(f"开始字幕翻译: {params}")
        # 这里实现实际的翻译逻辑
        # 可以调用 Deepseek、Gemini、ChatGPT 等 API

        # 模拟处理过程
        import time

        for i in range(0, 101, 10):
            webview.windows[0].evaluate_js(f"window.updateProgress({i})")
            time.sleep(0.5)

        return {"status": "success", "message": "翻译完成"}

    def process_ffmpeg(self, params):
        """
        视频压制处理
        params: 包含输入文件、输出路径、CRF、预设等参数
        """
        print(f"开始视频压制: {params}")
        # 这里实现实际的 FFmpeg 处理逻辑
        # 可以调用 FFmpeg 命令行工具

        # 模拟处理过程
        import time

        for i in range(0, 101, 5):
            webview.windows[0].evaluate_js(f"window.updateProgress({i})")
            time.sleep(0.3)

        return {"status": "success", "message": "视频压制完成"}

    def get_system_info(self):
        """
        获取系统信息
        """
        import platform

        return {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "machine": platform.machine(),
        }

    def open_folder(self, path):
        """
        打开文件夹
        """
        import platform
        import subprocess

        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
            return {"status": "success"}
        except Exception as e:
            return {"error": str(e)}


def main():
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # React 构建后的 HTML 文件路径
    html_path = os.path.join(script_dir, "frontend", "index.html")

    # 如果构建文件不存在，尝试使用开发服务器
    if not os.path.exists(html_path):
        print("警告: 未找到构建文件，请先运行 npm run build")
        print("或者使用开发模式: npm run dev")
        print("当前将尝试使用本地文件...")
        html_path = os.path.join(
            script_dir, "..", "Fairy-Kekkai-Workshop-Web", "index.html"
        )

    # 创建 API 实例
    api = Api()

    # 创建 webview 窗口
    window = webview.create_window(  # noqa
        "Fairy Kekkai Workshop",
        html_path,
        js_api=api,
        width=1280,
        height=800,
        min_size=(800, 600),
        resizable=True,
        fullscreen=False,
        background_color="#202020",
    )

    # 启动应用
    webview.start(debug=True)


if __name__ == "__main__":
    main()
