# coding: utf-8
import sys
from pathlib import Path

AUTHOR = "baby2016"
TEAM = "天机阁(Fairy-Oracle-Sanctuary)"
VERSION = "1.14.0"
YEAR = "2025"
UPDATE_TIME = "2026-2-16"

RELEASE_URL = "https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases"
GITHUB_URL = "https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate"

CONFIG_FOLDER = Path("AppData").absolute()

CONFIG_FILE = CONFIG_FOLDER / "config.json"
DB_PATH = CONFIG_FOLDER / "database.db"

COVER_FOLDER = CONFIG_FOLDER / "Cover"
COVER_FOLDER.mkdir(exist_ok=True, parents=True)

PIC_SUFFIX = ".jpg"

with open("PADDLEOCR_VERSION", "r") as f:
    PADDLEOCR_VERSION = f.read().strip()
# CPU-v1.3.2
# GPU-v1.3.2-CUDA-11.8
# GPU-v1.3.2-CUDA-12.9

# videocr
videocr_languages_dict = {
    # 常见语言
    "中文与英文": "ch",
    "繁体中文": "chinese_cht",
    "英语": "en",
    "日语": "japan",
    "韩语": "korean",
    "法语": "fr",
    "德语": "german",
    "西班牙语": "es",
    "葡萄牙语": "pt",
    "意大利语": "it",
    "俄语": "ru",
    "阿拉伯语": "ar",
    # 其他欧洲语言
    "荷兰语": "nl",
    "希腊语": "el",
    "瑞典语": "sv",
    "挪威语": "no",
    "丹麦语": "da",
    "芬兰语": "fi",
    "波兰语": "pl",
    "捷克语": "cs",
    "匈牙利语": "hu",
    "罗马尼亚语": "ro",
    "保加利亚语": "bg",
    "塞尔维亚语(西里尔文)": "rs_cyrillic",
    "塞尔维亚语(拉丁文)": "rs_latin",
    "克罗地亚语": "hr",
    "斯洛伐克语": "sk",
    "斯洛文尼亚语": "sl",
    "乌克兰语": "uk",
    "白俄罗斯语": "be",
    "阿尔巴尼亚语": "sq",
    "爱沙尼亚语": "et",
    "拉脱维亚语": "lv",
    "立陶宛语": "lt",
    "冰岛语": "is",
    "爱尔兰语": "ga",
    "威尔士语": "cy",
    "马耳他语": "mt",
    # 亚洲语言
    "印地语": "hi",
    "乌尔都语": "ur",
    "孟加拉语": "bh",
    "泰米尔语": "ta",
    "泰卢固语": "te",
    "马拉地语": "mr",
    "泰语": "th",
    "越南语": "vi",
    "印度尼西亚语": "id",
    "马来语": "ms",
    "菲律宾语": "tl",
    "波斯语": "fa",
    "土耳其语": "tr",
    "希伯来语": "he",
    "尼泊尔语": "ne",
    "僧伽罗语": "si",
    "缅甸语": "my",
    "高棉语": "km",
    "老挝语": "lo",
    "蒙古语": "mn",
    "维吾尔语": "ug",
    "乌兹别克语": "uz",
    # 其他语言
    "斯瓦希里语": "sw",
    "南非荷兰语": "af",
    "拉丁语": "la",
    "梵语": "sa",
    "毛利语": "mi",
    # 较少使用的语言
    "阿巴扎语": "abq",
    "阿迪格语": "ady",
    "安吉卡语": "ang",
    "阿瓦尔语": "ava",
    "阿塞拜疆语": "az",
    "博杰普尔语": "bho",
    "比哈尔语": "bh",
    "波斯尼亚语": "bs",
    "车臣语": "che",
    "达尔格瓦语": "dar",
    "果阿康卡尼语": "gom",
    "哈里亚纳语": "bgc",
    "印古什语": "inh",
    "卡巴尔达语": "kbd",
    "库尔德语": "ku",
    "拉克语": "lbe",
    "列兹金语": "lez",
    "马加希语": "mah",
    "迈蒂利语": "mai",
    "那格浦尔语": "sck",
    "尼瓦尔语": "new",
    "奥克语": "oc",
    "巴利语": "pi",
    "塔巴萨兰语": "tab",
}
subtitle_positions_list = {
    "居中": "center",
    "左对齐": "left",
    "右对齐": "right",
    "任意": "any",
}

