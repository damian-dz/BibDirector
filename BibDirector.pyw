#!/usr/bin/env python3

from pathlib import Path

from PySide2.QtCore import (
    QCoreApplication,
    Qt
)

from PySide2.QtGui import (
    QColor,
    QFont,
    QIcon,
    QKeySequence,
    QTextCharFormat,
QTextOption
)

from PySide2.QtSql import (
    QSqlDatabase,
    QSqlQuery,
    QSqlTableModel
)

from PySide2.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QMainWindow,
    QMessageBox,
    QLineEdit,
    QPlainTextEdit,
    QSplitter,
    QTabBar,
    QTableView,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget
)

from custom import Highlighter
from parsing_tools_v2 import (Bib, Entry)

IMG_PATH = 'resources/img/'


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('BibDirector')
        self.resize(920, 480)
        self.setMinimumSize(300, 200)
        self.generateMenus()

        self.bibTableView = QTableView()

        detailsFormWidget = QWidget()
        detailsFormLayout = QFormLayout()
        authorsLineEdit = QLineEdit()
        detailsFormLayout.addRow('Authors:', authorsLineEdit)
        titleLineEdit = QLineEdit()
        detailsFormLayout.addRow('Title:', titleLineEdit)

        detailsFormWidget.setLayout(detailsFormLayout)

        ##
        self.highlighter = Highlighter()

        variableFormat = QTextCharFormat()
        variableFormat.setFontWeight(QFont.Bold)
        variableFormat.setForeground(Qt.blue)
        categories = Entry().get_categories()
        for category in categories:
            self.highlighter.addMapping(f'(?i)@{category}\\b', variableFormat)

        # singleLineCommentFormat = QTextCharFormat()
        # singleLineCommentFormat.setBackground(QColor("#77ff77"))
        # self.highlighter.addMapping("#[^\n]*", singleLineCommentFormat)

        # quotationFormat = QTextCharFormat()
        # quotationFormat.setBackground(Qt.cyan)
        # quotationFormat.setForeground(Qt.blue)
        # self.highlighter.addMapping("\".*\"", quotationFormat)
        #
        # functionFormat = QTextCharFormat()
        # functionFormat.setFontItalic(True)
        # functionFormat.setForeground(Qt.blue)
        # self.highlighter.addMapping("\\b[a-z0-9_]+\\(.*\\)", functionFormat)

        # font = QFont()
        # font.setFamily('Courier')
        # font.setFixedPitch(True)
        # font.setPixelSize(8)

        self.editor = QPlainTextEdit()
        self.editor.setStyleSheet('font: 10pt "Courier New";')
        # self.editor.setFont(font)
        self.highlighter.setDocument(self.editor.document())
        ##

        self.tabWidget = QTabWidget()


        mainSplitter = QSplitter(Qt.Horizontal)
        mainSplitter.addWidget(self.bibTableView)
        mainSplitter.addWidget(detailsFormWidget)

        self.tabWidget.addTab(mainSplitter, 'Database Viewer')
        self.tabWidget.addTab(self.editor, 'Editor')

        option = QTextOption()
        option.setFlags(QTextOption.ShowLineAndParagraphSeparators | QTextOption.ShowTabsAndSpaces)
        self.editor.document().setDefaultTextOption(option)

        mainWidget = QWidget()

        mainVerLayout = QVBoxLayout()
        mainVerLayout.addWidget(self.tabWidget)
        mainWidget.setLayout(mainVerLayout)
        self.setCentralWidget(mainWidget)



        # tabWidget = QTabWidget()
        # tabWidget.setTabsClosable(True)
        # tabWidget.addTab(QWidget(), "First")
        # tabWidget.setStyleSheet('''QTabBar::close-button {
        #                                     image: url(resources/img/remove-line.svg);
        #                                     subcontrol-position: left;
        #                                     }
        #                                 QTabBar::close-button:hover  {
        #                                     image: url(resources/img/remove-solid.svg);
        #                                 }''')
        # tabWidget.tabBar().setTabButton(0, QTabBar.LeftSide, QWidget())
        # self.setCentralWidget(mainSplitter)

    def generateMenus(self):
        fileMenu = self.menuBar().addMenu(self.tr('File'))
        fileMenu.addAction(QIcon(IMG_PATH + 'document-line.svg'), self.tr('New'), self.onNew, QKeySequence.New)
        fileMenu.addAction(QIcon(IMG_PATH + 'folder-open-line.svg'), self.tr('Open'), self.onOpen, QKeySequence.Open)
        fileMenu.addAction(QIcon(IMG_PATH + 'floppy-line.svg'), self.tr('Save'), self.onSave, QKeySequence.Save)
        fileMenu.addSeparator()
        fileMenu.addAction(QIcon(IMG_PATH + 'power-line.svg'), self.tr('Exit'), self.onExit)
        toolsMenu = self.menuBar().addMenu(self.tr('Tools'))
        toolsMenu.addAction(self.tr('Format'), self.onFormat)

    def onFormat(self):
        bib = Bib()
        bib.parse_text(self.editor.toPlainText())
        self.editor.setPlainText(bib.generate_output())

    def onNew(self):
        pass

    def onOpen(self):
        fileName = QFileDialog.getOpenFileName(self, self.tr('Open File'), '/', self.tr("BibTex Files (*.bib)"))
        if fileName and fileName[0]:
            db_path = Path(fileName[0]).stem + '.db'
            if Path(db_path).is_file():
                reply = QMessageBox.question(self, 'Confirm Delete', 'Delete the existing file?',
                                             QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    Path(db_path).unlink()
            bib = Bib()
            bib.parse_file(fileName[0])
            db = QSqlDatabase.addDatabase('QSQLITE')
            db.setDatabaseName(Path(fileName[0]).stem + '.db')
            db.open()
            db.exec_('CREATE TABLE articles (id INTEGER PRIMARY KEY, Type TEXT, Author TEXT, Title TEXT)')

            types = []
            authors = []
            titles = []
            for entry in bib.entries:
                types.append(entry.get_category())
                authors.append(entry.get_field_value('author'))
                titles.append(entry.get_field_value('title'))

            query = QSqlQuery(db)
            query.prepare('INSERT INTO articles VALUES(?, ?, ?, ?)')
            query.addBindValue([None] * len(bib.entries))
            query.addBindValue(types)
            query.addBindValue(authors)
            query.addBindValue(titles)
            query.execBatch()

            # db.exec_('INSERT INTO articles VALUES(NULL, "Doe Moe", "Revolutionary Title")')

            model = QSqlTableModel(self, db)
            model.setTable('articles')
            model.setEditStrategy(QSqlTableModel.OnManualSubmit)
            model.select()
            # model.removeColumn(0)  # don't show the ID
            model.setHeaderData(1, Qt.Horizontal, self.tr('Type'))
            model.setHeaderData(2, Qt.Horizontal, self.tr('Author'))
            model.setHeaderData(3, Qt.Horizontal, self.tr('Title'))

            self.bibTableView.setModel(model)

            # print(bib.generate_output())


    def onSave(self):
        pass

    def onExit(self):
        if self.close():
            QApplication.quit()


def main():
    import sys
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
