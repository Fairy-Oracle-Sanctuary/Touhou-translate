import argparse

from bilibili_api import Credential, sync, video_uploader  # noqa


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
