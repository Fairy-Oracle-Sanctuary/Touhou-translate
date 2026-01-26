# coding:utf-8

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QIntValidator, QPainter
from PySide6.QtWidgets import QHBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    FluentIcon,
    LineEdit,
    ToolTipPosition,
    TransparentToolButton,
    isDarkTheme,
    themeColor,
)

from ..resource import resource_rc  # noqa: F401
from .tool_tip import setToolTipInfos


class PageButton(QWidget):
    clicked = Signal(int)

    def __init__(self, page: int, selected=False, parent=None):
        super().__init__(parent)
        self.page: int = page
        self._text = str(page)
        self._isSelected: bool = selected
        self._isHover: bool = False
        self.setFixedSize(35, 35)

    def setSelected(self, isSelected: bool) -> None:
        if self._isSelected == isSelected:
            return
        self._isSelected = isSelected
        self.update()

    def isSelected(self) -> bool:
        return self._isSelected

    def enterEvent(self, event):
        self._isHover = True
        self.update()

    def leaveEvent(self, event):
        self._isHover = False
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() is Qt.LeftButton:
            self.clicked.emit(self.page)
            self._isSelected = not self._isSelected
            self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        painter.setPen(Qt.NoPen)
        rect = self.rect().adjusted(1, 1, -1, -1)
        isDark = isDarkTheme()
        c = 0 if isDark else 255
        if self._isSelected:
            painter.setBrush(themeColor())
        elif self._isHover:
            if isDark:
                pc = 255
                bc = 46
            else:
                pc = 0
                bc = 224
            painter.setPen(QColor(pc, pc, pc, 64))
            painter.setBrush(QColor(bc, bc, bc))
        painter.drawRoundedRect(rect, 6, 6)

        painter.setPen(
            QColor(c, c, c)
            if self._isSelected
            else (QColor(255, 255, 255) if isDark else QColor(0, 0, 0))
        )
        painter.drawText(rect, Qt.AlignCenter, self._text)


