#! /usr/bin/env python3
# -*- coding: utf-8 -*-

'''
PyMOL Demo Plugin

The plugin resembles the old "Rendering Plugin" from Michael Lerner, which
was written with Tkinter instead of PyQt.

(c) Schrodinger, Inc.

License: BSD-2-Clause
'''

from __future__ import absolute_import
from __future__ import print_function

# Avoid importing "expensive" modules here (e.g. scipy), since this code is
# executed on PyMOL's startup. Only import such modules inside functions.

import os


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
        dialog = make_dialog()

    dialog.show()


def make_dialog():
    # entry point to PyMOL's API
    from pymol import cmd

    # pymol.Qt provides the PyQt5 interface
    from pymol.Qt import QtWidgets
    from pymol.Qt.utils import loadUi
    from pymol.Qt.utils import getSaveFileNameWithExt

    # create a new Window
    dialog = QtWidgets.QDialog()

    # populate the Window from our *.ui file which was created with the Qt Designer
    uifile = os.path.join(os.path.dirname(__file__), 'KVFinder-web.ui')
    form = loadUi(uifile, dialog)

    ######################
    ### Dialog Buttons ###
    ######################

    # hook up dialog buttons callbacks
    form.button_run.clicked.connect(KVFinderWeb.Buttons.run)
    form.button_exit.clicked.connect(dialog.close)
    form.button_restore.clicked.connect(KVFinderWeb.Buttons.restore)
    form.button_grid.clicked.connect(KVFinderWeb.Buttons.show_grid)

    return dialog


class KVFinderWeb():
    
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
