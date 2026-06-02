#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
openISP GUI Application
Image Signal Processor with Real-time Parameter Tuning
"""

import sys
import os
import csv
import numpy as np
from pathlib import Path
from collections import OrderedDict

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QSpinBox, QDoubleSpinBox, QComboBox, QPushButton,
    QFileDialog, QTabWidget, QScrollArea, QGridLayout, QGroupBox,
    QMessageBox, QSplitter, QProgressBar, QStatusBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
import cv2
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from model.dpc import DPC
from model.blc import BLC
from model.aaf import AAF
from model.awb import WBGC
from model.cnf import CNF
from model.cfa import CFA
from model.gac import GC
from model.ccm import CCM
from model.csc import CSC
from model.bnf import BNF
from model.eeh import EE
from model.fcs import FCS
from model.bcc import BCC
from model.hsc import HSC
from model.nlm import NLM


class ImageProcessingThread(QThread):
    """Background thread for image processing"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(np.ndarray)
    error = pyqtSignal(str)

    def __init__(self, rawimg, parameters, selected_modules):
        super().__init__()
        self.rawimg = rawimg
        self.parameters = parameters
        self.selected_modules = selected_modules

    def run(self):
        try:
            img = self.rawimg.copy().astype(np.float32)
            total_steps = len(self.selected_modules)
            current_step = 0

            # RAW Domain Processing
            if 'dpc' in self.selected_modules:
                dpc = DPC(img.astype(np.uint16), int(self.parameters['dpc_thres']),
                         self.parameters['dpc_mode'], int(self.parameters['dpc_clip']))
                img = dpc.execute()
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            if 'blc' in self.selected_modules:
                parameter = [int(self.parameters['bl_r']), int(self.parameters['bl_gr']),
                           int(self.parameters['bl_gb']), int(self.parameters['bl_b']),
                           int(self.parameters['alpha']), int(self.parameters['beta'])]
                blc = BLC(img.astype(np.uint16), parameter, self.parameters['bayer_pattern'],
                         int(self.parameters['blc_clip']))
                img = blc.execute()
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            if 'aaf' in self.selected_modules:
                aaf = AAF(img.astype(np.uint16))
                img = aaf.execute()
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            if 'awb' in self.selected_modules:
                parameter = [float(self.parameters['r_gain']), float(self.parameters['gr_gain']),
                           float(self.parameters['gb_gain']), float(self.parameters['b_gain'])]
                awb = WBGC(img.astype(np.uint16), parameter, self.parameters['bayer_pattern'],
                          int(self.parameters['awb_clip']))
                img = awb.execute()
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            if 'cnf' in self.selected_modules:
                parameter = [float(self.parameters['r_gain']), float(self.parameters['gr_gain']),
                           float(self.parameters['gb_gain']), float(self.parameters['b_gain'])]
                cnf = CNF(img.astype(np.uint16), self.parameters['bayer_pattern'], 0, parameter, 1023)
                img = cnf.execute()
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            # RGB Domain Processing
            if 'cfa' in self.selected_modules:
                cfa = CFA(img.astype(np.uint16), self.parameters['cfa_mode'],
                         self.parameters['bayer_pattern'], int(self.parameters['cfa_clip']))
                img = cfa.execute()
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            if 'ccm' in self.selected_modules:
                ccm_matrix = np.array([
                    [int(self.parameters['ccm_00']), int(self.parameters['ccm_01']),
                     int(self.parameters['ccm_02']), int(self.parameters['ccm_03'])],
                    [int(self.parameters['ccm_10']), int(self.parameters['ccm_11']),
                     int(self.parameters['ccm_12']), int(self.parameters['ccm_13'])],
                    [int(self.parameters['ccm_20']), int(self.parameters['ccm_21']),
                     int(self.parameters['ccm_22']), int(self.parameters['ccm_23'])]
                ])
                ccm = CCM(img.astype(np.uint16), ccm_matrix)
                img = ccm.execute()
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            if 'gc' in self.selected_modules:
                bw = 10
                gamma = 0.5
                maxval = pow(2, bw)
                ind = range(0, maxval)
                val = [round(pow(float(i) / maxval, gamma) * maxval) for i in ind]
                lut = dict(zip(ind, val))
                gc = GC(img.astype(np.uint16), lut, 'rgb')
                img = gc.execute()
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            # Color Space Conversion
            if 'csc' in self.selected_modules:
                csc_matrix = np.array([
                    [1024 * float(self.parameters['csc_00']), 1024 * float(self.parameters['csc_01']),
                     1024 * float(self.parameters['csc_02']), 1024 * float(self.parameters['csc_03'])],
                    [1024 * float(self.parameters['csc_10']), 1024 * float(self.parameters['csc_11']),
                     1024 * float(self.parameters['csc_12']), 1024 * float(self.parameters['csc_13'])],
                    [1024 * float(self.parameters['csc_20']), 1024 * float(self.parameters['csc_21']),
                     1024 * float(self.parameters['csc_22']), 1024 * float(self.parameters['csc_23'])]
                ])
                csc = CSC(img.astype(np.uint16), csc_matrix)
                img = csc.execute()
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            # YUV Domain Processing
            if 'nlm' in self.selected_modules:
                nlm = NLM(img[:, :, 0].astype(np.uint16), 1, 4,
                         int(self.parameters['nlm_h']), int(self.parameters['nlm_clip']))
                img_nlm = nlm.execute()
                img[:, :, 0] = img_nlm
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            if 'bnf' in self.selected_modules:
                bnf_dw = np.array([
                    [int(self.parameters['bnf_dw_00']), int(self.parameters['bnf_dw_01']),
                     int(self.parameters['bnf_dw_02']), int(self.parameters['bnf_dw_03']),
                     int(self.parameters['bnf_dw_04'])],
                    [int(self.parameters['bnf_dw_10']), int(self.parameters['bnf_dw_11']),
                     int(self.parameters['bnf_dw_12']), int(self.parameters['bnf_dw_13']),
                     int(self.parameters['bnf_dw_14'])],
                    [int(self.parameters['bnf_dw_20']), int(self.parameters['bnf_dw_21']),
                     int(self.parameters['bnf_dw_22']), int(self.parameters['bnf_dw_23']),
                     int(self.parameters['bnf_dw_24'])],
                    [int(self.parameters['bnf_dw_30']), int(self.parameters['bnf_dw_31']),
                     int(self.parameters['bnf_dw_32']), int(self.parameters['bnf_dw_33']),
                     int(self.parameters['bnf_dw_34'])],
                    [int(self.parameters['bnf_dw_40']), int(self.parameters['bnf_dw_41']),
                     int(self.parameters['bnf_dw_42']), int(self.parameters['bnf_dw_43']),
                     int(self.parameters['bnf_dw_44'])]
                ])
                bnf_rw = [int(self.parameters['bnf_rw_0']), int(self.parameters['bnf_rw_1']),
                         int(self.parameters['bnf_rw_2']), int(self.parameters['bnf_rw_3'])]
                bnf_rthres = [int(self.parameters['bnf_rthres_0']), int(self.parameters['bnf_rthres_1']),
                             int(self.parameters['bnf_rthres_2'])]
                bnf = BNF(img[:, :, 0].astype(np.uint16), bnf_dw, bnf_rw, bnf_rthres,
                         int(self.parameters['bnf_clip']))
                img_bnf = bnf.execute()
                img[:, :, 0] = img_bnf
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            if 'ee' in self.selected_modules:
                edge_filter = np.array([
                    [int(self.parameters['edge_filter_00']), int(self.parameters['edge_filter_01']),
                     int(self.parameters['edge_filter_02']), int(self.parameters['edge_filter_03']),
                     int(self.parameters['edge_filter_04'])],
                    [int(self.parameters['edge_filter_10']), int(self.parameters['edge_filter_11']),
                     int(self.parameters['edge_filter_12']), int(self.parameters['edge_filter_13']),
                     int(self.parameters['edge_filter_14'])],
                    [int(self.parameters['edge_filter_20']), int(self.parameters['edge_filter_21']),
                     int(self.parameters['edge_filter_22']), int(self.parameters['edge_filter_23']),
                     int(self.parameters['edge_filter_24'])]
                ])
                ee_gain = [int(self.parameters['ee_gain_min']), int(self.parameters['ee_gain_max'])]
                ee_thres = [int(self.parameters['ee_thres_min']), int(self.parameters['ee_thres_max'])]
                ee_emclip = [int(self.parameters['ee_emclip_min']), int(self.parameters['ee_emclip_max'])]
                ee = EE(img[:, :, 0].astype(np.uint16), edge_filter, ee_gain, ee_thres, ee_emclip)
                img_ee, _ = ee.execute()
                img[:, :, 0] = img_ee
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            if 'fcs' in self.selected_modules:
                fcs_edge = [int(self.parameters['fcs_edge_min']), int(self.parameters['fcs_edge_max'])]
                fcs = FCS(img[:, :, 1:3], np.zeros_like(img[:, :, 0]), fcs_edge,
                         int(self.parameters['fcs_gain']), int(self.parameters['fcs_intercept']),
                         int(self.parameters['fcs_slope']))
                img_fcs = fcs.execute()
                img[:, :, 1:3] = img_fcs
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            if 'hsc' in self.selected_modules:
                hsc = HSC(img[:, :, 1:3], int(self.parameters['hue']),
                         int(self.parameters['saturation']), int(self.parameters['hsc_clip']))
                img_hsc = hsc.execute()
                img[:, :, 1:3] = img_hsc
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            if 'bcc' in self.selected_modules:
                contrast = int(self.parameters['contrast']) / pow(2, 5)
                bcc = BCC(img[:, :, 0].astype(np.uint16), int(self.parameters['brightness']),
                         contrast, int(self.parameters['bcc_clip']))
                img_bcc = bcc.execute()
                img[:, :, 0] = img_bcc
                current_step += 1
                self.progress.emit(int((current_step / total_steps) * 100))

            self.finished.emit(img.astype(np.uint8))

        except Exception as e:
            self.error.emit(f"Processing error: {str(e)}")


