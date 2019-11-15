import errno
import os
import tempfile

import numpy as np


def isDirWritable(path):
    try:
        testfile = tempfile.TemporaryFile(dir = path)
        testfile.close()
    except OSError as e:
        if e.errno == errno.EACCES:
            return False
        e.filename = path
        raise
    return True


def dirExists(path):
    return os.path.exists(path) and os.path.isdir(path)


def fileExists(path):
    return os.path.exists(path) and os.path.isfile(path)


def isValidFileExtension(path, exts):
    (root, ext) = os.path.splitext(path)
    if ext.lower() in exts:
        return True
    return False


def isValidImage(img):
    if isinstance(img, np.ndarray) and img.dtype == np.uint8:
        if img.ndim == 2 or (img.ndim == 3 and img.shape[2] == 3):
            return True
    return False


def swapExt(filePath, newExt):
    return os.path.splitext(filePath)[0] + newExt
