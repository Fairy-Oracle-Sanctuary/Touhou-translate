import re

import requests
from PySide6.QtCore import QThread, Signal

from ..common.event_bus import event_bus
from ..common.events import EventBuilder
from .project_service import project


class DownloadListThread(QThread):
    """下载线程 - 使用QProcess版本"""

    finished_signal = Signal(bool, str, bool)  # 成功/失败, 消息, 是否全部完成

    def __init__(self, url, project_name, project_title):
        super().__init__()
        self.url = url
        self.project_name = project_name
        self.project_title = project_title

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
            self.finished_signal.emit(False, "请求超时", True)
            return

        pattern = r'\[\{"url":"(.*?)","width":\d*,"height":\d*\}\]\},"title":\{"runs":\[\{"text":"(.*?)"\}\]'

        name = re.findall(pattern, resp.text)

        if not name:
            self.finished_signal.emit(False, "网址错误", True)
            return

        for i in name[:-1]:
            video = [
                i[-1],
                re.findall(r'\{"url":"(.*?)"', i[-2])[0].replace(
                    "hqdefault", "maxresdefault"
                ),
                "https://www.youtube.com/watch?v="
                + re.findall(r"vi/(.*)/", re.findall(r'\{"url":"(.*?)"', i[-2])[0])[0],
            ]
            for j in video:
                print(j)

            url_list.append(video)

        project.creat_files(self.project_name, len(url_list), self.project_title)

        with open(self.project_name + "/标题.txt", "w", encoding="utf-8") as title:
            for title_name in url_list:
                title.write(title_name[0])
                title.write("\n")
            title.write("\n")
            for title_name in url_list:
                title.write(title_name[0])
                title.write("\n")
                title.write(title_name[-1])
                title.write("\n\n")

        self.finished_signal.emit(True, "已创建项目文件夹,正在下载封面", False)

        cover_num = len(url_list)
        for i in range(1, cover_num + 1):
            self.download_image(
                url_list[i - 1][1], self.project_name + "/" + str(i) + "/封面.jpg"
            )

        self.finished_signal.emit(True, "封面下载完成,开始添加下载视频任务", False)

        video_list = []
        for i in url_list:
            video_list.append(i[-1])
        for num, video_url in enumerate(video_list):
            event_bus.download_requested.emit(
                EventBuilder.download_video(
                    video_url,
                    str(project.projects_location / self.project_name / str(num + 1)),
                )
            )

        self.finished_signal.emit(True, "已完成项目初始化！", True)

    def download_image(self, image_url, save_path):
        """
        一个简单的图片下载函数
        :param image_url: 图片的URL地址
        :param save_path: 图片要保存的本地路径和文件名
        """
        try:
            # 1. 发送GET请求
            # stream=True 是一个好习惯，特别是对于大文件，但我们先看最简单的写法
            response = requests.get(image_url)

            # 检查请求是否成功 (状态码 200)
            response.raise_for_status()  # 如果请求失败 (如404, 500), 会抛出异常

            # 2. 以二进制写入模式打开文件
            with open(save_path, "wb") as f:
                # 3. 将响应的二进制内容写入文件
                f.write(response.content)

            self.finished_signal.emit(True, f"图片成功下载并保存到: {save_path}", False)

        except requests.exceptions.RequestException as e:
            self.finished_signal.emit(False, f"下载图片时出错: {e}", False)
