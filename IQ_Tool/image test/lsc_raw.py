import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk
import os
import csv
from scipy.interpolate import griddata
from scipy.ndimage import convolve, gaussian_filter

class LSCToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mesh LSC 校正工具")
        self.root.geometry("1200x800")

        # 變數初始化
        self.raw_image_data = None
        self.corrected_raw_data = None
        self.gain_map_data = {}
        self.image_params = {
            "width": tk.StringVar(value="3264"),
            "height": tk.StringVar(value="2448"),
            "pattern": tk.StringVar(value="BGGR"),
            "depth": tk.StringVar(value="16-bit")
        }
        self.grid_size = tk.IntVar(value=16)

        # --- UI 佈局 ---
        # 主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. 控制面板框架
        control_panel = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_panel.pack(fill=tk.X, pady=5)

        # 檔案選擇
        file_frame = ttk.Frame(control_panel)
        file_frame.pack(fill=tk.X, pady=5)
        ttk.Label(file_frame, text="RAW 檔案:").pack(side=tk.LEFT, padx=5)
        self.filepath_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.filepath_var, width=60).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(file_frame, text="瀏覽...", command=self.browse_file).pack(side=tk.LEFT, padx=5)

        # 影像參數
        param_frame = ttk.Frame(control_panel)
        param_frame.pack(fill=tk.X, pady=5)
        
        # 解析度
        ttk.Label(param_frame, text="解析度:").pack(side=tk.LEFT, padx=5)
        resolutions = ["3264x2448", "2592x1944", "1920x1080"]
        self.res_combobox = ttk.Combobox(param_frame, values=resolutions, width=12)
        self.res_combobox.set("3264x2448")
        self.res_combobox.bind("<<ComboboxSelected>>", self.update_resolution)
        self.res_combobox.pack(side=tk.LEFT, padx=5)

        # 色彩排列
        ttk.Label(param_frame, text="色彩排列:").pack(side=tk.LEFT, padx=5)
        patterns = ["RGGB", "BGGR", "GRBG", "GBRG"]
        ttk.Combobox(param_frame, textvariable=self.image_params["pattern"], values=patterns, width=8).pack(side=tk.LEFT, padx=5)

        # 資料深度
        ttk.Label(param_frame, text="資料深度:").pack(side=tk.LEFT, padx=5)
        depths = ["16-bit", "12-bit", "10-bit"]
        ttk.Combobox(param_frame, textvariable=self.image_params["depth"], values=depths, width=8).pack(side=tk.LEFT, padx=5)

        # 網格大小
        grid_frame = ttk.Frame(control_panel)
        grid_frame.pack(fill=tk.X, pady=5)
        ttk.Label(grid_frame, text="網格大小:").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(grid_frame, text="16x16", variable=self.grid_size, value=16).pack(side=tk.LEFT)
        ttk.Radiobutton(grid_frame, text="32x32", variable=self.grid_size, value=32).pack(side=tk.LEFT)
        ttk.Radiobutton(grid_frame, text="64x64", variable=self.grid_size, value=64).pack(side=tk.LEFT)

        # 操作按鈕
        action_frame = ttk.Frame(control_panel)
        action_frame.pack(fill=tk.X, pady=10)
        ttk.Button(action_frame, text="載入並顯示 RAW", command=self.load_raw_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="執行 LSC 校正", command=self.apply_lsc).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="另存校正後 RAW", command=self.save_corrected_raw).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="匯出 Gain Map (CSV)", command=self.save_gain_map_csv).pack(side=tk.LEFT, padx=5)

        # 2. 影像顯示框架
        image_display_frame = ttk.Frame(main_frame)
        image_display_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 原始影像
        original_frame = ttk.LabelFrame(image_display_frame, text="原始影像")
        original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.original_label = ttk.Label(original_frame)
        self.original_label.pack(fill=tk.BOTH, expand=True)

        # 校正後影像
        corrected_frame = ttk.LabelFrame(image_display_frame, text="LSC 校正後影像")
        corrected_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.corrected_label = ttk.Label(corrected_frame)
        self.corrected_label.pack(fill=tk.BOTH, expand=True)

        # 3. 狀態列
        self.status_var = tk.StringVar(value="請選擇 RAW 檔案並設定參數")
        ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

    def infer_params_from_filename(self, filepath):
        filename = os.path.basename(filepath).upper()

        if "BGGR" in filename:
            self.image_params["pattern"].set("BGGR")
        elif "RGGB" in filename:
            self.image_params["pattern"].set("RGGB")
        elif "GRBG" in filename:
            self.image_params["pattern"].set("GRBG")
        elif "GBRG" in filename:
            self.image_params["pattern"].set("GBRG")

        if "16BIT" in filename or "16-BIT" in filename:
            self.image_params["depth"].set("16-bit")
        elif "12BIT" in filename or "12-BIT" in filename:
            self.image_params["depth"].set("12-bit")
        elif "10BIT" in filename or "10-BIT" in filename:
            self.image_params["depth"].set("10-bit")

        # 解析解析度：例如 3264_2448
        parts = filename.replace(".RAW", "").split("_")
        for i in range(len(parts) - 1):
            if parts[i].isdigit() and parts[i + 1].isdigit():
                if len(parts[i]) >= 3 and len(parts[i + 1]) >= 3:
                    self.image_params["width"].set(parts[i])
                    self.image_params["height"].set(parts[i + 1])
                    self.res_combobox.set(f"{parts[i]}x{parts[i + 1]}")
                    break

    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="選擇 RAW 檔案",
            filetypes=[("RAW files", "*.raw"), ("All files", "*.*")]
        )
        if filepath:
            self.filepath_var.set(filepath)
            self.infer_params_from_filename(filepath)

    def update_resolution(self, event):
        res_str = self.res_combobox.get()
        w, h = res_str.split('x')
        self.image_params["width"].set(w)
        self.image_params["height"].set(h)

    def load_raw_image(self):
        filepath = self.filepath_var.get()
        if not os.path.exists(filepath):
            messagebox.showerror("錯誤", "檔案路徑不存在！")
            return

        try:
            self.infer_params_from_filename(filepath)

            w = int(self.image_params["width"].get())
            h = int(self.image_params["height"].get())
            depth_str = self.image_params["depth"].get()
            
            bits = int(depth_str.split('-')[0])
            dtype = np.uint16 if bits > 8 else np.uint8
            
            # 驗證檔案大小
            bytes_per_pixel = 2 if bits > 8 else 1
            expected_size = w * h * bytes_per_pixel
            actual_size = os.path.getsize(filepath)

            if actual_size != expected_size:
                # 如果是已知的 16-bit RAW，但使用者手動選了錯誤深度，嘗試從檔名自動校正
                if "16BIT" in os.path.basename(filepath).upper() or "16-BIT" in os.path.basename(filepath).upper():
                    self.image_params["depth"].set("16-bit")
                    bits = 16
                    dtype = np.uint16
                    bytes_per_pixel = 2
                    expected_size = w * h * bytes_per_pixel
                if actual_size != expected_size:
                    messagebox.showerror("錯誤", f"檔案大小不符！\n預期: {expected_size} bytes\n實際: {actual_size} bytes\n請檢查解析度與資料深度設定。")
                    return

            # 讀取 RAW 檔案
            self.raw_image_data = np.fromfile(filepath, dtype=dtype).reshape((h, w))
            
            # 根據位元深度進行正規化
            if bits == 10:
                self.raw_image_data = (self.raw_image_data.astype(np.float32) / 1023.0 * 65535).astype(np.uint16)
            elif bits == 12:
                self.raw_image_data = (self.raw_image_data.astype(np.float32) / 4095.0 * 65535).astype(np.uint16)

            self.display_image(self.raw_image_data, self.original_label, "原始影像")
            self.status_var.set(f"成功載入: {os.path.basename(filepath)}")
            self.corrected_label.config(image='') # 清除舊的校正影像
            self.corrected_raw_data = None

        except Exception as e:
            messagebox.showerror("載入失敗", f"無法讀取或解析檔案：\n{e}")
            self.status_var.set("載入失敗")

    def display_image(self, raw_data, label_widget, title):
        # 優化：使用雙線性去馬賽克 (Bilinear Demosaicing) 進行預覽
        h, w = raw_data.shape
        
        # 為了計算，先將 16-bit 數據轉換為 float
        raw_float = np.nan_to_num(raw_data).astype(np.float32)

        # 分離各個色彩通道
        pattern = self.image_params["pattern"].get().upper()
        channels = {}
        if pattern == 'RGGB':
            channels['R']  = raw_float * np.tile([[1, 0], [0, 0]], (h//2, w//2))
            channels['G']  = raw_float * np.tile([[0, 1], [1, 0]], (h//2, w//2))
            channels['B']  = raw_float * np.tile([[0, 0], [0, 1]], (h//2, w//2))
        elif pattern == 'BGGR':
            channels['B']  = raw_float * np.tile([[1, 0], [0, 0]], (h//2, w//2))
            channels['G']  = raw_float * np.tile([[0, 1], [1, 0]], (h//2, w//2))
            channels['R']  = raw_float * np.tile([[0, 0], [0, 1]], (h//2, w//2))
        else: # 如果有其他模式，預設回退到舊方法
            self.simple_display(raw_data, label_widget)
            return

        # 定義雙線性內插的卷積核 (Kernel)
        # G at R/B locations
        kernel_G = np.array([[0, 1, 0], [1, 4, 1], [0, 1, 0]]) / 4
        # R/B at G locations
        kernel_RB_at_G = np.array([[1, 0, 1], [0, 4, 0], [1, 0, 1]]) / 4
        # R/B at B/R locations (diagonal)
        kernel_RB_at_RB = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]]) / 4
        
        # 執行卷積來內插缺失的像素
        R = convolve(channels['R'], kernel_RB_at_RB, mode='mirror')
        G = convolve(channels['G'], kernel_G, mode='mirror')
        B = convolve(channels['B'], kernel_RB_at_RB, mode='mirror')

        # 將分離的通道合併為 RGB 影像
        # 先將數據從 16-bit 範圍 (0-65535) 縮放到 8-bit (0-255)
        rgb_display = np.stack([R, G, B], axis=-1)
        rgb_display = np.clip(rgb_display / 256, 0, 255).astype(np.uint8)

        img = Image.fromarray(rgb_display, 'RGB')

        # 縮放以適應視窗
        max_w, max_h = 550, 550
        img.thumbnail((max_w, max_h))
        
        photo = ImageTk.PhotoImage(img)
        label_widget.config(image=photo)
        label_widget.image = photo

    def simple_display(self, raw_data, label_widget):
        """舊的簡易顯示方法，作為不支援模式的回退選項"""
        h, w = raw_data.shape
        rgb_display = np.zeros((h, w, 3), dtype=np.uint8)
        
        safe_data = np.nan_to_num(raw_data, nan=0.0, posinf=0.0, neginf=0.0)
        display_data = (safe_data / 256).astype(np.uint8)

        pattern = self.image_params["pattern"].get().upper()
        
        if pattern == 'RGGB':
            rgb_display[::2, ::2, 0] = display_data[::2, ::2]
            rgb_display[::2, 1::2, 1] = display_data[::2, 1::2]
            rgb_display[1::2, ::2, 1] = display_data[1::2, ::2]
            rgb_display[1::2, 1::2, 2] = display_data[1::2, 1::2]
        elif pattern == 'BGGR':
            rgb_display[::2, ::2, 2] = display_data[::2, ::2]
            rgb_display[::2, 1::2, 1] = display_data[::2, 1::2]
            rgb_display[1::2, ::2, 1] = display_data[1::2, ::2]
            rgb_display[1::2, 1::2, 0] = display_data[1::2, 1::2]
        
        img = Image.fromarray(rgb_display, 'RGB')
        img = img.resize((w, h), Image.Resampling.BILINEAR)

        max_w, max_h = 550, 550
        img.thumbnail((max_w, max_h))
        photo = ImageTk.PhotoImage(img)
        label_widget.config(image=photo)
        label_widget.image = photo

    def apply_lsc(self):
        if self.raw_image_data is None:
            messagebox.showwarning("警告", "請先載入 RAW 影像！")
            return

        self.status_var.set("正在計算 LSC...")
        self.root.update_idletasks()

        try:
            # 1. 分離 Bayer 通道
            h, w = self.raw_image_data.shape
            pattern = self.image_params["pattern"].get().upper()
            
            channels = {}
            if pattern == 'RGGB':
                channels['R']  = self.raw_image_data[::2, ::2]
                channels['Gr'] = self.raw_image_data[::2, 1::2]
                channels['Gb'] = self.raw_image_data[1::2, ::2]
                channels['B']  = self.raw_image_data[1::2, 1::2]
            elif pattern == 'BGGR':
                channels['B']  = self.raw_image_data[::2, ::2]
                channels['Gr'] = self.raw_image_data[::2, 1::2]
                channels['Gb'] = self.raw_image_data[1::2, ::2]
                channels['R']  = self.raw_image_data[1::2, 1::2]
            else:
                messagebox.showerror("錯誤", f"不支援的色彩排列: {pattern}")
                return

            # 2. 尋找光學中心 (亮度最高點)
            # 為了穩定性，使用高斯平滑後的影像來找中心。
            # 直接使用 SciPy 的 gaussian_filter，避免 Pillow 在 'F' / 'I;16' 模式下
            # 對濾波器的模式相容性問題。
            blurred_data = gaussian_filter(self.raw_image_data.astype(np.float32), sigma=20, mode='nearest')
            center_y, center_x = np.unravel_index(np.argmax(blurred_data), blurred_data.shape)
            
            # 3. 建立網格節點並計算節點亮度
            grid_n = self.grid_size.get()
            y_nodes = np.linspace(0, h - 1, grid_n, dtype=int)
            x_nodes = np.linspace(0, w - 1, grid_n, dtype=int)
            
            self.gain_map_data = {}
            gain_maps = {}

            for ch_name, ch_data in channels.items():
                ch_h, ch_w = ch_data.shape
                
                # 計算中心點在該通道的座標與亮度
                center_ch_y, center_ch_x = center_y // 2, center_x // 2
                center_val = ch_data[center_ch_y, center_ch_x]
                if center_val == 0: center_val = 1 # 避免除以零

                # 計算網格節點在該通道的座標與亮度
                y_ch_nodes = np.linspace(0, ch_h - 1, grid_n, dtype=int)
                x_ch_nodes = np.linspace(0, ch_w - 1, grid_n, dtype=int)
                node_coords = []
                node_gains = []

                self.gain_map_data[ch_name] = np.zeros((grid_n, grid_n))

                for i, r in enumerate(y_ch_nodes):
                    for j, c in enumerate(x_ch_nodes):
                        node_val = ch_data[r, c]
                        if node_val == 0: node_val = 1
                        gain = center_val / node_val
                        
                        node_coords.append([r, c])
                        node_gains.append(gain)
                        self.gain_map_data[ch_name][i, j] = gain

                # 4. 使用雙線性內插生成整個通道的 Gain Map
                grid_y, grid_x = np.mgrid[0:ch_h, 0:ch_w]
                full_gain_map = griddata(node_coords, node_gains, (grid_y, grid_x), method='linear', fill_value=1.0)
                gain_maps[ch_name] = np.clip(full_gain_map, 0, 4.0) # 限制最大增益為4倍

            # 5. 套用 Gain Map 到原始 RAW 影像
            self.corrected_raw_data = self.raw_image_data.copy().astype(np.float32)
            
            if pattern == 'RGGB':
                self.corrected_raw_data[::2, ::2]   *= gain_maps['R']
                self.corrected_raw_data[::2, 1::2] *= gain_maps['Gr']
                self.corrected_raw_data[1::2, ::2] *= gain_maps['Gb']
                self.corrected_raw_data[1::2, 1::2] *= gain_maps['B']
            elif pattern == 'BGGR':
                self.corrected_raw_data[::2, ::2]   *= gain_maps['B']
                self.corrected_raw_data[::2, 1::2] *= gain_maps['Gr']
                self.corrected_raw_data[1::2, ::2] *= gain_maps['Gb']
                self.corrected_raw_data[1::2, 1::2] *= gain_maps['R']

            self.corrected_raw_data = np.clip(self.corrected_raw_data, 0, 65535).astype(np.uint16)

            # 6. 顯示校正後影像
            self.display_image(self.corrected_raw_data, self.corrected_label, "校正後影像")
            self.status_var.set(f"LSC 校正完成 (網格: {grid_n}x{grid_n})")

        except Exception as e:
            messagebox.showerror("校正失敗", f"執行 LSC 時發生錯誤：\n{e}")
            self.status_var.set("LSC 校正失敗")

    def save_corrected_raw(self):
        if self.corrected_raw_data is None:
            messagebox.showwarning("警告", "沒有可儲存的校正後影像。")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="儲存校正後的 RAW 檔案",
            defaultextension=".raw",
            filetypes=[("RAW files", "*.raw")]
        )
        if not filepath:
            return

        try:
            # 根據原始位元深度還原
            depth_str = self.image_params["depth"].get()
            bits = int(depth_str.split('-')[0])
            
            save_data = self.corrected_raw_data.copy()
            if bits == 10:
                save_data = (save_data.astype(np.float32) / 65535.0 * 1023).astype(np.uint16)
            elif bits == 12:
                save_data = (save_data.astype(np.float32) / 65535.0 * 4095).astype(np.uint16)

            save_data.tofile(filepath)
            self.status_var.set(f"已儲存校正後 RAW 至: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("儲存失敗", f"儲存檔案時發生錯誤：\n{e}")

    def save_gain_map_csv(self):
        if not self.gain_map_data:
            messagebox.showwarning("警告", "沒有可儲存的 Gain Map 資料。請先執行校正。")
            return

        filepath = filedialog.asksaveasfilename(
            title="儲存 Gain Map",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not filepath:
            return

        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                grid_n = self.grid_size.get()
                
                for ch_name, data in self.gain_map_data.items():
                    writer.writerow([f"Channel: {ch_name} (Grid: {grid_n}x{grid_n})"])
                    header = [f"Col_{j}" for j in range(grid_n)]
                    writer.writerow(["Row"] + header)
                    for i, row_data in enumerate(data):
                        writer.writerow([f"Row_{i}"] + list(row_data))
                    writer.writerow([]) # 空一行分隔
            
            self.status_var.set(f"已儲存 Gain Map 至: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("儲存失敗", f"儲存 CSV 時發生錯誤：\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = LSCToolApp(root)
    root.mainloop()
