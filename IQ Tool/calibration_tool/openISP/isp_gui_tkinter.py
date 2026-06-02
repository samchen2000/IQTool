#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenISP GUI Application - Tkinter Version
Simpler alternative without matplotlib dependency
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import numpy as np
import csv
from collections import OrderedDict
from PIL import Image, ImageTk

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


class ISPProcessingEngine:
    """核心ISP處理引擎"""
    
    def __init__(self):
        self.parameters = {}
        self.load_parameters()
        
    def load_parameters(self):
        """從config.csv加載參數"""
        config_path = './config/config.csv'
        self.parameters = OrderedDict()
        
        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=',')
                for row in reader:
                    if len(row) >= 2:
                        param_name = row[0].strip()
                        param_value = row[1].strip()
                        self.parameters[param_name] = param_value
        except FileNotFoundError:
            print(f'Warning: Config file not found: {config_path}')
    
    def process(self, rawimg, selected_modules, param_dict, progress_callback=None):
        """處理圖像"""
        try:
            img = rawimg.copy().astype(np.float32)
            total_steps = len(selected_modules)
            current_step = 0
            
            # RAW Domain
            if 'dpc' in selected_modules:
                dpc = DPC(img.astype(np.uint16), int(param_dict.get('dpc_thres', 30)),
                         param_dict.get('dpc_mode', 'gradient'), int(param_dict.get('dpc_clip', 1023)))
                img = dpc.execute()
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            if 'blc' in selected_modules:
                parameter = [int(param_dict.get('bl_r', 0)), int(param_dict.get('bl_gr', 0)),
                           int(param_dict.get('bl_gb', 0)), int(param_dict.get('bl_b', 0)),
                           int(param_dict.get('alpha', 0)), int(param_dict.get('beta', 0))]
                blc = BLC(img.astype(np.uint16), parameter, param_dict.get('bayer_pattern', 'rggb'),
                         int(param_dict.get('blc_clip', 1023)))
                img = blc.execute()
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            if 'aaf' in selected_modules:
                aaf = AAF(img.astype(np.uint16))
                img = aaf.execute()
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            if 'awb' in selected_modules:
                parameter = [float(param_dict.get('r_gain', 1.5)), float(param_dict.get('gr_gain', 1.0)),
                           float(param_dict.get('gb_gain', 1.0)), float(param_dict.get('b_gain', 1.1))]
                awb = WBGC(img.astype(np.uint16), parameter, param_dict.get('bayer_pattern', 'rggb'),
                          int(param_dict.get('awb_clip', 1023)))
                img = awb.execute()
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            if 'cnf' in selected_modules:
                parameter = [float(param_dict.get('r_gain', 1.5)), float(param_dict.get('gr_gain', 1.0)),
                           float(param_dict.get('gb_gain', 1.0)), float(param_dict.get('b_gain', 1.1))]
                cnf = CNF(img.astype(np.uint16), param_dict.get('bayer_pattern', 'rggb'), 0, parameter, 1023)
                img = cnf.execute()
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            # RGB Domain
            if 'cfa' in selected_modules:
                cfa = CFA(img.astype(np.uint16), param_dict.get('cfa_mode', 'malvar'),
                         param_dict.get('bayer_pattern', 'rggb'), int(param_dict.get('cfa_clip', 1023)))
                img = cfa.execute()
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            if 'ccm' in selected_modules:
                ccm_matrix = np.array([
                    [int(param_dict.get('ccm_00', 1024)), int(param_dict.get('ccm_01', 0)),
                     int(param_dict.get('ccm_02', 0)), int(param_dict.get('ccm_03', 0))],
                    [int(param_dict.get('ccm_10', 0)), int(param_dict.get('ccm_11', 1024)),
                     int(param_dict.get('ccm_12', 0)), int(param_dict.get('ccm_13', 0))],
                    [int(param_dict.get('ccm_20', 0)), int(param_dict.get('ccm_21', 0)),
                     int(param_dict.get('ccm_22', 1024)), int(param_dict.get('ccm_23', 0))]
                ])
                ccm = CCM(img.astype(np.uint16), ccm_matrix)
                img = ccm.execute()
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            if 'gc' in selected_modules:
                bw = 10
                gamma = 0.5
                maxval = pow(2, bw)
                ind = range(0, maxval)
                val = [round(pow(float(i) / maxval, gamma) * maxval) for i in ind]
                lut = dict(zip(ind, val))
                gc = GC(img.astype(np.uint16), lut, 'rgb')
                img = gc.execute()
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            # Color Space Conversion
            if 'csc' in selected_modules:
                csc_matrix = np.array([
                    [1024 * float(param_dict.get('csc_00', 0.257)), 1024 * float(param_dict.get('csc_01', 0.504)),
                     1024 * float(param_dict.get('csc_02', 0.098)), 1024 * float(param_dict.get('csc_03', 16))],
                    [1024 * float(param_dict.get('csc_10', -0.148)), 1024 * float(param_dict.get('csc_11', -0.291)),
                     1024 * float(param_dict.get('csc_12', 0.439)), 1024 * float(param_dict.get('csc_13', 128))],
                    [1024 * float(param_dict.get('csc_20', 0.439)), 1024 * float(param_dict.get('csc_21', -0.368)),
                     1024 * float(param_dict.get('csc_22', -0.071)), 1024 * float(param_dict.get('csc_23', 128))]
                ])
                csc = CSC(img.astype(np.uint16), csc_matrix)
                img = csc.execute()
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            # YUV Domain
            if 'nlm' in selected_modules:
                nlm = NLM(img[:, :, 0].astype(np.uint16), 1, 4,
                         int(param_dict.get('nlm_h', 10)), int(param_dict.get('nlm_clip', 255)))
                img_nlm = nlm.execute()
                img[:, :, 0] = img_nlm
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            if 'bnf' in selected_modules:
                bnf_dw = np.array([
                    [int(param_dict.get('bnf_dw_00', 8)), int(param_dict.get('bnf_dw_01', 12)),
                     int(param_dict.get('bnf_dw_02', 32)), int(param_dict.get('bnf_dw_03', 12)),
                     int(param_dict.get('bnf_dw_04', 8))],
                    [int(param_dict.get('bnf_dw_10', 12)), int(param_dict.get('bnf_dw_11', 64)),
                     int(param_dict.get('bnf_dw_12', 128)), int(param_dict.get('bnf_dw_13', 64)),
                     int(param_dict.get('bnf_dw_14', 12))],
                    [int(param_dict.get('bnf_dw_20', 32)), int(param_dict.get('bnf_dw_21', 128)),
                     int(param_dict.get('bnf_dw_22', 1024)), int(param_dict.get('bnf_dw_23', 128)),
                     int(param_dict.get('bnf_dw_24', 32))],
                    [int(param_dict.get('bnf_dw_30', 12)), int(param_dict.get('bnf_dw_31', 64)),
                     int(param_dict.get('bnf_dw_32', 128)), int(param_dict.get('bnf_dw_33', 64)),
                     int(param_dict.get('bnf_dw_34', 12))],
                    [int(param_dict.get('bnf_dw_40', 8)), int(param_dict.get('bnf_dw_41', 12)),
                     int(param_dict.get('bnf_dw_42', 32)), int(param_dict.get('bnf_dw_43', 12)),
                     int(param_dict.get('bnf_dw_44', 8))]
                ])
                bnf_rw = [int(param_dict.get('bnf_rw_0', 1)), int(param_dict.get('bnf_rw_1', 8)),
                         int(param_dict.get('bnf_rw_2', 16)), int(param_dict.get('bnf_rw_3', 32))]
                bnf_rthres = [int(param_dict.get('bnf_rthres_0', 128)), int(param_dict.get('bnf_rthres_1', 32)),
                             int(param_dict.get('bnf_rthres_2', 8))]
                bnf = BNF(img[:, :, 0].astype(np.uint16), bnf_dw, bnf_rw, bnf_rthres,
                         int(param_dict.get('bnf_clip', 255)))
                img_bnf = bnf.execute()
                img[:, :, 0] = img_bnf
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            if 'ee' in selected_modules:
                edge_filter = np.array([
                    [int(param_dict.get('edge_filter_00', -1)), int(param_dict.get('edge_filter_01', 0)),
                     int(param_dict.get('edge_filter_02', -1)), int(param_dict.get('edge_filter_03', 0)),
                     int(param_dict.get('edge_filter_04', -1))],
                    [int(param_dict.get('edge_filter_10', -1)), int(param_dict.get('edge_filter_11', 0)),
                     int(param_dict.get('edge_filter_12', 8)), int(param_dict.get('edge_filter_13', 0)),
                     int(param_dict.get('edge_filter_14', -1))],
                    [int(param_dict.get('edge_filter_20', -1)), int(param_dict.get('edge_filter_21', 0)),
                     int(param_dict.get('edge_filter_22', -1)), int(param_dict.get('edge_filter_23', 0)),
                     int(param_dict.get('edge_filter_24', -1))]
                ])
                ee_gain = [int(param_dict.get('ee_gain_min', 32)), int(param_dict.get('ee_gain_max', 128))]
                ee_thres = [int(param_dict.get('ee_thres_min', 32)), int(param_dict.get('ee_thres_max', 64))]
                ee_emclip = [int(param_dict.get('ee_emclip_min', -64)), int(param_dict.get('ee_emclip_max', 64))]
                ee = EE(img[:, :, 0].astype(np.uint16), edge_filter, ee_gain, ee_thres, ee_emclip)
                img_ee, _ = ee.execute()
                img[:, :, 0] = img_ee
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            if 'fcs' in selected_modules:
                fcs_edge = [int(param_dict.get('fcs_edge_min', 32)), int(param_dict.get('fcs_edge_max', 64))]
                fcs = FCS(img[:, :, 1:3], np.zeros_like(img[:, :, 0]), fcs_edge,
                         int(param_dict.get('fcs_gain', 32)), int(param_dict.get('fcs_intercept', 2)),
                         int(param_dict.get('fcs_slope', 3)))
                img_fcs = fcs.execute()
                img[:, :, 1:3] = img_fcs
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            if 'hsc' in selected_modules:
                hsc = HSC(img[:, :, 1:3], int(param_dict.get('hue', 128)),
                         int(param_dict.get('saturation', 256)), int(param_dict.get('hsc_clip', 255)))
                img_hsc = hsc.execute()
                img[:, :, 1:3] = img_hsc
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            if 'bcc' in selected_modules:
                contrast = int(param_dict.get('contrast', 10)) / pow(2, 5)
                bcc = BCC(img[:, :, 0].astype(np.uint16), int(param_dict.get('brightness', 10)),
                         contrast, int(param_dict.get('bcc_clip', 255)))
                img_bcc = bcc.execute()
                img[:, :, 0] = img_bcc
                current_step += 1
                if progress_callback:
                    progress_callback(int((current_step / total_steps) * 100))
            
            return img.astype(np.uint8)
        
        except Exception as e:
            raise Exception(f"Processing error: {str(e)}")


