# coding: utf-8
"""
启动错误处理器
用于捕获和记录应用程序启动过程中的错误
"""

import logging
import os
import sys
import traceback

from .setting import CONFIG_FOLDER, VERSION


class StartupErrorHandler:
    """启动错误处理器"""

    def __init__(self):
        self.log_dir = CONFIG_FOLDER / "Log"
        self.log_dir.mkdir(exist_ok=True, parents=True)
        self.startup_log_file = self.log_dir / "startup_error.log"

        # 配置启动错误日志
        self._setup_startup_logger()

    def _setup_startup_logger(self):
        """配置启动错误日志记录器"""
        self.startup_logger = logging.getLogger("startup_error")
        self.startup_logger.setLevel(logging.DEBUG)

        # 清除现有处理器
        self.startup_logger.handlers.clear()

        # 文件处理器
        file_handler = logging.FileHandler(
            self.startup_log_file, mode="a", encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)

        # 格式化器
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)

        self.startup_logger.addHandler(file_handler)

    def log_startup_info(self):
        """记录启动信息"""
        self.startup_logger.info("=" * 50)
        self.startup_logger.info(f"Fairy-Kekkai-Workshop 启动 - 版本: {VERSION}")
        self.startup_logger.info(f"Python版本: {sys.version}")
        self.startup_logger.info(f"操作系统: {os.name}")
        self.startup_logger.info(f"平台: {sys.platform}")
        self.startup_logger.info(f"工作目录: {os.getcwd()}")
        self.startup_logger.info(f"脚本路径: {sys.argv[0] if sys.argv else 'Unknown'}")
        self.startup_logger.info("=" * 50)

    def log_exception(self, exception_type, exception_value, traceback_obj):
        """记录异常信息"""
        self.startup_logger.error(
            f"启动失败 - {exception_type.__name__}: {exception_value}"
        )
        self.startup_logger.error("详细错误信息:")

        # 格式化完整的traceback
        tb_lines = traceback.format_exception(
            exception_type, exception_value, traceback_obj
        )
        for line in tb_lines:
            self.startup_logger.error(line.rstrip())

        self.startup_logger.error("=" * 50)

    def log_critical_error(self, message):
        """记录关键错误信息"""
        self.startup_logger.critical(f"关键错误: {message}")
        self.startup_logger.critical("=" * 50)

    def check_environment(self):
        """检查运行环境"""
        try:
            # 检查Python版本
            if sys.version_info < (3, 8):
                self.log_critical_error(
                    f"Python版本过低: {sys.version}. 需要Python 3.8或更高版本"
                )
                return False

            # 检查必要目录
            if not CONFIG_FOLDER.exists():
                self.log_critical_error(f"配置目录不存在: {CONFIG_FOLDER}")
                return False

            # 检查写入权限
            test_file = CONFIG_FOLDER / "write_test.tmp"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                self.log_critical_error(f"配置目录无写入权限: {e}")
                return False

            self.startup_logger.info("环境检查通过")
            return True

        except Exception as e:
            self.log_critical_error(f"环境检查失败: {e}")
            return False


# 全局启动错误处理器实例
startup_handler = StartupErrorHandler()


def handle_startup_error():
    """处理启动错误的装饰器函数"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # 记录启动信息
                startup_handler.log_startup_info()

                # 环境检查
                if not startup_handler.check_environment():
                    return 1

                # 执行主函数
                return func(*args, **kwargs)

            except Exception as e:
                # 记录异常
                exc_type, exc_value, exc_tb = sys.exc_info()
                startup_handler.log_exception(exc_type, exc_value, exc_tb)

                # 尝试显示错误对话框
                try:
                    from PySide6.QtWidgets import QApplication, QMessageBox

                    if not QApplication.instance():
                        app = QApplication([])  # noqa
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Critical)
                    msg_box.setWindowTitle("启动错误")
                    msg_box.setText("应用程序启动失败")
                    msg_box.setInformativeText(
                        f"错误信息: {str(e)}\n\n详细日志已保存到:\n{startup_handler.startup_log_file}"
                    )
                    msg_box.exec()
                except ImportError:
                    # 如果Qt导入失败，只打印到控制台
                    print(f"启动失败: {e}")
                    print(f"详细日志: {startup_handler.startup_log_file}")

                return 1

        return wrapper

    return decorator


def setup_global_exception_handler():
    """设置全局异常处理器"""

    def handle_exception(exc_type, exc_value, exc_tb):
        """全局异常处理函数"""
        if issubclass(exc_type, KeyboardInterrupt):
            # 允许Ctrl+C正常退出
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        # 记录未捕获的异常
        startup_handler.log_exception(exc_type, exc_value, exc_tb)

        # 尝试显示错误对话框
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox

            app = QApplication.instance()
            if app:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle("程序错误")
                msg_box.setText("程序运行时发生未处理的错误")
                msg_box.setInformativeText(
                    f"错误信息: {str(exc_value)}\n\n详细日志已保存到:\n{startup_handler.startup_log_file}"
                )
                msg_box.exec()
        except Exception:
            # 如果无法显示对话框，至少记录到控制台
            print(f"未处理异常: {exc_value}")
            print(f"详细日志: {startup_handler.startup_log_file}")

    # 设置全局异常处理器
    sys.excepthook = handle_exception
