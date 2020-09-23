#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

import os, sys, json, toml
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal
from typing import Optional, Any, Dict


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
    - Prepare Results window
    """

    # Signals
    msgbox_signal = pyqtSignal(bool)

    def __init__(self, server="http://localhost", port="8081"):
        super(PyMOLKVFinderWebTools, self).__init__()
        from PyQt5.QtNetwork import QNetworkAccessManager
        # entry point to PyMOL's API
        from pymol import cmd

        # Define Default Parameters
        self._default = _Default()
        
        # Initialize PyMOLKVFinderWebTools GUI
        self.initialize_gui()
        
        # Restore Default Parameters
        self.restore(is_startup=True)
        
        # Set box centers
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        
        # Define server
        self.server = f"{server}:{port}"
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._handle_post_response)

        # Create ./KVFinder-web directory for jobs
        jobs_dir = os.path.join(os.path.expanduser('~'), '.KVFinder-web')
        try: 
            os.mkdir(jobs_dir)
        except FileExistsError:
            pass

        # Start Worker thread to handle available jobs
        self._check_job_status()

        # Get available jobs
        self.available_jobs.addItems(self._get_available_jobs())

        # Results
        self.results = None
        self.input_pdb = None
        self.ligand_pdb = None
        self.cavity_pdb = None

        # TODO: Debug
        cmd.load('../examples/1FMO.pdb')


    def initialize_gui(self) -> None:
        """
        Qt elements are located in self
        """
        # pymol.Qt provides the PyQt5 interface
        from PyQt5 import QtWidgets
        from PyQt5.uic import loadUi
        # from pymol.Qt.utils import loadUi

        # populate the QMainWindow from our *.ui file
        uifile = os.path.join(os.path.dirname(__file__), 'KVFinder-web.ui')
        loadUi(uifile, self)

        # ScrollBars binded to QListWidgets in Descriptors
        scroll_bar_volume = QtWidgets.QScrollBar(self)
        self.volume_list.setVerticalScrollBar(scroll_bar_volume)
        scroll_bar_area = QtWidgets.QScrollBar(self)
        self.area_list.setVerticalScrollBar(scroll_bar_area)
        scroll_bar_residues = QtWidgets.QScrollBar(self)
        self.residues_list.setVerticalScrollBar(scroll_bar_residues)

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
        self.button_box_adjustment_help.clicked.connect(self.box_adjustment_help)
        # Ligand Adjustment
        self.refresh_ligand.clicked.connect(lambda: self.refresh(self.ligand))

        # hook up methods to results tab
        # Jobs
        self.available_jobs.currentIndexChanged.connect(self.fill_job_information)
        self.button_show_job.clicked.connect(self.show_id)
        # Visualization
        self.button_browse_results.clicked.connect(self.select_results_file)
        self.button_load_results.clicked.connect(self.load_results)
        self.volume_list.itemSelectionChanged.connect(lambda list1=self.volume_list, list2=self.area_list: self.show_cavities(list1, list2))
        self.area_list.itemSelectionChanged.connect(lambda list1=self.area_list, list2=self.volume_list: self.show_cavities(list1, list2))
        self.residues_list.itemSelectionChanged.connect(self.show_residues)


    def run(self) -> None:
        from PyQt5 import QtNetwork
        from PyQt5.QtCore import QUrl, QJsonDocument

        print('Running job in KVFinder-web server ...')
        
        # Create job
        parameters = self.create_parameters()
        if type(parameters) is dict:
            self.job = Job(parameters)
        else:
            return
        
        # Post request
        try:
            # Prepare request
            url = QUrl(f'{self.server}/create')
            request = QtNetwork.QNetworkRequest(url)
            request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, "application/json")

            # Prepare data
            data = QJsonDocument(self.job.input)

            # Post requests
            self.network_manager.post(request, data.toJson())
        except Exception as e:
            print(e)


    def _handle_post_response(self, reply) -> None:
        from PyQt5 import QtNetwork
        # Get QNetworkReply error status
        er = reply.error()
        
        # Handle Post Response
        if er == QtNetwork.QNetworkReply.NoError:
            print('Job submitted!') # TODO: QMessageBox
            reply = json.loads(str(reply.readAll(), 'utf-8'))

            # Results not available
            if 'output' not in reply.keys():
                # Save job id
                job_id = reply['id']

                # Save job file
                self.job.status = 'queued'
                self.job.save(job_id)
                
            # Job already sent to KVFinder-web server
            else:
                status = reply["status"]
                
                # handle job completed
                if status == 'completed':
                    print('Job already submitted and completed!') # TODO: QMessageBox
                # handle job not completed
                elif status == 'running':
                    print('Job currently running') # TODO: QMessageBox               
        
        else:
            print("Error ocurred: ", er)
            print(reply.errorString())

    
    def show_grid(self) -> None:
        """
        Callback for the "Show Grid" button
        - Get minimum and maximum coordinates of the KVFinder-web 3D-grid, dependent on selected parameters.
        :return: Call draw_grid function with minimum and maximum coordinates or return Error.
        """
        from pymol import cmd
        from PyQt5 import QtWidgets

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
            QtWidgets.QMessageBox.critical(self, "Error", "Select an input PDB!")
            return


    def draw_grid(self, min_x, max_x, min_y, max_y, min_z, max_z) -> None:
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


    def restore(self, is_startup=False) -> None:
        """
        Callback for the "Restore Default Values" button
        """
        from pymol import cmd
        from PyQt5.QtWidgets import QMessageBox

        # Restore Results Tab
        if not is_startup:
            reply = QMessageBox.question(self, "Restore Values", "Also restore Results Visualization tab?", QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                # Remove cavities, residues and pdbs (input, ligand, cavity)
                cmd.delete("cavities")
                cmd.delete("residues")
                if self.input_pdb:
                    cmd.delete(self.input_pdb)
                if self.ligand_pdb:
                    cmd.delete(self.ligand_pdb)
                if self.cavity_pdb:
                    cmd.delete(self.cavity_pdb)
                results = self.input_pdb = self.ligand_pdb = self.cavity_pdb = None
                cmd.frame(1)
                
                # Clean results
                self.clean_results()
                self.vis_results_file_entry.clear()

        # Restore PDB and ligand input
        self.refresh(self.input)
        self.refresh(self.ligand)
        
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

    
    def refresh(self, combo_box) -> None:
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


    def select_directory(self) -> None:
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


    def set_box(self) -> None:
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


    def draw_box(self) -> None:
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
        

    def delete_box(self) -> None:
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


    def redraw_box(self) -> None:
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


    def box_adjustment_help(self) -> None:
        from PyQt5 import QtWidgets, QtCore
        text = QtCore.QCoreApplication.translate("KVFinderWeb", u"<html><head/><body><p align=\"justify\"><span style=\" font-weight:600; text-decoration: underline;\">Box Adjustment mode:</span></p><p align=\"justify\">- Create a selection (optional);</p><p align=\"justify\">- Define a <span style=\" font-weight:600;\">Padding</span> (optional);</p><p align=\"justify\">- Click on <span style=\" font-weight:600;\">Draw Box</span> button.</p><p align=\"justify\"><br/><span style=\"text-decoration: underline;\">Customize your <span style=\" font-weight:600;\">box</span></span>:</p><p align=\"justify\">- Change one item at a time (e.g. <span style=\" font-style:italic;\">Padding</span>, <span style=\" font-style:italic;\">Minimum X</span>, <span style=\" font-style:italic;\">Maximum X</span>, ...);</p><p align=\"justify\">- Click on <span style=\" font-weight:600;\">Redraw Box</span> button.<br/></p><p><span style=\" font-weight:400; text-decoration: underline;\">Delete </span><span style=\" text-decoration: underline;\">box</span><span style=\" font-weight:400; text-decoration: underline;\">:</span></p><p align=\"justify\">- Click on <span style=\" font-weight:600;\">Delete Box</span> button.<br/></p><p align=\"justify\"><span style=\"text-decoration: underline;\">Colors of the <span style=\" font-weight:600;\">box</span> object:</span></p><p align=\"justify\">- <span style=\" font-weight:600;\">Red</span> corresponds to <span style=\" font-weight:600;\">X</span> axis;</p><p align=\"justify\">- <span style=\" font-weight:600;\">Green</span> corresponds to <span style=\" font-weight:600;\">Y</span> axis;</p><p align=\"justify\">- <span style=\" font-weight:600;\">Blue</span> corresponds to <span style=\" font-weight:600;\">Z</span> axis.</p></body></html>", None)
        help_information = QtWidgets.QMessageBox(self)
        help_information.setText(text)
        help_information.setWindowTitle("Help")
        help_information.setStyleSheet("QLabel{min-width:500 px;}")
        help_information.exec_()

    
    def create_parameters(self) -> Dict[str, Any]:
        # Create dict
        parameters = dict()

        # title
        parameters['title'] = 'KVFinder-web job file'

        # status
        parameters['status'] = 'submitting'

        # files
        parameters['files'] = dict()
        # pdb
        if self.input.currentText() != '':
            parameters['files']['pdb'] = self.input.currentText()
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", "Select an input PDB!")
            return False
        # ligand
        if self.ligand_adjustment.isChecked():
            if self.ligand.currentText() != '':
                parameters['files']['pdb_ligand'] = self.ligand.currentText()
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Error", "Select an ligand PDB!")
                return False
        # output
        parameters['files']['output'] = self.output_dir_path.text()
        # base_name
        parameters['files']['base_name'] = self.base_name.text()

        # modes
        parameters['modes'] = dict()
        # whole protein mode
        parameters['modes']['whole_protein_mode'] = not self.box_adjustment.isChecked()
        # box adjustment mode
        parameters['modes']['box_mode'] = self.box_adjustment.isChecked()
        # resolution_mode
        parameters['modes']['resolution_mode'] = "Low"
        # surface_mode
        parameters['modes']['surface_mode'] = True
        # kvp_mode
        parameters['modes']['kvp_mode'] = False
        # ligand_mode
        parameters['modes']['ligand_mode'] = self.ligand_adjustment.isChecked()

        # step_size
        parameters['step_size'] = dict()
        parameters['step_size']['step_size'] = 0.0

        # probes
        parameters['probes'] = dict()
        # probe_in
        parameters['probes']['probe_in'] = self.probe_in.value()
        # probe_out
        parameters['probes']['probe_out'] = self.probe_out.value()

        # cutoffs
        parameters['cutoffs'] = dict()
        # volume_cutoff
        parameters['cutoffs']['volume_cutoff'] = self.volume_cutoff.value()
        # ligand_cutoff
        parameters['cutoffs']['ligand_cutoff'] = self.ligand_cutoff.value()
        # removal_distance
        parameters['cutoffs']['removal_distance'] = self.removal_distance.value()

        # visiblebox
        box = self.create_box_parameters()
        parameters['visiblebox'] = dict()
        parameters['visiblebox'].update(box)

        # internalbox
        box = self.create_box_parameters(is_internal_box=True)
        parameters['internalbox'] = dict()
        parameters['internalbox'].update(box)

        return parameters


    def create_box_parameters(self, is_internal_box=False):
        from math import pi, cos, sin

        # Get box parameters
        if self.box_adjustment.isChecked():
            min_x = self.min_x_set.value()
            max_x = self.max_x_set.value()
            min_y = self.min_y_set.value()
            max_y = self.max_y_set.value()
            min_z = self.min_z_set.value()
            max_z = self.max_z_set.value()
            angle1 = self.angle1_set.value()
            angle2 = self.angle2_set.value()
        else:
            min_x = 0.0
            max_x = 0.0
            min_y = 0.0
            max_y = 0.0
            min_z = 0.0
            max_z = 0.0
            angle1 = 0.0
            angle2 = 0.0


        # Add probe_out to internal box
        if is_internal_box:
            min_x += self.probe_out.value()
            max_x += self.probe_out.value()
            min_y += self.probe_out.value()
            max_y += self.probe_out.value()
            min_z += self.probe_out.value()
            max_z += self.probe_out.value()
            
        # Convert angle # TODO: check if it is necessary
        angle1 = (angle1 / 180.0) * pi
        angle2 = (angle2 / 180.0) * pi

        # Get positions of box vertices
        # P1
        x1 = -min_x * cos(angle2) - (-min_y) * sin(angle1) * sin(angle2) + (-min_z) * cos(angle1) * sin(angle2) + self.x

        y1 = -min_y * cos(angle1) + (-min_z) * sin(angle1) + self.y
        
        z1 = min_x * sin(angle2) + min_y * sin(angle1) * cos(angle2) - min_z * cos(angle1) * cos(angle2) + self.z

        # P2
        x2 = max_x * cos(angle2) - (-min_y) * sin(angle1) * sin(angle2) + (-min_z) * cos(angle1) * sin(angle2) + self.x
        
        y2 = (-min_y) * cos(angle1) + (-min_z) * sin(angle1) + self.y
        
        z2 = (-max_x) * sin(angle2) - (-min_y) * sin(angle1) * cos(angle2) + (-min_z) * cos(angle1) * cos(angle2) + self.z

        # P3
        x3 = (-min_x) * cos(angle2) - max_y * sin(angle1) * sin(angle2) + (-min_z) * cos(angle1) * sin(angle2) + self.x

        y3 = max_y * cos(angle1) + (-min_z) * sin(angle1) + self.y

        z3 = -(-min_x) * sin(angle2) - max_y * sin(angle1) * cos(angle2) + (-min_z) * cos(angle1) * cos(angle2) + self.z

        # P4
        x4 = (-min_x) * cos(angle2) - (-min_y) * sin(angle1) * sin(angle2) + max_z * cos(angle1) * sin(angle2) + self.x
        
        y4 = (-min_y) * cos(angle1) + max_z * sin(angle1) + self.y
        
        z4 = -(-min_x) * sin(angle2) - (-min_y) * sin(angle1) * cos(angle2) + max_z * cos(angle1) * cos(angle2) + self.z

        # Create points
        p1 = {'x': x1, 'y': y1, 'z': z1}
        p2 = {'x': x2, 'y': y2, 'z': z2}
        p3 = {'x': x3, 'y': y3, 'z': z3}
        p4 = {'x': x4, 'y': y4, 'z': z4}
        box = {'p1': p1, 'p2': p2, 'p3': p3, 'p4': p4}

        return box


    def closeEvent(self, event) -> None:
        """
        Add one step to closeEvent from QMainWindow
        """
        global dialog
        dialog = None


    def _get_available_jobs(self) -> list:       
        # Get job dir
        d = os.path.join(os.path.expanduser('~'), '.KVFinder-web/')
        
        # Get jobs availables in dir
        jobs = os.listdir(d)

        return jobs


    def _check_job_status(self) -> bool:
        # Get KVFinder-web server status
        server_status = self._check_server_status()
        
        # Start Worker thread
        self.thread = Worker(self.server, server_status)
        self.thread.start()
        
        # Communication between GUI and Worker threads
        self.thread.id_signal.connect(self.msg_results_not_available)
        self.thread.server_down.connect(self.server_down)
        self.thread.server_up.connect(self.server_up)
        self.thread.server_status_signal.connect(self.set_server_status)
        self.thread.available_jobs_signal.connect(self.set_available_jobs)
        self.msgbox_signal.connect(self.thread.wait_status)
        
        return True


    def show_id(self) -> None:
        # Get job ID
        job_id = self.available_jobs.currentText()
        print(f"Displaying results from job ID: {job_id}\n")
        
        # Get job path
        job_fn = os.path.join(os.path.expanduser('~'), '.KVFinder-web', self.available_jobs.currentText(), 'job.toml')

        # Get job information of ID
        with open(job_fn, 'r') as f:
            job_info = toml.load(f=f)

        # Set results file
        results_file = f"{job_info['files']['output']}/{job_id}/{job_info['files']['base_name']}.KVFinder.results.toml"
        self.vis_results_file_entry.setText(results_file)

        # Select Visualization tab
        self.results_tabs.setCurrentIndex(1)

        # Load results
        self.load_results()


    def load_results(self) -> None:
        from pymol import cmd

        # Get results file
        results_file = self.vis_results_file_entry.text()
        
        # Check if results file exist
        if os.path.exists(results_file) and results_file.endswith('KVFinder.results.toml'):
            print(f"Loading results from: {self.vis_results_file_entry.text()}\n\n")
        else:
            from PyQt5.QtWidgets import QMessageBox
            error_msg = QMessageBox.critical(self, "Error", "Results file cannot be opened! Check results file path.")
            return False

        # Create global variable for results
        global results

        # Read results file 
        results = toml.load(results_file)

        # Clean results
        self.clean_results()

        # Refresh information
        self.refresh_information()

        # Refresh volume
        self.refresh_volume()

        # Refresh area
        self.refresh_area()

        # Refresh residues
        self.refresh_residues()

        # Load files as PyMOL objects
        cmd.delete("cavities")
        cmd.delete("residues")
        cmd.frame(1)

        # Load input
        input_fn = results['FILES_PATH']['INPUT']
        self.input_pdb = os.path.basename(input_fn.replace('.pdb', ''))
        self.load_file(input_fn, self.input_pdb)

        # Load ligand
        if 'LIGAND' in results['FILES_PATH'].keys():
            ligand_fn = results['FILES_PATH']['LIGAND']
            self.ligand_pdb = os.path.basename(ligand_fn.replace('.pdb', ''))
            self.load_file(ligand_fn, self.ligand_pdb)
        else:
            self.ligand_pdb = None

        # Load cavity
        cavity_fn = results['FILES_PATH']['OUTPUT']
        self.cavity_pdb = os.path.basename(cavity_fn.replace('.pdb', ''))
        self.load_cavity(cavity_fn, self.cavity_pdb)

        # TODO: Handle if results already loaded

        return


    def select_results_file(self) -> None:
        """ 
        Callback for the "Browse ..." button
        Open a QFileDialog to select a directory.
        """
        from PyQt5.QtWidgets import QFileDialog
        from PyQt5.QtCore import QUrl, QDir
        
        
        # Get results file
        fname, _ = QFileDialog.getOpenFileName(self, caption='Choose KVFinder Results File', directory=os.getcwd(), filter="KVFinder Results File (*.KVFinder.results.toml)")

        if fname:
            fname = QDir.toNativeSeparators(fname)
            if os.path.exists(fname):
                self.vis_results_file_entry.setText(fname)

        return


    @staticmethod
    def load_cavity(fname, name):
        from pymol import cmd
     
        # Remove previous results in objects with same cavity name
        for obj in cmd.get_names("all"):
            if name == obj:
                cmd.delete(obj)
        
        # Load cavity filename
        if os.path.exists(fname):
            cmd.load(fname, name, zoom=0)
            cmd.hide('everything', name)
            cmd.show('nonbonded', name)


    @staticmethod
    def load_file(fname, name):
        from pymol import cmd
       
        # Remove previous results in objects with same cavity name
        for obj in cmd.get_names("all"):
            if name == obj:
                cmd.delete(obj)
        
        # Load cavity filename
        if os.path.exists(fname):
            cmd.load(fname, name, zoom=0)


    def refresh_information(self) -> None:
        # Input File
        self.vis_input_file_entry.setText(f"{results['FILES_PATH']['INPUT']}")

        # Ligand File
        if 'LIGAND' in results['FILES_PATH'].keys():
            self.vis_ligand_file_entry.setText(f"{results['FILES_PATH']['LIGAND']}")
        else:
            self.vis_ligand_file_entry.setText(f"")
        
        # Cavities File
        self.vis_cavities_file_entry.setText(f"{results['FILES_PATH']['OUTPUT']}")

        # Step Size
        self.vis_step_size_entry.setText(f"{results['PARAMETERS']['STEP_SIZE']:.2f}")

        return


    def refresh_volume(self) -> None:
        # Get cavity indexes
        indexes = sorted(results['RESULTS']['VOLUME'].keys())
        # Include Volume
        for index in indexes:
            item = f"{index}: {results['RESULTS']['VOLUME'][index]}"
            self.volume_list.addItem(item)
        return


    def refresh_area(self) -> None:
        # Get cavity indexes
        indexes = sorted(results['RESULTS']['AREA'].keys())
        # Include Area
        for index in indexes:
            item = f"{index}: {results['RESULTS']['AREA'][index]}"
            self.area_list.addItem(item)
        return

    
    def refresh_residues(self):
        # Get cavity indexes
        indexes = sorted(results['RESULTS']['RESIDUES'].keys())
        # Include Interface Residues
        for index in indexes:
            self.residues_list.addItem(index)
        return


    def show_residues(self):
        from pymol import cmd
        # Get selected cavities from residues list
        cavs = [item.text() for item in self.residues_list.selectedItems()]

        # Return if no cavity is selected 
        if len(cavs) < 1:
            return
        
        # Get residues from cavities selected
        residues = []
        for cav in cavs:
            for residue in results['RESULTS']['RESIDUES'][cav]:
                if residue not in residues:
                    residues.append(residue)

        # Clean objects
        cmd.set("auto_zoom", 0)
        cmd.delete("res")
        cmd.delete("residues")

        # Check if input pdb is loaded
        control = 0
        for item in cmd.get_names("all"):
            if item == self.input_pdb:
                control = 1
        if control == 0:
            return

        # Select residues
        command = f"{self.input_pdb} and"
        while len(residues) > 0:
            res, chain, _ = residues.pop(0) 
            command = f"{command} (resid {res} and chain {chain}) or"
        command = f"{command[:-3]}"
        cmd.select("res", command)

        # Create residues object
        cmd.create("residues", "res")
        cmd.delete("res")
        cmd.hide("everything", "residues")
        cmd.show('sticks', 'residues')
        cmd.disable(self.cavity_pdb)
        cmd.enable(self.cavity_pdb)
        cmd.set("auto_zoom", 1)


    def show_cavities(self, list1, list2):
        from pymol import cmd
        # Get items from list1
        cavs = [item.text()[0:3] for item in list1.selectedItems()]

        # Select items of list2
        number_of_items = list1.count()
        for index in range(number_of_items):
            if list2.item(index).text()[0:3] in cavs:
                list2.item(index).setSelected(True)
            else:
                list2.item(index).setSelected(False)

        # Return if no cavity is selected 
        if len(cavs) < 1:
            return

        # Clean objects
        cmd.set("auto_zoom", 0)
        cmd.delete("cavs")
        cmd.delete("cavities")
        
        # Check if cavity file is loaded
        control = 0
        for item in cmd.get_names("all"):
            if item == self.cavity_pdb:
                control = 1
        if control == 0:
            return

        # Color filling cavity points as blue nonbonded
        command = f"{self.cavity_pdb} and (resname "
        while len(cavs) > 0:
            command = f"{command}{cavs.pop(0)},"
        command = f"{command[:-1]})"
        cmd.select("cavs", command)

        # Create cavities object with blue nonbonded
        cmd.create("cavities", "cavs")
        cmd.delete("cavs")
        cmd.color("blue", "cavities")
        cmd.show("nonbonded", "cavities")

        # Color surface cavity points as red nb_spheres
        cmd.select("cavs", "cavities and name HS")
        cmd.color("red", "cavs")
        cmd.show("nb_spheres", "cavs")
        cmd.delete("cavs")

        # Reset cavities output object
        cmd.disable(self.cavity_pdb)
        cmd.enable(self.cavity_pdb)
        cmd.set("auto_zoom", 1)


    def clean_results(self):
        # Input File
        self.vis_input_file_entry.setText(f"")

        # Ligand File
        self.vis_ligand_file_entry.setText(f"")
        
        # Cavities File
        self.vis_cavities_file_entry.setText(f"")

        # Step Size
        self.vis_step_size_entry.setText(f"")

        # Volume
        self.volume_list.clear()

        # Area
        self.area_list.clear()

        # Residues
        self.residues_list.clear()


    def _check_server_status(self):
        # TODO: check a better way to do this
        import urllib.request
        try:
            urllib.request.urlopen(self.server, timeout=1).getcode()
            self.server_up()
            return True
        except:
            self.server_down()
            return False


    @pyqtSlot(bool)
    def set_server_status(self, status):
        if status:
            self.server_up()
        else:
            self.server_down()


    @pyqtSlot()
    def server_up(self):
        self.server_status.clear()
        self.server_status.setText('Online')
        self.server_status.setStyleSheet('color: green;')
    

    @pyqtSlot()
    def server_down(self):
        self.server_status.clear()
        self.server_status.setText('Offline')
        self.server_status.setStyleSheet('color: red;') 


    @pyqtSlot(list)
    def set_available_jobs(self, available_jobs) -> None:
        # TODO: Check if it works and put with other slots
        # Get current selected job
        current = self.available_jobs.currentText()
        
        # Update available jobs
        self.available_jobs.clear()
        self.available_jobs.addItems(available_jobs)

        # If current still in available jobs, select it
        if current in available_jobs:
            self.available_jobs.setCurrentText(current)
        
        # Fill job information
        self.fill_job_information()


    def fill_job_information(self):
        if self.available_jobs.currentText() != '': 
            # Get job path
            job_fn = os.path.join(os.path.expanduser('~'), '.KVFinder-web', self.available_jobs.currentText(), 'job.toml')
            
            # Read job file
            with open(job_fn, 'r') as f:
                job_info = toml.load(f=f)

            # Fill job information labels
            status = job_info['status'].capitalize()
            if status == 'Queued' or status == 'Running':
                self.job_status_entry.setText(status)
                self.job_status_entry.setStyleSheet('color: blue;')
                # Disable button
                self.button_show_job.setEnabled(False)
            elif status == 'Completed':
                self.job_status_entry.setText(status)
                self.job_status_entry.setStyleSheet('color: green;')
                # Enable button
                self.button_show_job.setEnabled(True)
            self.job_input_entry.setText(f"{job_info['files']['pdb']}")
            if 'ligand' in job_info['files'].keys():
                self.job_ligand_entry.setText(f"{job_info['files']['ligand']}")
            else:
                self.job_ligand_entry.clear()
            self.job_output_dir_path_entry.setText(f"{job_info['files']['output']}")
            if 'is_added_manually' in job_info.keys():
                if job_info['is_added_manually']:
                    self.job_parameters_entry.setText(f"Not available")
            else:
                self.job_parameters_entry.setText(f"{job_info['files']['output']}/{self.available_jobs.currentText()}/{job_info['files']['base_name']}_parameters.toml")
        else:
            # Disable button
            self.button_show_job.setEnabled(False)
            # Fill job information labels
            self.job_status_entry.clear()
            self.job_input_entry.clear()
            self.job_ligand_entry.clear()
            self.job_output_dir_path_entry.clear()
            self.job_parameters_entry.clear()


    @pyqtSlot(str)
    def msg_results_not_available(self, job_id) -> None:
        from PyQt5.QtWidgets import QMessageBox
        from PyQt5.QtCore import QTimer, QEventLoop

        # Message Box
        message = QMessageBox(self)
        message.setWindowTitle(f"Job Notification")
        message.setText(f'Job ID: {job_id}\nThis job is not available anymore in KVFinder-web server!\n')
        message.setInformativeText('Jobs are kept for one week days after completion.')
        if message.exec_() == QMessageBox.Ok:
            # Send signal to Worker thread
            self.msgbox_signal.emit(False)


class Job(object):


    def __init__(self, parameters: Optional[Dict[str, Any]]):
        # Job Information (local)
        self.status: Optional[str] = None
        self.pdb: Optional[str] = None
        self.ligand: Optional[str] = None
        self.output_directory: Optional[str] = None
        self.base_name: Optional[str] = None
        self.id_added_manually: Optional[bool] = False
        # Request information (server)
        self.id: Optional[str] = None
        self.input: Optional[Dict[str, Any]] = {} 
        self.output: Optional[Dict[str, Any]] = None
        # Upload parameters in self.input
        self.upload(parameters)


    @property
    def cavity(self):
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


    def upload(self, parameters: Optional[Dict[str, Any]]):
        from pymol import cmd
        """ Load Job from paramters Dict """
        # Job Information (local)
        # Status
        self.status = parameters['status']
        # ID Added Manually
        if 'id_added_manually' in parameters.keys():
            # if parameters['id_added_manually']:
            self.id_added_manually = parameters['id_added_manually']
        # Output directory
        self.output_directory = parameters['files']['output']
        # Base_name
        self.base_name = parameters['files']['base_name']
        # Input PDB
        self.pdb = os.path.join(self.output_directory, parameters['files']['pdb'] + '.pdb')
        cmd.save(self.pdb, parameters['files']['pdb'], 0,  'pdb')
        # Ligand PDB
        if 'ligand' in parameters['files'].keys():
            self.ligand = os.path.join(self.output_directory, parameters['files']['ligand'] + '.pdb')
            cmd.save(self.ligand, parameters['files']['ligand'], 0, "pdb")

        # Request information (server)
        # Input PDB
        self._add_pdb(self.pdb)
        # Ligand PDB
        if self.ligand is not None:
            self._add_pdb(self.ligand, is_ligand=True)
        # Settings
        self.input['settings'] = dict()
        # Modes
        self.input['settings']['modes'] = parameters['modes']
        # Step size
        self.input['settings']['step_size'] = parameters['step_size']
        # Probes
        self.input['settings']['probes'] = parameters['probes']
        # Cutoffs
        self.input['settings']['cutoffs'] = parameters['cutoffs']
        # Visible box
        self.input['settings']['visiblebox'] = parameters['visiblebox']
        # Internal box
        self.input['settings']['internalbox'] = parameters['internalbox']


    def save(self, id: int):
        """ Save Job to job.toml """
        # Create job directory in ~/.KVFinder-web/
        job_dn = os.path.join(os.path.expanduser('~'), '.KVFinder-web', str(id))
        try:
            os.mkdir(job_dn)
        except FileExistsError:
            pass

        # Create job file inside ~/.KVFinder-web/id
        job_fn = os.path.join(job_dn, 'job.toml')
        with open(job_fn, 'w') as f:
            f.write("# TOML configuration file for KVFinder-web job\n\n")
            f.write("title = \"KVFinder-web job file\"\n\n")
            f.write(f"status = \"{self.status}\"\n\n")
            if self.id_added_manually:
                f.write(f"id_added_manually = \"{self.id_added_manually}\"\n\n")
            f.write(f"[files]\n")
            f.write(f"pdb = \"{self.pdb}\"\n")
            if self.ligand is not None:
                f.write(f"ligand = \"{self.ligand}\"\n")
            f.write(f"output = \"{self.output_directory}\"\n")
            f.write(f"base_name = \"{self.base_name}\"\n")
            f.write('\n')
            toml.dump(o=self.input['settings'], f=f)
            f.write('\n')


    @classmethod
    def load(cls, fn: Optional[str]):
        """ Load Job from job.toml """
        # Read job file
        with open(fn, 'r') as f:
            job_info = toml.load(f=f)
        
        # Fix pdb and ligand in job_info
        job_info['files']['pdb'] = os.path.basename(job_info['files']['pdb']).replace('.pdb', '')
        if 'ligand' in job_info['files'].keys():
            job_info['files']['ligand'] = os.path.basename(job_info['files']['ligand']).replace('.pdb', '')

        return cls(job_info)

    
    def export(self):
        # Prepare base file
        base_dir = os.path.join(self.output_directory, self.id)

        try:
            os.mkdir(base_dir)
        except:
            pass

        # Export cavity
        cavity_fn = os.path.join(base_dir, f'{self.base_name}.KVFinder.output.pdb')
        with open(cavity_fn, 'w') as f:
            f.write(self.cavity)

        # Export report
        report_fn = os.path.join(base_dir, f'{self.base_name}.KVFinder.results.toml')
        report = toml.loads(self.report)
        report['FILES_PATH']['INPUT'] = self.pdb
        report['FILES_PATH']['LIGAND'] = self.ligand
        report['FILES_PATH']['OUTPUT'] = cavity_fn
        with open(report_fn, 'w') as f:
            f.write('# TOML results file for parKVFinder software')
            toml.dump(o=report, f=f)
   
        # Export log
        log_fn = os.path.join(base_dir, 'KVFinder.log')
        with open(log_fn, 'w') as f:
            for line in self.log.split('\n'):
                if 'Running parKVFinder for: ' in line:
                    line = f'Running parKVFinder for job ID: {self.id}'
                    f.write(f'{line}\n')
                elif 'Dictionary: ' in line:
                    pass
                else:
                    f.write(f'{line}\n')

        # Export parameters
        if not self.id_added_manually:
            parameter_fn = os.path.join(self.output_directory, self.id, f'{self.base_name}_parameters.toml')
            with open(parameter_fn, 'w') as f:
                f.write("# TOML configuration file for KVFinder-web job.\n\n")
                f.write("title = \"KVFinder-web parameters file\"\n\n")
                f.write(f"[files]\n")
                f.write("# The path of the input PDB file.\n")
                f.write(f"pdb = \"{self.pdb}\"\n")
                f.write("# The path for the ligand's PDB file.\n")
                if self.ligand is not None:
                    f.write(f"ligand = \"{self.ligand}\"\n")
                else:
                    f.write(f"ligand = \"-\"\n")
                f.write('\n')
                f.write(f"[settings]\n")
                f.write(f"# Settings for cavity detection.\n\n")
                settings = {'settings': self.input['settings']}
                toml.dump(o=settings, f=f)
                f.write('\n')


class Worker(QThread):

    # Signals
    id_signal = pyqtSignal(str)
    server_down = pyqtSignal()
    server_up = pyqtSignal()
    server_status_signal = pyqtSignal(bool)
    available_jobs_signal = pyqtSignal(list)

    # TODO: check if this break code
    # server_status = None
    # wait = False

    def __init__(self, server, server_status):
        super().__init__()
        self.server = server
        self.wait = False
        self.server_status = server_status


    def run(self) -> None:
        from PyQt5.QtCore import QTimer, QEventLoop
        
        counter = 0
        while True:
            
            # Wait QMessageBox signal from GUI thread that deletes unavailable jobs
            while self.wait:
                loop = QEventLoop()
                QTimer.singleShot(1000, loop.quit)
                loop.exec_()
               
            # Constantly getting available jobs
            jobs = self._get_jobs()
            self.available_jobs_signal.emit(jobs)
            print(jobs)

            # Jobs available to check status and server up
            if jobs and self.server_status:
                print("\n\nChecking job status ...")
                # Check all job ids
                for job_id in jobs:
                    print('[==> '+ job_id)

                    # Get job information 
                    job_fn = os.path.join(os.path.expanduser('~'), '.KVFinder-web', job_id, 'job.toml')
                    self.job_info = Job.load(fn=job_fn)
                    self.job_info.id = job_id

                    # Save current status
                    status = self.job_info.status

                    # Handle job status
                    if status == 'queued' or status == 'running':
                        # Get request for job results
                        self._get_results(job_id)

                    elif status == 'completed':
                        # Check if results files exist
                        output_exists = self._check_output_exists()

                        if not output_exists:
                            self._get_results(job_id)
                        else:
                            if counter == 10:
                                self._check_server_status()
                                counter = 0
                            counter += 1

                    # Wait 10 sec to next job_id
                    loop = QEventLoop()
                    QTimer.singleShot(10000, loop.quit)
                    loop.exec_()  
            
            # No jobs available to check status
            else:
                # Check server status

                while not ( status := self._check_server_status() ):
                    # Send signal that server is down
                    # self.server_status_signal.emit(status)
                    
                    print('Checking server status ... \n')
                    # Wait 60 sec to repeat
                    loop = QEventLoop()
                    QTimer.singleShot(60000, loop.quit)
                    loop.exec_()

                # Update server_status value
                self.server_status = status
                # Send signal that server is up
                # self.server_status_signal.emit(self.server_status)
            
            # Wait 10 sec to repeat
            loop = QEventLoop()
            QTimer.singleShot(10000, loop.quit)
            loop.exec_()                 


    def _get_jobs(self) -> list:       
        # Get job dir
        d = os.path.join(os.path.expanduser('~'), '.KVFinder-web/')
        
        # Get jobs availables in dir
        jobs = os.listdir(d)

        return jobs

    
    def _get_results(self, job_id) -> None:
        from PyQt5 import QtNetwork
        from PyQt5.QtCore import QUrl, QTimer, QEventLoop

        try:
            self.network_manager = QtNetwork.QNetworkAccessManager()
            # self.network_manager.finished.connect(self._handle_get_response)

            # Prepare request
            url = QUrl(f'{self.server}/{job_id}')
            request = QtNetwork.QNetworkRequest(url)
            request.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, "application/json")

            # Get Request
            self.reply = self.network_manager.get(request)
            self.reply.finished.connect(self._handle_get_response)
        except Exception as e:
            print(e)
    

    def _handle_get_response(self) -> None:
        from PyQt5 import QtNetwork
        
        # Get QNetwork error status
        error = self.reply.error()
        # print(error)

        if error == QtNetwork.QNetworkReply.NoError:

            # Read data retrived from server
            reply = json.loads(str(self.reply.readAll(), 'utf-8'))
            
            # Pass outputs to Job class
            self.job_info.output = reply
            self.job_info.status = reply['status']
            self.job_info.save(self.job_info.id)

            # Export results
            try:
                self.job_info.export()
            except:
                pass

            # Send Server Up Signal to GUI Thread
            self.server_up.emit()  

        elif error == QtNetwork.QNetworkReply.ContentNotFoundError:
            # Send Server Up Signal to GUI Thread
            self.server_up.emit()  
            
            # Send Job Id to GUI Thread
            self.wait = True
            self.id_signal.emit(self.job_info.id)

            # Remove job id from .KVFinder-web
            job_dn = os.path.join(os.path.expanduser('~'), '.KVFinder-web', self.job_info.id)
            try:
                self.erase_job_dir(job_dn)
                self.available_jobs_signal.emit(self._get_jobs())
            except:
                pass

        elif error == QtNetwork.QNetworkReply.ConnectionRefusedError:
            print("KVFinder-web server is Offline!\n")
            # Send Server Down Signal to GUI Thread 
            self.server_down.emit()


    def _check_output_exists(self):
        # Prepare base file
        base_dir = os.path.join(self.job_info.output_directory, self.job_info.id)
        
        # Get output files paths
        log = os.path.join(base_dir, 'KVFinder.log')
        report = os.path.join(base_dir, f'{self.job_info.base_name}.KVFinder.results.toml')
        cavity = os.path.join(base_dir, f'{self.job_info.base_name}.KVFinder.output.pdb')
        if not self.job_info.id_added_manually:
            parameters = os.path.join(base_dir, f'{self.job_info.base_name}_parameters.toml')
        else:
            parameters = True

        # Check if files exist
        log_exist = os.path.exists(log)
        report_exist = os.path.exists(report)
        cavity_exist = os.path.exists(cavity)
        parameters_exist = os.path.exists(parameters)

        return log_exist and report_exist and cavity_exist and parameters


    def _check_server_status(self):
        # TODO: check a better way to do this
        import urllib.request
        try:
            urllib.request.urlopen(self.server, timeout=1).getcode()
            self.server_status_signal.emit(True)
            return True
        except:
            return False
            self.server_status_signal.emit(False)


    @pyqtSlot(bool)
    def wait_status(self, status):
        self.wait = status


    @staticmethod
    def erase_job_dir(d):
        for f in os.listdir(d):
            f = os.path.join(d, f)
            if os.path.isdir(f):
                self.erase_job_dir(f)
            else:
                os.remove(f)
        os.rmdir(d)


def KVFinderWebTools() -> None:
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
