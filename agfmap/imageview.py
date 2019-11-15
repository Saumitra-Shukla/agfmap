import json
from typing import List, Dict

import cv2 as cv
import numpy as np
from PyQt5 import QtCore
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import (
    QImage,
    QPainter,
    QPalette,
    qRed,
    qGreen,
    qBlue,
    QWheelEvent,
    QShowEvent,
    QKeyEvent,
    QCursor,
    QPixmap
)
from PyQt5.QtWidgets import (
    QSizePolicy,
    QLabel,
    QFrame,
    QHBoxLayout
)

import utils
import values
from applog import logger
from scale import ColorScale
from shape import Shape


JOIN_THR = 20


class Layer:
    # noinspection PyTypeChecker
    def __init__(self, name: str, filePath: str = '', flags=None):

        self.name: str = name
        self.filePath: str = filePath
        self.shapes: Dict[str, List[Shape]] = {}
        self.position: list = [0, 0]
        self.scale: float = 1.0
        self.colormap: list = None
        self.maprange: list = [0, 1]
        self.transform: list = None
        self.flags = flags
        self.image: np.ndarray = None

        self.read()

    def read(self):
        if utils.fileExists(self.filePath):
            self.image: np.ndarray = cv.imread(self.filePath, flags=self.flags)
            if self.image is None:
                return

            try:
                with open(utils.swapExt(self.filePath, '.im')) as fp:
                    data: dict = json.load(fp)
                    self.name = data.get('name', self.name)
                    self.position = data.get('position', self.position)
                    self.scale = data.get('scale', self.scale)
                    self.colormap = data.get('colormap', self.colormap)
                    self.maprange = data.get('maprange', self.maprange)
                    self.transform = data.get('transform', self.transform)
                    self.flags = data.get('flags', self.flags)
                    shapesData = data.get('shapes', None)
                    if shapesData is not None:
                        for name, shapeSet in shapesData.items():
                            self.shapes[name] = []
                            for shapeData in shapeSet:
                                shape = Shape()
                                shape.data = shapeData
                                self.shapes[name].append(shape)

            except OSError:
                pass
            except Exception as err:
                logger.error(err)

    def save(self):
        if self.filePath and self.image is not None:
            cv.imwrite(self.filePath, self.image)
            try:
                dataPath = utils.swapExt(self.filePath, '.im')
                with open(dataPath, 'wt') as fp:
                    shapes = {}
                    for name, shapeSet in self.shapes.items():
                        shapes[name] = [shape.data for shape in shapeSet]
                    data = {
                        'name': self.name,
                        'shapes': shapes,
                        'position': self.position,
                        'scale': self.scale,
                        'colormap': self.colormap,
                        'maprange': self.maprange,
                        'transform': self.transform,
                        'flags': self.flags,
                    }
                    jsonData = json.dumps(data)
                    fp.write(jsonData)
            except Exception as err:
                logger.error(err)

    @property
    def qImage(self):
        if not self.isEmpty:
            return QImage(self.filePath)
        return None

    @property
    def isEmpty(self):
        return not utils.fileExists(self.filePath)

    def getLatLon(self, pos):
        x, y = pos.x(), pos.y()
        M = self.transform
        lon = M[0][0]*x + M[0][1]*y + M[0][2]
        lat = M[1][0]*x + M[1][1]*y + M[1][2]
        return lat, lon

    def getShape(self, name):
        if name in self.shapes:
            return self.shapes[name]
        return None


