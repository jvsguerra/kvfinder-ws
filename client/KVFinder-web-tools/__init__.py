#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

import os, sys

# DEBUG flag
DEBUG = True


# global reference to avoid garbage collection of our dialog
dialog = None


class _Default(object):

    def __init__(self):
        super(_Default, self).__init__()
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
        self.ligand_adjustment = False
        self.ligand_cutoff = 5.0
        self.box_adjustment = False
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
        dialog = PyMOLKVFinderWebTools()

    dialog.gui.show()


class PyMOLKVFinderWebTools(object):
    """
    PyMOL KVFinder Web Tools

    - creates Graphical User Interface in PyQt5 in PyMOL viewer
    - defines and connects callbacks for Qt elements

    """
    def __init__(self):
        super(PyMOLKVFinderWebTools, self).__init__()
        # Define Default Parameters
        self._default = _Default()
        # Initialize PyMOLKVFinderWebTools GUI
        self.initialize_gui()
        # Restore Default Parameters
        self.restore()


    def initialize_gui(self):
        """
        Qt elements are located in self.gui
        """
        # entry point to PyMOL's API
        from pymol import cmd
        # pymol.Qt provides the PyQt5 interface
        from pymol.Qt import QtWidgets
        from pymol.Qt.utils import loadUi, getSaveFileNameWithExt

        # create a new QMainWindow
        self.gui = QtWidgets.QMainWindow()

        # populate the QMainWindow from our *.ui file
        uifile = os.path.join(os.path.dirname(__file__), 'KVFinder-web.ui')
        loadUi(uifile, self.gui)

        ########################
        ### Buttons Callback ###
        ########################

        # hook up QMainWindow buttons callbacks
        self.gui.button_run.clicked.connect(self.run)
        self.gui.button_exit.clicked.connect(self.gui.close)
        self.gui.button_restore.clicked.connect(self.restore)
        self.gui.button_grid.clicked.connect(self.show_grid)
        
        # hook up Parameters button callbacks
        self.gui.button_browse.clicked.connect(self.select_directory)
        self.gui.refresh_input.clicked.connect(lambda: self.refresh(self.gui.input))
        self.gui.refresh_ligand.clicked.connect(lambda: self.refresh(self.gui.ligand))


    ### Button Methods
    def run(self):
        """
        Callback for the "Run KVFinder-web" button
        """
        id = 1 # dummy id value
        print(f'\nRunning KVFinder-web for job id: {id}\n')
        # TODO: 
        # - integrate client.py 
        # - check in ./KVFinder-web for the id
        # - if complete load results


    def show_grid(self):
        """
        Callback for the "Show Grid" button
        """
        print('Showing Grid for current parameters ...\n')


    def restore(self):
        """
        Callback for the "Restore Default Values" button
        """
        print('Restoring values ...\n')
        # Restore PDB and ligand input
        self.refresh(self.gui.input)
        # self.refresh(self.gui.ligand) # TODO: think what is better

        ### Main tab ###
        self.gui.base_name.setText(self._default.base_name)
        self.gui.probe_in.setValue(self._default.probe_in)
        self.gui.probe_out.setValue(self._default.probe_out)
        self.gui.volume_cutoff.setValue(self._default.volume_cutoff)
        self.gui.removal_distance.setValue(self._default.removal_distance)
        self.gui.output_dir_path.setText(self._default.output_dir_path)

        ### Search Space Tab ###
        # Box Adjustment
        self.gui.box_adjustment.setChecked(self._default.box_adjustment)
        # Ligand Adjustment
        self.gui.ligand_adjustment.setChecked(self._default.ligand_adjustment)
        self.gui.ligand.clear()
        self.gui.ligand_cutoff.setValue(self._default.ligand_cutoff)

        if DEBUG:
            print(f"Base Name: {self.gui.base_name.text()}")
            print(f"Probe In: {self.gui.probe_in.value()}")
            print(f"Probe Out: {self.gui.probe_out.value()}")
            print(f"Volume Cutoff: {self.gui.volume_cutoff.value()}")
            print(f"Removal Distance: {self.gui.removal_distance.value()}")
            print(f"Output Directory: {self.gui.output_dir_path.text()}")
            print(f"Box adjustment: {self.gui.box_adjustment.isChecked()}")
            print(f"Ligand adjustment: {self.gui.ligand_adjustment.isChecked()}")
            print(f"Ligand Cutoff: {self.gui.ligand_cutoff.value()}")

    
    def refresh(self, combo_box):
        """
        Callback for the "Refresh" button
        """
        from pymol import cmd

        combo_box.clear()
        for item in cmd.get_names("all"):
            if cmd.get_type(item) == "object:molecule" and \
                item != "box" and \
                item != "grid" and \
                item != "cavities" and \
                item != "residues" and \
                item[-16:] != ".KVFinder.output" and \
                item != "target_exclusive":
                combo_box.addItem(item)
        
        return


    def select_directory(self):
        """ 
        Callback for the "Browse ..." button
        Open a QFileDialog to select a directory.
        """
        from PyQt5.QtWidgets import QFileDialog
        from PyQt5.QtCore import QDir
        
        fname = QFileDialog.getExistingDirectory(caption='Choose Output Directory', directory=os.getcwd())

        if fname:
            fname = QDir.toNativeSeparators(fname)
            if os.path.isdir(fname):
                self.gui.output_dir_path.setText(fname)

        return


def KVFinderWebTools():
    """ Debug KVFinderWebTools """
    # TODO: transform it in a new tools without PyMOL later
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = PyMOLKVFinderWebTools()
    dialog.gui.setWindowTitle('KVFinder-web Tools')
    dialog.gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    KVFinderWebTools()
