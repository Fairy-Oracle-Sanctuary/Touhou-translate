# coding: utf-8
import sys
from pathlib import Path

AUTHOR = "baby2016"
VERSION = "1.8.0"
YEAR = "2025"

RELEASE_URL = "https://github.com/Fairy-Oracle-Sanctuary/Touhou-translate/releases"

CONFIG_FOLDER = Path("AppData").absolute()

CONFIG_FILE = CONFIG_FOLDER / "config.json"
DB_PATH = CONFIG_FOLDER / "database.db"

COVER_FOLDER = CONFIG_FOLDER / "Cover"
COVER_FOLDER.mkdir(exist_ok=True, parents=True)

PIC_SUFFIX = ".jpg"

# videocr
videocr_languages_dict = {
    "阿巴扎语": "abq",
    "阿迪格语": "ady",
    "南非荷兰语": "af",
    "阿尔巴尼亚语": "sq",
    "安吉卡语": "ang",
    "阿拉伯语": "ar",
    "阿瓦尔语": "ava",
    "阿塞拜疆语": "az",
    "白俄罗斯语": "be",
    "博杰普尔语": "bho",
    "比哈尔语": "bh",
    "波斯尼亚语": "bs",
    "保加利亚语": "bg",
    "车臣语": "che",
    "中文与英文": "ch",
    "繁体中文": "chinese_cht",
    "克罗地亚语": "hr",
    "捷克语": "cs",
    "丹麦语": "da",
    "达尔格瓦语": "dar",
    "荷兰语": "nl",
    "英语": "en",
    "爱沙尼亚语": "et",
    "法语": "fr",
    "德语": "german",
    "果阿康卡尼语": "gom",
    "希腊语": "el",
    "哈里亚纳语": "bgc",
    "印地语": "hi",
    "匈牙利语": "hu",
    "冰岛语": "is",
    "印度尼西亚语": "id",
    "印古什语": "inh",
    "爱尔兰语": "ga",
    "意大利语": "it",
    "日语": "japan",
    "卡巴尔达语": "kbd",
    "韩语": "korean",
    "库尔德语": "ku",
    "拉克语": "lbe",
    "拉丁语": "la",
    "拉脱维亚语": "lv",
    "列兹金语": "lez",
    "立陶宛语": "lt",
    "马加希语": "mah",
    "迈蒂利语": "mai",
    "马来语": "ms",
    "马耳他语": "mt",
    "毛利语": "mi",
    "马拉地语": "mr",
    "蒙古语": "mn",
    "那格浦尔语": "sck",
    "尼泊尔语": "ne",
    "尼瓦尔语": "new",
    "挪威语": "no",
    "奥克语": "oc",
    "巴利语": "pi",
    "波斯语": "fa",
    "波兰语": "pl",
    "葡萄牙语": "pt",
    "罗马尼亚语": "ro",
    "俄语": "ru",
    "梵语": "sa",
    "塞尔维亚语(西里尔文)": "rs_cyrillic",
    "塞尔维亚语(拉丁文)": "rs_latin",
    "斯洛伐克语": "sk",
    "斯洛文尼亚语": "sl",
    "西班牙语": "es",
    "斯瓦希里语": "sw",
    "瑞典语": "sv",
    "塔巴萨兰语": "tab",
    "他加禄语": "tl",
    "泰米尔语": "ta",
    "泰卢固语": "te",
    "泰语": "th",
    "土耳其语": "tr",
    "乌克兰语": "uk",
    "乌尔都语": "ur",
    "维吾尔语": "ug",
    "乌兹别克语": "uz",
    "越南语": "vi",
    "威尔士语": "cy",
}
subtitle_positions_list = {
    "居中": "center",
    "左对齐": "left",
    "右对齐": "right",
    "任意": "any",
}

if sys.platform == "win32":
    EXE_SUFFIX = ".exe"
else:
    EXE_SUFFIX = ""