class ParameterPanel(QWidget):
    """Parameter control panel"""
    parameter_changed = pyqtSignal(dict)

    def __init__(self, parameters):
        super().__init__()
        self.parameters = parameters
        self.controls = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        grid = QGridLayout(content_widget)

        row = 0
        for param_name, param_info in self.parameters.items():
            label = QLabel(f"{param_name}:")
            label.setFont(QFont('Arial', 9))

            param_type = param_info.get('type', 'int')
            default_value = param_info.get('value', 0)

            if param_type == 'float':
                control = QDoubleSpinBox()
                control.setRange(-1000, 1000)
                control.setSingleStep(0.1)
                control.setValue(float(default_value))
            elif param_type in ['int', 'slider']:
                if param_type == 'slider':
                    control = QSlider(Qt.Horizontal)
                    control.setRange(-255, 255)
                    control.setValue(int(default_value))
                else:
                    control = QSpinBox()
                    control.setRange(-1000, 2048)
                    control.setValue(int(default_value))
            else:
                control = QComboBox()
                control.addItems(param_info.get('options', []))

            self.controls[param_name] = control
            control.valueChanged.connect(self.on_parameter_changed)

            grid.addWidget(label, row, 0)
            grid.addWidget(control, row, 1)
            row += 1

        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        self.setLayout(layout)

    def on_parameter_changed(self):
        params = {}
        for name, control in self.controls.items():
            if isinstance(control, (QSpinBox, QDoubleSpinBox)):
                params[name] = control.value()
            elif isinstance(control, QSlider):
                params[name] = control.value()
            else:
                params[name] = control.currentText()
        self.parameter_changed.emit(params)

    def get_parameters(self):
        params = {}
        for name, control in self.controls.items():
            if isinstance(control, (QSpinBox, QDoubleSpinBox)):
                params[name] = control.value()
            elif isinstance(control, QSlider):
                params[name] = control.value()
            else:
                params[name] = control.currentText()
        return params


