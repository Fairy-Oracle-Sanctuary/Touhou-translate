from openai import OpenAI
from PySide6.QtCore import QThread, QTimer, Signal
from zai import ZhipuAiClient

from ..common.config import cfg
from ..common.event_bus import event_bus
from .srt_service import Srt


class TranslateTask:
    """OCR任务类"""

    _id_counter = 0

    def __init__(self, args):
        self.args = args
        self.status = "等待中"  # 等待中, 翻译中, 已完成, 失败
        self.progress = 0
        self.error_message = ""
        self.input_file = args.get("srt_path")
        self.output_file = args.get("output_path")
        self.origin_lang = args.get("origin_lang")
        self.target_lang = args.get("target_lang")
        self.raw_content = args.get("raw_content")
        self.AI = args.get("AI")
        self.temperature = args.get("temperature")

        TranslateTask._id_counter += 1
        self.id = TranslateTask._id_counter


class TranslateThread(QThread):
    """OCR处理线程"""

    finished_signal = Signal(bool, str)  # 成功/失败, 消息
    cancelled_signal = Signal()  # 新增：取消完成信号

    def __init__(self, task):
        super().__init__()
        self.task = task
        self.is_cancelled = False

    def run(self):
        try:
            num = 0
            resp_content = ""
            final_content = ""
            content_all = self.task.raw_content.split("\n\n")
            for content in content_all:
                resp_content += f"{content}\n\n"
                num += 1
                if num % 100 == 0 or num == len(content_all):
                    # deepseek
                    if self.task.AI == "deepseek":
                        final_content = DeepseekTranslateService.translate(
                            self.task.origin_lang,
                            self.task.target_lang,
                            resp_content,
                            self.task.temperature,
                        )

                    # glm4.5flash
                    elif self.task.AI == "glm-4.5-flash":
                        final_content = GLMTranslateService.translate(
                            self.task.origin_lang,
                            self.task.target_lang,
                            resp_content,
                            self.task.temperature,
                        )

                    # 写入文件
                    Srt.write_raw_content(final_content, self.task.output_file)

            # 最终输出
            if content_all and not self.is_cancelled:
                self.finished_signal.emit(True, "翻译完成")
                event_bus.translate_finished_signal.emit(
                    True, [final_content, self.task.output_file]
                )

        except Exception as e:
            error_message = self._handle_error(e)
            self.finished_signal.emit(False, f"翻译失败: {error_message}")
            event_bus.translate_finished_signal.emit(False, [error_message])

    def cancel(self):
        """取消翻译处理 - 异步非阻塞版本"""
        if not self.isRunning() or self.is_cancelled:
            return

        self.is_cancelled = True
        self.task.status = "已取消"

        # 使用定时器异步检查线程状态，避免阻塞
        self._cancellation_timer = QTimer()
        self._cancellation_timer.timeout.connect(self._checkCancellationStatus)
        self._cancellation_timer.start(100)  # 每100ms检查一次

        # 设置超时保护，5秒后强制终止
        QTimer.singleShot(5000, self._forceTerminateIfNeeded)

    def _checkCancellationStatus(self):
        """检查取消状态"""
        if not self.isRunning():
            # 线程已结束
            self._cancellation_timer.stop()
            self.cancelled_signal.emit()
        elif self.isFinished():
            # 线程已完成
            self._cancellation_timer.stop()
            self.cancelled_signal.emit()

    def _forceTerminateIfNeeded(self):
        """如果需要，强制终止线程"""
        if self.isRunning():
            self.terminate()
            # 等待一小段时间让线程终止
            if self.wait(1000):
                self.cancelled_signal.emit()
            else:
                self.cancelled_signal.emit()

    def _handle_error(self, error):
        """根据错误类型返回对应的错误信息"""
        error_str = str(error)

        if self.task.AI == "deepseek":
            return DeepseekTranslateService.analysis_error(error_str)
        elif self.task.AI == "glm-4.5-flash":
            return GLMTranslateService.analysis_error(error_str)


