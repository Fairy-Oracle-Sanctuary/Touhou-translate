import os
import re

import requests
from PySide6.QtCore import QThread, Signal


class DownloadListThread(QThread):
    """下载线程 - 使用QProcess版本"""

    finished_signal = Signal(bool, str)  # 成功/失败, 消息

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        """下载整个视频列表"""
        url_list = []
        headers = {
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-arch": "x86",
            "sec-ch-ua-bitness": "64",
            "sec-ch-ua-form-factors": "Desktop",
            "sec-ch-ua-full-version": "140.0.7339.81",
            "sec-ch-ua-full-version-list": '"Chromium";v="140.0.7339.81", "Not=A?Brand";v="24.0.0.0", "Google Chrome";v="140.0.7339.81"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": "",
            "sec-ch-ua-platform": "Windows",
            "sec-ch-ua-platform-version": "19.0.0",
            "sec-ch-ua-wow64": "?0",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        }

        try:
            resp = requests.get(url=self.url, headers=headers, timeout=3)
        except requests.exceptions.Timeout:
            self.finished_signal.emit(False, "请求超时")
            return

        pattern = r'\[\{"url":"(.*?)","width":\d*,"height":\d*\}\]\},"title":\{"runs":\[\{"text":"(.*?)"\}\]'

        name = re.findall(pattern, resp.text)

        if not name:
            self.finished_signal.emit(False, "网址错误")
            return

        for i in name[:-1]:
            video = [
                i[-1],
                re.findall('\{"url":"(.*?)"', i[-2])[0].replace(
                    "hqdefault", "maxresdefault"
                ),
                "https://www.youtube.com/watch?v="
                + re.findall("vi/(.*)/", re.findall('\{"url":"(.*?)"', i[-2])[0])[0],
            ]
            for j in video:
                print(j)

            url_list.append(video)

        # 获取工程名
        while True:
            project_name = "" + input("请输入工程名（父文件夹名）: ").strip()
            if not project_name:
                print("工程名不能为空！")
                continue

            # 检查是否已存在同名文件夹
            if os.path.exists(project_name):
                print(f"错误：'{project_name}' 文件夹已存在！")
                continue

            # 检查非法字符
            invalid_chars = '<>:"\\|?*'
            if any(char in project_name for char in invalid_chars):
                print(f"工程名不能包含以下字符：{invalid_chars}")
                continue

            break

        # 获得标识名
        while True:
            try:
                label = input("请输入标识名: ").strip()
                break
            except Exception:
                print("请输入有效的标识名！")

        creat_files(project_name, len(url_list), label)

        with open(project_name + "/标题.txt", "w", encoding="utf-8") as title:
            for title_name in url_list:
                title.write(title_name[0])
                title.write("\n")
            title.write("\n")
            for title_name in url_list:
                title.write(title_name[0])
                title.write("\n")
                title.write(title_name[-1])
                title.write("\n\n")

        print("已写入标题文件")
        print("正在获取封面")

        cover_num = len(url_list)
        for i in range(1, cover_num + 1):
            download_image(
                url_list[i - 1][1], project_name + "/" + str(i) + "/封面.jpg"
            )
        print("封面提取完成")
        print("开始下载视频")

        video_list = []
        for i in url_list:
            video_list.append(i[-1])
        download_videos_multithreaded(video_list, save_path=project_name, max_workers=4)

        print("初始化完成\n")
