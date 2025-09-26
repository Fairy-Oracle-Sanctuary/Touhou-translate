import requests
import re

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
    
    return url_list

resp = get_video_list("https://www.youtube.com/playlist?list=PLmc6eO_qCE4nYR7tYmTsppAF1CTxhcrTP")
print(resp)