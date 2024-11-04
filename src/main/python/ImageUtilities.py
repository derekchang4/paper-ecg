"""
ImageUtilities.py
Created November 9, 2020

-
"""
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from PyQt5 import QtGui
import scipy.stats as stats
import pdf2image as pdf2image


def readImage(path: Path) -> np.ndarray:
    if path.suffix == '.pdf':
        return _pdf2png(path)
    else:
        return cv2.imread(str(path.absolute()))

def opencvImageToPixmap(image):
    # SOURCE: https://stackoverflow.com/a/50800745/7737644 (Creative Commons - Credit, share-alike)

    height, width, channel = image.shape
    bytesPerLine = 3 * width

    pixmap = QtGui.QPixmap(
        QtGui.QImage(
            image.data,
            width,
            height,
            bytesPerLine,
            QtGui.QImage.Format_RGB888
        ).rgbSwapped()
    )

    return pixmap

def _pdf2png(pdfPath: Path) -> np.ndarray:
    # https://stackoverflow.com/questions/14134892/convert-image-from-pil-to-opencv-format 
    # Poppler must be in dependencies

    # Only convert first page
    dpi = 200   # Default is 200
    pdfPilImage = pdf2image.convert_from_path(str(pdfPath.absolute()), dpi)[0].convert('RGB')
    open_cv_image = np.array(pdfPilImage)
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    return open_cv_image