class Pager(QWidget):
    currentPageChanged = Signal(int)

    def __init__(self, pages: int, maxVisible: int, parent=None):
        super().__init__(parent)
        self.__pages: int = pages
        self.__currentPage: int = 0
        self.__maxVisible: int = maxVisible

        self._widgetLayout: QHBoxLayout = QHBoxLayout(self)
        self.__initWidget()
        self.__connectSignalSlot()
        self.__updateButtons()

        setToolTipInfos(
            [self.topButton, self.bottomButton, self.previousButton, self.nextButton],
            ["跳转到第一页", "跳转到最后一页", "上一页", "下一页"],
            2500,
            ToolTipPosition.TOP,
        )

    def __initWidget(self):
        self.topLabel: BodyLabel = BodyLabel("...")
        self.topLabel.setFixedWidth(20)
        self.topLabel.setAlignment(Qt.AlignCenter)

        self.bottomLabel: BodyLabel = BodyLabel("...")
        self.bottomLabel.setFixedWidth(20)
        self.bottomLabel.setAlignment(Qt.AlignCenter)

        self.topButton: TransparentToolButton = TransparentToolButton(
            QIcon(
                f":/app/images/controls/SkipStartFill_{'white' if isDarkTheme() else 'black'}.svg"
            ),
            self,
        )
        self.bottomButton: TransparentToolButton = TransparentToolButton(
            QIcon(
                f":/app/images/controls/SkipEndFill_{'white' if isDarkTheme() else 'black'}.svg"
            ),
            self,
        )
        self.topButton.setIconSize(QSize(20, 20))
        self.bottomButton.setIconSize(QSize(20, 20))

        self.previousButton: TransparentToolButton = TransparentToolButton(
            FluentIcon.CARE_LEFT_SOLID, self
        )
        self.nextButton: TransparentToolButton = TransparentToolButton(
            FluentIcon.CARE_RIGHT_SOLID, self
        )

        self.jumpLabel: BodyLabel = BodyLabel("跳转到")
        self.countLabel: BodyLabel = BodyLabel(f"页 共计 {self.__pages} 页")

        self.jumpEdit: LineEdit = LineEdit(self)
        self.jumpEdit.setValidator(QIntValidator(self))
        self.jumpEdit.setAlignment(Qt.AlignCenter)
        self.jumpEdit.setFixedWidth(64)

    def __onCurrentPageChanged(self, page):
        self.jumpEdit.setText(str(page))

    def __jumpToTop(self):
        if self.__pages >= 1:
            self._onClicked(1)

    def __jumpToBottom(self):
        self._onClicked(self.__pages)

    def __onPreviousButton(self):
        self._onClicked(self.__currentPage - 1)

    def __onNextButton(self):
        self._onClicked(self.__currentPage + 1)

    def __updateButtons(self) -> None:
        for i in reversed(range(self._widgetLayout.count())):
            widget = self._widgetLayout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
            self.topLabel.setParent(self)
            self.bottomLabel.setParent(self)

        self._widgetLayout.addWidget(self.topButton)
        self._widgetLayout.addWidget(self.previousButton)
        enable = self.__currentPage > 1
        self.topButton.setEnabled(enable)
        self.previousButton.setEnabled(enable)

        start = max(1, self.__currentPage - self.__maxVisible // 2)
        end = min(self.__pages, start + self.__maxVisible - 1)
        if end - start + 1 < self.__maxVisible:
            start = max(1, end - self.__maxVisible + 1)

        if start > 2:
            self._addButtonToPage(1)
            self.topLabel.setParent(self)
            self._widgetLayout.addWidget(self.topLabel)
        elif start == 2:
            self._addButtonToPage(1)

        for i in range(start, end + 1):
            self._addButtonToPage(i, selected=(i == self.__currentPage))

        if end < self.__pages - 1:
            self.bottomLabel.setParent(self)
            self._widgetLayout.addWidget(self.bottomLabel)
            self._addButtonToPage(self.__pages)
        elif end == self.__pages - 1:
            self._addButtonToPage(self.__pages)

        enable = self.__currentPage < self.__pages
        self._widgetLayout.addWidget(self.nextButton)
        self._widgetLayout.addWidget(self.bottomButton)
        self.nextButton.setEnabled(enable)
        self.bottomButton.setEnabled(enable)

        self._widgetLayout.addWidget(self.jumpLabel)
        self._widgetLayout.addWidget(self.jumpEdit)
        self._widgetLayout.addWidget(self.countLabel)

        self.currentPageChanged.emit(self.__currentPage)

    def __connectSignalSlot(self) -> None:
        self.topButton.clicked.connect(self.__jumpToTop)
        self.bottomButton.clicked.connect(self.__jumpToBottom)
        self.previousButton.clicked.connect(self.__onPreviousButton)
        self.nextButton.clicked.connect(self.__onNextButton)
        self.jumpEdit.returnPressed.connect(self.jumpToPage)
        self.currentPageChanged.connect(self.__onCurrentPageChanged)

    def currentPage(self) -> int:
        return self.__currentPage

    def pages(self) -> int:
        return self.__pages

    def maxVisible(self) -> int:
        return self.__maxVisible

    def setPages(self, number: int) -> None:
        if self.__pages == number:
            return
        self.__pages = number
        self.countLabel.setText(f"页 共计 {self.__pages} 页")
        self.__updateButtons()

    def setCurrentPage(self, page: int) -> None:
        if page > self.__pages:
            return
        self.__currentPage = page
        self._onClicked(page)

    def setMaxVisible(self, number: int) -> None:
        if self.__maxVisible == number or self.__maxVisible > self.__pages:
            return
        self.__maxVisible = number
        self.__updateButtons()

    def _addButtonToPage(self, number: int, selected=False) -> None:
        button = PageButton(number, selected, self)
        button.clicked.connect(self._onClicked)
        self._widgetLayout.addWidget(button)

    def _onClicked(self, page: int) -> None:
        self.__currentPage = page
        self.__updateButtons()

    def jumpToPage(self) -> None:
        try:
            page = int(self.jumpEdit.text())
            if 1 <= page <= self.__pages:
                self.__currentPage = page
                self.__updateButtons()
        except ValueError:
            return
