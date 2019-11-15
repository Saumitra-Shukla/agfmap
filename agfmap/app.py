import math
import os
from math import atan2
from typing import Dict

import cv2 as cv
import mcrops
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QFileDialog, QAction, QListWidgetItem

import utils
import values
from applog import logger
from imageview import Layer, Shape
from settings import (
    ProjectSettings,
    AppSettings,
    MAX_RECENT_FILES,
    PROJECT_FILE_EXT,
    COLORMAPS
)
from ui_mainwindow import Ui_MainWindow

IMAGE_CROP_FIELD = 'Crop Field'
IMAGE_NORM_FIELD = 'Norm Field'
IMAGE_VEG_MASK = 'Vegetation Mask'
IMAGE_WEED_MASK = 'Weed Mask'
IMAGE_VEG_DENSITY = 'Vegetation Density'
IMAGE_WEED_DENSITY = 'Weed Density'
IMAGE_ROI_MASK = 'Roi Mask'

IMAGES = (
    IMAGE_CROP_FIELD,
    IMAGE_NORM_FIELD,
    IMAGE_VEG_MASK,
    IMAGE_WEED_MASK,
    IMAGE_VEG_DENSITY,
    IMAGE_WEED_DENSITY,
    IMAGE_ROI_MASK,
)

SHAPE_ROWS_RIDGES = 'Row Ridges'
SHAPE_ROWS_FURROWS = 'Row Furrows'
SHAPE_ROWS_DIR = 'Rows Direction'
SHAPE_ROI_POLY = 'Roi Poly'

