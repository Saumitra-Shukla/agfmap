# -*- coding: utf-8 -*-
import pickle
from os import path, mkdir
from typing import List, Tuple, Dict
import cv2 as cv


DATA_DIR_NAME = '.data'

APP_SETTINGS_FILE_NAME: str = 'settings'

MAX_RECENT_FILES: int = 10

TOOLBAR_ICON_SIZE = 32

IMAGE_EXTENSIONS: Tuple[str, ...] = (
    ".jpg",
    ".jpeg",
    ".png",
    ".tiff",
    ".bmp",
    ".JPG",
    ".JPEG",
    ".PNG",
    ".TIFF",
    ".BMP"
)

PROJECT_FILE_EXT = '.agf'

COLORMAPS = {
    cv.COLORMAP_HOT: 'Hot',
    cv.COLORMAP_HSV: 'HSV',
    cv.COLORMAP_JET: 'Jet',
    cv.COLORMAP_COOL: 'Cool',
    cv.COLORMAP_AUTUMN: 'Autumn',
}

currDir = path.dirname(path.abspath(__file__))
rootPath = path.join(currDir, DATA_DIR_NAME)

if not path.exists(rootPath) or not path.isdir(rootPath):
    mkdir(rootPath)

APP_SETTINGS_PATH = path.join(rootPath, APP_SETTINGS_FILE_NAME)


class AppSettings:
    def __init__(self):
        self.recentFiles: List[str] = []
        self.mainWindowPos: Tuple[int, int] = (0, 0)
        self.mainWindowSize: Tuple[int, int] = (640, 480)
        self.openFilesDirPath: str = ''
        self.lastProjectPath: str = ''

    def save(self):
        with open(APP_SETTINGS_PATH, 'wb') as appFile:
            pickle.dump(self, appFile)

    @staticmethod
    def load() -> 'AppSettings':
        with open(APP_SETTINGS_PATH, 'rb') as appFile:
            return pickle.load(appFile)


class ProjectSettings(object):
    # noinspection PyTypeChecker
    def __init__(self):
        self.projectName = ''
        self.projectPath: str = rootPath
        self.cropFieldImagePath: str = ''
        self.resolution: float = 20
        self.runSegmentVeg: bool = True
        self.runDetectRows: bool = True
        self.runMapVeg: bool = True
        self.runMapWeeds: bool = True
        self.segmentVegThr: float = 1.0
        self.rowsSeparation: float = 0.7
        self.roiAutoDetect: bool = True
        self.roiPolygon: list = None
        self.roiTrim: bool = True
        self.dirAutoDetect: bool = True
        self.rowsDirection: float = 0
        self.rowsDirWindowWidth: float = 30
        self.rowsDirWindowHeight: float = 20
        self.rowsDetectExtentThr: float = 0.1
        self.rowsDetectMaxExtent: float = 5
        self.rowsDetectFusionThr: float = 0.1
        self.rowsDetectLinkThr: int = 3
        self.mapsCellWidth: float = 5
        self.mapsCellHeight: float = 5
        self.mapsColormap: int = cv.COLORMAP_JET
        self.shownImageName: str = ''
        self.shapesVisible: Dict[str, bool] = {}
        self.roiColor: Tuple[int, int, int] = (255, 0, 0)
        self.rowsDirColor: Tuple[int, int, int] = (0, 255, 0)
        self.rowsRidgesColor: Tuple[int, int, int] = (255, 0, 255)
        self.rowsFurrowsColor: Tuple[int, int, int] = (255, 255, 0)
        self.drawLineWidth: int = 2

    @property
    def projectSettingsPath(self) -> str:
        return path.join(self.projectPath, self.projectName + PROJECT_FILE_EXT)

    def save(self):
        with open(self.projectSettingsPath, 'wb') as projectFile:
            pickle.dump(self, projectFile)

    @staticmethod
    def load(projectPath) -> 'ProjectSettings':
        with open(projectPath, 'rb') as projectFile:
            return pickle.load(projectFile)
