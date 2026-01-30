import argparse
import sys

from bilibili_api import Credential, sync, video_uploader  # noqa


def setup_bilibili_api_clients():
    """手动设置 bilibili_api 的 HTTP 客户端"""

    # 首先检查是否已经有选中的客户端
    from bilibili_api.utils.network import get_selected_client, select_client

    try:
        # 尝试获取当前选中的客户端
        current_client, _ = get_selected_client()
        print(f"当前已选中客户端: {current_client}")
        return  # 如果已经有选中的客户端，直接返回
    except:
        pass  # 如果没有选中的客户端，继续手动注册

    # 尝试注册可用的 HTTP 客户端
    clients_registered = False

    # 尝试 httpx
    if not clients_registered:
        try:
            import httpx
            from bilibili_api.clients import HTTPXClient
            from bilibili_api.utils.network import register_client

            register_client("httpx", HTTPXClient, {"http2": False})
            select_client("httpx")
            print("[OK] 已注册 httpx 客户端")
            clients_registered = True
        except ImportError:
            print("[ERROR] httpx 不可用")
        except Exception as e:
            print(f"[ERROR] 注册 httpx 失败: {e}")

            # curl_cffi
        try:
            import curl_cffi
            from bilibili_api.clients import CurlCFFIClient
            from bilibili_api.utils.network import register_client

            register_client(
                "curl_cffi", CurlCFFIClient, {"impersonate": "", "http2": False}
            )
            select_client("curl_cffi")
            print("[OK] 已注册 curl_cffi 客户端")
            clients_registered = True
        except ImportError:
            print("[ERROR] curl_cffi 不可用")
        except Exception as e:
            print(f"[ERROR] 注册 curl_cffi 失败: {e}")

    # 如果前两个都不可用，尝试 aiohttp
    if not clients_registered:
        try:
            import aiohttp
            from bilibili_api.clients import AioHTTPClient
            from bilibili_api.utils.network import register_client

            register_client("aiohttp", AioHTTPClient, {})
            select_client("aiohttp")
            print("[OK] 已注册 aiohttp 客户端")
            clients_registered = True
        except ImportError:
            print("[ERROR] aiohttp 不可用")
        except Exception as e:
            print(f"[ERROR] 注册 aiohttp 失败: {e}")

    # 如果所有客户端都不可用，报错退出
    if not clients_registered:
        print("错误: 未找到任何可用的 HTTP 客户端库")
        print("请安装以下任一库:")
        print("  pip install curl_cffi")
        print("  pip install httpx")
        print("  pip install aiohttp")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Upload video to Bilibili.")

    parser.add_argument(
        "--video_path", type=str, required=True, help="Path to the video file"
    )
    parser.add_argument(
        "--cover",
        type=str,
        default="cover.jpg",
        help="Path to the cover image file (default: cover.jpg)",
    )
    parser.add_argument(
        "--SESSDATA",
        type=str,
        default=None,
        help="SESSDATA cookie (default: None)",
    )
    parser.add_argument(
        "--BILI_JCT",
        type=str,
        default=None,
        help="BILI_JCT cookie (default: None)",
    )
    parser.add_argument(
        "--BUVID3",
        type=str,
        default=None,
        help="BUVID3 cookie (default: None)",
    )
    parser.add_argument(
        "--tid",
        type=int,
        default=1,
        help="Video type ID (default: 1)",
    )

    parser.add_argument(
        "--title", type=str, default="", help="Video title (default: empty)"
    )
    parser.add_argument(
        "--desc", type=str, default="", help="Video description (default: empty)"
    )
    parser.add_argument(
        "--tags", type=list, default=[], help="Video tags (default: empty)"
    )
    parser.add_argument(
        "--original",
        type=lambda x: x.lower() == "true",
        default=False,
        help="Original video (true/false)",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Video source (default: empty)",
    )
    parser.add_argument(
        "--recreate",
        type=lambda x: x.lower() == "true",
        default=False,
        help="Recreate video if it already exists (true/false)",
    )
    parser.add_argument(
        "--delay_time",
        type=int,
        default=None,
        help="Delay time in seconds (default: None)",
    )

    args = parser.parse_args()

    setup_bilibili_api_clients()

    sync(upload_video(parser, args))


async def upload_video(parser, args):
    try:
        # 获取 B 站cookie
        sessdata = args.SESSDATA
        bili_jct = args.BILI_JCT
        buvid3 = args.BUVID3

        if not all([sessdata, bili_jct, buvid3]):
            error_msg = "B站cookie未配置，请在设置中填写"
            parser.error(error_msg)

        credential = Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)

        # 创建视频元数据
        vu_meta = video_uploader.VideoMeta(
            tid=args.tid,
            title=args.title,
            tags=args.tags,
            desc=args.desc,
            cover=args.cover if args.cover else None,
            original=args.original,
            source=args.source if not args.original else None,
            recreate=args.recreate,
            delay_time=args.delay_time,
        )

        # 创建视频页面
        page = video_uploader.VideoUploaderPage(path=args.video_path, title=args.title)

        # 创建上传器
        uploader = video_uploader.VideoUploader([page], vu_meta, credential)

        @uploader.on("__ALL__")
        async def ev(data):
            print(data)

        await uploader.start()

    except Exception as e:
        error_msg = f"上传失败: {str(e)}"
        parser.error(error_msg)


if __name__ == "__main__":
    main()
