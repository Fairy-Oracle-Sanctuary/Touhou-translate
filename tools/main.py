# pip install yt_dlp requests opencv-python numpy

import os

from tool import *


def get_project_paths(directory: str) -> list:
    """
    获取projects文件夹下所有子文件夹
    """
    project_paths = []
    for item in os.listdir(directory):
        full_path = os.path.join(directory, item)
        if (
            os.path.isdir(full_path)
            and not full_path.endswith(".git")
            and not full_path.endswith("tools")
            and not full_path.endswith("CLI")
        ):
            project_paths.append(full_path)
    return project_paths


def check_project():
    project_paths = get_project_paths(".")
    if not project_paths:
        print("\n=== 未找到任何工程文件夹 ===")
        return

    print("\n=== 工程列表 ===")
    for n, project in enumerate(project_paths):
        project_name = project.split("\\")[-1]
        print(f"{n + 1}.{project_name}")
    check_num = int(input("\n请输入要检查的项目序号：")) - 1

    project_ifm = dict()
    # 项目名称
    project_ifm["project_name"] = project_paths[check_num].split("\\")[-1]
    # 总集数
    project_ifm["video_num"] = 0

    for dir in os.listdir(project_paths[check_num]):
        if dir.startswith("标题"):
            content = []
            title_org = []
            title_zh = []
            video_link = []
            title_len = 0
            with open(
                project_paths[check_num] + "/标题.txt", "r", encoding="utf-8"
            ) as title_file:
                try:
                    for line in title_file.readlines():
                        if not line.replace("\n", "") and not title_len:
                            title_len = len(content)
                        content.append(line.replace("\n", ""))

                    for i in range(title_len):
                        title_org.append(content[i])
                        title_zh.append(content[title_len + 2 + i * 4])
                        video_link.append(content[title_len + 3 + i * 4])

                    project_ifm["title_org"] = title_org
                    project_ifm["title_zh"] = title_zh
                    project_ifm["video_link"] = video_link
                except Exception:
                    print("工程错误，检查标题文件\n")
                    return

        elif dir.endswith(".txt"):
            # 项目标识名
            project_ifm["project_logo"] = dir.split(".")[0]
        else:
            project_ifm["video_num"] += 1

    print(
        f"\n=== 项目信息 ===\n项目名称：{project_ifm['project_name']}\n原标题：{project_ifm['project_logo']}\n总集数：{project_ifm['video_num']}\n"
    )

    num = 0
    for t1, t2, t3 in zip(
        project_ifm["title_org"], project_ifm["title_zh"], project_ifm["video_link"]
    ):
        num += 1
        print(f"{num}.\n原标题：{t1}\n中文译名：{t2}\n视频链接：{t3}\n")


if __name__ == "__main__":
    while True:
        print(
            "0.退出程序\n1.检查项目\n2.创建项目\n3.根据播放列表一键初始化项目\n4.补充空缺的视频\n5.视频硬字幕框选\n6.硬字幕文件复制\n7.文件改名"
        )

        func = int(input("请选择功能："))

        if func == 0:
            break
        elif func == 1:
            check_project()
        elif func == 2:
            create_project()
        elif func == 3:
            get_video_list(input("请输入视频列表网址："))
        elif func == 4:
            fix_video_list()
        elif func == 5:
            tool = VideoCoordinateTool(input("请输入视频路径："))
            tool.run()
        elif func == 6:
            file_copy()
        elif func == 7:
            rename_files()

# https://youtube.com/playlist?list=PLwnprYHAfPHaqEZqQFi2nQiPLg5Igo3mT&si=5RNTZWuao9UJS3p2
# C:\Users\ZHANGBaoHang\AppData\Local\Programs\Python\Python312\python.exe CLI\videocr_cli.py --video_path D:/东方project/projects/被捡回来的管家我竟要和主人蕾米莉亚交往了/1/生肉copy.mp4 --lang japan --subtitle_position center --output D:/东方project/projects/被捡回来的管家我竟要和主人蕾米莉亚交往了/1/原文copy.srt --time_start 0:00 --conf_threshold 75 --sim_threshold 80 --max_merge_gap 0.1 --ssim_threshold 92 --ocr_image_max_width 1280 --frames_to_skip 1 --min_subtitle_duration 0.2 --use_gpu true --use_fullframe false --use_dual_zone false --use_angle_cls false --post_processing true --use_server_model true --crop_x 1 --crop_y 680 --crop_width 1912 --crop_height 393