SHAPES = (
    SHAPE_ROWS_RIDGES,
    SHAPE_ROWS_FURROWS,
    SHAPE_ROWS_DIR,
    SHAPE_ROI_POLY,
)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.images: Dict[str, Layer] = {}

        self.projectSettings: ProjectSettings = ProjectSettings()
        self.appSettings: AppSettings = AppSettings()
        self.loadAppSettings()
        self.connectActions()

    def closeEvent(self, event):
        self.saveAppSettings()
        self.saveProject()
        event.accept()

    def loadAppSettings(self):

        try:
            self.appSettings = AppSettings.load()
        except Exception as err:
            logger.error(err)

        self.ui.pos = self.appSettings.mainWindowPos
        self.ui.size = self.appSettings.mainWindowSize

        lastProjectPath = self.appSettings.lastProjectPath
        if utils.fileExists(lastProjectPath):
            self.loadProjectFile(lastProjectPath)
        self.updateRecentProjectsActions()

    def saveAppSettings(self):
        self.appSettings.mainWindowPos = self.ui.pos
        self.appSettings.mainWindowSize = self.ui.size

        try:
            self.appSettings.save()
        except Exception as err:
            logger.error(err)
            self.ui.errorMsg('An error occurred while trying to save the application settings')

    def setCurrentProject(self):

        projectName = self.projectSettings.projectName
        self.setWindowTitle(f'{projectName} - {values.appName}')

        recentPaths = self.appSettings.recentFiles
        currentPath = self.projectSettings.projectSettingsPath

        if currentPath in recentPaths:
            recentPaths.remove(currentPath)
        else:
            pass

        recentPaths.insert(0, currentPath)
        del recentPaths[MAX_RECENT_FILES:]

        self.appSettings.recentFiles = recentPaths
        self.appSettings.lastProjectPath = currentPath
        self.updateRecentProjectsActions()

    def updateRecentProjectsActions(self):

        menu = self.ui.openRecentAct.menu()
        if menu.isEmpty():
            for i in range(MAX_RECENT_FILES):
                action = QtWidgets.QAction(self)
                action.visible = False
                action.triggered.connect(self.openRecentProject)
                menu.addAction(action)

        recentPaths = self.appSettings.recentFiles
        recentPaths[:] = [
            file for file in recentPaths
            if utils.fileExists(file)
        ]
        self.appSettings.recentFiles = recentPaths

        if len(recentPaths) == 0:
            self.ui.openRecentAct.setDisabled(True)
            return
        self.ui.openRecentAct.setDisabled(False)

        numRecentFiles = min(len(recentPaths), MAX_RECENT_FILES)
        actions = menu.actions()
        for i in range(numRecentFiles):
            fileName = os.path.basename(recentPaths[i])
            text = f'&{i + 1} {fileName}'
            actions[i].setText(text)
            actions[i].setData(recentPaths[i])
            actions[i].setVisible(True)

        for j in range(numRecentFiles, MAX_RECENT_FILES):
            actions[j].setVisible(False)

    def updateShownShapesActions(self):

        menu = self.ui.shownShapesAct.menu()
        menu.clear()

        for name in SHAPES:
            action = QtWidgets.QAction(name, self)
            action.setCheckable(True)
            visible = self.projectSettings.shapesVisible.get(name, True)
            action.setChecked(visible)
            action.triggered.connect(self.setShapeVisible)
            action.setData(name)
            menu.addAction(action)

    def fillImageList(self):
        listWidget = self.ui.imageListWidget
        for name in IMAGES:
            item = QListWidgetItem(name)
            item.setData(0, name)
            listWidget.addItem(item)
        # noinspection PyUnresolvedReferences
        listWidget.itemSelectionChanged.connect(self.imageSelected)
        self.updateImageList()

    def updateImageList(self):
        listWidget = self.ui.imageListWidget
        for i in range(listWidget.count()):
            item = listWidget.item(i)
            name = item.data(0)
            if name in self.images:
                item.setHidden(self.images[name].isEmpty)
                if name == self.projectSettings.shownImageName:
                    listWidget.setCurrentItem(item)

    ######################################################################
    #  Actions
    ######################################################################

    def newProject(self):

        se = ProjectSettings()
        ui = self.ui.newProjectDialog.ui

        if self.ui.newProjectDialog.exec_():
            se.projectName = ui.projectNameEdit.text()
            se.projectPath = os.path.join(
                ui.projectPathEdit.text(), se.projectName
            )
            if not utils.dirExists(se.projectPath):
                os.mkdir(se.projectPath)
            se.cropFieldImagePath = ui.imagePathEdit.text()
            se.resolution = ui.resolutionSpinBox.value()

            # if not utils.dirExists(prjSettings['project-path']['value']):
            #     self.ui.errorMsg(values.projectPathErrorMessage)
            #     return
            #
            # if not utils.dirExists(prjSettings['images-path']['value']):
            #     self.ui.errorMsg(values.strings["invalid_images_path_msg"])
            #     return
            self.loadProject(se)

    def openProject(self):
        title = values.openProjectDialogTitle
        extFilter = f'Files (*{PROJECT_FILE_EXT})'
        dirPath = self.appSettings.openFilesDirPath
        filePath, _ = QFileDialog.getOpenFileName(self, title, dirPath, extFilter)
        if filePath:
            self.loadProjectFile(filePath)

    def openRecentProject(self):
        action = self.sender()
        if action:
            self.loadProjectFile(action.data())

    def loadProjectFile(self, filePath):
        try:
            projectSettings = ProjectSettings.load(filePath)
        except Exception as err:
            logger.error(err)
            self.ui.errorMsg(f'Error loading project {filePath}.')
            self.updateRecentProjectsActions()
        else:
            self.loadProject(projectSettings)

    def loadProject(self, projectSettings: ProjectSettings):
        self.projectSettings = projectSettings
        self.setCurrentProject()
        self.buildImages()
        self.updateShownShapesActions()
        shownImageName = self.projectSettings.shownImageName
        if shownImageName not in self.images:
            shownImageName = IMAGE_CROP_FIELD
        self.fillImageList()
        self.ui.imageListDockWidget.show()
        self.updateShownImage(shownImageName)
        self.saveProject()

    def buildImages(self):
        self.images = {}
        se = self.projectSettings
        readInfo = [
            (IMAGE_CROP_FIELD, cv.IMREAD_COLOR),
            (IMAGE_NORM_FIELD, cv.IMREAD_COLOR),
            (IMAGE_VEG_DENSITY, cv.IMREAD_COLOR),
            (IMAGE_VEG_MASK, cv.IMREAD_GRAYSCALE),
            (IMAGE_WEED_DENSITY, cv.IMREAD_COLOR),
            (IMAGE_WEED_MASK, cv.IMREAD_GRAYSCALE),
            (IMAGE_ROI_MASK, cv.IMREAD_GRAYSCALE),
        ]
        for name, flags in readInfo:
            fileName = '_'.join(name.lower().split()) + '.png'
            filePath = os.path.join(se.projectPath, fileName)
            self.images[name] = Layer(
                name=name, filePath=filePath, flags=flags
            )

        if not utils.fileExists(self.images[IMAGE_CROP_FIELD].filePath):
            image = cv.imread(se.cropFieldImagePath, cv.IMREAD_UNCHANGED)
            if image.ndim == 3 and image.shape[2] == 4:
                alpha = image[:, :, 3]
                image = image[:, :, 0:3]
                image[alpha < 200] = 0
            self.images[IMAGE_CROP_FIELD].image = image
            self.images[IMAGE_CROP_FIELD].save()

    def saveProject(self):
        if not self.projectSettings.projectName:
            return
        try:
            self.projectSettings.save()
            for image in self.images.values():
                image.save()
        except Exception as err:
            logger.error(err)
            self.ui.errorMsg(values.saveProjectErrorMessage)

    def setSettings(self):
        self.setSettingsWidgetsValues()
        dialog = self.ui.settingsDialog
        if dialog.exec_():
            self.getSettingsWidgetsValues()

    def getSettingsWidgetsValues(self):
        ui = self.ui.settingsDialog.ui
        se = self.projectSettings

        se.resolution = ui.resolutionSpinBox.value()
        se.runSegmentVeg = ui.runSegmentVegCheckBox.isChecked()
        se.runDetectRows = ui.runDetectRowsCheckBox.isChecked()
        se.runMapVeg = ui.runMapVegCheckBox.isChecked()
        se.runMapWeeds = ui.runMapWeedsCheckBox.isChecked()
        se.segmentVegThr = ui.segmentVegThrSpinBox.value()
        se.rowsSeparation = ui.rowsSeparationSpinBox.value()
        se.roiAutoDetect = ui.roiAutoDetectCheckBox.isChecked()
        se.dirAutoDetect = ui.dirAutoDetectCheckBox.isChecked()
        se.rowsDirWindowWidth = ui.rowsDirWindowWidthSpinBox.value()
        se.rowsDirWindowHeight = ui.rowsDirWindowHeightSpinBox.value()
        se.rowsDetectMaxExtent = ui.rowsDetectMaxExtentSpinBox.value()
        se.rowsDetectExtentThr = ui.rowsDetectExtentThrSpinBox.value()
        se.rowsDetectLinkThr = ui.rowsDetectLinkThrSpinBox.value()
        se.rowsDetectFusionThr = ui.rowsDetectFusionThrSpinBox.value()
        se.mapsCellWidth = ui.mapsCellWidthSpinBox.value()
        se.mapsCellHeight = ui.mapsCellHeightSpinBox.value()
        se.mapsColormap = ui.mapsColormapComboBox.currentData()

        c = ui.roiLineColorButton.color()
        se.roiColor = (c.red(), c.green(), c.blue())

        c = ui.rowsDirLineColorButton.color()
        se.rowsDirColor = (c.red(), c.green(), c.blue())

        c = ui.rowsRidgesColorButton.color()
        se.rowsRidgesColor = (c.red(), c.green(), c.blue())

        c = ui.rowsFurrowsColorButton.color()
        se.rowsFurrowsColor = (c.red(), c.green(), c.blue())

    def setSettingsWidgetsValues(self):
        ui = self.ui.settingsDialog.ui
        se = self.projectSettings

        ui.resolutionSpinBox.setValue(se.resolution)
        ui.runSegmentVegCheckBox.setChecked(se.runSegmentVeg)
        ui.runDetectRowsCheckBox.setChecked(se.runDetectRows)
        ui.runMapVegCheckBox.setChecked(se.runMapVeg)
        ui.runMapWeedsCheckBox.setChecked(se.runMapWeeds)
        ui.segmentVegThrSpinBox.setValue(se.segmentVegThr)
        ui.rowsSeparationSpinBox.setValue(se.rowsSeparation)
        ui.roiAutoDetectCheckBox.setChecked(se.roiAutoDetect)
        ui.dirAutoDetectCheckBox.setChecked(se.dirAutoDetect)
        ui.rowsDirWindowWidthSpinBox.setValue(se.rowsDirWindowWidth)
        ui.rowsDirWindowHeightSpinBox.setValue(se.rowsDirWindowHeight)
        ui.rowsDetectMaxExtentSpinBox.setValue(se.rowsDetectMaxExtent)
        ui.rowsDetectExtentThrSpinBox.setValue(se.rowsDetectExtentThr)
        ui.rowsDetectLinkThrSpinBox.setValue(se.rowsDetectLinkThr)
        ui.rowsDetectFusionThrSpinBox.setValue(se.rowsDetectFusionThr)
        ui.mapsCellWidthSpinBox.setValue(se.mapsCellWidth)
        ui.mapsCellHeightSpinBox.setValue(se.mapsCellHeight)
        ui.mapsColormapComboBox.currentData(se.mapsColormap)

        r, g, b = se.roiColor
        ui.roiLineColorButton.setColor(QColor(r, g, b))

        r, g, b = se.rowsDirColor
        ui.rowsDirLineColorButton.setColor(QColor(r, g, b))

        r, g, b = se.rowsRidgesColor
        ui.rowsRidgesColorButton.setColor(QColor(r, g, b))

        r, g, b = se.rowsFurrowsColor
        ui.rowsFurrowsColorButton.setColor(QColor(r, g, b))

        ui.mapsColormapComboBox.clear()
        for value, name in COLORMAPS.items():
            ui.mapsColormapComboBox.addItem(name, value)
        if se.mapsColormap in COLORMAPS:
            ui.mapsColormapComboBox.setCurrentText(COLORMAPS[se.mapsColormap])

    def buildCropMaps(self):
        poly = self.ui.imageView.canvas.getShape(SHAPE_ROI_POLY)
        line = self.ui.imageView.canvas.getShape(SHAPE_ROWS_DIR)
        if poly is not None:
            self.projectSettings.roiPolygon = poly[0].points
        if line is not None:
            points = line[0].points
            self.projectSettings.rowsDirection = atan2(
                points[1][1] - points[0][1],
                points[1][0] - points[0][0]
            )

        self.run()
        self.updateImageList()
        # else:
        #     buttons = QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel
        #     ret = self.ui.warnMsg(
        #         values.strings["no_orthophoto_dialog_msg"],
        #         buttons
        #     )

    def selectRoiPoly(self):
        self.ui.imageView.canvas.deleteShape(SHAPE_ROI_POLY)
        self.ui.imageView.canvas.setToolDrawPolygon(
            name=SHAPE_ROI_POLY,
            lineWidth=self.projectSettings.drawLineWidth,
            lineColor=self.projectSettings.roiColor
        )

    def setCropRowsDir(self):
        self.ui.imageView.canvas.deleteShape(SHAPE_ROWS_DIR)
        self.ui.imageView.canvas.setToolDrawLine(
            name=SHAPE_ROWS_DIR,
            lineWidth=self.projectSettings.drawLineWidth,
            lineColor=self.projectSettings.rowsDirColor
        )

    def imageInfoTool(self):
        if self.ui.imageInfoToolAct.isChecked():
            self.ui.imageView.canvas.setToolInfo()
        else:
            self.ui.imageView.canvas.setToolPan()

    def imageSelected(self):
        listWidget = self.ui.imageListWidget
        item = listWidget.currentItem()
        name = item.data(0)
        self.updateShownImage(name)

    def updateShownImage(self, name: str):
        self.ui.imageView.showImage(self.images[name])
        self.projectSettings.shownImageName = name
        for name, visible in self.projectSettings.shapesVisible.items():
            self.ui.imageView.canvas.setShapeVisible(name, visible)

    def setShapeVisible(self):
        action: QAction = self.sender()
        if action:
            name = action.data()
            if name in SHAPES:
                checked = action.isChecked()
                self.projectSettings.shapesVisible[name] = checked
                self.ui.imageView.canvas.setShapeVisible(name, checked)

    def aboutAction(self):
        QtWidgets.QMessageBox.about(
            self,
            values.aboutDialogTitle,
            values.aboutDialogMessage
        )

    def connectActions(self):

        self.ui.newProjectAct.triggered.connect(self.newProject)
        self.ui.openProjectAct.triggered.connect(self.openProject)
        self.ui.saveProjectAct.triggered.connect(self.saveProject)
        self.ui.setSettingsAct.triggered.connect(self.setSettings)
        self.ui.buildCropMapsAct.triggered.connect(self.buildCropMaps)
        self.ui.selectRoiPolyAct.triggered.connect(self.selectRoiPoly)
        self.ui.setCropRowsDirAct.triggered.connect(self.setCropRowsDir)
        self.ui.imageInfoToolAct.toggled.connect(self.imageInfoTool)

        # noinspection PyTypeChecker
        self.ui.exitAct.triggered.connect(self.close)
        self.ui.zoomInAct.triggered.connect(self.ui.imageView.zoomIn)
        self.ui.zoomOutAct.triggered.connect(self.ui.imageView.zoomOut)

        self.ui.aboutAct.triggered.connect(self.aboutAction)

    def run(self):

        se = self.projectSettings

        cropField = self.images[IMAGE_CROP_FIELD]
        normField = self.images[IMAGE_NORM_FIELD]
        vegMask = self.images[IMAGE_VEG_MASK]
        vegDensity = self.images[IMAGE_VEG_DENSITY]
        weedMask = self.images[IMAGE_WEED_MASK]
        weedDensity = self.images[IMAGE_WEED_DENSITY]
        roiMask = self.images[IMAGE_ROI_MASK]

        if se.runSegmentVeg:
            vegMask.image = mcrops.veget.segment_vegetation(
                cropField.image, threshold=se.segmentVegThr
            )
            vegMask.transform = cropField.transform
            vegMask.save()

        if se.runDetectRows:

            (h, w) = vegMask.image.shape
            roiPoly = np.int32([[0, 0], [w, 0], [w, h], [0, h]])

            try:
                if se.roiPolygon is not None:
                    roiPoly = np.array(se.roiPolygon, np.int32)
                elif se.roiAutoDetect:
                    roiPoly = mcrops.veget.detect_roi(
                        vegMask.image,
                        row_sep=se.rowsSeparation,
                        resolution=se.resolution
                    )
                roiPoly = roiPoly.reshape((-1, 1, 2))
                roiPoly = mcrops.utils.trim_poly(roiPoly, (0, 0, w, h))
                cropField.shapes[SHAPE_ROI_POLY] = [Shape(
                    name=SHAPE_ROI_POLY,
                    points=roiPoly.reshape((-1, 2)).tolist(),
                    form=Shape.POLYGON,
                    lineColor=se.roiColor,
                    lineWidth=se.drawLineWidth,
                    visible=se.shapesVisible.get(SHAPE_ROI_POLY, True)
                )]
            except Exception as err:
                logger.error(err)

            rowsDir = se.rowsDirection
            if se.dirAutoDetect:
                rowsDir = mcrops.rows.detect_direction(
                    vegMask.image,
                    resolution=se.resolution,
                    window_shape=(se.rowsDirWindowHeight, se.rowsDirWindowWidth)
                )

                # Draw an arrow indicating the direction of the crop rows
                pt1 = (int(w / 2), int(h / 2))
                length = min(w / 2, h / 2)
                dx = int(math.cos(rowsDir) * length)
                dy = int(math.sin(rowsDir) * length)
                pt2 = (
                    pt1[0] + min(max(0, dx), w - 1),
                    pt1[1] + min(max(0, dy), h - 1)
                )
                cropField.shapes[SHAPE_ROWS_DIR] = [Shape(
                    name=SHAPE_ROWS_DIR,
                    points=[pt1, pt2],
                    form=Shape.LINE,
                    lineColor=se.rowsDirColor,
                    lineWidth=se.drawLineWidth,
                    visible=se.shapesVisible.get(SHAPE_ROWS_DIR, True)
                )]

            vegMask.image, _, _ = mcrops.veget.norm_image(
                vegMask.image,
                roi_poly=roiPoly,
                rows_direction=rowsDir,
                roi_trim=se.roiTrim,
                is_mask=True
            )

            normField.image, roiPoly, transform = mcrops.veget.norm_image(
                cropField.image,
                roi_poly=roiPoly,
                rows_direction=rowsDir,
                roi_trim=se.roiTrim
            )
            transform = transform.tolist()

            if cropField.transform is not None:
                # noinspection PyTypeChecker
                transform = np.dot(cropField.transform, transform).tolist()

            roiMask.image = mcrops.utils.poly_mask(
                roiPoly, vegMask.image.shape
            )

            normField.transform = transform
            vegMask.transform = transform
            roiMask.transform = transform

            rowsRidges, rowsFurrows = mcrops.rows.detect_rows(
                veg_mask=vegMask.image,
                roi_mask=roiMask.image,
                row_sep=se.rowsSeparation,
                extent_max=se.rowsDetectMaxExtent,
                extent_thr=se.rowsDetectExtentThr,
                fusion_thr=se.rowsDetectFusionThr,
                link_thr=se.rowsDetectLinkThr,
                resolution=se.resolution
            )

            rowsRidges[:, :, [1, 0]] = rowsRidges[:, :, [0, 1]]
            rowsFurrows[:, :, [1, 0]] = rowsFurrows[:, :, [0, 1]]

            shapes = []
            visible = se.shapesVisible.get(SHAPE_ROWS_RIDGES, True)
            # noinspection PyTypeChecker
            for points in rowsRidges.tolist():
                shapes.append(
                    Shape(
                        name=SHAPE_ROWS_RIDGES,
                        points=points,
                        form=Shape.POLYLINE,
                        lineColor=se.rowsRidgesColor,
                        lineWidth=se.drawLineWidth,
                        visible=visible
                    )
                )
            normField.shapes[SHAPE_ROWS_RIDGES] = shapes
            vegMask.shapes[SHAPE_ROWS_RIDGES] = shapes

            shapes = []
            visible = se.shapesVisible.get(SHAPE_ROWS_FURROWS, True)
            # noinspection PyTypeChecker
            for points in rowsFurrows.tolist():
                shapes.append(
                    Shape(
                        name=SHAPE_ROWS_FURROWS,
                        points=points,
                        form=Shape.POLYLINE,
                        lineColor=se.rowsFurrowsColor,
                        lineWidth=se.drawLineWidth,
                        visible=visible
                    )
                )
            normField.shapes[SHAPE_ROWS_FURROWS] = shapes
            vegMask.shapes[SHAPE_ROWS_FURROWS] = shapes

            cropField.save()
            normField.save()
            vegMask.save()
            roiMask.save()

        if se.runMapVeg:
            densityMap = mcrops.veget.mask_density(
                mask=vegMask.image,
                roi_mask=roiMask.image,
                cell_size=(se.mapsCellWidth, se.mapsCellHeight),
                resolution=se.resolution
            )

            vegDensity.image = mcrops.utils.array_image(
                values=densityMap,
                colormap=se.mapsColormap,
                full_scale=True
            )
            vegDensity.transform = vegMask.transform
            colormap = mcrops.utils.array_image(
                values=np.arange(0, 255, dtype=np.uint8),
                colormap=se.mapsColormap,
                full_scale=True
            ).reshape((-1, 3))
            # Change BGR format to RGB
            colormap[:, [2, 0]] = colormap[:, [0, 2]]
            vegDensity.colormap = colormap.tolist()
            # noinspection PyArgumentList
            vegDensity.maprange = [
                float(densityMap.min()), float(densityMap.max())
            ]
            vegDensity.save()

        if se.runMapWeeds:

            rowsRidges = []
            rowsShapes = vegMask.shapes[SHAPE_ROWS_RIDGES]
            for shape in rowsShapes:
                rowsRidges.append(shape.points)

            weedMask.image = mcrops.weeds.segment_weeds(
                image=normField.image,
                veg_mask=vegMask.image,
                crop_rows=np.array(rowsRidges)
            )

            densityMap = mcrops.veget.mask_density(
                mask=weedMask.image,
                roi_mask=roiMask.image,
                cell_size=(se.mapsCellWidth, se.mapsCellHeight),
                resolution=se.resolution
            )

            weedDensity.image = mcrops.utils.array_image(
                values=densityMap,
                colormap=se.mapsColormap,
                full_scale=True
            )
            weedDensity.transform = vegMask.transform
            colormap = mcrops.utils.array_image(
                values=np.arange(0, 255, dtype=np.uint8),
                colormap=se.mapsColormap,
                full_scale=True
            ).reshape((-1, 3)).tolist()
            # Change BGR format to RGB
            colormap[:, [2, 0]] = colormap[:, [0, 2]]
            weedDensity.colormap = colormap.tolist()
            # noinspection PyArgumentList
            weedDensity.maprange = [
                float(densityMap.min()), float(densityMap.max())
            ]
            weedDensity.save()

        shownImageName = self.projectSettings.shownImageName
        if shownImageName in self.images:
            self.ui.imageView.showImage(self.images[shownImageName])


if __name__ == '__main__':

    import sys

    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
