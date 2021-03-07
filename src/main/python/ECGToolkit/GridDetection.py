"""
Common.py
Created March 2, 2021

Converts a color image to binary mask of the grid.
"""


from . import Visualization
from .Common import *
from .Vision import *
from .Visualization import Color, displayImages


def extractGridUsingKernels(colorImage):
    binaryImage = binarize(greyscale(colorImage), 240)

    opened = openImage(binaryImage)
    opened = openImage(opened)

    # Subtract the opened image from the binary image
    subtracted = cv2.subtract(binaryImage, opened)

    final = cv2.erode(
        subtracted,
        cv2.getStructuringElement(cv2.MORPH_CROSS, (2,2))
    )

    displayImages([
        (binaryImage, Color.greyscale, "Binary"),
        (opened, Color.greyscale, "Opened"),
        (subtracted, Color.greyscale, "Subtracted"),
        (final, Color.greyscale, "Final")
    ])

    return final
