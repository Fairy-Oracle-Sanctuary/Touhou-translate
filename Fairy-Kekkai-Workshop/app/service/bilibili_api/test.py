from bilibili_api import Credential, sync, video_uploader

SessionData = "8999a340%2C1785328471%2C6f044%2A12CjD6C0P6aoUb7LVPnihqkwcVt9bRZ-1vEYhG7f2kpoJqX_j4Nu6jJkFS4pKm0mKroq8SVktnV1BiQmxfc1g5cXJkSHFQZ1JGVnYtS2JxT0pGbnQ1bG1XWEZJcjV0R05mVmNjV3BGU1lDUDlXelJGZ1N5SDV5ZjZQci1fUktFOTRUUUd4cUJHeXVBIIEC"
BiliJct = "adc52578109c5da1906beaac8c3aa705"
Buvid3 = "0195C6E0-8C18-7E8F-044F-6324714AF8EE86683infoc"


async def main():
    credential = Credential(sessdata=SessionData, bili_jct=BiliJct, buvid3=Buvid3)
    # 具体请查阅相关文档和 VideoMeta 内代码注释
    # 建议使用 VideoMeta 类来构建 meta 信息，避免参数错误，但也兼容直接传入 dict
    # meta = {
    #     "act_reserve_create": 0,
    #     "copyright": 1,
    #     "source": "",
    #     "desc": "",
    #     "desc_format_id": 0,
    #     "dynamic": "",
    #     "interactive": 0,
    #     "no_reprint": 1,
    #     "open_elec": 0,
    #     "origin_state": 0,
    #     "subtitles": {
    #         "lan": "",
    #         "open": 0
    #     },
    #     "tag": "音乐,音乐综合",
    #     "tid": 130,
    #     "title": "title",
    #     "up_close_danmaku": False,
    #     "up_close_reply": False,
    #     "up_selection_reply": False,
    #     "dtime": 0
    # }
    # vu_porden_meta = video_uploader.VideoPorderMeta(video_uploader.VideoPorderType.FIREWORK) # 商单参数
    vu_meta = video_uploader.VideoMeta(
        tid=130,
        title="茶番剧",
        tags=["东方"],
        desc="",
        cover=r"C:\Users\ZHANGBaoHang\Videos\Captures\test.png",
        no_reprint=True,
        delay_time=1769854920,
    )
    # await vu_meta.verify(credential=credential) # 本地预检 meta 信息，出错则抛出异常
    page = video_uploader.VideoUploaderPage(
        path="D:/Touhou-project/projects/世界因你而多彩第一季/11/熟肉_压制.mp4",
        title="茶番剧",
        description="",
    )
    uploader = video_uploader.VideoUploader(
        [page], vu_meta, credential
    )  # 选择七牛线路，不选则自动测速选择最优线路
    # uploader = video_uploader.VideoUploader([page], meta, credential, cover='cover.png')
    # # meta 直接传入 dict 则需要在 video_uploader.VideoUploader 传入封面

    @uploader.on("__ALL__")
    async def ev(data):
        print(data)

    await uploader.start()


sync(main())