class DeepseekTranslateService:
    @staticmethod
    def translate(
        origin_lang: str, target_lang: str, resp_content: str, temperature: float
    ) -> str:
        """翻译字幕"""
        final_content = ""

        client = OpenAI(
            api_key=cfg.get(cfg.deepseekApiKey), base_url="https://api.deepseek.com"
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "user",
                    "content": f"请将以下{origin_lang}srt文件翻译成{target_lang},人名优先匹配《东方Project》,保留原本srt格式,你只需要输出结果\n{resp_content}",
                },
            ],
            stream=False,
            temperature=temperature,
        )
        resp_content = ""

        # 处理成功的情况
        resp = response.choices[0].message.content.replace("```srt\n", "")
        final_content += resp.replace("```", "\n")

        return final_content

    @staticmethod
    def analysis_error(error_str):
        """根据错误类型返回对应的错误信息"""

        # API密钥错误
        if "invalid_api_key" in error_str or "authentication" in error_str.lower():
            return "API密钥无效，请检查设置"

        # 额度不足
        elif "insufficient_quota" in error_str or "quota" in error_str.lower():
            return "API额度不足，请检查账户余额"

        # 请求频率限制
        elif "rate_limit" in error_str.lower():
            return "请求频率超限，请稍后重试"

        # 模型过载
        elif "overloaded" in error_str or "busy" in error_str.lower():
            return "服务器繁忙，请稍后重试"

        # 网络连接问题
        elif "connection" in error_str.lower() or "timeout" in error_str:
            return "网络连接失败，请检查网络设置"

        # 请求超时
        elif "timeout" in error_str.lower():
            return "请求超时，请检查网络连接"

        # 服务器错误
        elif "internal" in error_str.lower() or "server" in error_str.lower():
            return "服务器内部错误，请稍后重试"

        # 无效请求
        elif "invalid_request" in error_str:
            return "请求参数无效，请检查输入内容"

        # 模型不可用
        elif "model_not_found" in error_str or "unavailable" in error_str.lower():
            return "模型暂时不可用，请稍后重试"

        # 未知错误
        else:
            return f"未知错误: {error_str}"


class GLMTranslateService:
    @staticmethod
    def translate(
        origin_lang: str, target_lang: str, resp_content: str, temperature: float
    ) -> str:
        """翻译字幕"""
        final_content = ""

        client = ZhipuAiClient(api_key=cfg.get(cfg.glmApiKey))

        response = client.chat.completions.create(
            model="glm-4.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": f"请将以下{origin_lang}srt文件翻译成{target_lang},人名优先匹配《东方Project》,保留原本srt格式,你只需要输出结果\n{resp_content}",
                },
            ],
            stream=False,
            temperature=temperature,
        )
        resp = response.choices[0].message.content.replace("```srt\n", "")
        final_content += resp.replace("```", "\n")

        return final_content

    @staticmethod
    def analysis_error(error_str):
        """根据错误类型返回对应的错误信息"""

        # API密钥错误 (401 Unauthorized)
        if (
            "401" in error_str
            or "unauthorized" in error_str.lower()
            or "invalid api key" in error_str.lower()
        ):
            return "API密钥无效或已过期，请在设置中检查并更新API密钥"

        # 请求参数错误 (400 Bad Request)
        elif (
            "400" in error_str
            or "bad request" in error_str.lower()
            or "invalid request" in error_str.lower()
        ):
            return "请求参数错误，请检查输入内容格式是否正确"

        # 请求频率限制 (429 Too Many Requests)
        elif (
            "429" in error_str
            or "too many requests" in error_str.lower()
            or "rate limit" in error_str.lower()
        ):
            return "请求频率超限，请稍后重试或联系智谱AI调整配额"

        # 服务器内部错误 (500 Internal Server Error)
        elif "500" in error_str or "internal server error" in error_str.lower():
            return "服务器内部错误，请稍后重试"

        # 服务不可用 (503 Service Unavailable)
        elif "503" in error_str or "service unavailable" in error_str.lower():
            return "服务暂时不可用，请稍后重试"

        # 模型不可用或未找到
        elif "model_not_found" in error_str or "model unavailable" in error_str.lower():
            return "模型暂时不可用，请检查模型名称或稍后重试"

        # 额度不足
        elif (
            "insufficient_quota" in error_str
            or "quota" in error_str.lower()
            or "余额不足" in error_str
        ):
            return "API额度不足，请检查账户余额或联系智谱AI充值"

        # 网络连接问题
        elif "connection" in error_str.lower() or "connect" in error_str.lower():
            return "网络连接失败，请检查网络设置"

        # 请求超时
        elif "timeout" in error_str.lower():
            return "请求超时，请检查网络连接或稍后重试"

        # 未知错误
        else:
            return f"未知错误: {error_str}"
