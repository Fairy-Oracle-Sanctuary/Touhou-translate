import os

class Project():
    def __init__(self):
        self.project_path = self.get_project_paths('.')
        self.project_name = self.get_project_names()
        self.project_title = self.get_project_titles()
        # print(self.project_title)

    def get_project_paths(self, directory):
        '''
        获取projects文件夹下所有子文件夹
        '''
        project_paths = []
        ban_end = [".git", "tools", "Fairy-Kekkai-Workshop"]
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isdir(full_path):
                project_paths.append(full_path)
            for ban in ban_end:
                if full_path.endswith(ban):
                    project_paths.pop()
        return project_paths
    
    def get_project_names(self):
        '''
        获取工程名
        '''
        project_names = []
        for name in self.project_path:
            project_names.append(name.split('\\')[-1])
        return project_names
    
    def get_project_titles(self):
        '''
        获取原标题
        '''
        project_titles = []
        for project in self.project_path:
            for dir in os.listdir(project):
                if dir.endswith(".txt") and not dir.startswith("标题."):
                    project_titles.append(dir.split('.')[0])
        return project_titles
    
    def creat_files(self, project_name, subfolder_count, label):
        """创建工程文件夹"""
        os.makedirs(project_name)
        print(f"已创建工程文件夹: {project_name}")

        # 创建子文件夹
        for i in range(1, subfolder_count + 1):
            subfolder_path = os.path.join(project_name, str(i))
            os.makedirs(subfolder_path)
            print(f"已创建子文件夹: {i}")

        # 创建空的标题文件
        title_file = os.path.join(project_name, "标题.txt")
        with open(title_file, "w", encoding="utf-8"):
            pass  # 创建空文件
        print("已创建文件: 标题.txt")

        # 创建标识文件
        id_file = os.path.join(project_name, f"{label}.txt")
        with open(id_file, "w", encoding="utf-8"):
            pass  # 创建空文件
        print(f"已创建文件: {label}.txt")

        print(f"\n工程 '{project_name}' 创建完成！")
        print(f"包含 {subfolder_count} 个子文件夹和 2 个空文件")

def check_project():
    return
    project_paths = get_project_paths('.')
    if not project_paths:
        print("\n=== 未找到任何工程文件夹 ===")
        return
    
    print("\n=== 工程列表 ===")
    # for n, project in enumerate(project_paths):
    #     print(f"{n+1}.{project.split('\\')[-1]}")
    check_num = int(input("\n请输入要检查的项目序号：")) - 1

    project_ifm = dict()
    #项目名称
    project_ifm['project_name'] = project_paths[check_num].split('\\')[-1]
    #总集数
    project_ifm['video_num'] = 0

    for dir in os.listdir(project_paths[check_num]):
        if dir.startswith('标题'):
            content = []
            title_org = []
            title_zh = []
            video_link = []
            title_len = 0
            with open(project_paths[check_num] + "/标题.txt", "r", encoding="utf-8") as title_file:
                try:
                    for line in title_file.readlines():
                        if not line.replace('\n', '') and not title_len:
                            title_len = len(content)
                        content.append(line.replace('\n', ''))
                    
                    for i in range(title_len):
                        title_org.append(content[i])
                        title_zh.append(content[title_len + 2 + i*4])
                        video_link.append(content[title_len + 3 + i*4])
                    
                    project_ifm['title_org'] = title_org
                    project_ifm['title_zh'] = title_zh
                    project_ifm['video_link'] = video_link
                except Exception:
                    print('工程错误，检查标题文件\n')
                    return
                    
        elif dir.endswith('.txt'):
            #项目标识名
            project_ifm['project_logo'] = dir.split('.')[0]
        else:
            project_ifm['video_num'] += 1


    print(f"\n=== 项目信息 ===\n项目名称：{project_ifm['project_name']}\n原标题：{project_ifm['project_logo']}\n总集数：{project_ifm['video_num']}\n")
    
    num = 0
    for t1, t2, t3 in zip(project_ifm['title_org'], project_ifm['title_zh'], project_ifm['video_link']):
        num += 1
        print(f"{num}.\n原标题：{t1}\n中文译名：{t2}\n视频链接：{t3}\n")