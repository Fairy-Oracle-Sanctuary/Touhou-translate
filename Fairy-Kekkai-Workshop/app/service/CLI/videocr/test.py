import os
import sys


def find_paddleocr(base_folders) -> str:
    program_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    # 定义搜索的目录范围
    search_dirs = []

    # 1. 添加当前目录
    search_dirs.append(program_dir)

    # 2. 添加上层目录（最多上溯3层）
    current_dir = program_dir
    for _ in range(5):  # 上溯3层
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # 已经到达根目录
            break
        search_dirs.append(parent_dir)
        current_dir = parent_dir

    base_folder = [base_folders]
    program_name = "paddleocr"
    ext = ".exe"
    executable_name = f"{program_name}{ext}"

    # 搜索所有目录及其子目录（最多2层深度）
    for search_dir in search_dirs:
        for root, dirs, files in os.walk(search_dir):
            # 计算当前深度（相对于搜索目录）
            relative_depth = len(os.path.relpath(root, search_dir).split(os.sep))
            if relative_depth > 2:  # 限制搜索深度为2层
                continue

            for dir_name in dirs:
                for base in base_folder:
                    if dir_name.startswith(base):
                        path = os.path.join(root, dir_name, executable_name)
                        if os.path.isfile(path):
                            return path

    raise FileNotFoundError(
        f"Could not find {executable_name} in any folder matching: {base_folders}"
    )


base_folders = [
    "PaddleOCR-CPU-v1.3.2",
    "PaddleOCR-GPU-v1.3.2-CUDA-11.8",
    "PaddleOCR-GPU-v1.3.2-CUDA-12.9",
]
for i in base_folders:
    print(find_paddleocr(i))
