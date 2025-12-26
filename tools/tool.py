import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor

import requests
import yt_dlp
from get_video_pos import VideoCoordinateTool
from main import get_project_paths


def download_video(url, save_path):
    ydlopts = {
        # "proxy": os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy"),
        "outtmpl": save_path,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",  # 强制输出为 MP4
        "noplaylist": True,
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydlopts) as ydl:
        ydl.download([url])


def download_videos_multithreaded(url_list, save_path="./videos", max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for n, url in enumerate(url_list):
            executor.submit(
                download_video,
                url,
                save_path=save_path + "/" + str(n + 1) + "/生肉.mp4",
            )


def download_image(image_url: str, save_path: str) -> None:
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

        print(f"图片成功下载并保存到: {save_path}")

    except requests.exceptions.RequestException as e:
        print(f"下载图片时出错: {e}")


def creat_files(project_name: str, subfolder_count: int, label: str) -> None:
    """创建工程文件夹"""
    os.makedirs(project_name)
    print(f"已创建工程文件夹: {project_name}")

    # 创建子文件夹
    for i in range(1, subfolder_count + 1):
        subfolder_path = os.path.join(project_name, str(i))
        os.makedirs(subfolder_path)
        print(f"已创建子文件夹: {i}")

    # 创建空的标题文件
    title_file = os.path.join(project_name, "标题.txt")
    with open(title_file, "w", encoding="utf-8"):
        pass  # 创建空文件
    print("已创建文件: 标题.txt")

    # 创建标识文件
    id_file = os.path.join(project_name, f"{label}.txt")
    with open(id_file, "w", encoding="utf-8"):
        pass  # 创建空文件
    print(f"已创建文件: {label}.txt")

    print(f"\n工程 '{project_name}' 创建完成！")
    print(f"包含 {subfolder_count} 个子文件夹和 2 个空文件")


def create_project():
    """
    创建新工程结构：
    1. 让用户输入工程名（父文件夹名）
    2. 让用户输入子文件夹数量
    3. 创建工程文件夹
    4. 在工程文件夹下创建指定数量的子文件夹（1~m）
    5. 在工程文件夹下创建空的"标题.txt"和"标识.txt"文件
    """
    print("\n=== 创建新工程 ===")

    base_path = ""
    # 获取工程名
    while True:
        project_name = base_path + input("请输入工程名（父文件夹名）: ").strip()
        if not project_name:
            print("工程名不能为空！")
            continue

        # 检查是否已存在同名文件夹
        if os.path.exists(base_path + project_name):
            print(f"错误：'{project_name}' 文件夹已存在！")
            continue

        # 检查非法字符
        invalid_chars = '<>:"\\|?*'
        if any(char in project_name for char in invalid_chars):
            print(f"工程名不能包含以下字符：{invalid_chars}")
            continue

        break

    # 获取子文件夹数量
    while True:
        try:
            subfolder_count = int(input("请输入子文件夹数量: ").strip())
            if subfolder_count <= 0:
                print("子文件夹数量必须大于0！")
                continue
            break
        except ValueError:
            print("请输入有效的数字！")

    # 获得标识名
    while True:
        try:
            label = input("请输入标识名: ").strip()
            break
        except Exception:
            print("请输入有效的标识名！")

    creat_files(project_name, subfolder_count, label)


def file_copy():
    """
    复制硬字幕文件
    """
    # 获取当前路径下的所有父文件夹
    print("\n=== 复制字幕文件 ===")
    current_dir = os.getcwd()
    parent_folders = [
        d
        for d in os.listdir(current_dir)
        if os.path.isdir(os.path.join(current_dir, d))
        and not d.startswith(".")
        and not d.endswith("tools")
        and d != os.path.basename(__file__)
    ]

    if not parent_folders:
        print("当前路径下没有找到任何工程文件夹！")
        return

    # 显示父文件夹列表供用户选择
    print("请选择要处理的工程文件夹（输入序号，多个用逗号分隔）：")
    for i, folder in enumerate(parent_folders, 1):
        print(f"{i}. {folder}")

    # 获取用户输入
    while True:
        try:
            choices = input("请输入序号: ").strip()
            if not choices:
                print("输入不能为空！")
                continue

            selected_indices = [int(x.strip()) - 1 for x in choices.split(",")]
            if any(idx < 0 or idx >= len(parent_folders) for idx in selected_indices):
                print("序号超出范围，请重新输入！")
                continue

            selected_folders = [parent_folders[idx] for idx in selected_indices]
            break
        except ValueError:
            print("请输入有效的数字序号！")

    # 处理选中的父文件夹
    for parent in selected_folders:
        parent_path = os.path.join(current_dir, parent)
        print(f"\n正在处理工程文件夹: {parent}")

        # 遍历子文件夹
        for subfolder in os.listdir(parent_path):
            subfolder_path = os.path.join(parent_path, subfolder)

            # 确保是子文件夹
            if not os.path.isdir(subfolder_path):
                continue

            # 检查目标文件是否存在
            source_file = os.path.join(subfolder_path, "原文.srt")
            if not os.path.exists(source_file):
                print(f"  跳过 {subfolder}: 未找到原文.srt")
                continue

            # 创建副本
            target_file = os.path.join(subfolder_path, "原文copy.txt")
            try:
                shutil.copy2(source_file, target_file)
                print(f"  成功处理 {subfolder}: 已创建原文copy.txt")
            except Exception as e:
                print(f"  处理 {subfolder} 时出错: {str(e)}")

    print("\n所有操作已完成!")


def rename_files():
    """
    重命名工程文件夹中子文件夹内的媒体文件：
    1. 让用户选择一个工程文件夹
    2. 遍历该工程下的所有子文件夹
    3. 检查每个子文件夹中是否有且仅有1个jpg文件和1个mp4文件
    4. 如果符合条件，将jpg重命名为"封面.jpg"，mp4重命名为"生肉.mp4"
    5. 如果不符合条件（无文件/多个文件/文件类型不匹配），则跳过该子文件夹
    """
    print("\n=== 重命名媒体文件 ===")

    # 获取当前目录下的所有工程文件夹
    current_dir = os.getcwd()
    project_folders = [
        d
        for d in os.listdir(current_dir)
        if os.path.isdir(os.path.join(current_dir, d))
    ]

    if not project_folders:
        print("当前目录下没有找到任何工程文件夹！")
        return

    # 显示工程文件夹列表供用户选择
    print("请选择要处理的工程文件夹：")
    for i, folder in enumerate(project_folders, 1):
        print(f"{i}. {folder}")

    # 获取用户选择
    while True:
        try:
            choice = int(input("请输入工程编号: ")) - 1
            if 0 <= choice < len(project_folders):
                selected_project = project_folders[choice]
                break
            else:
                print("无效的编号，请重新输入！")
        except ValueError:
            print("请输入有效的数字编号！")

    project_path = os.path.join(current_dir, selected_project)
    print(f"\n正在处理工程: {selected_project}")

    # 遍历工程下的所有子文件夹
    subfolders = [
        d
        for d in os.listdir(project_path)
        if os.path.isdir(os.path.join(project_path, d))
    ]

    processed = 0
    skipped = 0

    for subfolder in subfolders:
        subfolder_path = os.path.join(project_path, subfolder)
        files = os.listdir(subfolder_path)

        # 筛选jpg和mp4文件
        jpg_files = [f for f in files if f.lower().endswith(".jpg")]
        mp4_files = [f for f in files if f.lower().endswith(".mp4")]
        srt_files = [f for f in files if f.lower().endswith("copy.txt")]

        # 检查文件数量是否符合要求
        if len(jpg_files) != 1 or len(mp4_files) != 1:
            print(
                f"跳过子文件夹 '{subfolder}': 需要1个jpg和1个mp4文件，但找到 {len(jpg_files)}个jpg和 {len(mp4_files)}个mp4"
            )
            skipped += 1
            continue

        # 重命名文件
        try:
            jpg_old = os.path.join(subfolder_path, jpg_files[0])
            jpg_new = os.path.join(subfolder_path, "封面.jpg")

            mp4_old = os.path.join(subfolder_path, mp4_files[0])
            mp4_new = os.path.join(subfolder_path, "生肉.mp4")

            srt_old = os.path.join(subfolder_path, srt_files[0])
            srt_new = os.path.join(subfolder_path, "译文.srt")

            os.rename(jpg_old, jpg_new)
            os.rename(mp4_old, mp4_new)
            os.rename(srt_old, srt_new)

            print(
                f"已处理子文件夹 '{subfolder}': {jpg_files[0]} -> 封面.jpg, {mp4_files[0]} -> 生肉.mp4, {srt_files[0]} -> 译文.srt"
            )
            processed += 1
        except Exception as e:
            print(f"处理子文件夹 '{subfolder}' 时出错: {str(e)}")
            skipped += 1

    print(f"\n处理完成！成功处理 {processed} 个子文件夹，跳过 {skipped} 个子文件夹")


def get_video_list(url):
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
        resp = requests.get(url=url, headers=headers, timeout=3)
    except requests.exceptions.Timeout:
        print("请求失败")
        return

    pattern = r'\[\{"url":"(.*?)","width":\d*,"height":\d*\}\]\},"title":\{"runs":\[\{"text":"(.*?)"\}\]'

    name = re.findall(pattern, resp.text)

    if not name:
        print("网址错误")
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
        download_image(url_list[i - 1][1], project_name + "/" + str(i) + "/封面.jpg")
    print("封面提取完成")
    print("开始下载视频")

    video_list = []
    for i in url_list:
        video_list.append(i[-1])
    download_videos_multithreaded(video_list, save_path=project_name, max_workers=4)

    print("初始化完成\n")


def fix_video_list():
    project_paths = get_project_paths(".")
    if not project_paths:
        print("\n=== 未找到任何工程文件夹 ===")
        return

    print("\n=== 工程列表 ===")
    for n, project in enumerate(project_paths):
        project_name = project.split("\\")[-1]
        print(f"{n + 1}.{project_name}")
    check_num = int(input("\n请输入要补充视频的项目序号：")) - 1

    # 项目名称
    project_path = project_paths[check_num].split("\\")[-1] + "/"

    list_url = input("请输入视频列表网址：")

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
        resp = requests.get(url=list_url, headers=headers, timeout=3)
    except requests.exceptions.Timeout:
        print("请求失败")
        return

    pattern = r'\[\{"url":"(.*?)","width":\d*,"height":\d*\}\]\},"title":\{"runs":\[\{"text":"(.*?)"\}\]'

    name = re.findall(pattern, resp.text)

    if not name:
        print("网址错误")
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
        print("成功获取视频链接\n正在下载")

        video_list = []
        for i in url_list:
            video_list.append(i[-1])
        download_videos_multithreaded(video_list, save_path=project_path, max_workers=4)

        print("下载完成")


def fix_subtitle_numbers():
    """
    重新排布srt文件的字幕序号
    """
    print("\n=== 重新排布字幕序号 ===")

    # 获取当前目录下的所有工程文件夹
    current_dir = os.getcwd()
    project_folders = [
        d
        for d in os.listdir(current_dir)
        if os.path.isdir(os.path.join(current_dir, d))
        and not d.startswith(".")
        and not d.endswith("tools")
        and d != os.path.basename(__file__)
    ]

    if not project_folders:
        print("当前目录下没有找到任何工程文件夹！")
        return

    # 显示工程文件夹列表供用户选择
    print("请选择要处理的工程文件夹：")
    for i, folder in enumerate(project_folders, 1):
        print(f"{i}. {folder}")

    # 获取用户选择
    while True:
        try:
            choice = int(input("请输入工程编号: ")) - 1
            if 0 <= choice < len(project_folders):
                selected_project = project_folders[choice]
                break
            else:
                print("无效的编号，请重新输入！")
        except ValueError:
            print("请输入有效的数字编号！")

    project_path = os.path.join(current_dir, selected_project)
    print(f"\n正在处理工程: {selected_project}")

    # 列出所有子文件夹
    subfolders = [
        d
        for d in os.listdir(project_path)
        if os.path.isdir(os.path.join(project_path, d))
        and d.isdigit()  # 只处理数字命名的子文件夹
    ]

    if not subfolders:
        print("未找到数字命名的子文件夹！")
        return

    # 显示子文件夹列表供用户选择
    print("请选择要处理的集数（输入序号，多个用逗号分隔）：")
    for i, subfolder in enumerate(sorted(subfolders), 1):
        print(f"{i}. 第{subfolder}集")

    # 获取用户输入
    while True:
        try:
            choices = input("请输入序号: ").strip()
            if not choices:
                print("输入不能为空！")
                continue

            selected_indices = [int(x.strip()) - 1 for x in choices.split(",")]
            sorted_subfolders = sorted(subfolders)
            if any(
                idx < 0 or idx >= len(sorted_subfolders) for idx in selected_indices
            ):
                print("序号超出范围，请重新输入！")
                continue

            selected_subfolders = [sorted_subfolders[idx] for idx in selected_indices]
            break
        except ValueError:
            print("请输入有效的数字序号！")

    # 询问要处理的srt文件名
    srt_filename = input("请输入要处理的srt文件名（例如：译文.srt）: ").strip()
    if not srt_filename.endswith(".srt"):
        print("文件名必须以.srt结尾！")
        return

    # 处理每个选中的子文件夹
    for subfolder in selected_subfolders:
        subfolder_path = os.path.join(project_path, subfolder)
        srt_file_path = os.path.join(subfolder_path, srt_filename)

        if not os.path.exists(srt_file_path):
            print(f"  跳过第{subfolder}集: 未找到{srt_filename}")
            continue

        try:
            with open(srt_file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 解析字幕并重新排序
            subtitles = []
            current_subtitle = []
            for line in lines:
                if line.strip():
                    current_subtitle.append(line)
                else:
                    if current_subtitle:
                        subtitles.append(current_subtitle)
                        current_subtitle = []
            # 添加最后一个字幕
            if current_subtitle:
                subtitles.append(current_subtitle)

            # 重新生成字幕文件
            with open(srt_file_path, "w", encoding="utf-8") as f:
                for i, subtitle in enumerate(subtitles, 1):
                    # 写入新的序号
                    f.write(f"{i}\n")
                    # 写入时间戳和字幕内容
                    for j in range(1, len(subtitle)):
                        f.write(subtitle[j])
                    # 写入空行分隔
                    if i < len(subtitles):
                        f.write("\n")

            print(f"  成功处理第{subfolder}集: 已重新排布{srt_filename}的字幕序号")
        except Exception as e:
            print(f"  处理第{subfolder}集时出错: {str(e)}")

    print("\n所有操作已完成!")


if __name__ == "__main__":
    while True:
        print(
            "0.退出程序\n1.项目初始化\n2.硬字幕文件复制\n3.重命名文件\n4.根据播放列表一键初始化项目\n5.视频字幕区域框选\n6.重新排布字幕序号"
        )

        func = int(input("请选择功能："))

        if func == 0:
            break
        elif func == 1:
            create_project()
        elif func == 2:
            file_copy()
        elif func == 3:
            rename_files()
        elif func == 4:
            get_video_list(input("请输入视频列表网址："))
        elif func == 5:
            tool = VideoCoordinateTool(input("请输入视频路径："))
            tool.run()
        elif func == 6:
            fix_subtitle_numbers()

# # "D:\东方project\油库里茶番剧\被捡回来的管家我竟要和主人蕾米莉亚交往了\8\生肉.mp4"
