import srt


class Srt:
    def __init__(self, file_path):
        self.file_path = file_path
        self.subtitle_data = []
        self.timeline = []
        self.subtitles = []
        self.raw_content = ""  # 存储原始文件内容
        self.parse_srt_file(file_path)  # 直接填充三个列表

    def parse_srt_file(self, file_path):
        """解析SRT文件并返回标准格式数据"""
        with open(file_path, "r", encoding="utf-8") as f:
            self.raw_content = f.read()  # 存储原始内容
            subtitles = srt.parse(self.raw_content)

        # 一次遍历同时填充三个列表
        for sub in subtitles:
            timeline_str = f"{sub.start} --> {sub.end}".replace(".", ",")
            content = sub.content.strip()

            self.subtitle_data.append((sub.index, timeline_str, content))
            self.timeline.append(timeline_str)
            self.subtitles.append(content.replace("\n", " "))

        return self.subtitles

    @staticmethod
    def create_from_lists(dialogues, timestamps, output_file=None):
        """
        从对话列表和时间戳列表创建SRT文件

        Args:
            dialogues (list): 对话文本列表
            timestamps (list): 时间戳列表
            output_file (str, optional): 输出文件路径

        Returns:
            str: SRT格式的字符串
        """

        def format_timestamp(ts):
            """格式化时间戳为SRT标准格式"""
            # 移除微秒部分，只保留毫秒（3位）
            if "," in ts:
                parts = ts.split(",")
                if len(parts) == 2:
                    milliseconds = parts[1][:3]  # 只取前3位毫秒
                    return f"{parts[0]},{milliseconds}"
            return ts

        def parse_timestamp_range(ts_range):
            """解析时间戳范围并格式化"""
            if " --> " in ts_range:
                start, end = ts_range.split(" --> ")
                return f"{format_timestamp(start)} --> {format_timestamp(end)}"
            return ts_range

        srt_content = []

        for i, (dialogue, timestamp) in enumerate(zip(dialogues, timestamps), 1):
            # 序号
            srt_content.append(str(i))

            # 时间戳
            formatted_timestamp = parse_timestamp_range(timestamp)
            srt_content.append(formatted_timestamp)

            # 对话内容
            srt_content.append(dialogue)

            # 空行
            srt_content.append("")

        srt_text = "\n".join(srt_content)

        # 如果需要保存文件
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(srt_text)

        return srt_text

    def write_raw_content(self, content, output_file):
        """
        将传入的内容原封不动写入文件

        Args:
            content (str): 要写入的内容
            output_file (str): 输出文件路径
        """
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        return f"内容已成功写入 {output_file}"


if __name__ == "__main__":
    srt_file = r"D:\Touhou-project\projects\名为喜欢的这份心情终将抵达之所\13\原文.srt"
    srt_obj = Srt(srt_file)
    for i in srt_obj.raw_content.split("\n\n"):
        print(i + "\n\n")
