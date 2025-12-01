import shutil
from pathlib import Path


class Project:
    def __init__(self):
        self.isLink = []
        self.projects_location = Path.cwd()
        self.project_path = self.get_project_paths()
        self.project_num = self.project_path.__len__()
        self.project_video_url = [[] for _ in range(self.project_num)]
        self.project_subtitle_isTranslated = [[] for _ in range(self.project_num)]
        self.project_name = self.get_project_names()
        self.project_title = self.get_project_titles()
        self.project_subtitle = self.get_project_subtitles()

    def get_project_paths(self):
        """
        获取projects文件夹下所有子文件夹的完整路径,排除特定文件夹
        """
        project_paths = []

        for item in self.projects_location.iterdir():
            if self.is_project(item):
                project_paths.append(item)
                self.isLink.append(False)

        # 处理外部路径
        if __name__ == "__name__":
            link_paths = cfg.linkProject.get("project_link")
            true_paths = []
            for path in link_paths:
                if self.is_project(path):
                    self.isLink.append(True)
                    true_paths.append(path)
                project_paths.append(Path(path))
            cfg.linkProject.set("project_link", true_paths)

        return project_paths

    def get_project_names(self):
        """获取工程名"""
        project_names = []
        for id in range(self.project_num):
            project_names.append(self.get_name(id))
        return project_names

    def get_name(self, id):
        """获取单个工程名"""
        return self.project_path[id].name

    def get_project_titles(self):
        """获取原标题"""
        project_titles = []
        for id in range(self.project_num):
            project_titles.append(self.get_title(id))
        return project_titles

    def get_title(self, id):
        """获取单个工程原标题"""
        project_folder = self.project_path[id]
        for file_path in project_folder.iterdir():
            if (
                file_path.is_file()
                and file_path.suffix == ".txt"
                and not file_path.name.startswith("标题.")
            ):
                return file_path.stem

    def get_project_subtitles(self):
        """获取每集的标题"""
        project_subtitles = []

        for path in self.project_path:
            subtitles = self.get_subtitle(self.project_path.index(path))
            project_subtitles.append(subtitles)
        return project_subtitles

    def get_subtitle(self, id):
        """获取单个工程的标题"""
        try:
            with open(self.project_path[id] / "标题.txt", "r", encoding="utf-8") as f:
                is_subtitle = False
                subtitles = []
                video_urls = []
                subtitle_num = 0

                content = f.readlines()
                for n, line in enumerate(content):
                    if line == "\n" and not is_subtitle:
                        subtitle_num = n
                        if content[n + 3] != "\n":
                            self.project_subtitle_isTranslated.append(True)
                        else:
                            self.project_subtitle_isTranslated.append(False)
                        is_subtitle = True
                    elif (
                        line == "\n"
                        and is_subtitle
                        and subtitle_num > 0
                        or len(content) == n + 1
                    ):
                        video_urls.append(content[n - 1].replace("\n", ""))
                        subtitles.append(content[n - 2].replace("\n", ""))
                        # print(subtitle_num)
                        subtitle_num -= 1
                    elif line == "\n" and is_subtitle and subtitle_num <= 0:
                        break

                self.project_video_url[id] = video_urls
                return subtitles
        except Exception:
            return []

    def refresh_project(self, id):
        """
        刷新项目

        参数:
            id: 项目的id
        """
        # 刷新项目名
        self.project_name[id] = self.get_name(id)

        # 刷新原标题
        self.project_title[id] = self.get_title(id)

        # 刷新每集标题
        self.project_subtitle[id] = self.get_subtitle(id)

    def creat_files(self, project_name, subfolder_count, label):
        """
        创建工程文件夹

        参数:
            project_name: 项目名称
            subfolder_count: 子文件数量
            label: 系列原标题
        """
        project_path = Path(project_name)
        project_path.mkdir(parents=True, exist_ok=True)

        # 创建子文件夹
        for i in range(1, subfolder_count + 1):
            subfolder_path = project_path / str(i)
            subfolder_path.mkdir(parents=True, exist_ok=True)

        # 创建空的标题文件
        title_file = project_path / "标题.txt"
        with title_file.open("w", encoding="utf-8") as f:
            for i in range(1, subfolder_count + 1):
                f.write(f"{i}\n")
            f.write("\n")
            for i in range(1, subfolder_count + 1):
                f.write(f"{i}\nhttps://www.youtube.com/watch?v=\n\n")
            f.write("\n---")

        # 创建标识文件
        id_file = project_path / f"{label}.txt"
        id_file.touch()  # 创建空文件

    def delete_project(self, project_path):
        """删除项目并刷新变量"""
        try:
            shutil.rmtree(project_path)
            self.__init__()
            return [True, ""]
        except Exception as e:
            return [False, e]

    def change_name(self, path, name):
        """更改项目文件名"""
        try:
            old_path = Path(path)
            new_path = old_path.parent / name
            old_path.rename(new_path)
            self.__init__()
            return [True, ""]
        except Exception as e:
            return [False, str(e)]

    def change_subtitle(self, id, num, text, offset=0):
        """
        修改项目文件标题

        参数:
            id: 项目的id
            num: 第几集
            text: 修改的内容
            offset: 指针偏移
        """
        file_path = str(self.project_path[id]) + "/标题.txt"
        if self.project_subtitle_isTranslated[id]:
            line_number = 4 * num + len(self.project_subtitle[id]) - 1
        else:
            line_number = 3 * num + len(self.project_subtitle[id]) - 1

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
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            # 检查行号是否有效
            if line_number < 1 or line_number > len(lines):
                print(f"错误: 行号 {line_number} 超出文件范围(1-{len(lines)})")
                return False

            # 替换指定行
            lines[line_number - 1] = new_content + "\n"

            # 将修改后的内容写回文件
            with open(file_path, "w", encoding="utf-8") as file:
                file.writelines(lines)

            # print(f"成功替换第 {line_number} 行")
            return True

        except FileNotFoundError:
            e = f"错误: 文件 {file_path} 不存在"
            return [False, str(e).strip()]

        except Exception as e:
            return [False, str(e).strip()]

    def is_project(self, folder_path):
        """判断文件夹是否为一个合法的项目"""
        folder_path = Path(folder_path)
        if not (folder_path / "标题.txt").exists():
            return False
        for folder_num in range(
            sum(1 for item in folder_path.iterdir() if item.is_dir())
        ):
            if not (folder_path / str(folder_num + 1)).exists():
                return False
        return True

    def addEpisode(
        self, id, episode_num, origin_title, trans_title, video_url, isTranslated=False
    ):
        """
        增加新集

        参数:
            id: 项目id
            episode_num: 第几集
            origin_title: 要插入的原标题
            trans_title: 要插入的需要翻译的标题
            video_url: 原视频地址
            isTranslated: 标题是否被翻译
        """
        file_path = self.project_path[id] / "标题.txt"
        project_dir = self.project_path[id]

        try:
            # 读取文件所有行
            with file_path.open("r", encoding="utf-8") as file:
                lines = file.readlines()

            length = len(self.project_subtitle[id])
            if isTranslated:
                line_number = length + 4 * (episode_num - 1)
                lines.insert(line_number, origin_title + "\n")
                lines.insert(line_number, trans_title + "\n")
                lines.insert(line_number, video_url + "\n")
                lines.insert(line_number, "\n")
                lines.insert(id, origin_title + "\n")
            else:
                line_number = length + 3 * (episode_num - 1)
                lines.insert(line_number, origin_title + "\n")
                lines.insert(line_number, video_url + "\n")
                lines.insert(line_number, "\n")
                lines.insert(id, origin_title + "\n")

            # 将修改后的内容写回文件
            with file_path.open("w", encoding="utf-8") as file:
                file.writelines(lines)

            # 重命名子文件夹
            for sub_folder in range(length, episode_num - 1, -1):
                old_folder = project_dir / str(sub_folder)
                new_folder = project_dir / str(sub_folder + 1)
                if old_folder.exists():
                    old_folder.rename(new_folder)

            # 创建新子文件夹
            new_episode_folder = project_dir / str(episode_num)
            new_episode_folder.mkdir(parents=True, exist_ok=True)

            return [True, ""]

        except FileNotFoundError:
            e = f"错误: 文件 {file_path} 不存在"
            return [False, str(e).strip()]

        except Exception as e:
            return [False, str(e).strip()]

    def deleteEpisode(self, id, episode_num, isTranslated=False):
        """
        增加新集

        参数:
            id: 项目id
            episode_num: 第几集
            isTranslated: 标题是否被翻译
        """
        file_path = self.project_path[id] / "标题.txt"
        project_dir = self.project_path[id]

        try:
            # 读取文件所有行
            with file_path.open("r", encoding="utf-8") as file:
                lines = file.readlines()

            length = len(self.project_subtitle[id])
            if isTranslated:
                line_number = length + 4 * (episode_num - 1)
                for _ in range(4):
                    lines.pop(line_number)
            else:
                line_number = length + 3 * (episode_num - 1)
                for _ in range(3):
                    lines.pop(line_number)

            lines.pop(episode_num - 1)

            # 将修改后的内容写回文件
            with file_path.open("w", encoding="utf-8") as file:
                file.writelines(lines)

            # 删除子文件夹
            shutil.rmtree(project_dir / str(episode_num))

            # 重命名子文件夹
            for sub_folder in range(episode_num + 1, length + 1):
                old_folder = project_dir / str(sub_folder)
                new_folder = project_dir / str(sub_folder - 1)
                if old_folder.exists():
                    old_folder.rename(new_folder)

            return [True, ""]

        except Exception as e:
            return [False, str(e).strip()]

    @staticmethod
    def isAdjacentFileExists(file_path):
        """判断这个文件上一个和下一个同名文件是否存在"""
        file_path = Path(file_path)
        isExists = [False, False]
        if not file_path.exists():
            return isExists
        try:
            root_path = file_path.parent.parent
            episode_num = int(file_path.parent.name)
            file_name = file_path.name
            previous_path = root_path / str(episode_num - 1) / file_name
            next_path = root_path / str(episode_num + 1) / file_name
            if previous_path.exists():
                isExists[0] = True
            if next_path.exists():
                isExists[1] = True
            return isExists
        except Exception:
            return [False, False]

    @staticmethod
    def get_previous_path(file_path):
        """如果存在，返回上一个文件"""
        file_path = Path(file_path)
        root_path = file_path.parent.parent
        episode_num = int(file_path.parent.name)
        file_name = file_path.name
        previous_path = root_path / str(episode_num - 1) / file_name
        if previous_path.exists():
            return previous_path
        else:
            return False

    @staticmethod
    def get_next_path(file_path):
        """如果存在，返回下一个文件"""
        file_path = Path(file_path)
        root_path = file_path.parent.parent
        episode_num = int(file_path.parent.name)
        file_name = file_path.name
        next_path = root_path / str(episode_num + 1) / file_name
        if next_path.exists():
            return next_path
        else:
            return False


if __name__ == "__main__":
    project = Project()
    print(project.project_path)
    pass
else:
    from ..common.config import cfg

    project = Project()
