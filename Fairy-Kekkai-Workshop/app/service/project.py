import os
import shutil

class Project():
    def __init__(self):
        self.project_subtitle_isTranslated = []
        self.project_video_url = []
        self.project_path = self.get_project_paths('.')
        self.project_name = self.get_project_names()
        self.project_title = self.get_project_titles()
        self.project_subtitle = self.get_project_subtitles()
        # print(self.project_title)

    def get_project_paths(self, directory):
        '''
        获取projects文件夹下所有子文件夹的完整路径，排除特定文件夹
        '''
        project_paths = []
        ban_names = [".git", "tools", "Fairy-Kekkai-Workshop"]  # 要排除的文件夹名称
        
        # 确保目录路径是绝对路径
        directory = os.path.abspath(directory)
        
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            
            # 只处理目录，不处理文件
            if os.path.isdir(full_path):
                # 获取目录的基本名称（最后一部分）
                dir_name = os.path.basename(full_path)
                
                # 检查目录是否在排除列表中
                if dir_name not in ban_names:
                    project_paths.append(full_path)
        return project_paths
    
    def get_project_names(self):
        '''获取工程名'''
        project_names = []
        for name in self.project_path:
            project_names.append(name.split('\\')[-1])
        return project_names
    
    def get_project_titles(self):
        '''获取原标题'''
        project_titles = []
        for project in self.project_path:
            for dir in os.listdir(project):
                if dir.endswith(".txt") and not dir.startswith("标题."):
                    project_titles.append(dir.split('.')[0])
        return project_titles
    
    def get_project_subtitles(self):
        '''获取每集的标题'''
        project_subtitles = []
        self.project_subtitle_isTranslated = []

        for path in self.project_path:
            with open(path + "/标题.txt", "r", encoding="utf-8") as f:
                is_subtitle = False
                subtitles = []
                video_urls = []
                subtitle_num = 0

                content = f.readlines()
                for n, line in enumerate(content):
                    if line == '\n' and not is_subtitle:
                        subtitle_num = n
                        if content[n+3] != '\n':
                            self.project_subtitle_isTranslated.append(True)
                        else:
                            self.project_subtitle_isTranslated.append(False)
                        is_subtitle = True
                    elif line == '\n' and is_subtitle and subtitle_num > 0 or len(content) == n+1:
                        video_urls.append(content[n-1].replace('\n', ''))
                        subtitles.append(content[n-2].replace('\n', ''))
                        # print(subtitle_num)
                        subtitle_num -= 1
                    elif line == '\n' and is_subtitle and subtitle_num <= 0:
                        break
                
                self.project_video_url.append(video_urls)
                project_subtitles.append(subtitles)
        
        return project_subtitles

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
        with open(title_file, "w", encoding="utf-8") as f:
            for i in range(1, subfolder_count + 1):
                f.write(f'{i}\n')
            f.write('\n')
            for i in range(1, subfolder_count + 1):
                f.write(f'{i}\nhttps://www.youtube.com/watch?v=\n\n')
            f.write('\n---')
        print("已创建文件: 标题.txt")

        # 创建标识文件
        id_file = os.path.join(project_name, f"{label}.txt")
        with open(id_file, "w", encoding="utf-8"):
            pass  # 创建空文件
        print(f"已创建文件: {label}.txt")

        print(f"\n工程 '{project_name}' 创建完成！")
        print(f"包含 {subfolder_count} 个子文件夹和 2 个空文件")

    def delete_project(self, project_path):
        '''删除项目并刷新变量'''
        try:
            import shutil
            shutil.rmtree(project_path)
            self.project_path = self.get_project_paths('.')
            self.project_name = self.get_project_names()
            self.project_title = self.get_project_titles()
            return True
        except Exception:
            return False
    
    def change_subtitle(self, id, num, text, offset=0):
        file_path = self.project_path[id] + '/标题.txt'
        if self.project_subtitle_isTranslated[id]:
            line_number = 4*num + len(self.project_subtitle[id]) - 1
        else:
            line_number = 3*num + len(self.project_subtitle[id]) - 1

        new_content = text
        # print(file_path)

        self.replace_line_in_file(file_path, line_number + offset, new_content)
        self.__init__()
    
    def replace_line_in_file(self, file_path, line_number, new_content):
        """
        删除文件中的第n行并替换为新内容
        
        参数:
            file_path: 文件路径
            line_number: 要替换的行号(从1开始计数)
            new_content: 新行内容
        """
        try:
            # 读取文件所有行
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # 检查行号是否有效
            if line_number < 1 or line_number > len(lines):
                print(f"错误: 行号 {line_number} 超出文件范围(1-{len(lines)})")
                return False
            
            # 替换指定行
            lines[line_number - 1] = new_content + '\n'
            
            # 将修改后的内容写回文件
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
            
            # print(f"成功替换第 {line_number} 行")
            return True
        
        except FileNotFoundError:
            print(f"错误: 文件 {file_path} 不存在")
            return False
        except Exception as e:
            print(f"发生错误: {str(e)}")
            return False


if __name__ == "__main__":
    proj = Project()
    # print(proj.project_path)
    # print(proj.project_name)
    # print(proj.project_title)
    # print(proj.project_subtitle_isTranslated)
    print(proj.project_video_url)
    # proj.change_subtitle(5, 7, "雪中萌发的春天1")


    