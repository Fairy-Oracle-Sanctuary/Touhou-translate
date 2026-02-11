import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator
from urllib.parse import urlparse

from openai import OpenAI
from PySide6.QtCore import QThread, Signal
from sparkai.llm.llm import (
    ChatSparkLLM,
    ChunkPrintHandler,
)

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.logger import Logger
from ..common.setting import AI_ERROR_MAP


def remove_thinking_content(text: str) -> str:
    # 匹配<think>和</think>
    thinking_pattern = r"<think>.*?</think>"

    cleaned_text = re.sub(thinking_pattern, "", text, flags=re.DOTALL).strip()

    return cleaned_text


@dataclass
class TranslateTask:
    args: dict
    id: int = 0
    status: str = "等待中"
    progress: int = 0
    error_message: str = ""

    _id_counter = 0

    def __post_init__(self):
        TranslateTask._id_counter += 1
        self.id = TranslateTask._id_counter
        self.input_file = self.args.get("srt_path")
        self.output_file = self.args.get("output_path")
        self.origin_lang = self.args.get("origin_lang")
        self.target_lang = self.args.get("target_lang")
        self.raw_content = self.args.get("raw_content", "")
        self.AI = self.args.get("AI")
        self.temperature = self.args.get("temperature", 0.7)


class BaseTranslateService(ABC):
    """翻译服务类"""

    ERROR_MAP = AI_ERROR_MAP

    @abstractmethod
    def get_client(self):
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        pass

    def translate(
        self, origin_lang: str, target_lang: str, content: str, temperature: float
    ) -> Generator[str, None, None]:
        prompt = cfg.get(cfg.promptTemplate).format(
            origin_lang=origin_lang,
            target_lang=target_lang,
            content=content,
        )
        print(prompt)
        model = self.get_model_name()
        if model == "spark-lite":
            try:
                response = self.get_client()
                messages = [{"role": "user", "content": prompt}]
                handler = ChunkPrintHandler()
                a = response.stream(messages, callbacks=[handler])
                for chunk in a:
                    yield chunk.content
            except Exception as e:
                print(e)
                raise e
        else:
            try:
                response = self.get_client().chat.completions.create(
                    model=self.get_model_name(),
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                    temperature=temperature,
                )
                for chunk in response:
                    if content_piece := chunk.choices[0].delta.content:
                        yield content_piece
            except Exception as e:
                raise e

    @classmethod
    def analysis_error(cls, error_str: str) -> str:
        error_str = error_str.lower()
        for key, msg in cls.ERROR_MAP.items():
            if key in error_str:
                return msg
        return f"未知错误: {error_str}"


class DeepseekService(BaseTranslateService):
    def get_client(self):
        return OpenAI(
            api_key=cfg.get(cfg.deepseekApiKey), base_url="https://api.deepseek.com"
        )

    def get_model_name(self):
        return "deepseek-chat"


class GLMService(BaseTranslateService):
    def get_client(self):
        return OpenAI(
            api_key=cfg.get(cfg.glmApiKey),
            base_url="https://open.bigmodel.cn/api/paas/v4/",
        )
        # return ZhipuAiClient(api_key=cfg.get(cfg.glmApiKey))

    def get_model_name(self):
        return "glm-4.5-flash"


class SparkLiteService(BaseTranslateService):
    def get_client(self):
        return ChatSparkLLM(
            spark_api_url="wss://spark-api.xf-yun.com/v1.1/chat",
            spark_app_id=cfg.get(cfg.sparkAppId),
            spark_api_key=cfg.get(cfg.sparkApiKey),
            spark_api_secret=cfg.get(cfg.sparkApiSecret),
            spark_llm_domain="lite",
            streaming=True,
        )

    def get_model_name(self):
        return "spark-lite"


class HunyuanService(BaseTranslateService):
    def get_client(self):
        return OpenAI(
            api_key=cfg.get(cfg.hunyuanApiKey),
            base_url="https://api.hunyuan.cloud.tencent.com/v1",
        )

    def get_model_name(self):
        return "hunyuan-turbos-latest"


class InternService(BaseTranslateService):
    def get_client(self):
        return OpenAI(
            api_key=cfg.get(cfg.internApiKey),
            base_url="https://chat.intern-ai.org.cn/api/v1",
        )

    def get_model_name(self):
        return "intern-latest"


class ErnieSpeedService(BaseTranslateService):
    def get_client(self):
        return OpenAI(
            api_key=cfg.get(cfg.ernieSpeedApiKey),
            base_url="https://qianfan.baidubce.com/v2/",
        )

    def get_model_name(self):
        return "ernie-speed-128k"


