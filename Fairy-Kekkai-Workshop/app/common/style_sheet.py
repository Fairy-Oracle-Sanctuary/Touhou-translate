# coding: utf-8
from enum import Enum

from qfluentwidgets import StyleSheetBase, Theme, qconfig


class StyleSheet(StyleSheetBase, Enum):
    """Style sheet"""

    SAMPLE_CARD = "sample_card"

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f":/app/qss/{theme.value.lower()}/{self.value}.qss"
