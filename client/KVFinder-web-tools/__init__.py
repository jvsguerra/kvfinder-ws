#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

import os, sys
from PyQt5.QtWidgets import QMainWindow
from typing import Optional, Any, Dict

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
        # Box Adjustment
        self.box_adjustment = False
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.min_x = 0.0
        self.max_x = 0.0
        self.min_y = 0.0
        self.max_y = 0.0
        self.min_z = 0.0
        self.max_z = 0.0
        self.angle1 = 0
        self.angle2 = 0
        self.padding = 3.5
        # Ligand Adjustment
        self.ligand_adjustment = False
        self.ligand_cutoff = 5.0
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

    dialog.show()


class PyMOLKVFinderWebTools(QMainWindow):
    """
    PyMOL KVFinder Web Tools

    - creates Graphical User Interface in PyQt5 in PyMOL viewer
    - defines and connects callbacks for Qt elements
    TODO:
    - Run process in the background to check job status
    - Run process to clean job ids from ./KVFinder-web in the background
    - Prepare Run function
    - Prepare Results window
    """
    def __init__(self, server="http://localhost", port="8081"):
        super(PyMOLKVFinderWebTools, self).__init__()
        # Define Default Parameters
        self._default = _Default()
        # Initialize PyMOLKVFinderWebTools GUI
        self.initialize_gui()
        # Restore Default Parameters
        self.restore()
        # Set box centers
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        # Define server
        self.server = f"{server}:{port}"

        print("\nRunning Background Process to check job status KVFinderWebTools\n")
        # TODO: 
        # - function to check jobs id availables
        # - start checking jobs id status -> if complete: download and delete job id


    def initialize_gui(self):
        """
        Qt elements are located in self
        """
        # entry point to PyMOL's API
        from pymol import cmd
        # pymol.Qt provides the PyQt5 interface
        from pymol.Qt import QtWidgets
        from pymol.Qt.utils import loadUi, getSaveFileNameWithExt

        # populate the QMainWindow from our *.ui file
        uifile = os.path.join(os.path.dirname(__file__), 'KVFinder-web.ui')
        loadUi(uifile, self)

        ########################
        ### Buttons Callback ###
        ########################

        # hook up QMainWindow buttons callbacks
        self.button_run.clicked.connect(self.run)
        self.button_exit.clicked.connect(self.close)
        self.button_restore.clicked.connect(self.restore)
        self.button_grid.clicked.connect(self.show_grid)
        
        # hook up Parameters button callbacks
        self.button_browse.clicked.connect(self.select_directory)
        self.refresh_input.clicked.connect(lambda: self.refresh(self.input))
        
        # hook up Search Space button callbacks
        # Box Adjustment
        self.button_draw_box.clicked.connect(self.set_box)
        self.button_delete_box.clicked.connect(self.delete_box)
        self.button_redraw_box.clicked.connect(self.redraw_box)
        # Ligand Adjustment
        self.refresh_ligand.clicked.connect(lambda: self.refresh(self.ligand))


    def run(self):
        """
        Callback for the "Run KVFinder-web" button
        """
        id = 1 # dummy id value
        print(f'\nRunning KVFinder-web for job id: {id}\n')
        
        if DEBUG:
            print(self.x, self.y, self.z)
            print(f"Base Name: {self.base_name.text()}")
            print(f"Probe In: {self.probe_in.value()}")
            print(f"Probe Out: {self.probe_out.value()}")
            print(f"Volume Cutoff: {self.volume_cutoff.value()}")
            print(f"Removal Distance: {self.removal_distance.value()}")
            print(f"Output Directory: {self.output_dir_path.text()}")
            print(f"Box adjustment: {self.box_adjustment.isChecked()}")
            print(f"Ligand adjustment: {self.ligand_adjustment.isChecked()}")
            print(f"Ligand Cutoff: {self.ligand_cutoff.value()}")
           
        # TODO: 
        # - integrate client.py 
        # - check in ./KVFinder-web for the id
        # - if complete load results


    def show_grid(self):
        """
        Callback for the "Show Grid" button
        - Get minimum and maximum coordinates of the KVFinder-web 3D-grid, dependent on selected parameters.
        :return: Call draw_grid function with minimum and maximum coordinates or return Error.
        """
        from pymol import cmd
        from pymol.Qt import QtWidgets

        global x, y, z

        if self.input.count() > 0:
            # Get minimum and maximum dimensions of target PDB
            pdb = self.input.currentText()
            ([min_x, min_y, min_z], [max_x, max_y, max_z]) = cmd.get_extent(pdb)

            # Get Probe Out value
            probe_out = self.probe_out.value()
            probe_out = round(probe_out - round(probe_out, 4) % round(0.6, 4), 1)

            # Prepare dimensions
            min_x = round(min_x - (min_x % 0.6), 1) - probe_out
            min_y = round(min_y - (min_y % 0.6), 1) - probe_out
            min_z = round(min_z - (min_z % 0.6), 1) - probe_out
            max_x = round(max_x - (max_x % 0.6) + 0.6, 1) + probe_out
            max_y = round(max_y - (max_y % 0.6) + 0.6, 1) + probe_out
            max_z = round(max_z - (max_z % 0.6) + 0.6, 1) + probe_out

            # Get center of each dimension (x, y, z)
            x = (min_x + max_x) / 2
            y = (min_y + max_y) / 2
            z = (min_z + max_z) / 2

            # Draw Grid
            self.draw_grid(min_x, max_x, min_y, max_y, min_z, max_z)
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Load a PDB file!")
            return


    def draw_grid(self, min_x, max_x, min_y, max_y, min_z, max_z):
        """
        Draw Grid in PyMOL.
        :param min_x: minimum X coordinate.
        :param max_x: maximum X coordinate.
        :param min_y: minimum Y coordinate.
        :param max_y: maximum Y coordinate.
        :param min_z: minimum Z coordinate.
        :param max_z: maximum Z coordinate.
        :return: grid object in PyMOL.
        """
        from pymol import cmd
        from math import sin, cos
        
        # Prepare dimensions
        angle1 = 0.0
        angle2 = 0.0
        min_x = x - min_x
        max_x = max_x - x 
        min_y = y - min_y 
        max_y = max_y - y 
        min_z = z - min_z 
        max_z = max_z - z 

        # Get positions of grid vertices
        # P1
        x1 = -min_x * cos(angle2) - (-min_y) * sin(angle1) * sin(angle2) + (-min_z) * cos(angle1) * sin(angle2) + x

        y1 = -min_y * cos(angle1) + (-min_z) * sin(angle1) + y

        z1 = min_x * sin(angle2) + min_y * sin(angle1) * cos(angle2) - min_z * cos(angle1) * cos(angle2) + z
        
        # P2
        x2 = max_x * cos(angle2) - (-min_y) * sin(angle1) * sin(angle2) + (-min_z) * cos(angle1) * sin(angle2) + x

        y2 = (-min_y) * cos(angle1) + (-min_z) * sin(angle1) + y
        
        z2 = (-max_x) * sin(angle2) - (-min_y) * sin(angle1) * cos(angle2) + (-min_z) * cos(angle1) * cos(angle2) + z
        
        # P3
        x3 = (-min_x) * cos(angle2) - max_y * sin(angle1) * sin(angle2) + (-min_z) * cos(angle1) * sin(angle2) + x

        y3 = max_y * cos(angle1) + (-min_z) * sin(angle1) + y

        z3 = -(-min_x) * sin(angle2) - max_y * sin(angle1) * cos(angle2) + (-min_z) * cos(angle1) * cos(angle2) + z
        
        # P4
        x4 = (-min_x) * cos(angle2) - (-min_y) * sin(angle1) * sin(angle2) + max_z * cos(angle1) * sin(angle2) + x

        y4 = (-min_y) * cos(angle1) + max_z * sin(angle1) + y

        z4 = -(-min_x) * sin(angle2) - (-min_y) * sin(angle1) * cos(angle2) + max_z * cos(angle1) * cos(angle2) + z

        
        # P5
        x5 = max_x * cos(angle2) - max_y * sin(angle1) * sin(angle2) + (-min_z) * cos(angle1) * sin(angle2) + x

        y5 = max_y * cos(angle1) + (-min_z) * sin(angle1) + y

        z5 = (-max_x) * sin(angle2) - max_y * sin(angle1) * cos(angle2) + (-min_z) * cos(angle1) * cos(angle2) + z
        
        # P6
        x6 = max_x * cos(angle2) - (-min_y) * sin(angle1) * sin(angle2) + max_z * cos(angle1) * sin(angle2) + x

        y6 = (-min_y) * cos(angle1) + max_z * sin(angle1) + y

        z6 = (-max_x) * sin(angle2) - (-min_y) * sin(angle1) * cos(angle2) + max_z * cos(angle1) * cos(angle2) + z
        
        # P7
        x7 = (-min_x) * cos(angle2) - max_y * sin(angle1) * sin(angle2) + max_z * cos(angle1) * sin(angle2) + x

        y7 = max_y * cos(angle1) + max_z * sin(angle1) + y

        z7 = -(-min_x) * sin(angle2) - max_y * sin(angle1) * cos(angle2) + max_z * cos(angle1) * cos(angle2) + z

        # P8
        x8 = max_x * cos(angle2) - max_y * sin(angle1) * sin(angle2) + max_z * cos(angle1) * sin(angle2) + x

        y8 = max_y * cos(angle1) + max_z * sin(angle1) + y

        z8 = (-max_x) * sin(angle2) - max_y * sin(angle1) * cos(angle2) + max_z * cos(angle1) * cos(angle2) + z        

        # Create box object
        if "grid" in cmd.get_names("objects"):
            cmd.delete("grid")

        # Create vertices
        cmd.pseudoatom("grid", name="v2", pos=[x2, y2, z2], color="white")
        cmd.pseudoatom("grid", name="v3", pos=[x3, y3, z3], color="white")
        cmd.pseudoatom("grid", name="v4", pos=[x4, y4, z4], color="white")
        cmd.pseudoatom("grid", name="v5", pos=[x5, y5, z5], color="white")
        cmd.pseudoatom("grid", name="v6", pos=[x6, y6, z6], color="white")
        cmd.pseudoatom("grid", name="v7", pos=[x7, y7, z7], color="white")
        cmd.pseudoatom("grid", name="v8", pos=[x8, y8, z8], color="white")

        # Connect vertices
        cmd.select("vertices", "(name v3,v7)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v2,v6)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v5,v8)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v2,v5)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v4,v6)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v4,v7)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v3,v5)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v6,v8)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v7,v8)")
        cmd.bond("vertices", "vertices")
        cmd.pseudoatom("grid", name="v1x", pos=[x1, y1, z1], color='white')
        cmd.pseudoatom("grid", name="v2x", pos=[x2, y2, z2], color='white')
        cmd.select("vertices", "(name v1x,v2x)")
        cmd.bond("vertices", "vertices")
        cmd.pseudoatom("grid", name="v1y", pos=[x1, y1, z1], color='white')
        cmd.pseudoatom("grid", name="v3y", pos=[x3, y3, z3], color='white')
        cmd.select("vertices", "(name v1y,v3y)")
        cmd.bond("vertices", "vertices")
        cmd.pseudoatom("grid", name="v4z", pos=[x4, y4, z4], color='white')
        cmd.pseudoatom("grid", name="v1z", pos=[x1, y1, z1], color='white')
        cmd.select("vertices", "(name v1z,v4z)")
        cmd.bond("vertices", "vertices")
        cmd.delete("vertices")


    def restore(self):
        """
        Callback for the "Restore Default Values" button
        """
        from pymol import cmd

        print('Restoring values ...\n')
        # Restore PDB and ligand input
        self.refresh(self.input)
        self.refresh(self.ligand) # TODO: think what is better
        
        # Delete grid
        cmd.delete("grid")

        ### Main tab ###
        self.base_name.setText(self._default.base_name)
        self.probe_in.setValue(self._default.probe_in)
        self.probe_out.setValue(self._default.probe_out)
        self.volume_cutoff.setValue(self._default.volume_cutoff)
        self.removal_distance.setValue(self._default.removal_distance)
        self.output_dir_path.setText(self._default.output_dir_path)

        ### Search Space Tab ###
        # Box Adjustment
        self.box_adjustment.setChecked(self._default.box_adjustment)
        self.padding.setValue(self._default.padding)
        self.delete_box()
        # Ligand Adjustment
        self.ligand_adjustment.setChecked(self._default.ligand_adjustment)
        self.ligand.clear()
        self.ligand_cutoff.setValue(self._default.ligand_cutoff)

    
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
                self.output_dir_path.setText(fname)

        return


    def set_box(self):
        """
        Create box coordinates, enable 'Delete Box' and 'Redraw Box' buttons and call draw_box function.
        :param padding: box padding value.
        """
        from pymol import cmd
        # Delete Box object in PyMOL
        if "box" in cmd.get_names("selections"):
            cmd.delete("box")
        # Get dimensions of selected residues
        selection = "sele"
        if selection in cmd.get_names("selections"):
            ([min_x, min_y, min_z], [max_x, max_y, max_z]) = cmd.get_extent(selection)
        else:
            ([min_x, min_y, min_z], [max_x, max_y, max_z]) = cmd.get_extent("")
        
        # Get center of each dimension (x, y, z)
        self.x = (min_x + max_x) / 2
        self.y = (min_y + max_y) / 2
        self.z = (min_z + max_z) / 2

        # Set Box variables in interface
        self.min_x.setValue(round(self.x - (min_x - self.padding.value()), 1))
        self.max_x.setValue(round((max_x + self.padding.value()) - self.x, 1))
        self.min_y.setValue(round(self.y - (min_y - self.padding.value()), 1))
        self.max_y.setValue(round((max_y + self.padding.value()) - self.y, 1))
        self.min_z.setValue(round(self.z - (min_z - self.padding.value()), 1))
        self.max_z.setValue(round((max_z + self.padding.value()) - self.z, 1))
        self.angle1.setValue(0)
        self.angle2.setValue(0)

        # Setting background box values
        self.min_x_set = self.min_x.value()
        self.max_x_set = self.max_x.value()
        self.min_y_set = self.min_y.value()
        self.max_y_set = self.max_y.value()
        self.min_z_set = self.min_z.value()
        self.max_z_set = self.max_z.value()
        self.angle1_set = self.angle1.value()
        self.angle2_set = self.angle2.value()
        self.padding_set = self.padding.value()

        # Draw box
        self.draw_box()

        # Enable/Disable buttons
        self.button_draw_box.setEnabled(False)
        self.button_redraw_box.setEnabled(True)
        self.min_x.setEnabled(True)
        self.min_y.setEnabled(True)
        self.min_z.setEnabled(True)
        self.max_x.setEnabled(True)
        self.max_y.setEnabled(True)
        self.max_z.setEnabled(True)
        self.angle1.setEnabled(True)
        self.angle2.setEnabled(True)


    def draw_box(self):
        """
            Draw box in PyMOL interface.
            :return: box object.
        """
        from math import pi, sin, cos
        import pymol
        from pymol import cmd

        # Convert angle # TODO: check if it is necessary
        angle1 = (self.angle1.value() / 180.0) * pi
        angle2 = (self.angle2.value() / 180.0) * pi

        # Get positions of box vertices
        # P1
        x1 = -self.min_x.value() * cos(angle2) - (-self.min_y.value()) * sin(angle1) * sin(angle2) + (-self.min_z.value()) * cos(angle1) * sin(angle2) + self.x

        y1 = -self.min_y.value() * cos(angle1) + (-self.min_z.value()) * sin(angle1) + self.y
        
        z1 = self.min_x.value() * sin(angle2) + self.min_y.value() * sin(angle1) * cos(angle2) - self.min_z.value() * cos(angle1) * cos(angle2) + self.z

        # P2
        x2 = self.max_x.value() * cos(angle2) - (-self.min_y.value()) * sin(angle1) * sin(angle2) + (-self.min_z.value()) * cos(angle1) * sin(angle2) + self.x
        
        y2 = (-self.min_y.value()) * cos(angle1) + (-self.min_z.value()) * sin(angle1) + self.y
        
        z2 = (-self.max_x.value()) * sin(angle2) - (-self.min_y.value()) * sin(angle1) * cos(angle2) + (-self.min_z.value()) * cos(angle1) * cos(angle2) + self.z

        # P3
        x3 = (-self.min_x.value()) * cos(angle2) - self.max_y.value() * sin(angle1) * sin(angle2) + (-self.min_z.value()) * cos(angle1) * sin(angle2) + self.x

        y3 = self.max_y.value() * cos(angle1) + (-self.min_z.value()) * sin(angle1) + self.y

        z3 = -(-self.min_x.value()) * sin(angle2) - self.max_y.value() * sin(angle1) * cos(angle2) + (-self.min_z.value()) * cos(angle1) * cos(angle2) + self.z

        # P4
        x4 = (-self.min_x.value()) * cos(angle2) - (-self.min_y.value()) * sin(angle1) * sin(angle2) + self.max_z.value() * cos(angle1) * sin(angle2) + self.x
        
        y4 = (-self.min_y.value()) * cos(angle1) + self.max_z.value() * sin(angle1) + self.y
        
        z4 = -(-self.min_x.value()) * sin(angle2) - (-self.min_y.value()) * sin(angle1) * cos(angle2) + self.max_z.value() * cos(angle1) * cos(angle2) + self.z

        # P5
        x5 = self.max_x.value() * cos(angle2) - self.max_y.value() * sin(angle1) * sin(angle2) + (-self.min_z.value()) * cos(angle1) * sin(angle2) + self.x
        
        y5 = self.max_y.value() * cos(angle1) + (-self.min_z.value()) * sin(angle1) + self.y

        z5 = (-self.max_x.value()) * sin(angle2) - self.max_y.value() * sin(angle1) * cos(angle2) + (-self.min_z.value()) * cos(angle1) * cos(angle2) + self.z

        # P6
        x6 = self.max_x.value() * cos(angle2) - (-self.min_y.value()) * sin(angle1) * sin(angle2) + self.max_z.value() * cos(angle1) * sin(angle2) + self.x
        
        y6 = (-self.min_y.value()) * cos(angle1) + self.max_z.value() * sin(angle1) + self.y
        
        z6 = (-self.max_x.value()) * sin(angle2) - (-self.min_y.value()) * sin(angle1) * cos(angle2) + self.max_z.value() * cos(angle1) * cos(angle2) + self.z

        # P7
        x7 = (-self.min_x.value()) * cos(angle2) - self.max_y.value() * sin(angle1) * sin(angle2) + self.max_z.value() * cos(angle1) * sin(angle2) + self.x

        y7 = self.max_y.value() * cos(angle1) + self.max_z.value() * sin(angle1) + self.y

        z7 = -(-self.min_x.value()) * sin(angle2) - self.max_y.value() * sin(angle1) * cos(angle2) + self.max_z.value() * cos(angle1) * cos(angle2) + self.z

        # P8
        x8 = self.max_x.value() * cos(angle2) - self.max_y.value() * sin(angle1) * sin(angle2) + self.max_z.value() * cos(angle1) * sin(angle2) + self.x
        
        y8 = self.max_y.value() * cos(angle1) + self.max_z.value() * sin(angle1) + self.y
        
        z8 = (-self.max_x.value()) * sin(angle2) - self.max_y.value() * sin(angle1) * cos(angle2) + self.max_z.value() * cos(angle1) * cos(angle2) + self.z

        # Create box object
        pymol.stored.list = []
        if "box" in cmd.get_names("selections"):
            cmd.iterate("box", "stored.list.append((name, color))", quiet=1)
        list_color = pymol.stored.list
        cmd.delete("box")
        if len(list_color) > 0:
            for item in list_color:
                at_name = item[0]
                at_c = item[1]
                cmd.set_color(at_name + "color", cmd.get_color_tuple(at_c))
        else:
            for at_name in ["v2", "v3", "v4", "v5", "v6", "v7", "v8", "v1x", "v1y", "v1z", "v2x", "v3y", "v4z"]:
                cmd.set_color(at_name + "color", [0.86, 0.86, 0.86])

        # Create vertices
        cmd.pseudoatom("box", name="v2", pos=[x2, y2, z2], color="v2color")
        cmd.pseudoatom("box", name="v3", pos=[x3, y3, z3], color="v3color")
        cmd.pseudoatom("box", name="v4", pos=[x4, y4, z4], color="v4color")
        cmd.pseudoatom("box", name="v5", pos=[x5, y5, z5], color="v5color")
        cmd.pseudoatom("box", name="v6", pos=[x6, y6, z6], color="v6color")
        cmd.pseudoatom("box", name="v7", pos=[x7, y7, z7], color="v7color")
        cmd.pseudoatom("box", name="v8", pos=[x8, y8, z8], color="v8color")

        # Connect vertices
        cmd.select("vertices", "(name v3,v7)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v2,v6)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v5,v8)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v2,v5)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v4,v6)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v4,v7)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v3,v5)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v6,v8)")
        cmd.bond("vertices", "vertices")
        cmd.select("vertices", "(name v7,v8)")
        cmd.bond("vertices", "vertices")
        cmd.pseudoatom("box", name="v1x", pos=[x1, y1, z1], color='red')
        cmd.pseudoatom("box", name="v2x", pos=[x2, y2, z2], color='red')
        cmd.select("vertices", "(name v1x,v2x)")
        cmd.bond("vertices", "vertices")
        cmd.pseudoatom("box", name="v1y", pos=[x1, y1, z1], color='forest')
        cmd.pseudoatom("box", name="v3y", pos=[x3, y3, z3], color='forest')
        cmd.select("vertices", "(name v1y,v3y)")
        cmd.bond("vertices", "vertices")
        cmd.pseudoatom("box", name="v4z", pos=[x4, y4, z4], color='blue')
        cmd.pseudoatom("box", name="v1z", pos=[x1, y1, z1], color='blue')
        cmd.select("vertices", "(name v1z,v4z)")
        cmd.bond("vertices", "vertices")
        cmd.delete("vertices")
        

    def delete_box(self):
        """
        Delete box object, disable 'Delete Box' and 'Redraw Box' buttons and enable 'Draw Box' button.
        """
        from pymol import cmd

        # Reset all box variables
        self.x = 0
        self.y = 0
        self.z = 0
        # self.min_x_set = 0.0
        # self.max_x_set = 0.0
        # self.min_y_set = 0.0
        # self.max_y_set = 0.0
        # self.min_z_set = 0.0
        # self.max_z_set = 0.0
        # self.angle1_set = 0.0
        # self.angle2_set = 0.0
        # self.padding_set = 3.5

        # Delete Box and Vertices objects in PyMOL
        cmd.delete("vertices")
        cmd.delete("box")

        # Set Box variables in the interface
        self.min_x.setValue(self._default.min_x)
        self.max_x.setValue(self._default.max_x)
        self.min_y.setValue(self._default.min_y)
        self.max_y.setValue(self._default.max_y)
        self.min_z.setValue(self._default.min_z)
        self.max_z.setValue(self._default.max_z)
        self.angle1.setValue(self._default.angle1)
        self.angle2.setValue(self._default.angle2)

        # Change state of buttons in the interface
        self.button_draw_box.setEnabled(True)
        self.button_redraw_box.setEnabled(False)
        self.min_x.setEnabled(False)
        self.min_y.setEnabled(False)
        self.min_z.setEnabled(False)
        self.max_x.setEnabled(False)
        self.max_y.setEnabled(False)
        self.max_z.setEnabled(False)
        self.angle1.setEnabled(False)
        self.angle2.setEnabled(False)


    def redraw_box(self):
        """
        Redraw box in PyMOL interface.
        :param padding: box padding.
        :return: box object.
        """
        from pymol import cmd
        
        # Provided a selection
        if "sele" in cmd.get_names("selections"):
            # Get dimensions of selected residues
            ([min_x, min_y, min_z], [max_x, max_y, max_z]) = cmd.get_extent("sele")

            if self.min_x.value() != self.min_x_set or self.max_x.value() != self.max_x_set or self.min_y.value() != self.min_y_set or self.max_y.value() != self.max_y_set or self.min_z.value() != self.min_z_set or self.max_z.value() != self.max_z_set or self.angle1.value() != self.angle1_set or self.angle2.value() != self.angle2_set:
                self.min_x_set = self.min_x.value()
                self.max_x_set = self.max_x.value()
                self.min_y_set = self.min_y.value()
                self.max_y_set = self.max_y.value()
                self.min_z_set = self.min_z.value()
                self.max_z_set = self.max_z.value()
                self.angle1_set = self.angle1.value()
                self.angle2_set = self.angle2.value()
            # Padding or selection altered
            else:
                # Get center of each dimension (x, y, z)
                self.x = (min_x + max_x) / 2
                self.y = (min_y + max_y) / 2
                self.z = (min_z + max_z) / 2

                # Set background box values
                self.min_x_set = round(self.x - (min_x - self.padding.value()), 1) + self.min_x.value() - self.min_x_set
                self.max_x_set = round((max_x + self.padding.value()) - self.x, 1) + self.max_x.value() - self.max_x_set
                self.min_y_set = round(self.y - (min_y - self.padding.value()), 1) + self.min_y.value() - self.min_y_set
                self.max_y_set = round((max_y + self.padding.value()) - self.y, 1) + self.max_y.value() - self.max_y_set
                self.min_z_set = round(self.z - (min_z - self.padding.value()), 1) + self.min_z.value() - self.min_z_set
                self.max_z_set = round((max_z + self.padding.value()) - self.z, 1) + self.max_z.value() - self.max_z_set
                self.angle1_set = 0 + self.angle1.value()
                self.angle2_set = 0 + self.angle2.value()
                self.padding_set = self.padding.value()
        # Not provided a selection
        else:
            if self.min_x.value() != self.min_x_set or self.max_x.value() != self.max_x_set or self.min_y.value() != self.min_y_set or self.max_y.value() != self.max_y_set or self.min_z.value() != self.min_z_set or self.max_z.value() != self.max_z_set or self.angle1.value() != self.angle1_set or self.angle2.value() != self.angle2_set:
                self.min_x_set = self.min_x.value()
                self.max_x_set = self.max_x.value()
                self.min_y_set = self.min_y.value()
                self.max_y_set = self.max_y.value()
                self.min_z_set = self.min_z.value()
                self.max_z_set = self.max_z.value()
                self.angle1_set = self.angle1.value()
                self.angle2_set = self.angle2.value()

            if self.padding_set != self.padding.value():
                # Prepare dimensions without old padding
                min_x = self.padding_set - self.min_x_set
                max_x = self.max_x_set - self.padding_set
                min_y = self.padding_set - self.min_y_set
                max_y = self.max_y_set - self.padding_set
                min_z = self.padding_set - self.min_z_set
                max_z = self.max_z_set - self.padding_set

                # Get center of each dimension (x, y, z)
                self.x = (min_x + max_x) / 2
                self.y = (min_y + max_y) / 2
                self.z = (min_z + max_z) / 2

                # Set background box values
                self.min_x_set = round(self.x - (min_x - self.padding.value()), 1)
                self.max_x_set = round((max_x + self.padding.value()) - self.x, 1)
                self.min_y_set = round(self.y - (min_y - self.padding.value()), 1)
                self.max_y_set = round((max_y + self.padding.value()) - self.y, 1)
                self.min_z_set = round(self.z - (min_z - self.padding.value()), 1)
                self.max_z_set = round((max_z + self.padding.value()) - self.z, 1)
                self.angle1_set = self.angle1.value()
                self.angle2_set = self.angle2.value()
                self.padding_set = self.padding.value()

        # Set Box variables in the interface
        self.min_x.setValue(self.min_x_set)
        self.max_x.setValue(self.max_x_set)
        self.min_y.setValue(self.min_y_set)
        self.max_y.setValue(self.max_y_set)
        self.min_z.setValue(self.min_z_set)
        self.max_z.setValue(self.max_z_set)
        self.angle1.setValue(self.angle1_set)
        self.angle2.setValue(self.angle2_set)           
                
        # Redraw box
        self.draw_box()

    
    def closeEvent(self, event):
        """
        Add one step to closeEvent from QMainWindow
        """
        global dialog
        dialog = None


    # TODO: Create Job class
    class Job(object):
        def __init__(self, path_protein_pdb: str, path_ligand_pdb: Optional[str]=None):
            self.id: Optional[str] = None
            self.input: Optional[Dict[str, Any]] = {}
            self.output: Optional[Dict[str, Any]] = None 
            self._add_pdb(path_protein_pdb)
            if path_ligand_pdb != None:
                self._add_pdb(path_ligand_pdb, is_ligand=True)
            self._default_settings()

        @property
        def kv_pdb(self):
            if self.output == None:
                return None
            else:
                return self.output["output"]["pdb_kv"]

        @property
        def report(self):
            if self.output == None:
                return None
            else:
                return self.output["output"]["report"]

        @property
        def log(self):
            if self.output == None:
                return None
            else:
                return self.output["output"]["log"]

        def _add_pdb(self, pdb_fn: str, is_ligand: bool=False):
            with open(pdb_fn) as f:
                pdb = f.readlines()
            if is_ligand:
                self.input["pdb_ligand"] = pdb
            else:
                self.input["pdb"] = pdb

        def _default_settings(self):
            self.input["settings"] = {}
            self.input["settings"]["modes"] = {
                "whole_protein_mode" : True,
                "box_mode" : False,
                "resolution_mode" : "Low",
                "surface_mode" : True,
                "kvp_mode" : False,
                "ligand_mode" : False,
            }
            self.input["settings"]["step_size"] = {"step_size": 0.0}
            self.input["settings"]["probes"] = {
                "probe_in" : 1.4,
                "probe_out" : 4.0,
            }
            self.input["settings"]["cutoffs"] = {
                "volume_cutoff" : 5.0,
                "ligand_cutoff" : 5.0,
                "removal_distance" : 2.4,
            }
            self.input["settings"]["visiblebox"] = {
                "p1" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
                "p2" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
                "p3" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
                "p4" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
            }
            self.input["settings"]["internalbox"] = {
                "p1" : {"x" : -4.00, "y" : -4.00, "z" : -4.00},
                "p2" : {"x" : 4.00, "y" : -4.00, "z" : -4.00},
                "p3" : {"x" : -4.00, "y" : 4.00, "z" : -4.00},
                "p4" : {"x" : -4.00, "y" : -4.00, "z" : 4.00},
            }


def KVFinderWebTools():
    """ Debug KVFinderWebTools """
    # TODO: transform it in a new tools without PyMOL later
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = PyMOLKVFinderWebTools()
    dialog.setWindowTitle('KVFinder-web Tools')
    dialog.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    KVFinderWebTools()
