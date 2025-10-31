from pathlib import Path

test = Path(r"D:\Touhou-project\projects\世界因你而多彩第一季\3\原文.srt")

print(test.parent.name)
print(test.parent.parent / "3" / test.name)
