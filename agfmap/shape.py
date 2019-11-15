from typing import List, Dict
import json

import cv2 as cv
import numpy as np
from PyQt5 import QtCore
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import (
    QImage,
    QPainter,
    QPolygon,
    QPen,
    QColor
)

import utils
from applog import logger


class Shape:

    RECTANGLE = 'rectangle'
    ELLIPSE = 'ellipse'
    POLYGON = 'polygon'
    POLYLINE = 'polyline'
    LINE = 'line'

    # noinspection PyTypeChecker
    def __init__(
        self,
        form: str = '',
        name: str = '',
        points: list = None,
        lineColor: tuple = (0, 0, 0),
        lineWidth: int = 2,
        visible: bool = True,
        drawing: bool = False
    ):

        self.name: str = name
        self.form: str = form
        self.points: list = [] if points is None else points
        self.lineColor: tuple = lineColor
        self.lineWidth: int = lineWidth
        self._pen = None
        self._brush = None
        self._initPaint()
        self.drawing: bool = drawing
        self.visible: bool = visible
        self.pos: list = None

    @property
    def data(self) -> dict:
        return {
            'name': self.name,
            'shape': self.form,
            'points': self.points,
            'lineColor': self.lineColor,
            'lineWidth': self.lineWidth,
            'visible': self.visible,
            'drawing': self.drawing
        }

    @data.setter
    def data(self, data: dict):
        self.name = data.get('name', self.name)
        self.form = data.get('shape', self.form)
        self.points = data.get('points', self.points)
        self.lineColor = data.get('lineColor', self.lineColor)
        self.lineWidth = data.get('lineWidth', self.lineWidth)
        self.visible = data.get('visible', self.visible)
        self.drawing = data.get('drawing', self.drawing)
        self._initPaint()

    def _initPaint(self):
        r, g, b = self.lineColor
        self._pen: QPen = QPen(QColor(r, g, b), self.lineWidth)
        self._pen.setCosmetic(True)
        self._brush = QtCore.Qt.NoBrush

    def draw(self, painter: QPainter):
        if len(self.points) > 1:
            painter.setPen(self._pen)
            painter.setBrush(self._brush)
            if self.pos is not None:
                nPoints = len(self.points)
                points = []
                for i in range(nPoints):
                    points.append([
                        self.points[i][0] + self.pos[0],
                        self.points[i][1] + self.pos[1]
                    ])
            else:
                points = self.points
            if self.form == Shape.RECTANGLE:
                x1, y1 = points[0]
                x2, y2 = points[1]
                painter.drawRect(x1, y1, x2 - x1, y2 - y1)
            elif self.form == Shape.ELLIPSE:
                x1, y1 = points[0]
                x2, y2 = points[1]
                painter.drawEllipse(x1, y1, x2 - x1, y2 - y1)
            elif self.form == Shape.POLYGON:
                poly = QPolygon()
                for point in points:
                    poly << QPoint(point[0], point[1])
                if not self.drawing:
                    painter.drawPolygon(poly)
                else:
                    painter.drawPolyline(poly)
            elif self.form == Shape.POLYLINE:
                poly = QPolygon()
                for point in points:
                    poly << QPoint(point[0], point[1])
                painter.drawPolyline(poly)
            elif self.form == Shape.LINE:
                poly = QPolygon()
                for point in points[0:2]:
                    poly << QPoint(point[0], point[1])
                painter.drawPolyline(poly)


class ImageWrapper:
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

            if self.image.ndim == 3 and self.image.shape[2] == 4:
                alpha = self.image[:, :, 3]
                self.image = self.image[:, :, 0:3]
                self.image[alpha < 200] = 0

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