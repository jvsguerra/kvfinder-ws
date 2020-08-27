#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

import os, sys


def __init_plugin__(app=None):
    '''
    Add an entry to the PyMOL "Plugin" menu
    '''
    from pymol.plugins import addmenuitemqt
    addmenuitemqt('KVFinder-web Tools', run_plugin_gui)


# global reference to avoid garbage collection of our dialog
dialog = None


def run_plugin_gui():
    '''
    Open our custom dialog
    '''
    global dialog

    if dialog is None:
        dialog = KVFinderWeb().dialog

    dialog.show()


class KVFinderWeb(object):

    def __init__(self):
        super(KVFinderWeb, self).__init__()
        self.initUI()


    def initUI(self):
        # entry point to PyMOL's API
        from pymol import cmd

        # pymol.Qt provides the PyQt5 interface
        from PyQt5 import QtCore
        from pymol.Qt import QtWidgets
        from pymol.Qt.utils import loadUi
        from pymol.Qt.utils import getSaveFileNameWithExt

        # create a new Window
        self.dialog = QtWidgets.QDialog()

        # populate the Window from our *.ui file which was created with the Qt Designer
        uifile = os.path.join(os.path.dirname(__file__), 'KVFinder-web.ui')
        self.form = loadUi(uifile, self.dialog)

        ######################
        ### Dialog Buttons ###
        ######################

        # hook up dialog buttons callbacks
        self.form.button_run.clicked.connect(self.Buttons.run)
        self.form.button_exit.clicked.connect(self.dialog.close)
        self.form.button_restore.clicked.connect(self.Buttons.restore)
        self.form.button_grid.clicked.connect(self.Buttons.show_grid)

        # return dialog


    class Buttons():
        
        # Methods
        @staticmethod
        def run():
            id = 1 # dummy id value
            print(f'\nRunning KVFinder-web for job id: {id}\n')
            # TODO: 
            # - integrate client.py 
            # - check in ./KVFinder-web for the id
            # - if complete load results

        @staticmethod
        def show_grid():
            print('Showing Grid for current parameters ...\n')

        @staticmethod
        def restore():
            print('Restoring values ...\n')

    # callback for the "Browse" button
    def browse_filename():
        filename = getSaveFileNameWithExt(
            dialog, 'Save As...', filter='PNG File (*.png)')
        if filename:
            form.input_filename.setText(filename)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = KVFinderWeb().dialog
    dialog.show()
    sys.exit(app.exec_())