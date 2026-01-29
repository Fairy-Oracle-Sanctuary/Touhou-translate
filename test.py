from bilibili_api import Credential, sync, video_uploader  # noqa

SESSDATA = "13289b75%2C1785229161%2C5579c%2A12CjA-IYFgOPtuY2eYWKWXbIB6kUsbzED2AFx9HOxBTq4_OYuFzZCmZYJ9Q8cq96og_9oSVmdFRnNESGdSZmExZ2tFMkZGRnlkREhla1ctdlRuakQ4SHN5WFBQeXBCeXBid0FMS3BLcjZqVXJHRmJLYUFwTDY4elJjVGR4Wm83NUp3QzJBYlpFdnlBIIEC"
BILI_JCT = "cd147a00ad775fb39e2eece795bc50a6"
BUVID3 = "0195C6E0-8C18-7E8F-044F-6324714AF8EE86683infoc"


async def main():
    credential = Credential(sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3)
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
        tid=17,
        title="我的世界nxs指令",
        tags=["minecraft", "指令"],
        desc="最基础的nxs，能遍历一条直线",
        cover=r"C:\Users\ZHANGBaoHang\Videos\Captures\test.png",
        no_reprint=True,
    )
    # await vu_meta.verify(credential=credential) # 本地预检 meta 信息，出错则抛出异常
    page = video_uploader.VideoUploaderPage(
        path=r"C:\Users\ZHANGBaoHang\Videos\Captures\test.mp4",
        title="nxs指令",
        # description="最基础的nxs，能遍历直线",
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