# translate
translate_language_dict = {
    "英语": "en",
    "中文": "zh",
    "日语": "ja",
    "韩语": "ko",
    "法语": "fr",
    "德语": "de",
    "西班牙语": "es",
    "葡萄牙语": "pt",
    "俄语": "ru",
    "阿拉伯语": "ar",
    "意大利语": "it",
    "荷兰语": "nl",
    "印地语": "hi",
    "土耳其语": "tr",
    "越南语": "vi",
    "泰语": "th",
    "印尼语": "id",
    "瑞典语": "sv",
    "波兰语": "pl",
    "希腊语": "el",
    "捷克语": "cs",
    "丹麦语": "da",
    "芬兰语": "fi",
    "挪威语": "no",
    "匈牙利语": "hu",
    "罗马尼亚语": "ro",
    "乌克兰语": "uk",
    "波斯语": "fa",
    "希伯来语": "he",
}

# AI模型
AI_model_dict = {
    "GLM-4.5-FLASH": "glm-4.5-flash",
    "Deepseek": "deepseek",
    "Spark-Lite": "spark-lite",
    "腾讯混元": "hunyuan-turbos-latest",
    "书生": "intern-latest",
    "百度ERNIE-Speed-128K": "ernie-speed-128k",
}
AI_ERROR_MAP = {
    # --- 身份验证与权限 ---
    "invalid_api_key": "API密钥无效，请检查设置",
    "authentication": "认证失败，请检查API Key是否正确",
    "unauthorized": "未授权访问，密钥可能已过期",
    "permission": "账号权限不足，请确认模型访问权限",
    # --- 余额与额度 ---
    "insufficient_quota": "账户额度不足，请及时充值",
    "quota": "额度已耗尽或账号已欠费",
    "balance": "账户余额不足",
    "credit_limit": "已达到信用额度限制",
    # --- 请求频率与并发 ---
    "rate_limit": "请求频率过快（RPM），请稍后重试",
    "too_many_requests": "并发请求数过多（TPM），请稍后重试",
    "concurrency": "已达到最大并行任务数限制",
    "429": "请求过于频繁，触发流量控制",
    # --- 内容审核 (安全限制) ---
    "policy": "内容触发安全审核政策，无法处理",
    "sensitive": "包含敏感词汇，请求被拦截",
    "safety": "内容因安全风险被过滤器拦截",
    "filtered": "输出内容因合规性被过滤",
    # --- 服务器状态 ---
    "overloaded": "服务器负载过高，请稍后重试",
    "busy": "服务器繁忙，请稍后重试",
    "internal": "服务器内部错误，请联系厂商支持",
    "server": "后端服务异常",
    "upstream": "上游服务报错",
    "500": "服务器崩溃，请稍后再试",
    "503": "服务暂时不可用，可能正在维护",
    # --- 网络与超时 ---
    "timeout": "请求超时，网络不稳定或响应过慢",
    "connection": "网络连接失败，请检查代理或网络设置",
    "connect": "无法连接到 API 服务器",
    "proxy": "代理服务器配置错误或连接断开",
    # --- 参数与模型 ---
    "invalid_request": "请求参数有误，请检查设置",
    "model_not_found": "指定的模型不存在或已被下线",
    "context_length": "内容超出模型最大上下文长度限制",
    "bad_request": "无效请求，请检查输入格式",
}

if sys.platform == "win32":
    EXE_SUFFIX = ".exe"
else:
    EXE_SUFFIX = ""
