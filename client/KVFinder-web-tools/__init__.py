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
        # Set box centers
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0


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
        
        # hook up Search Space button callbacks
        # Box Adjustment
        self.gui.button_draw_box.clicked.connect(self.set_box)
        self.gui.button_delete_box.clicked.connect(self.delete_box)
        self.gui.button_redraw_box.clicked.connect(self.redraw_box)
        # Ligand Adjustment
        self.gui.refresh_ligand.clicked.connect(lambda: self.refresh(self.gui.ligand))


    def run(self):
        """
        Callback for the "Run KVFinder-web" button
        """
        id = 1 # dummy id value
        print(f'\nRunning KVFinder-web for job id: {id}\n')
        
        if DEBUG:
            print(self.x, self.y, self.z)
            print(f"Base Name: {self.gui.base_name.text()}")
            print(f"Probe In: {self.gui.probe_in.value()}")
            print(f"Probe Out: {self.gui.probe_out.value()}")
            print(f"Volume Cutoff: {self.gui.volume_cutoff.value()}")
            print(f"Removal Distance: {self.gui.removal_distance.value()}")
            print(f"Output Directory: {self.gui.output_dir_path.text()}")
            print(f"Box adjustment: {self.gui.box_adjustment.isChecked()}")
            print(f"Ligand adjustment: {self.gui.ligand_adjustment.isChecked()}")
            print(f"Ligand Cutoff: {self.gui.ligand_cutoff.value()}")
           
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

        if self.gui.input.count() > 0:
            # Get minimum and maximum dimensions of target PDB
            pdb = self.gui.input.currentText()
            ([min_x, min_y, min_z], [max_x, max_y, max_z]) = cmd.get_extent(pdb)

            # Get Probe Out value
            probe_out = self.gui.probe_out.value()
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
            QtWidgets.QMessageBox.critical(self.gui, "Error", "Load a PDB file!")
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
        self.refresh(self.gui.input)
        self.refresh(self.gui.ligand) # TODO: think what is better
        
        # Delete grid
        cmd.delete("grid")

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
        self.gui.padding.setValue(self._default.padding)
        self.delete_box()
        # Ligand Adjustment
        self.gui.ligand_adjustment.setChecked(self._default.ligand_adjustment)
        self.gui.ligand.clear()
        self.gui.ligand_cutoff.setValue(self._default.ligand_cutoff)

    
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

        # Set Box variables
        self.gui.min_x.setValue(round(self.x - (min_x - self.gui.padding.value()), 1))
        self.gui.max_x.setValue(round((max_x + self.gui.padding.value()) - self.x, 1))
        self.gui.min_y.setValue(round(self.y - (min_y - self.gui.padding.value()), 1))
        self.gui.max_y.setValue(round((max_y + self.gui.padding.value()) - self.y, 1))
        self.gui.min_z.setValue(round(self.z - (min_z - self.gui.padding.value()), 1))
        self.gui.max_z.setValue(round((max_z + self.gui.padding.value()) - self.z, 1))
        self.gui.angle1.setValue(0)
        self.gui.angle2.setValue(0)
        # self.gui.padding.setValue(self.gui.padding.value())

        # Draw box
        self.draw_box()

        # Enable/Disable buttons
        self.gui.button_draw_box.setEnabled(False)
        self.gui.button_redraw_box.setEnabled(True)


    def draw_box(self):
        """
            Draw box in PyMOL interface.
            :return: box object.
        """
        from math import pi, sin, cos
        import pymol
        from pymol import cmd

        # Convert angle # TODO: check if it is necessary
        angle1 = (self.gui.angle1.value() / 180.0) * pi
        angle2 = (self.gui.angle2.value() / 180.0) * pi

        # Get positions of box vertices
        # P1
        x1 = -self.gui.min_x.value() * cos(angle2) - (-self.gui.min_y.value()) * sin(angle1) * sin(angle2) + (-self.gui.min_z.value()) * cos(angle1) * sin(angle2) + self.x

        y1 = -self.gui.min_y.value() * cos(angle1) + (-self.gui.min_z.value()) * sin(angle1) + self.y
        
        z1 = self.gui.min_x.value() * sin(angle2) + self.gui.min_y.value() * sin(angle1) * cos(angle2) - self.gui.min_z.value() * cos(angle1) * cos(angle2) + self.z

        # P2
        x2 = self.gui.max_x.value() * cos(angle2) - (-self.gui.min_y.value()) * sin(angle1) * sin(angle2) + (-self.gui.min_z.value()) * cos(angle1) * sin(angle2) + self.x
        
        y2 = (-self.gui.min_y.value()) * cos(angle1) + (-self.gui.min_z.value()) * sin(angle1) + self.y
        
        z2 = (-self.gui.max_x.value()) * sin(angle2) - (-self.gui.min_y.value()) * sin(angle1) * cos(angle2) + (-self.gui.min_z.value()) * cos(angle1) * cos(angle2) + self.z

        # P3
        x3 = (-self.gui.min_x.value()) * cos(angle2) - self.gui.max_y.value() * sin(angle1) * sin(angle2) + (-self.gui.min_z.value()) * cos(angle1) * sin(angle2) + self.x

        y3 = self.gui.max_y.value() * cos(angle1) + (-self.gui.min_z.value()) * sin(angle1) + self.y

        z3 = -(-self.gui.min_x.value()) * sin(angle2) - self.gui.max_y.value() * sin(angle1) * cos(angle2) + (-self.gui.min_z.value()) * cos(angle1) * cos(angle2) + self.z

        # P4
        x4 = (-self.gui.min_x.value()) * cos(angle2) - (-self.gui.min_y.value()) * sin(angle1) * sin(angle2) + self.gui.max_z.value() * cos(angle1) * sin(angle2) + self.x
        
        y4 = (-self.gui.min_y.value()) * cos(angle1) + self.gui.max_z.value() * sin(angle1) + self.y
        
        z4 = -(-self.gui.min_x.value()) * sin(angle2) - (-self.gui.min_y.value()) * sin(angle1) * cos(angle2) + self.gui.max_z.value() * cos(angle1) * cos(angle2) + self.z

        # P5
        x5 = self.gui.max_x.value() * cos(angle2) - self.gui.max_y.value() * sin(angle1) * sin(angle2) + (-self.gui.min_z.value()) * cos(angle1) * sin(angle2) + self.x
        
        y5 = self.gui.max_y.value() * cos(angle1) + (-self.gui.min_z.value()) * sin(angle1) + self.y

        z5 = (-self.gui.max_x.value()) * sin(angle2) - self.gui.max_y.value() * sin(angle1) * cos(angle2) + (-self.gui.min_z.value()) * cos(angle1) * cos(angle2) + self.z

        # P6
        x6 = self.gui.max_x.value() * cos(angle2) - (-self.gui.min_y.value()) * sin(angle1) * sin(angle2) + self.gui.max_z.value() * cos(angle1) * sin(angle2) + self.x
        
        y6 = (-self.gui.min_y.value()) * cos(angle1) + self.gui.max_z.value() * sin(angle1) + self.y
        
        z6 = (-self.gui.max_x.value()) * sin(angle2) - (-self.gui.min_y.value()) * sin(angle1) * cos(angle2) + self.gui.max_z.value() * cos(angle1) * cos(angle2) + self.z

        # P7
        x7 = (-self.gui.min_x.value()) * cos(angle2) - self.gui.max_y.value() * sin(angle1) * sin(angle2) + self.gui.max_z.value() * cos(angle1) * sin(angle2) + self.x

        y7 = self.gui.max_y.value() * cos(angle1) + self.gui.max_z.value() * sin(angle1) + self.y

        z7 = -(-self.gui.min_x.value()) * sin(angle2) - self.gui.max_y.value() * sin(angle1) * cos(angle2) + self.gui.max_z.value() * cos(angle1) * cos(angle2) + self.z

        # P8
        x8 = self.gui.max_x.value() * cos(angle2) - self.gui.max_y.value() * sin(angle1) * sin(angle2) + self.gui.max_z.value() * cos(angle1) * sin(angle2) + self.x
        
        y8 = self.gui.max_y.value() * cos(angle1) + self.gui.max_z.value() * sin(angle1) + self.y
        
        z8 = (-self.gui.max_x.value()) * sin(angle2) - self.gui.max_y.value() * sin(angle1) * cos(angle2) + self.gui.max_z.value() * cos(angle1) * cos(angle2) + self.z

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

        # Delete Box and Vertices objects in PyMOL
        cmd.delete("vertices")
        cmd.delete("box")

        # Set Box variables in the interface
        self.gui.min_x.setValue(self._default.min_x)
        self.gui.max_x.setValue(self._default.max_x)
        self.gui.min_y.setValue(self._default.min_y)
        self.gui.max_y.setValue(self._default.max_y)
        self.gui.min_z.setValue(self._default.min_z)
        self.gui.max_z.setValue(self._default.max_z)
        self.gui.angle1.setValue(self._default.angle1)
        self.gui.angle2.setValue(self._default.angle2)

        # Change state of buttons in the interface
        self.gui.button_draw_box.setEnabled(True)
        self.gui.button_redraw_box.setEnabled(False)


    def redraw_box(self):
        print('Redrawing box ...\n')
        pass


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
