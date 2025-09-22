with open(r"D:\东方project\projects\吸血鬼同居\标题.txt", "r", encoding="utf-8") as f:
    is_subtitle = False
    subtitles = []
    subtitle_num = 0

    content = f.readlines()
    for n, line in enumerate(content):
        if line == '\n' and not is_subtitle:
            subtitle_num = n
            subtitles.append(subtitle_num)
            is_subtitle = True
        elif line == '\n' and is_subtitle and subtitle_num > 0 or len(content) == n+1:
            subtitles.append(content[n-2].replace('\n', ''))
            # print(subtitle_num)
            subtitle_num -= 1
        elif line == '\n' and is_subtitle and subtitle_num < 0:
            print(n)
            break

print(subtitles)
print(len(subtitles))