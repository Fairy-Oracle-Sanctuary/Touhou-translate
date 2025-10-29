# sk-d197ab76b90d4e86916e2bbfd2a975c9

from openai import OpenAI
from PySide6.QtCore import QThread

from ..common.config import cfg
from ..common.event_bus import event_bus


class TranslateThread(QThread):
    """OCR处理线程"""

    def __init__(self, task, output_file, origin_lang, target_lang):
        super().__init__()
        self.task = task
        self.output_file = output_file
        self.origin_lang = origin_lang
        self.target_lang = target_lang

    def run(self):
        try:
            client = OpenAI(
                api_key=cfg.get(cfg.deepseekApiKey), base_url="https://api.deepseek.com"
            )

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "user",
                        "content": f"请将以下{self.origin_lang}srt文件翻译成{self.target_lang},人名优先匹配《东方Project》,保留原本srt格式,你只需要输出结果\n{self.task.raw_content}",
                    },
                ],
                stream=False,
                temperature=1.3,
            )

            # 处理成功的情况
            resp = response.choices[0].message.content
            print(resp)
            event_bus.translate_finished_signal.emit(True, [resp, self.output_file])

        except Exception as e:
            error_message = self._handle_error(e)
            event_bus.translate_finished_signal.emit(False, [error_message])

    def _handle_error(self, error):
        """根据错误类型返回对应的错误信息"""
        error_str = str(error)

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