class ImageCanvas(FigureCanvasQTAgg):
    """Matplotlib canvas for image display"""

    def __init__(self, parent=None):
        fig = Figure(figsize=(5, 4), dpi=100)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

    def display_image(self, image):
        self.axes.clear()
        if len(image.shape) == 3 and image.shape[2] == 3:
            self.axes.imshow(cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_YUV2RGB))
        else:
            self.axes.imshow(image.astype(np.uint8), cmap='gray')
        self.axes.axis('off')
        self.draw()


class ISPGUIApplication(QMainWindow):
    """Main ISP GUI Application"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('OpenISP - Image Signal Processor GUI')
        self.setGeometry(100, 100, 1400, 900)

        self.raw_image = None
        self.processed_image = None
        self.parameters = {}
        self.load_parameters()

        self.init_ui()
        self.processing_thread = None

    def load_parameters(self):
        """Load parameters from config.csv"""
        config_path = './config/config.csv'
        self.parameters = OrderedDict()

        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=',')
                for row in reader:
                    if len(row) >= 2:
                        param_name = row[0].strip()
                        param_value = row[1].strip()
                        param_desc = row[2].strip() if len(row) > 2 else ''

                        # Determine parameter type
                        if param_name in ['bayer_pattern', 'dpc_mode', 'cfa_mode']:
                            param_type = 'combo'
                            options = ['rggb', 'bggr', 'gbrg', 'grbg'] if param_name == 'bayer_pattern' else \
                                     ['gradient'] if param_name == 'dpc_mode' else ['malvar', 'bilinear']
                        elif any(f in param_name for f in ['_gain', '_alpha', '_beta', 'csc']):
                            param_type = 'float'
                        else:
                            param_type = 'int'

                        self.parameters[param_name] = {
                            'value': param_value,
                            'type': param_type,
                            'description': param_desc,
                            'options': options if param_type == 'combo' else []
                        }
        except FileNotFoundError:
            QMessageBox.warning(self, 'Warning', f'Config file not found: {config_path}')

    def init_ui(self):
        """Initialize UI components"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # Left Panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # File operations
        file_group = QGroupBox('File Operations')
        file_layout = QVBoxLayout()
        load_btn = QPushButton('Load RAW Image')
        load_btn.clicked.connect(self.load_image)
        save_btn = QPushButton('Save Processed Image')
        save_btn.clicked.connect(self.save_image)
        file_layout.addWidget(load_btn)
        file_layout.addWidget(save_btn)
        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)

        # Module selection
        module_group = QGroupBox('Select Processing Modules')
        module_layout = QVBoxLayout()
        self.module_list = QListWidget()
        modules = ['dpc', 'blc', 'aaf', 'awb', 'cnf', 'cfa', 'ccm', 'gc', 'csc', 'nlm', 'bnf', 'ee', 'fcs', 'hsc', 'bcc']
        for module in modules:
            self.module_list.addItem(module)
            item = self.module_list.item(self.module_list.count() - 1)
            item.setCheckState(Qt.Checked)
        module_layout.addWidget(self.module_list)
        module_group.setLayout(module_layout)
        left_layout.addWidget(module_group)

        # Parameter panel
        param_group = QGroupBox('Parameters')
        param_layout = QVBoxLayout()
        self.param_panel = ParameterPanel(self.parameters)
        self.param_panel.parameter_changed.connect(self.on_parameters_changed)
        param_layout.addWidget(self.param_panel)
        param_group.setLayout(param_layout)
        left_layout.addWidget(param_group)

        # Process button
        process_btn = QPushButton('Process Image')
        process_btn.clicked.connect(self.process_image)
        left_layout.addWidget(process_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        left_layout.addWidget(self.progress_bar)

        left_layout.addStretch()

        # Right Panel - Image Display
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Original image
        original_group = QGroupBox('Original Image')
        original_layout = QVBoxLayout()
        self.original_canvas = ImageCanvas(self)
        original_layout.addWidget(self.original_canvas)
        original_group.setLayout(original_layout)

        # Processed image
        processed_group = QGroupBox('Processed Image')
        processed_layout = QVBoxLayout()
        self.processed_canvas = ImageCanvas(self)
        processed_layout.addWidget(self.processed_canvas)
        processed_group.setLayout(processed_layout)

        right_layout.addWidget(original_group, 1)
        right_layout.addWidget(processed_group, 1)

        # Add panels to main layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        # Status bar
        self.statusBar().showMessage('Ready')

    def load_image(self):
        """Load image file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Open Image', '', 'RAW Files (*.RAW);;Image Files (*.jpg *.png *.bmp)'
        )

        if file_path:
            try:
                if file_path.endswith('.RAW'):
                    self.raw_image = np.fromfile(file_path, dtype='uint16')
                    self.raw_image = self.raw_image.reshape([1280, 720])
                else:
                    img = cv2.imread(file_path)
                    self.raw_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.uint16)

                self.original_canvas.display_image(self.raw_image)
                self.statusBar().showMessage(f'Loaded: {file_path}')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to load image: {str(e)}')

    def save_image(self):
        """Save processed image"""
        if self.processed_image is None:
            QMessageBox.warning(self, 'Warning', 'No processed image to save')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Save Image', '', 'PNG Files (*.png);;JPG Files (*.jpg)'
        )

        if file_path:
            try:
                if self.processed_image.shape[2] == 3:
                    output = cv2.cvtColor(self.processed_image.astype(np.uint8), cv2.COLOR_YUV2BGR)
                else:
                    output = self.processed_image.astype(np.uint8)
                cv2.imwrite(file_path, output)
                self.statusBar().showMessage(f'Saved: {file_path}')
                QMessageBox.information(self, 'Success', 'Image saved successfully')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to save image: {str(e)}')

    def on_parameters_changed(self, params):
        """Handle parameter changes"""
        pass

    def process_image(self):
        """Process image with selected modules"""
        if self.raw_image is None:
            QMessageBox.warning(self, 'Warning', 'Please load an image first')
            return

        # Get selected modules
        selected_modules = []
        for i in range(self.module_list.count()):
            if self.module_list.item(i).checkState() == Qt.Checked:
                selected_modules.append(self.module_list.item(i).text())

        # Get current parameters
        params = self.param_panel.get_parameters()

        # Start processing thread
        self.processing_thread = ImageProcessingThread(self.raw_image, params, selected_modules)
        self.processing_thread.progress.connect(self.update_progress)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.error.connect(self.on_processing_error)
        self.processing_thread.start()

        self.statusBar().showMessage('Processing...')

    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)

    def on_processing_finished(self, image):
        """Handle processing completion"""
        self.processed_image = image
        self.processed_canvas.display_image(image)
        self.progress_bar.setValue(100)
        self.statusBar().showMessage('Processing completed')

    def on_processing_error(self, error_msg):
        """Handle processing error"""
        QMessageBox.critical(self, 'Processing Error', error_msg)
        self.statusBar().showMessage('Processing failed')


def main():
    app = QApplication(sys.argv)
    window = ISPGUIApplication()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
