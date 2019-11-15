# -*- coding: utf-8 -*-
from typing import Tuple

from PyQt5 import QtCore
from PyQt5.QtGui import QKeySequence, QIcon, QColor
from PyQt5.QtWidgets import (
    QAction,
    QMenu,
    QDockWidget,
    QMessageBox,
    QDialog,
    QFileDialog,
    QToolBar,
    QMainWindow,
    QListWidget,
    QAbstractItemView,
    QColorDialog,
    QPushButton, QSizePolicy
)

import settings
import values
from imageview import ImageView
from ui_newprojectdialog import Ui_NewProjectDialog
from ui_settingsdialog import Ui_SettingsDialog

# noinspection PyUnresolvedReferences
import resources


# noinspection PyPep8Naming
class Ui_MainWindow(object):

    # noinspection PyTypeChecker
    def __init__(self):
        self.mainWindow: QMainWindow = None
        self.imageListDockWidget: QDockWidget = None
        self.imageView: ImageView = None
        self.imageListWidget: QListWidget = None
        self.newProjectAct: QAction = None
        self.openProjectAct: QAction = None
        self.openRecentAct: QAction = None
        self.saveProjectAct: QAction = None
        self.setSettingsAct: QAction = None
        self.buildCropMapsAct: QAction = None
        self.selectImageAct: QAction = None
        self.selectRoiPolyAct: QAction = None
        self.setCropRowsDirAct: QAction = None
        self.imageInfoToolAct: QAction = None
        self.shownShapesAct: QAction = None
        self.zoomInAct: QAction = None
        self.zoomOutAct: QAction = None
        self.exitAct: QAction = None
        self.aboutAct: QAction = None
        self.toggleImageListViewAct: QAction = None
        self.fileMenu: QMenu = None
        self.viewMenu: QMenu = None
        self.toolsMenu: QMenu = None
        self.helpMenu: QMenu = None
        self.fileToolBar: QToolBar = None
        self.viewToolBar: QToolBar = None
        self.cropToolBar: QToolBar = None
        self.settingsDialog: SettingsDialog = None
        self.newProjectDialog: NewProjectDialog = None

    def setupUi(self, mainWindow):
        
        self.mainWindow = mainWindow
        self.createCentralWidget()
        self.createDockWidgets()
        self.createActions()        
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()
        self.createDialogs()

        self.mainWindow.setWindowIcon(QIcon(values.logoImage))

    @property
    def pos(self) -> Tuple[int, int]:
        pos = self.mainWindow.pos()
        return pos.x(), pos.y()

    @pos.setter
    def pos(self, pos: Tuple[int, int]):
        self.mainWindow.move(pos[0], pos[1])

    @property
    def size(self):
        size = self.mainWindow.size()
        return size.width(), size.height()

    @size.setter
    def size(self, size: Tuple[int, int]):
        self.mainWindow.resize(size[0], size[1])

    ######################################################################
    #  Initialization
    ######################################################################
    
    def createCentralWidget(self):
        self.imageView = ImageView(self.mainWindow)
        self.mainWindow.setCentralWidget(self.imageView)

    def createDockWidgets(self):

        self.imageListDockWidget = panel = QDockWidget(
            values.imageListPanelTitle,
            self.mainWindow
        )
        panel.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        self.mainWindow.addDockWidget(QtCore.Qt.LeftDockWidgetArea, panel)
        panel.close()

        self.imageListWidget = QListWidget(panel)
        self.imageListWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        panel.setWidget(self.imageListWidget)

    def createActions(self):

        self.newProjectAct = QAction(
            QIcon(values.newProjectImage),
            values.newProjectActText,
            self.mainWindow
        )
        self.newProjectAct.setShortcut(QKeySequence.New)
        self.newProjectAct.setStatusTip(values.newProjectActTip)

        self.openProjectAct = QAction(
            QIcon(values.openProjectImage),
            values.openProjectActText,
            self.mainWindow
        )
        self.openProjectAct.setShortcut(QKeySequence.Open)
        self.openProjectAct.setStatusTip(values.openProjectActTip)

        self.openRecentAct = QAction(
            values.openRecentActText,
            self.mainWindow
        )
        self.openRecentAct.setMenu(QMenu())
        
        self.saveProjectAct = QAction(
            QIcon(values.saveProjectImage),
            values.saveProjectActText,
            self.mainWindow
        )
        self.saveProjectAct.setShortcut(QKeySequence.Save)
        self.saveProjectAct.setStatusTip(values.saveProjectActTip)

        self.setSettingsAct = QAction(
            QIcon(values.settingsImage),
            values.settingsActText,
            self.mainWindow
        )
        self.setSettingsAct.setStatusTip(values.settingsActTip)

        self.buildCropMapsAct = QAction(
            QIcon(values.analyzeCropImage),
            values.analyzeCropActText,
            self.mainWindow
        )
        self.buildCropMapsAct.setStatusTip(values.analyzeCropActTip)

        self.selectRoiPolyAct = QAction(
            QIcon(values.setRoiImage),
            values.setRoiActText,
            self.mainWindow
        )
        self.selectRoiPolyAct.setStatusTip(values.setRoiActTip)

        self.setCropRowsDirAct = QAction(
            QIcon(values.setRowsDirImage),
            values.setRowsDirActText,
            self.mainWindow
        )
        self.setCropRowsDirAct.setStatusTip(values.setRowsDirActTip)
        
        self.imageInfoToolAct = QAction(
            QIcon(values.infoToolImage),
            values.infoToolActText,
            self.mainWindow
        )
        self.imageInfoToolAct.setStatusTip(values.infoToolActTip)
        self.imageInfoToolAct.setCheckable(True)
        self.imageInfoToolAct.setChecked(False)

        self.shownShapesAct = QAction(
            QIcon(values.shownShapesImage),
            values.showShapesActText,
            self.mainWindow
        )
        self.shownShapesAct.setStatusTip(values.showShapesActTip)
        self.shownShapesAct.setMenu(QMenu())

        self.zoomInAct = QAction(
            QIcon(values.zoomInImage),
            values.zoomInActText,
            self.mainWindow
        )
        self.zoomInAct.setShortcut("Ctrl++")
        self.zoomInAct.setStatusTip(values.zoomInActTip)

        self.zoomOutAct = QAction(
            QIcon(values.zoomOutImage),
            values.zoomOutActText,
            self.mainWindow
        )
        self.zoomOutAct.setShortcut("Ctrl+-")
        self.zoomOutAct.setStatusTip(values.zoomOutActTip)
            
        self.exitAct = QAction(
            values.exitActText,
            self.mainWindow
        )
        self.exitAct.setShortcut("Ctrl+Q")

        self.aboutAct = QAction(
            values.aboutActText,
            self.mainWindow
        )

        action = self.imageListDockWidget.toggleViewAction()
        action.setIcon(QIcon(values.panelViewImage))
        action.setText(values.togglePanelViewActText)
        action.setStatusTip(values.togglePanelViewActTip)
        self.toggleImageListViewAct = action

    def createMenus(self):
        self.fileMenu = self.mainWindow.menuBar().addMenu(values.fileMenuText)
        self.fileMenu.addAction(self.newProjectAct)
        self.fileMenu.addAction(self.openProjectAct)
        self.fileMenu.addAction(self.openRecentAct)
        self.fileMenu.addAction(self.saveProjectAct)
        self.fileMenu.addAction(self.setSettingsAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = self.mainWindow.menuBar().addMenu(values.viewMenuText)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.toggleImageListViewAct)

        self.toolsMenu = self.mainWindow.menuBar().addMenu(values.toolsMenuText)
        self.toolsMenu.addAction(self.buildCropMapsAct)
        self.toolsMenu.addAction(self.shownShapesAct)
        self.toolsMenu.addSeparator()
        self.toolsMenu.addAction(self.selectRoiPolyAct)
        self.toolsMenu.addAction(self.setCropRowsDirAct)
        self.toolsMenu.addAction(self.imageInfoToolAct)

        self.helpMenu = self.mainWindow.menuBar().addMenu(values.helpMenuText)
        self.helpMenu.addAction(self.aboutAct)

    def createToolBars(self):
        size = settings.TOOLBAR_ICON_SIZE
        iconSize = QtCore.QSize(size, size)

        self.fileToolBar = QToolBar(self.mainWindow)
        self.mainWindow.addToolBar(self.fileToolBar)
        self.fileToolBar.setIconSize(iconSize)
        self.fileToolBar.addAction(self.newProjectAct)
        self.fileToolBar.addAction(self.openProjectAct)
        self.fileToolBar.addAction(self.saveProjectAct)
        self.fileToolBar.addAction(self.setSettingsAct)

        self.viewToolBar = QToolBar(self.mainWindow)
        self.mainWindow.addToolBar(self.viewToolBar)
        self.viewToolBar.setIconSize(iconSize)
        self.viewToolBar.addAction(self.zoomOutAct)
        self.viewToolBar.addAction(self.zoomInAct)
        self.viewToolBar.addSeparator()
        self.viewToolBar.addAction(self.toggleImageListViewAct)

        self.cropToolBar = QToolBar(self.mainWindow)
        self.mainWindow.addToolBar(self.cropToolBar)
        self.cropToolBar.setIconSize(iconSize)
        self.cropToolBar.addAction(self.buildCropMapsAct)
        self.cropToolBar.addAction(self.selectRoiPolyAct)
        self.cropToolBar.addAction(self.setCropRowsDirAct)
        self.cropToolBar.addAction(self.imageInfoToolAct)
        self.cropToolBar.addAction(self.shownShapesAct)
        
    def createStatusBar(self):
        self.mainWindow.statusBar().showMessage("Ready")

    def createDialogs(self):
        self.settingsDialog = SettingsDialog(self.mainWindow)
        self.newProjectDialog = NewProjectDialog(self.mainWindow)

    def errorMsg(self, msg):
        QMessageBox.critical(
            self.mainWindow,
            values.errorDialogTitle,
            msg
        )

    def warnMsg(self, msg: str, title: str = '', buttons=None):
        if not title:
            title = values.warnDialogTitle
        if buttons is None:
            ret = QMessageBox.warning(self.mainWindow, title, msg)
        else:
            ret = QMessageBox.warning(self.mainWindow, title, msg, buttons)
        return ret


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super(NewProjectDialog, self).__init__(parent)

        # Set up the user interface from Designer.
        self.ui = Ui_NewProjectDialog()
        self.ui.setupUi(self)

        self.setWindowTitle(values.newProjectDialogTitle)
        self.ui.projectPathButton.clicked.connect(self._getProjectPath)
        self.ui.imagePathButton.clicked.connect(self._getImagesPath)

        helpFlag = QtCore.Qt.WindowContextHelpButtonHint
        self.setWindowFlags(self.windowFlags() & ~helpFlag)
        self.setFixedSize(self.size())
            
    def _getImagesPath(self):
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            values.selectDirDialogTitle,
            self.ui.imagePathEdit.text(),
            'Images (*.jpg *.jpeg *.png *.tiff)'
        )
        if filePath:
            self.ui.imagePathEdit.setText(filePath)
            
    def _getProjectPath(self):
        path = self.ui.projectPathEdit.text()
        path = QFileDialog.getExistingDirectory(
            self,
            values.selectDirDialogTitle,
            path
        )
        if path:
            self.ui.projectPathEdit.setText(path)


