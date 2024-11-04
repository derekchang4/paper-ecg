"""
MainController.py
Created November 9, 2020

Controls the primary window, including the menu bar and the editor.
"""
from pathlib import Path
import os

import cv2
import json
import dataclasses
import webbrowser
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QFileDialog

from ecgdigitize.image import ColorImage, openImage
import ImageUtilities
from itertools import chain

from Conversion import convertECGLeads, exportSignals
from controllers.FolderController import FolderController
from views.MainWindow import MainWindow
from views.ImageView import *
from views.EditorWidget import *
from views.ROIView import *
#from views.ExportFileDialog import *
from views.ExportFileDialog2 import *
from QtWrapper import *
import Annotation
from model.Lead import Lead, LeadId
import datetime
from model.InputParameters import InputParameters


class MainController:

    def __init__(self):
        self.window = MainWindow(self)
        self.folderController = FolderController(self)
        self.connectUI()
        self.openFile = None

        # Preset
        self.preset = None
        # self.usePreset = False

        self.openImage: Optional[ColorImage] = None

    def connectUI(self):
        """
        Hook UI up to handlers in the controller
        """
        self.window.fileMenuOpen.triggered.connect(self.openImageFile)

        # File Controller integration
        self.window.editor.EditPanelGlobalView.nextButton.clicked.connect(self.folderController.loadNextImage)
        self.window.editor.EditPanelGlobalView.prevButton.clicked.connect(self.folderController.loadPreviousImage)
        self.window.openFolder.triggered.connect(self.folderController.openFolderThenLoad)

        self.window.fileMenuClose.triggered.connect(self.closeImageFile)
        self.window.editor.processEcgData.connect(self.confirmDigitization)
        self.window.editor.saveAnnotationsButtonClicked.connect(self.saveAnnotations)
        
        ## Preset 9/22/24
        self.window.processFolder.triggered.connect(self.processFolder)
        self.window.preset1.triggered.connect(self.loadPreset1)
        self.window.presetNone.triggered.connect(self.loadPresetNone)

        self.window.reportIssueButton.triggered.connect(lambda: webbrowser.open('https://github.com/Tereshchenkolab/paper-ecg/issues'))
        self.window.userGuideButton.triggered.connect(lambda: webbrowser.open('https://github.com/Tereshchenkolab/paper-ecg/blob/master/USER-GUIDE.md'))

    def openImageFile(self):

        # Per pathlib documentation, if no selection is made then Path('.') is returned
        #  https://docs.python.org/3/library/pathlib.html
        path = Path(self.openFileBrowser("Open File", "Images (*.png *.jpg *.jpeg *.tif *.tiff)"))

        if path != Path('.'):
            self.window.editor.loadImageFromPath(path)
            self.window.editor.resetImageEditControls()
            self.openFile = path
            self.openImage = openImage(path)
            self.attempToLoadAnnotations()
            self.folderController.loadImagesFromFolder(path.parent) # Queue up the other files in the folder
        else:
            print("[Warning] No image selected")

    def openFileBrowser(self, caption: str, fileType: str, initialPath: str ="") -> str:
        """Launches a file browser for the user to select a file to open.

        Args:
            caption (str): The caption shown to the user
            fileType (str): The acceptable file types ex: `Images (*.png *.jpg)`
            initialPath (str, optional): The path at which the file browser opens. Defaults to "".

        Returns:
            str: Path to the selected file.
        """
        absolutePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window, # Parent
            caption,
            initialPath, # If the initial path is `""` it defaults to the most recent path.
            fileType
        )

        return absolutePath
    
    def openFolderBrowser(self, caption: str, initialPath: str ="") -> str:
        """Launches a folder browser for the user to select a folder to open.

        Args:
            caption (str): The caption shown to the user
            fileType (str): The acceptable file types ex: `Images (*.png *.jpg)`
            initialPath (str, optional): The path at which the file browser opens. Defaults to "".

        Returns:
            str: Path to the selected file.
        """
        print("Opening folder")
        absolutePath = str(QFileDialog.getExistingDirectory(self.window,
                                                            caption,
                                                            initialPath))

        return absolutePath

    def closeImageFile(self):
        """Closes out current image file and resets editor controls."""
        self.window.editor.removeImage()
        self.window.editor.deleteAllLeadRois()
        self.window.editor.resetImageEditControls()
        self.openFile = None
        self.openImage = None

    def confirmDigitization(self):
        inputParameters = self.getCurrentInputParameters()

        # <- One-off utility to save I lead as file ->
        # rotatedImage = digitize.image.rotated(self.window.editor.image, inputParameters.rotation)
        # leadData = inputParameters.leads[LeadId.I]
        # cropped = digitize.image.cropped(
        #     rotatedImage,
        #     digitize.image.Rectangle(
        #         leadData.x, leadData.y, leadData.width, leadData.height
        #     )
        # )
        # import random
        # cv2.imwrite(f"lead-pictures/{self.openFile.stem}-{random.randint(0,10**8)}.png", cropped)

        if len(inputParameters.leads) > 0:
            self.processEcgData(inputParameters)
        else:
            warningDialog = MessageDialog(
                message="Warning: No data to process\n\nPlease select at least one lead to digitize",
                title="Warning"
            )
            warningDialog.exec_()

    # we have all ECG data and export location - ready to pass off to backend to digitize
    def processEcgData(self, inputParameters):
        if self.window.editor.image is None:
            raise Exception("IMAGE NOT AVAILABLE WHEN `processEcgData` CALLED")

        extractedSignals, previewImages = convertECGLeads(self.openImage, inputParameters)

        if extractedSignals is None:
            errorDialog = MessageDialog(
                message="Error: Signal Processing Failed\n\nPlease check your lead selection boxes",
                title="Error"
            )
            errorDialog.exec_()
        else:
            exportFileDialog = ExportFileDialog(previewImages)
            if exportFileDialog.exec_():
                self.exportECGData(exportFileDialog.fileExportPath, exportFileDialog.delimiterDropdown.currentText(), extractedSignals)

    # we have all ECG data and export location - ready to pass off to backend to digitize
    def processEcgDataNoDialog(self, inputParameters, filepath: str, delimiter: str):
        '''For calling the function without a file explorer dialog'''
        if self.window.editor.image is None:
            raise Exception("IMAGE NOT AVAILABLE WHEN `processEcgData` CALLED")

        extractedSignals, previewImages = convertECGLeads(self.openImage, inputParameters)

        if extractedSignals is None:
            errorDialog = MessageDialog(
                message="Error: Signal Processing Failed\n\nPlease check your lead selection boxes",
                title="Error"
            )
            errorDialog.exec_()
        else:
            self.exportECGData(filepath, delimiter, extractedSignals)
            #for lead, img in previewImages.items():
            #    pixmap = ImageUtilities.opencvImageToPixmap(img)
            #    pixmap.save(self.getMetaDataDirectory() / self.openFile, "jpg")


    def exportECGData(self, exportPath, delimiter, extractedSignals):
        seperatorMap = {"Comma":',', "Tab":'\t', "Space":' '}
        assert delimiter in seperatorMap, f"Unrecognized delimiter {delimiter}"

        exportSignals(extractedSignals, exportPath, separator=seperatorMap[delimiter])

    def saveAnnotations(self):

        inputParameters = self.getCurrentInputParameters()

        if self.window.editor.image is None:
            return

        assert self.openFile is not None

        def extractLeadAnnotation(lead: Lead) -> Annotation.LeadAnnotation:
            return Annotation.LeadAnnotation(
                Annotation.CropLocation(
                    lead.x,
                    lead.y,
                    lead.width,
                    lead.height,
                ),
                lead.startTime
            )

        metadataDirectory = self.openFile.parent / '.paperecg'
        if not metadataDirectory.exists():
            metadataDirectory.mkdir()

        filePath = metadataDirectory / (self.openFile.stem + '-' + self.openFile.suffix[1:] + '.json')

        ## Saving modified preset
        #if self.preset != None:
        #    filePath = self.preset
            

        #print("leads\n", inputParameters.leads.items())

        leads = {
            name: extractLeadAnnotation(lead) for name, lead in inputParameters.leads.items()
        }

        currentDateTime = (datetime.datetime.now()).strftime("%m/%d/%Y, %H:%M:%S")

        Annotation.Annotation(
            timeStamp = currentDateTime,
            image=Annotation.ImageMetadata(self.openFile.name, directory=str(self.openFile.parent.absolute())),
            rotation=inputParameters.rotation,
            timeScale=inputParameters.timeScale,
            voltageScale=inputParameters.voltScale,
            leads=leads
        ).save(filePath)

        print("Metadata successfully saved to:", str(filePath))
        self.window.editor.EditPanelGlobalView.setLastSavedTimeStamp(currentDateTime)

    def attempToLoadAnnotations(self):
        if self.window.editor.image is None:
            print("[Couldn't load annotation] No image")
            return

        assert self.openFile is not None

        metadataDirectory = self.openFile.parent / '.paperecg'
        if not metadataDirectory.exists():
            print("[Couldn't load annotation] No metadata directory")
            return

        filePath = metadataDirectory / (self.openFile.stem + '-' + self.openFile.suffix[1:] + '.json')
        if not filePath.exists():
            print("[Couldn't load annotation] File not found")
            return

        print("Loading saved state from:", filePath, '...')

        # Load the saved state
        with open(filePath) as file:
            data = json.load(file)

        # Delete all existing ROIs first
        self.window.editor.deleteAllLeadRois()
        self.window.editor.loadSavedState(data)

    def getCurrentInputParameters(self):
        return InputParameters(
            rotation=self.window.editor.EditPanelGlobalView.getRotation(),
            timeScale=self.window.editor.EditPanelGlobalView.timeScaleSpinBox.value(),
            voltScale=self.window.editor.EditPanelGlobalView.voltScaleSpinBox.value(),
            leads=self.window.editor.imageViewer.getAllLeadRoisAsDict()
        )
    
    def attempToLoadPreset(self):
        '''Loads a default cropping setup'''
        
        ## Must clear previous presets first
        assert self.preset is not None

        metadataDirectory = Path.cwd() / '.paperecg'
        if not metadataDirectory.exists():
            return

        filePath = metadataDirectory / (self.preset.stem + '.json')
        if not filePath.exists():
            print(f"Couldn't find {self.preset.stem}")
            return

        print("Loading saved state from:", filePath, '...')

        # Load the saved state
        with open(filePath) as file:
            data = json.load(file)

        self.window.editor.resetImageEditControls()
        self.window.editor.deleteAllLeadRois()
        self.window.editor.loadSavedPreset(data)

        # self.window.editor.EditPanelGlobalView.saveAnnotationsButton.setText("Save Metadata (Current Preset)")
        
    def loadPreset1(self):
        ## Must open a file from that folder first
        # print("CWD = ", Path.cwd())
        metadataDirectory = Path.cwd() / '.paperecg'
        if not metadataDirectory.exists():
            metadataDirectory.mkdir()
        filePath = metadataDirectory / ("preset1" + '.json')
        self.preset = filePath
        self.attempToLoadPreset()

    def loadPresetNone(self):
        '''Resets the preset Lead ROIs and Image edit controls'''
        if self.preset != None:
            self.window.editor.deleteAllLeadRois()
            self.window.editor.resetImageEditControls()
            self.window.editor.EditPanelGlobalView.saveAnnotationsButton.setText("Save Metadata")
            self.preset == None


    def processFolder(self):
        # Prompt for the folder to analyze

        # <- One-off utility to save I lead as file ->
        # rotatedImage = digitize.image.rotated(self.window.editor.image, inputParameters.rotation)
        # leadData = inputParameters.leads[LeadId.I]
        # cropped = digitize.image.cropped(
        #     rotatedImage,
        #     digitize.image.Rectangle(
        #         leadData.x, leadData.y, leadData.width, leadData.height
        #     )
        # )
        # import random
        # cv2.imwrite(f"lead-pictures/{self.openFile.stem}-{random.randint(0,10**8)}.png", cropped)
        print("Digitizing folder...")
        if self.preset == None:
            warningDialog = MessageDialog(
                    message="Warning: No preset selected\n\nPlease select a preset to digitize a folder",
                    title="Warning"
                )
            warningDialog.exec_()
            return
        print("Select Directory")
        directory = Path(self.openFolderBrowser("Open Folder"))

        if directory == Path('.'):
            print("[Warning] No folder selected")
            return

        print(f"Globbing")
        files = chain(directory.glob('*.png'), directory.glob('*.jpg'), directory.glob('*.jpeg'), directory.glob('*.tif'), directory.glob('*.tiff'))
        print(f"Directory: {directory}")
        print(f"Files: {files}")

        ## Create a progress bar
        self.progress = QtWidgets.QProgressBar()
        #self.progress.setGeometry(200, 80, 250, 20)

        ## Ensure an exported_leads file is created
        metaDataDirectory = self.getMetaDataDirectory()
        exportDirectory = metaDataDirectory / 'exported_leads'
        imagePreviewDirectory = metaDataDirectory / 'image_previews'
        if not exportDirectory.exists():
            exportDirectory.mkdir()

        for file in files:
            print(f"Discovered {file}")
            self.window.editor.loadImageFromPath(file)
            self.openFile = file
            self.openImage = openImage(file)

            inputParameters = self.getCurrentInputParameters()

            if len(inputParameters.leads) > 0:
                self.processEcgData(inputParameters)
                #self.processEcgDataNoDialog(inputParameters, self.getMetaDataDirectory() / 'exported_leads' / self.openFile.with_suffix(".csv"), "Comma")
                #self
            else:
                warningDialog = MessageDialog(
                    message="Warning: No data to process\n\nPlease select at least one lead to digitize",
                    title="Warning"
                )
                warningDialog.exec_()
                break

    def getMetaDataDirectory(self):
        # probability density (/distribution) function
        # probability mass function = discrete
        # cumulative distribution function both
        metadataDirectory = Path.cwd() / '.paperecg'
        if not metadataDirectory.exists():
            metadataDirectory.mkdir()
        print(f"Using metadata folder: {metadataDirectory}")
        return metadataDirectory
