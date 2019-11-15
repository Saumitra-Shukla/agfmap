from typing import List

from PyQt5 import QtCore
from PyQt5.QtGui import QImage, qRgb, QPainter
from PyQt5.QtWidgets import QSizePolicy, QLabel


class ColorScale(QLabel):

    # noinspection PyTypeChecker
    def __init__(self, parent, colormap=None, limits=None):
        super(ColorScale, self).__init__(parent)

        self.labelMargin: float = 5
        self.nLabels: int = 4
        self.barWidth: float = 50
        self.labels: List[str] = []
        self.labelPos: List[float] = []
        self.labelOffset: List[float] = []
        self.labelMaxWidth: float = 0
        self.qImage: QImage = None
        self.widthHint: int = 0

        self.setColorMap(colormap, limits)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

    def setColorMap(self, colormap=None, limits=None):

        if colormap is None:
            colormap = [[0, 0, 0], [255, 255, 255]]

        if limits is None:
            limits = [0.0, 1.0]

        nColors = len(colormap)

        step = float(limits[1] - limits[0])/(self.nLabels - 1)
        labelValues = [i*step for i in range(self.nLabels)]
        maxVal = abs(max(labelValues))
        if maxVal > 0.1:
            self.labels = ['%.2f' % value for value in labelValues]
        else:
            self.labels = ['%.2E' % value for value in labelValues]

        self.labelPos = [float(i)/(self.nLabels - 1) for i in range(self.nLabels)]

        fm = self.fontMetrics()
        flag = QtCore.Qt.TextSingleLine
        sizes = [fm.size(flag, label) for label in self.labels]
        self.labelOffset = [0.3 * size.height() for size in sizes]
        self.labelOffset[0] /= 0.3
        self.labelOffset[len(self.labelOffset) - 1] = 0
        self.labelMaxWidth = max([size.width() for size in sizes])

        self.qImage = QImage(1, nColors, QImage.Format_RGB32)
        for i in range(nColors):
            color = colormap[i]
            self.qImage.setPixel(0, i, qRgb(color[0], color[1], color[2]))

        margin = max(self.labelOffset)
        self.setContentsMargins(margin, margin, margin, margin)
        self.widthHint = self.barWidth + self.labelMaxWidth + self.labelMargin + 2*margin + 1
        self.updateGeometry()
        self.update()

    def sizeHint(self):
        return QtCore.QSize(self.widthHint, self.parentWidget().height())

    def paintEvent(self, event):

        rect = self.contentsRect()
        x, y = rect.x(), rect.y()
        w, h = rect.width(), rect.height()
        w = w - self.labelMargin - self.labelMaxWidth - 1

        painter = QPainter(self)
        painter.setPen(QtCore.Qt.black)

        painter.drawImage(QtCore.QRect(x, y, w, h), self.qImage)

        labelXPos = x + w + self.labelMargin
        for i in range(self.nLabels):
            labelYPos = y + h*self.labelPos[i] + self.labelOffset[i]
            painter.drawText(labelXPos, labelYPos, self.labels[i])
