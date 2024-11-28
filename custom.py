import re

from PySide2.QtGui import QSyntaxHighlighter


class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        QSyntaxHighlighter.__init__(self, parent)
        self.mappings = {}

    def addMapping(self, pattern, _format):
        self.mappings[pattern] = _format

    def highlightBlock(self, text):
        for pattern in self.mappings:
            for m in re.finditer(pattern, text):
                s, e = m.span()
                self.setFormat(s, e - s, self.mappings[pattern])
