#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

import os, sys

# DEBUG flag
DEBUG=True


# global reference to avoid garbage collection of our dialog
dialog = None


class Default(object):

    def __init__(self):
        super(Default, self).__init__()
        #######################
        ### Main Parameters ###
        #######################
        self.probe_in = 1.4
        self.probe_out = 4.0
        self.removal_distance = 2.4
        self.volume_cutoff = 5.0
        self.base_name = "output"
        self.output_dir_path = os.getcwd()
        #######################
        ###  Search Space   ###
        #######################
        # self.
        #######################
        ###     Results     ###
        #######################
        # self.


def __init_plugin__(app=None):
    '''
    Add an entry to the PyMOL "Plugin" menu
    '''
    from pymol.plugins import addmenuitemqt
    addmenuitemqt('KVFinder-web Tools', run_plugin_gui)


def run_plugin_gui():
    '''
    Open our custom dialog
    '''
    global dialog

    if dialog is None:
        dialog = KVFinderWeb()

    dialog.gui.show()


class KVFinderWeb(object):

    def __init__(self):
        super(KVFinderWeb, self).__init__()
        self.initGUI()
        self.restore()

    def initGUI(self):
        """
        Qt elements are located in self.gui and self.form
        """

        # entry point to PyMOL's API
        from pymol import cmd

        # pymol.Qt provides the PyQt5 interface
        from pymol.Qt import QtWidgets
        from pymol.Qt.utils import loadUi, getSaveFileNameWithExt

        # create a new Window
        self.gui = QtWidgets.QMainWindow()

        # populate the Window from our *.ui file which was created with the Qt Designer
        uifile = os.path.join(os.path.dirname(__file__), 'KVFinder-web.ui')
        loadUi(uifile, self.gui)

        #######################
        ###   Gui Buttons   ###
        #######################

        # hook up dialog buttons callbacks
        self.gui.button_run.clicked.connect(self.run)
        self.gui.button_exit.clicked.connect(self.gui.close)
        self.gui.button_restore.clicked.connect(self.restore)
        self.gui.button_grid.clicked.connect(self.show_grid)


    ### Button Methods
    def run(self):
        id = 1 # dummy id value
        print(f'\nRunning KVFinder-web for job id: {id}\n')
        # TODO: 
        # - integrate client.py 
        # - check in ./KVFinder-web for the id
        # - if complete load results


    def show_grid(self):
        print('Showing Grid for current parameters ...\n')


    def restore(self):
        print('Restoring values ...\n')
        self.gui.base_name.setText(Default().base_name)
        self.gui.probe_in.setValue(Default().probe_in)
        self.gui.probe_out.setValue(Default().probe_out)
        self.gui.volume_cutoff.setValue(Default().volume_cutoff)
        self.gui.removal_distance.setValue(Default().removal_distance)
        self.gui.output_dir_path.setText(Default().output_dir_path)
        
        if DEBUG:
            print(f"Base Name: {self.gui.base_name.text()}")
            print(f"Probe In: {self.gui.probe_in.value()}")
            print(f"Probe Out: {self.gui.probe_out.value()}")
            print(f"Volume Cutoff: {self.gui.volume_cutoff.value()}")
            print(f"Removal Distance: {self.gui.removal_distance.value()}")
            print(f"Output Directory: {self.gui.output_dir_path.text()}")

    # callback for the "Browse" button
    def browse_filename():
        filename = getSaveFileNameWithExt(
            dialog, 'Save As...', filter='PNG File (*.png)')
        if filename:
            form.input_filename.setText(filename)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = KVFinderWeb()
    dialog.gui.show()
    sys.exit(app.exec_())