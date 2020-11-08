"""
Main.py
Created November 1, 2020

Entry point for the application
"""

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5 import QtWidgets
from PyQt5 import uic

from Utility import *
from MainWindow import MainWindow

import os, sys

if __name__ == '__main__':
    appctxt = ApplicationContext()

    # Translate asset paths to useable format for PyInstaller
    def resource(relativePath):
      return appctxt.get_resource(relativePath)

    window = MainWindow()
    window.setWindowTitle("Paper ECG")
    window.setWindowIcon(QtGui.QIcon('pythonlogo.png'))
    window.resize(800, 500)
    window.show()

    exit_code = appctxt.app.exec_()
    print(f"Exiting with status {exit_code}")
    sys.exit(exit_code)