class ColorPickerButton(QPushButton):

    def __init__(self, parent, color: QColor = None):
        super(ColorPickerButton, self).__init__(parent)

        sp = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        sp.setHorizontalStretch(0)
        sp.setVerticalStretch(0)
        self.setSizePolicy(sp)
        self.setAutoFillBackground(False)
        self.setText("")

        if color is None:
            color = QColor()
        self._color: QColor = color

        self.clicked.connect(self._getColor)

    def _getColor(self):
        color = QColorDialog.getColor(self._color, self)
        if color.isValid():
            self._color = color
            self.setStyleSheet("background-color: " + color.name())

    def color(self):
        return self._color

    def setColor(self, color: QColor):
        self._color = color
        self.setStyleSheet("background-color: " + color.name())
    

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)
        self.setWindowTitle(values.settingsDialogTitle)

        helpFlag = QtCore.Qt.WindowContextHelpButtonHint
        self.setWindowFlags(self.windowFlags() & ~helpFlag)
        self.setFixedSize(self.size())

        self.ui.roiLineColorButton = ColorPickerButton(self)
        self.ui.roiLineColorLayout.addWidget(self.ui.roiLineColorButton)
        self.ui.rowsDirLineColorButton = ColorPickerButton(self)
        self.ui.rowsDirLineColorLayout.addWidget(self.ui.rowsDirLineColorButton)
        self.ui.rowsRidgesColorButton = ColorPickerButton(self)
        self.ui.rowsRidgesColorLayout.addWidget(self.ui.rowsRidgesColorButton)
        self.ui.rowsFurrowsColorButton = ColorPickerButton(self)
        self.ui.rowsFurrowsColorLayout.addWidget(self.ui.rowsFurrowsColorButton)
