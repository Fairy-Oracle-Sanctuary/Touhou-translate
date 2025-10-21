# coding:utf-8
from qfluentwidgets import ScrollArea


class HomeInterface(ScrollArea):
    """Home interface"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.__initWidget()
        # self.loadSamples()

    def __initWidget(self):
        self.setObjectName("homeInterface")
        self.enableTransparentBackground()
