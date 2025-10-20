import os
import sys

def reverse_rename_folders(folder_path):
    """
    将文件夹下的数字文件夹逆序重命名
    例如：n -> 1, n-1 -> 2, ..., 1 -> n
    """
    
    # 检查文件夹路径是否存在
    if not os.path.exists(folder_path):
        print(f"错误：文件夹路径 '{folder_path}' 不存在")
        return False
    
    # 获取所有文件夹，只保留数字名称的文件夹
    folders = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path) and item.isdigit():
            folders.append(int(item))
    
    if not folders:
        print("在指定文件夹中未找到数字命名的文件夹")
        return False
    
    # 排序并找到最大值n
    folders.sort()
    n = max(folders)
    
    print(f"找到 {len(folders)} 个数字文件夹，最大值为 {n}")
    
    # 创建重命名映射：旧名称 -> 新名称
    rename_map = {}
    for old_num in folders:
        new_num = n - old_num + 1
        rename_map[str(old_num)] = str(new_num)
    
    # 为了避免重命名冲突，先重命名为临时名称
    temp_suffix = "_temp"
    
    # 第一步：重命名为临时名称
    print("第一步：重命名为临时名称...")
    for old_name, new_name in rename_map.items():
        old_path = os.path.join(folder_path, old_name)
        temp_path = os.path.join(folder_path, old_name + temp_suffix)
        
        if os.path.exists(old_path):
            os.rename(old_path, temp_path)
            print(f"  {old_name} -> {old_name + temp_suffix}")
    
    # 第二步：从临时名称重命名为最终名称
    print("第二步：重命名为最终名称...")
    for old_name, new_name in rename_map.items():
        temp_path = os.path.join(folder_path, old_name + temp_suffix)
        new_path = os.path.join(folder_path, new_name)
        
        if os.path.exists(temp_path):
            os.rename(temp_path, new_path)
            print(f"  {old_name + temp_suffix} -> {new_name}")
    
    print("重命名完成！")
    print("重命名映射：")
    for old_name, new_name in sorted(rename_map.items(), key=lambda x: int(x[0])):
        print(f"  {old_name} -> {new_name}")
    
    return True

def main():
    # 使用方法说明
    if len(sys.argv) != 2:
        print("使用方法：")
        print("  python reverse_rename.py <文件夹路径>")
        print("")
        print("示例：")
        print("  python reverse_rename.py ./my_folders")
        print("")
        
        # 如果未提供参数，询问用户输入
        folder_path = input("请输入要处理的文件夹路径: ").strip()
        if not folder_path:
            print("未提供文件夹路径，程序退出")
            return
    else:
        folder_path = sys.argv[1]
    
    # 执行重命名
    try:
        success = reverse_rename_folders(folder_path)
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"执行过程中发生错误：{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()