class GeminiService(BaseTranslateService):
    def get_client(self):
        return OpenAI(
            api_key=cfg.get(cfg.geminiApiKey),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

    def get_model_name(self):
        return "gemini-3-flash-preview"


class CustomModelService(BaseTranslateService):
    """自定义模型服务类"""

    def get_client(self):
        if not cfg.get(cfg.customModelEnabled):
            raise Exception("自定义模型未启用")

        api_key = cfg.get(cfg.customModelApiKey)
        base_url = cfg.get(cfg.customModelBaseUrl)

        if not api_key:
            raise Exception("请填写自定义模型的API密钥")

        if not base_url:
            raise Exception("请填写自定义模型的API基础URL")

        # 规范化 base_url：若只有 host[:port] 而无 path，则自动追加 /v1
        def _normalize_base_url(url: str) -> str:
            parsed = urlparse(url)
            if not parsed.path or parsed.path == "":
                return url.rstrip("/") + "/v1"
            return url.rstrip("/")

        normalized_base = _normalize_base_url(base_url)

        return OpenAI(api_key=api_key, base_url=normalized_base)

    def get_model_name(self):
        if not cfg.get(cfg.customModelEnabled):
            return "custom-model"

        model_name = cfg.get(cfg.customModelName)
        if not model_name:
            raise Exception("请填写自定义模型名称")

        # 如果有自定义端点，优先使用端点
        endpoint = cfg.get(cfg.customModelEndpoint)
        if endpoint:
            return endpoint

        return model_name


class TranslateThread(QThread):
    finished_signal = Signal(bool, str)
    cancelled_signal = Signal()

    SERVICES = {
        "deepseek": DeepseekService,
        "glm-4.5-flash": GLMService,
        "spark-lite": SparkLiteService,
        "hunyuan-turbos-latest": HunyuanService,
        "intern-latest": InternService,
        "ernie-speed-128k": ErnieSpeedService,
        "gemini-3-flash-preview": GeminiService,
        "custom-model": CustomModelService,
    }

    def __init__(self, task: TranslateTask):
        super().__init__()
        self.logger = Logger("TranslateProcess", "translate")
        self.task = task
        self._is_running = True

    def run(self):
        try:
            service_cls = self.SERVICES.get(self.task.AI)
            if not service_cls:
                event_bus.translate_finished_signal.emit(
                    False, f"不支持的AI模型: {self.task.AI}"
                )
                self.logger.error(f"不支持的AI模型: {self.task.AI}")
                return

            service = service_cls()
            chunks_to_translate = self.task.raw_content.split("\n\n")
            batch_size = 50

            with open(self.task.output_file, "w", encoding="utf-8") as f:
                for i in range(0, len(chunks_to_translate), batch_size):
                    # 检查状态
                    if not self._is_running:
                        break

                    batch_content = "\n\n".join(chunks_to_translate[i : i + batch_size])

                    # 传递运行状态检查
                    for text_piece in service.translate(
                        self.task.origin_lang,
                        self.task.target_lang,
                        batch_content,
                        self.task.temperature,
                    ):
                        if not self._is_running:
                            break
                        self._write_and_notify(text_piece, f)

                    f.write("\n\n")

            # 正常运行结束或被拦截后的信号处理
            if not self._is_running:
                # 如果是因为取消而停止，发送取消信号
                self.cancelled_signal.emit()
                self.logger.info(f"翻译任务已取消: {self.task.input_file}")
            else:
                # 翻译完成后进行后处理：去除思考内容
                try:
                    self._post_process_translation()
                    self.finished_signal.emit(True, "翻译完成")
                    event_bus.translate_finished_signal.emit(
                        True, ["", self.task.output_file]
                    )
                    self.logger.info(f"翻译任务已完成: {self.task.input_file}")
                except Exception as e:
                    error_msg = f"后处理失败: {str(e)}"
                    self.finished_signal.emit(False, error_msg)
                    event_bus.translate_finished_signal.emit(False, [error_msg])
                    self.logger.error(
                        f"翻译后处理失败: {self.task.input_file} - {error_msg}"
                    )

        except Exception as e:
            # 如果是报错导致的线程停止，不再发取消信号，只发错误信号
            error_msg = BaseTranslateService.analysis_error(str(e))
            self.finished_signal.emit(False, f"翻译失败: {error_msg}")
            event_bus.translate_finished_signal.emit(False, [error_msg])
            self.logger.error(f"翻译任务失败: {self.task.input_file} - {error_msg}")

    def _post_process_translation(self):
        """翻译后处理：去除思考内容"""
        # 读取翻译后的文件内容
        with open(self.task.output_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 去除思考内容
        cleaned_content = remove_thinking_content(content)

        # 如果内容有变化，重新写入文件
        if cleaned_content != content:
            with open(self.task.output_file, "w", encoding="utf-8") as f:
                f.write(cleaned_content)
            self.logger.info(f"已去除思考内容，文件已更新: {self.task.output_file}")
            event_bus.translate_update_signal.emit(str(self.task.id), cleaned_content)
        else:
            self.logger.info(f"未检测到思考内容，文件保持不变: {self.task.output_file}")

    def _write_and_notify(self, chunk: str, file_handle):
        file_handle.write(chunk)
        file_handle.flush()
        event_bus.translate_update_signal.emit(str(self.task.id), chunk)

    def cancel(self):
        self._is_running = False
        self.task.status = "已取消"
