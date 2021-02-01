# start custom imports - DO NOT MANUALLY EDIT BELOW
from amp.cohorttreewidget import CohortTreeWidget
from amp.plotlistwidget import PlotListWidget
from amp.mplwidget import MplWidget
# end custom imports - DO NOT MANUALLY EDIT ABOVE
from amp.cohorttreewidget import CohortTreeWidgetItem
from amp.plotlistwidget import PlotListWidgetItem
import sys

from PyQt5 import QtWidgets, QtCore, uic

from amp.mplwidget import ImagePlot
from amp.figure_manager import FigureManager

from PIL import Image
from numpy import asarray

import os
import concurrent.futures

from amp.plguin_loader import load_plugin

from amp.resource_path import resource_path

from typing import Dict, Any


class MainViewer(QtWidgets.QMainWindow):

    def __init__(self):
        # start typedef - DO NOT MANUALLY EDIT BELOW
        self.statusbar: QtWidgets.QStatusBar
        self.menuPlugins: QtWidgets.QMenu
        self.menuEdit: QtWidgets.QMenu
        self.menuFile: QtWidgets.QMenu
        self.menubar: QtWidgets.QMenuBar
        self.CohortTreeWidget: CohortTreeWidget
        self.label_2: QtWidgets.QLabel
        self.PlotListWidget: PlotListWidget
        self.label: QtWidgets.QLabel
        self.MplWidget: MplWidget
        self.centralwidget: QtWidgets.QWidget
        # end typedef - DO NOT MANUALLY EDIT ABOVE

        super().__init__()
        # load ui elements into MainViewer class
        uic.loadUi(
            resource_path('ui/MainViewer.ui'),
            self
        )

        # TODO: load cached plugins
        self.plugins: Dict[str, QtWidgets.QMainWindow] = {}

        # General UI threadpool (probably shouldn't use this for big algos)
        self.executer = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        # connect UI callbacks
        self.PlotListWidget.itemChanged.connect(self.on_plot_item_change)
        self.PlotListWidget.currentItemChanged.connect(self.on_plot_list_change)
        self.CohortTreeWidget.itemClicked.connect(self.on_file_toggle)
        self.actionOpen_Cohort.triggered.connect(self.load_cohort)
        self.actionAdd_Plugins.triggered.connect(self.add_plugin)

        # configure figure manager
        self.figures = FigureManager(self.PlotListWidget)

        self.setWindowTitle("Main Viewer")

    # reserved by PyQt ( can't follow style guide :/ )
    def closeEvent(self, event: QtCore.QEvent) -> None:
        """ Callback for Main Window Exit/Close

        Calls individual close events on open plugins and accepts close event
        """
        for plugin in self.plugins.values():
            plugin.close()

        event.accept()

    def create_plugin_callback(self, ui_name: str) -> Any:
        """ Creates a callback function for showing/opening the plugin

        Args:
            ui_name: Key to access plugin within plugins dictionary

        Returns:
            Callback function to show/open the plugin

        """
        def plugin_callback():
            self.plugins[ui_name].show()
        return plugin_callback

    def on_plot_item_change(self, item: PlotListWidgetItem) -> None:
        """ Change plot list item name callback

        Updates PlotListWidget's path to name/ui-text map.
        This enables user editable names.

        Args:
            item: PlotListWidgetItem given via signal

        """
        self.PlotListWidget.path_to_name[item.path] = item.text()

    # submit update to plot viewer (multithreading makes ui smoother here)
    def on_plot_list_change(self, current: PlotListWidgetItem,
                            previous: PlotListWidgetItem) -> None:
        """ Callback for updating viewer to display new plots

        Uses threadpool for 'pause-less' UI

        Args:
            current: newly selected PlotListItem (given via signal)
            previous: previously selected PlotListItem (given via signal)

        """
        if current:
            self.executer.submit(
                current.plot.plot_update,
                self.MplWidget._canvas,
                current.plot.plot_data
            )

    def refresh_plots(self) -> None:
        """ Manually update viewer

        Use this when PlotListWidget won't directly change, but new plot
        data has been written to an existing PlotListItem

        """
        self.executer.submit(
            self.PlotListWidget.refresh_current_plot,
            self.MplWidget._canvas
        )

    def load_cohort(self) -> None:
        """ Callback for loading files into main viewer
        """
        flags = QtWidgets.QFileDialog.ShowDirsOnly
        folderpath = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                                'Open Cohort',
                                                                '~',
                                                                flags)
        self.CohortTreeWidget.load_cohort(folderpath)

    def on_file_toggle(self, item: CohortTreeWidgetItem, column: int) -> None:
        """ Callback for toggling image plot of tiff file

        Adds/Removes plot of image to main viewer + plot list
        while managing associated memory

        Currently, this bypasses the 'figures' system, but this
        might change...

        Args:
            item: toggled file in CohortTreeWidgetItem format
            column: (unused)

        """
        # discard non-checkable items
        if not (item.flags() & QtCore.Qt.ItemIsUserCheckable):
            return
        # set default name
        name = os.path.basename(item.path).split('.')[0]
        name = f'{os.path.split(item.path)[0].split("/")[-1]}_{name}'
        row = self.PlotListWidget.get_item_row_by_path(item.path)
        # add image if not already in plot list
        if (
            item.checkState(0)
            and row < 0
        ):
            self.PlotListWidget.add_item(
                name, ImagePlot(asarray(Image.open(item.path))), item.path)
        # remove image otherwise
        elif (
            row >= 0
            and not item.checkState(0)
        ):
            self.PlotListWidget.delete_item(row)

    def add_plugin(self) -> None:
        """ Call back for loading plugin

        In the future, new (i.e uncached) plugins will be cached for
        easy reuse.

        """
        ui_path = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                            'New Plugin',
                                                            '~')
        ui_name = os.path.basename(ui_path).split('.')[0]
        # load plugin if it doesn't exist already
        if ui_name not in self.plugins.keys():
            self.plugins[ui_name] = load_plugin(ui_path, self)

            # TODO: cache plugin so its present on reopening
            #

            # bind plugin+creation callback to menu action
            self.menuPlugins.addAction(
                ui_name,
                self.create_plugin_callback(ui_name))


# start application
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainViewer()
    window.show()
    sys.exit(app.exec_())