class Canvas(QLabel):
    # noinspection PyTypeChecker
    def __init__(self, parent):
        super(Canvas, self).__init__(parent)

        self.activeTool = None
        self.layer: Layer = None
        self.qImage: QImage = None
        self.currentShape: Shape = None
        self.lastDragPos: QPoint = QtCore.QPoint()
        self.sizeLimits: tuple = (128, 8192)
        self.setToolPan()
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setSizePolicy(sizePolicy)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.infoLabel: QLabel = QLabel(self.parentWidget())
        self.infoLabel.setBackgroundRole(QPalette.ToolTipBase)
        self.infoLabel.setAutoFillBackground(True)
        self.infoLabel.setMargin(5)
        self.infoLabel.setVisible(False)
        self.cursorClose = QCursor(QPixmap(values.cursorCloseImage))

    def sizeHint(self):
        if self.layer is not None and self.qImage is not None:
            return self.layer.scale * self.qImage.size()
        return QtCore.QSize(0, 0)

    def reset(self):
        if self.layer is not None:
            self.layer.scale = None
            self.layer.position = None

    def setImage(self, imageWrapper):

        self.layer = imageWrapper
        self.qImage = imageWrapper.qImage

    def updateView(self):
        if self.layer is not None:
            if self.layer.scale == 1.0 and self.layer.position == [0, 0]:
                self.adjustToParentSize()
            else:
                self.resize(self.layer.scale * self.qImage.size())
                self.move(self.layer.position[0], self.layer.position[1])
            self.update()

    def scaleImage(self, factor):

        if self.layer is not None:
            scale = factor * self.layer.scale
            size = scale * self.qImage.size()
            sizeMax = max(size.width(), size.height())
            sizeMin = max(size.width(), size.height())
            if sizeMin > self.sizeLimits[0] and sizeMax < self.sizeLimits[1]:
                offset = self.geometry().center()
                self.resize(size)
                pos = offset - self.rect().center()
                self.move(pos)
                self.layer.scale = scale
                self.layer.position = [pos.x(), pos.y()]

    def adjustToParentSize(self):
        if self.layer is not None:
            w, h = self.qImage.width(), self.qImage.height()
            W, H = self.parentWidget().width(), self.parentWidget().height()
            self.layer.scale = min(W / float(w), H / float(h))
            self.resize(self.layer.scale * self.qImage.size())
            self.center()

    def center(self):

        offset = (self.parentWidget().size() - self.size())/2
        self.layer.position = [offset.width(), offset.height()]
        self.move(offset.width(), offset.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.layer is not None:
            painter.resetTransform()
            painter.drawImage(self.rect(), self.qImage)
            self.drawShapes(painter)
        else:
            painter.eraseRect(self.rect())

    def drawShapes(self, painter):
        if len(self.layer.shapes) > 0:
            painter.resetTransform()
            painter.scale(self.layer.scale, self.layer.scale)
            for shapes in self.layer.shapes.values():
                for shape in shapes:
                    if shape.visible:
                        shape.draw(painter)

    def mousePressEvent(self, event):
        if self.layer is not None:
            if event.buttons() == QtCore.Qt.LeftButton:
                if self.activeTool == self.Tools.PAN:
                    self.lastDragPos = QtCore.QPoint(event.globalPos())
                    self.setCursor(QtCore.Qt.ClosedHandCursor)
                elif self.activeTool == self.Tools.DRAW:
                    shape = self.currentShape
                    if shape is not None and (
                        shape.form == Shape.POLYGON or
                        shape.form == Shape.POLYLINE or
                        shape.form == Shape.LINE
                    ):
                        if shape.form == Shape.LINE and len(shape.points) == 2:
                            self.endDrawing()
                            return
                        point = event.pos() / self.layer.scale
                        if shape.form == shape.POLYGON and len(shape.points) >= 4:
                            dx = abs(point.x() - shape.points[0][0])
                            dy = abs(point.y() - shape.points[0][1])
                            if (dx + dy) < JOIN_THR:
                                index = len(shape.points) - 1
                                del shape.points[index]
                                self.endDrawing()
                                return
                        shape.points.append([point.x(), point.y()])
                        shape.points.append([point.x(), point.y()])
                    self.update()
                elif self.activeTool == self.Tools.INFO:
                    text = self.getInfo(event.pos())
                    tpos = self.mapTo(self.parentWidget(), event.pos())
                    self.infoLabel.move(tpos)
                    self.infoLabel.setText(text)
                    self.infoLabel.setVisible(True)
                    self.infoLabel.adjustSize()

    def mouseMoveEvent(self, event):
        if self.layer is not None:
            leftButtonPressed = event.buttons() == QtCore.Qt.LeftButton
            if self.activeTool == self.Tools.PAN and leftButtonPressed:
                newPos = self.pos() + event.globalPos() - self.lastDragPos
                self.move(newPos)
                self.layer.position = [newPos.x(), newPos.y()]
                self.lastDragPos = QtCore.QPoint(event.globalPos())
            elif self.activeTool == self.Tools.DRAW:
                shape = self.currentShape
                if shape is not None and (
                    shape.form == Shape.POLYGON or
                    shape.form == Shape.POLYLINE or
                    shape.form == Shape.LINE
                ) and len(shape.points):
                    point = event.pos() / self.layer.scale
                    index = len(shape.points) - 1
                    shape.points[index] = [point.x(), point.y()]
                    if shape.form == shape.POLYGON and len(shape.points) >= 4:
                        dx = abs(point.x() - shape.points[0][0])
                        dy = abs(point.y() - shape.points[0][1])
                        if (dx + dy) < JOIN_THR:
                            self.setCursor(self.cursorClose)
                        else:
                            self.setCursor(QtCore.Qt.CrossCursor)
                    self.update()

    def mouseReleaseEvent(self, event):
        if self.layer is not None:
            if self.activeTool == self.Tools.PAN:
                self.setCursor(QtCore.Qt.OpenHandCursor)

    def mouseDoubleClickEvent(self, event):
        self.parentWidget().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if (
            event.key() == QtCore.Qt.Key_Escape and
            self.activeTool == self.Tools.DRAW
        ):
            self.endDrawing()
            if (
                self.currentShape is not None and
                self.currentShape.name in self.layer.shapes
            ):
                del self.layer.shapes[self.currentShape.name]

    def setToolPan(self):
        self.unsetTool()
        self.activeTool = self.Tools.PAN
        self.setMouseTracking(False)
        self.setCursor(QtCore.Qt.OpenHandCursor)

    def setToolInfo(self):
        if self.layer is None:
            return
        self.unsetTool()
        self.activeTool = self.Tools.INFO
        self.setMouseTracking(False)
        self.setCursor(QtCore.Qt.ArrowCursor)

    def setToolSelect(self):
        self.activeTool = self.Tools.SELECT
        self.setMouseTracking(False)
        self.setCursor(QtCore.Qt.Cursor)

    def setToolDrawPolygon(
        self,
        name: str = '',
        lineColor: tuple = (0, 0, 0),
        lineWidth: int = 2
    ):
        if self.layer is None:
            return
        self.unsetTool()
        if not name:
            name = str(len(self.layer.shapes) + 1)
        shape = Shape(
            Shape.POLYGON,
            name,
            lineColor=lineColor,
            lineWidth=lineWidth
        )
        self.currentShape = shape
        self.layer.shapes[name] = [shape]
        self.setToolDraw()
        return shape

    def setToolDrawLine(
        self,
        name: str = '',
        lineColor: tuple = (0, 0, 0),
        lineWidth: int = 2
    ):
        if self.layer is None:
            return
        self.unsetTool()
        if not name:
            name = str(len(self.layer.shapes) + 1)
        shape = Shape(
            Shape.LINE,
            name,
            lineColor=lineColor,
            lineWidth=lineWidth
        )
        self.currentShape = shape
        self.layer.shapes[name] = [shape]
        self.setToolDraw()
        return shape

    def setToolDraw(self):
        self.activeTool = self.Tools.DRAW
        self.currentShape.drawing = True
        self.setMouseTracking(True)
        self.setFocus()
        self.setCursor(QtCore.Qt.CrossCursor)

    def endDrawing(self):
        self.currentShape.drawing = False
        self.setToolPan()
        self.setMouseTracking(False)
        self.update()

    def getInfo(self, pos):
        info = ''
        if self.qImage is not None:
            pos /= self.layer.scale
            pixel = self.qImage.pixel(pos)
            r, g, b = qRed(pixel), qGreen(pixel), qBlue(pixel)
            info += f'RGB color: ({r}, {g}, {b})\n'
            info += f'Position: ({pos.x()}, {pos.y()})'
        return info

    def unsetTool(self):
        if self.activeTool == self.Tools.INFO:
            self.infoLabel.setVisible(False)
            self.update()
        if self.activeTool == self.Tools.DRAW and (
            self.currentShape is not None and
            self.currentShape.drawing and
            self.currentShape.name in self.layer.shapes
        ):
            del self.layer.shapes[self.currentShape.name]
            self.update()

    def deleteShape(self, name: str = None):
        if self.layer is not None:
            if name is None:
                self.layer.shapes.clear()
                self.update()
            elif name in self.layer.shapes:
                del self.layer.shapes[name]
                self.update()

    def setShapeVisible(self, name: str = None, visible: bool = True):
        if self.layer is not None:
            if name is None:
                for shapeSet in self.layer.shapes.values():
                    for shape in shapeSet:
                        shape.visible = visible
                self.update()
            elif name in self.layer.shapes:
                for shape in self.layer.shapes[name]:
                    shape.visible = visible
                self.update()

    def getShape(self, name):
        if self.layer is None:
            return None
        return self.layer.getShape(name)

    class Tools:
        PAN = 0
        DRAW = 1
        SHOT = 2
        SELECT = 4
        INFO = 5


class ImageView(QFrame):
    # noinspection PyTypeChecker
    def __init__(self, parent):
        super(ImageView, self).__init__(parent)

        self.zoomInScale = 1.25
        self.canvas = Canvas(self)
        self.canvas.resize(0, 0)
        self.setBackgroundRole(QPalette.Shadow)
        self.setFrameShadow(QFrame.Plain)
        self.setFrameShape(QFrame.StyledPanel)
        self.colorScale = ColorScale(self)

        # self.resize(self.parentWidget().size())

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.colorScale, 0, QtCore.Qt.AlignLeft)
        self.setLayout(mainLayout)

        self.colorScale.setVisible(False)

    def showImage(self, imageWrapper: Layer):
        if not imageWrapper.isEmpty:
            self.canvas.setImage(imageWrapper)
            if self.isVisible():
                self.canvas.updateView()

            if imageWrapper.colormap is not None:
                self.colorScale.setColorMap(imageWrapper.colormap, imageWrapper.maprange)
                self.colorScale.setVisible(True)
            else:
                self.colorScale.setVisible(False)

    def clear(self):
        self.canvas.image = None
        self.canvas.resize(0, 0)

    def showEvent(self, event: QShowEvent) -> None:
        self.canvas.updateView()
        super(ImageView, self).showEvent(event)

    def resizeEvent(self, event):
        self.canvas.updateView()
        super(ImageView, self).resizeEvent(event)
        
    def zoomIn(self):
        self.canvas.scaleImage(self.zoomInScale)

    def zoomOut(self):
        self.canvas.scaleImage(1.0 / self.zoomInScale)

    def mouseDoubleClickEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.canvas.adjustToParentSize()

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta()
        if delta is not None:
            self.canvas.scaleImage(
                pow(self.zoomInScale, delta.y()/120.0)
            )
