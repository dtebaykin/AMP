# start custom imports - DO NOT MANUALLY EDIT BELOW
# end custom imports - DO NOT MANUALLY EDIT ABOVE
from PyQt5 import QtWidgets, QtCore, QtGui, uic

from amp.main_viewer import MainViewer
from amp.mplwidget import ImagePlot, HistPlot, Plot

import numpy as np

import os
import shutil
import json
import traceback

from typing import Tuple, List, Dict, Any, Union

class EzSegmenter(QtWidgets.QMainWindow):

    def __init__(self, main_viewer: MainViewer, ui_path: str):
        # start typedef - DO NOT MANUALLY EDIT BELOW
        # end typedef - DO NOT MANUALLY EDIT ABOVE

        super().__init__()

        # set reference to main window
        self.main_viewer = main_viewer

        # load ui elements
        uic.loadUi(
            ui_path,
            self
        )

        self.setWindowTitle("EZ Segmenter")

# function for amp plugin building
def build_as_plugin(main_viewer: MainViewer, plugin_path: str) -> EzSegmenter:
    """ Returns an instance of EzSegmenter

    This function is common to all plugins; it allows the plugin loader
    to correctly load the plugin.

    Args:
        main_viewer (MainViewer): reference to the main window
    """

    return EzSegmenter(main_viewer, plugin_path)