class ISPGUIApplication(tk.Tk):
    """OpenISP GUI應用主窗口"""
    
    def __init__(self):
        super().__init__()
        self.title('OpenISP - Image Signal Processor GUI')
        self.geometry('1200x800')
        
        self.engine = ISPProcessingEngine()
        self.raw_image = None
        self.processed_image = None
        self.processing = False
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # Main Frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left Panel
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5)
        
        # File Operations
        file_group = ttk.LabelFrame(left_frame, text='File Operations')
        file_group.pack(fill=tk.X, pady=5)
        
        ttk.Button(file_group, text='Load RAW Image', command=self.load_image).pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(file_group, text='Save Processed Image', command=self.save_image).pack(fill=tk.X, padx=5, pady=5)
        
        # Module Selection
        module_group = ttk.LabelFrame(left_frame, text='Processing Modules')
        module_group.pack(fill=tk.BOTH, expand=True, pady=5)
        
        canvas = tk.Canvas(module_group, height=150)
        scrollbar = ttk.Scrollbar(module_group, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.module_vars = {}
        for module in ['dpc', 'blc', 'aaf', 'awb', 'cnf', 'cfa', 'ccm', 'gc', 'csc', 'nlm', 'bnf', 'ee', 'fcs', 'hsc', 'bcc']:
            var = tk.BooleanVar(value=True)
            self.module_vars[module] = var
            ttk.Checkbutton(scrollable_frame, text=module.upper(), variable=var).pack(anchor=tk.W, padx=5)
        
        canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Parameter Frame
        param_group = ttk.LabelFrame(left_frame, text='Key Parameters')
        param_group.pack(fill=tk.BOTH, expand=True, pady=5)
        
        param_canvas = tk.Canvas(param_group, height=200)
        param_scrollbar = ttk.Scrollbar(param_group, orient=tk.VERTICAL, command=param_canvas.yview)
        param_scrollable = ttk.Frame(param_canvas)
        
        param_scrollable.bind(
            "<Configure>",
            lambda e: param_canvas.configure(scrollregion=param_canvas.bbox("all"))
        )
        
        param_canvas.create_window((0, 0), window=param_scrollable, anchor="nw")
        param_canvas.configure(yscrollcommand=param_scrollbar.set)
        
        self.param_vars = {}
        params_to_show = ['dpc_thres', 'bl_r', 'r_gain', 'b_gain', 'hue', 'saturation', 'brightness', 'contrast']
        
        for param in params_to_show:
            frame = ttk.Frame(param_scrollable)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            default_val = self.engine.parameters.get(param, '0')
            ttk.Label(frame, text=f"{param}:", width=15).pack(side=tk.LEFT)
            
            var = tk.StringVar(value=default_val)
            self.param_vars[param] = var
            ttk.Entry(frame, textvariable=var, width=10).pack(side=tk.LEFT, padx=5)
        
        param_canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        param_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Process Button
        ttk.Button(left_frame, text='▶ Process Image', command=self.process_image).pack(fill=tk.X, pady=10)
        
        # Progress Bar
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(left_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(left_frame, text='Ready', relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X, pady=5)
        
        # Right Panel - Image Display
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Original Image
        orig_group = ttk.LabelFrame(right_frame, text='Original Image')
        orig_group.pack(fill=tk.BOTH, expand=True, pady=5)
        self.orig_label = tk.Label(orig_group, bg='gray', width=400, height=250)
        self.orig_label.pack(fill=tk.BOTH, expand=True)
        
        # Processed Image
        proc_group = ttk.LabelFrame(right_frame, text='Processed Image')
        proc_group.pack(fill=tk.BOTH, expand=True, pady=5)
        self.proc_label = tk.Label(proc_group, bg='gray', width=400, height=250)
        self.proc_label.pack(fill=tk.BOTH, expand=True)
    
    def load_image(self):
        """加載圖像"""
        file_path = filedialog.askopenfilename(
            title='Open Image',
            filetypes=[('RAW Files', '*.RAW'), ('Image Files', '*.jpg *.png *.bmp')]
        )
        
        if file_path:
            try:
                if file_path.endswith('.RAW'):
                    self.raw_image = np.fromfile(file_path, dtype='uint16')
                    self.raw_image = self.raw_image.reshape([3264, 2448])
                else:
                    from PIL import Image as PILImage
                    img = PILImage.open(file_path).convert('L')
                    self.raw_image = np.array(img).astype(np.uint16)
                
                self.display_image(self.raw_image, self.orig_label)
                self.status_label.config(text=f'Loaded: {file_path}')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to load: {e}')
    
    def save_image(self):
        """保存圖像"""
        if self.processed_image is None:
            messagebox.showwarning('Warning', 'No processed image to save')
            return
        
        file_path = filedialog.asksaveasfilename(
            title='Save Image',
            filetypes=[('PNG Files', '*.png'), ('JPG Files', '*.jpg')]
        )
        
        if file_path:
            try:
                img = Image.fromarray(self.processed_image.astype(np.uint8))
                img.save(file_path)
                self.status_label.config(text=f'Saved: {file_path}')
                messagebox.showinfo('Success', 'Image saved successfully')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to save: {e}')
    
    def display_image(self, image, label):
        """顯示圖像"""
        # 縮小至合適大小
        display_size = (400, 250)
        if len(image.shape) == 3:
            pil_img = Image.fromarray(image.astype(np.uint8))
        else:
            # 灰度圖像
            norm_img = ((image - image.min()) / (image.max() - image.min() + 1e-6) * 255).astype(np.uint8)
            pil_img = Image.fromarray(norm_img)
        
        pil_img.thumbnail(display_size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(pil_img)
        
        label.config(image=photo)
        label.image = photo
    
    def process_image(self):
        """處理圖像"""
        if self.raw_image is None:
            messagebox.showwarning('Warning', 'Please load an image first')
            return
        
        if self.processing:
            messagebox.showwarning('Warning', 'Processing is already running')
            return
        
        # Get selected modules
        selected = [m for m, var in self.module_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning('Warning', 'Please select at least one module')
            return
        
        # Get parameters
        params = {}
        for param_name, param_value in self.engine.parameters.items():
            if param_name in self.param_vars:
                try:
                    params[param_name] = float(self.param_vars[param_name].get())
                except:
                    params[param_name] = param_value
            else:
                params[param_name] = param_value
        
        self.processing = True
        self.status_label.config(text='Processing...')
        
        def process_thread():
            try:
                def progress_cb(val):
                    self.progress_var.set(val)
                    self.update()
                
                result = self.engine.process(self.raw_image, selected, params, progress_cb)
                self.processed_image = result
                self.display_image(result, self.proc_label)
                
                self.progress_var.set(100)
                self.status_label.config(text='Completed!')
                self.processing = False
            except Exception as e:
                messagebox.showerror('Error', f'Processing failed: {e}')
                self.status_label.config(text='Failed')
                self.processing = False
        
        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()


if __name__ == '__main__':
    app = ISPGUIApplication()
    app.mainloop()
