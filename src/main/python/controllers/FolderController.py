from pathlib import Path
from controllers import MainController
from ecgdigitize.image import openImage
from itertools import chain


class FolderController:

    def __init__(self, mainController: MainController):
        self.mainController : MainController = mainController
        self.imageFiles : list[Path] = []
        self.currentImageIndex = -1

    def loadImagesFromFolder(self, directory: Path):
        '''Loads all of the files in a folder'''
        #directory = Path(self.mainController.openFolderBrowser("Select a Folder"))
        if directory == Path('.'):
            print("[Warning] No folder selected")
            return
        
        # Get the supported files in the folder
        self.imageFiles = list(sorted(chain(directory.glob('*.png'), directory.glob('*.jpg'), directory.glob('*.jpeg'), directory.glob('*.tif'), directory.glob('*.tiff'))))
        self.currentImageIndex = 0  # Starting from first image
        self.loadCurrentImage()     # Load first image

    def openFolderThenLoad(self):
        '''Opens a folder dialog'''
        directory = Path(self.mainController.openFolderBrowser("Select a Folder"))
        self.loadImagesFromFolder(directory)

    def loadCurrentImage(self):
        '''Loads the current image into the view'''
        if self.currentImageIndex >= 0 and self.currentImageIndex < len(self.imageFiles):
            currentFile = self.imageFiles[self.currentImageIndex]
            self.mainController.window.editor.loadImageFromPath(currentFile)
            self.mainController.window.editor.resetImageEditControls()
            self.mainController.openFile = currentFile
            self.mainController.openImage = openImage(currentFile)
            self.mainController.attempToLoadAnnotations()
        else:
            print("No images left to display")

    def loadNextImage(self):
        self.mainController.saveAnnotations()
        if self.currentImageIndex < len(self.imageFiles) - 1:
            self.currentImageIndex += 1
            self.loadCurrentImage()

    def loadPreviousImage(self):
        self.mainController.saveAnnotations()
        if self.currentImageIndex > 0:
            self.currentImageIndex -= 1
            self.loadCurrentImage()
