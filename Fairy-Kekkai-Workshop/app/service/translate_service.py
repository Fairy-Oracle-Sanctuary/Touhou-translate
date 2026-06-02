import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator
from urllib.parse import urlparse

from openai import OpenAI
from PySide6.QtCore import QThread, Signal

from ..common.config import cfg
from ..common.event_bus import event_bus
from ..common.logger import Logger
from ..common.setting import AI_ERROR_MAP


def parse_srt(srt_content: str) -> list[dict]:
    """解析 SRT 文件，提取纯文本和元数据"""
    items = []
    blocks = re.split(r"\n\s*\n", srt_content.strip())

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        # 第一行是序号
        index = lines[0].strip()

        # 第二行是时间轴
        time = lines[1].strip()

        # 剩余行是文本
        text = "\n".join(lines[2:]).strip()

        items.append({"index": index, "time": time, "text": text})

    return items


def assemble_srt(items: list[dict]) -> str:
    """将解析后的 SRT 项目重新组装为 SRT 格式"""
    blocks = []
    for item in items:
        block = f"{item['index']}\n{item['time']}\n{item['text']}"
        blocks.append(block)

    return "\n\n".join(blocks)


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
    output_history: str = ""  # 存储完整输出历史

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
        # Deepseek 专属参数
        self.deepseek_model = self.args.get("deepseek_model", "deepseek-v4-flash")
        self.deepseek_reasoning = self.args.get("deepseek_reasoning", False)


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

    def translate_with_context(
        self, origin_lang: str, target_lang: str, messages: list, temperature: float
    ) -> Generator[str, None, None]:
        """使用多轮对话进行翻译"""
        try:
            response = self.get_client().chat.completions.create(
                model=self.get_model_name(),
                messages=messages,
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
    def __init__(self, task: TranslateTask = None):
        self.task = task

    def get_client(self):
        return OpenAI(
            api_key=cfg.get(cfg.deepseekApiKey), base_url="https://api.deepseek.com"
        )

    def get_model_name(self):
        if self.task:
            return self.task.deepseek_model
        return cfg.get(cfg.deepseekModel)

    def translate(
        self, origin_lang: str, target_lang: str, content: str, temperature: float
    ) -> Generator[str, None, None]:
        prompt = cfg.get(cfg.promptTemplate).format(
            origin_lang=origin_lang,
            target_lang=target_lang,
            content=content,
        )
        print(prompt)

        try:
            # 构建基础参数
            create_params = {
                "model": self.get_model_name(),
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "temperature": temperature,
            }

            # 如果启用深度思考模式
            if self.task and self.task.deepseek_reasoning:
                create_params["reasoning_effort"] = "high"
                create_params["extra_body"] = {"thinking": {"type": "enabled"}}

            response = self.get_client().chat.completions.create(**create_params)
            for chunk in response:
                if content_piece := chunk.choices[0].delta.content:
                    yield content_piece
        except Exception as e:
            raise e


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
        return OpenAI(
            api_key=cfg.get(cfg.sparkApiKey),
            base_url="https://spark-api-open.xf-yun.com/v1",
        )

    def get_model_name(self):
        return "generalv3.5"


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

            service = (
                service_cls(self.task)
                if service_cls == DeepseekService
                else service_cls()
            )

            # 解析 SRT 文件
            srt_items = parse_srt(self.task.raw_content)
            batch_size = 100

            # 构建系统提示
            system_prompt = cfg.get(cfg.promptTemplate).format(
                origin_lang=self.task.origin_lang,
                target_lang=self.task.target_lang,
            )

            # 初始化对话历史
            messages = [{"role": "system", "content": system_prompt}]

            # 分批翻译
            for i in range(0, len(srt_items), batch_size):
                # 检查状态
                if not self._is_running:
                    break

                batch = srt_items[i : i + batch_size]
                batch_texts = [
                    f"{j + 1}. {item['text']}" for j, item in enumerate(batch)
                ]
                user_content = f"请翻译以下{len(batch)}句：\n" + "\n".join(batch_texts)

                # 添加用户消息
                messages.append({"role": "user", "content": user_content})

                # 调用翻译
                full_response = ""
                for text_piece in service.translate_with_context(
                    self.task.origin_lang,
                    self.task.target_lang,
                    messages,
                    self.task.temperature,
                ):
                    if not self._is_running:
                        break
                    full_response += text_piece

                # 添加助手回复到对话历史
                messages.append({"role": "assistant", "content": full_response})

                # 解析翻译结果
                translated_texts = self._parse_translation_response(
                    full_response, len(batch)
                )

                # 更新 SRT 项目
                for j, item in enumerate(batch):
                    if j < len(translated_texts):
                        item["text"] = translated_texts[j]

                # 更新进度
                progress = int((i + batch_size) / len(srt_items) * 100)
                progress_msg = f"翻译进度: {min(progress, 100)}%"
                self.task.output_history += progress_msg + "\n"
                event_bus.translate_update_signal.emit(str(self.task.id), progress_msg)

            # 组装最终的 SRT
            final_srt = assemble_srt(srt_items)

            # 写入文件
            with open(self.task.output_file, "w", encoding="utf-8") as f:
                f.write(final_srt)

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

    def _parse_translation_response(
        self, response: str, expected_count: int
    ) -> list[str]:
        """解析 AI 的翻译响应，提取翻译文本"""
        # 按行分割
        lines = response.strip().split("\n")

        # 过滤空行
        lines = [line.strip() for line in lines if line.strip()]

        # 尝试匹配 "1. 翻译文本" 格式
        translations = []
        for line in lines:
            # 移除序号前缀（如 "1. ", "2. " 等）
            match = re.match(r"^\d+\.\s*(.+)$", line)
            if match:
                translations.append(match.group(1))
            else:
                # 如果没有序号，直接使用
                translations.append(line)

        # 如果数量不匹配，尝试其他解析方式
        if len(translations) != expected_count:
            # 尝试按行直接分割
            translations = lines[:expected_count]

        # 确保数量匹配
        while len(translations) < expected_count:
            translations.append("***")

        return translations[:expected_count]

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
            self.task.output_history = cleaned_content
            event_bus.translate_update_signal.emit(str(self.task.id), cleaned_content)
        else:
            self.logger.info(f"未检测到思考内容，文件保持不变: {self.task.output_file}")

    def _write_and_notify(self, chunk: str, file_handle):
        file_handle.write(chunk)
        file_handle.flush()
        self.task.output_history += chunk
        event_bus.translate_update_signal.emit(str(self.task.id), chunk)

    def cancel(self):
        self._is_running = False
        self.task.status = "已取消"
