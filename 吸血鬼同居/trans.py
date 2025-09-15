def replace_srt_quotes(input_file: str, output_file: str) -> None:
    """
    读取 SRT 文件并替换引号：
    - 行首的“或"替换为「
    - 行尾的”或"替换为」
    """
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.readlines()

        new_content = []
        for line in content:
            # 处理行首引号
            if line.startswith("“") or line.startswith('"'):
                line = "「" + line[1:]

            # 处理行尾引号
            if line.endswith("”\n") or line.endswith('"\n'):
                line = line[:-2] + "」\n"
            elif line.endswith("”") or line.endswith('"'):
                line = line[:-1] + "」"

            new_content.append(line)

        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(new_content)

        print(f"处理完成！输出文件已保存为: {output_file}")

    except FileNotFoundError:
        print(f"错误：找不到输入文件 '{input_file}'")
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")


if __name__ == "__main__":
    for i in range(3, 11):
        input_filename = f"{i}/译文.srt"
        output_filename = f"{i}/译文.srt"

        replace_srt_quotes(input_filename, output_filename)
