# -*- coding: utf-8 -*-

# =============================================================================
# | Sam 影像處理小幫手 - v2.0
# |
# | 版本更新:
# | - 新增 [更新方框設定] 按鈕，避免即時調整造成的閃爍。
# | - 圖片顯示改為等比例縮放，固定寬度為 1080px，高度自適應。
# | - 新增調整功能總開關 (開啟/關閉)，可一鍵恢復原始影像或套用效果。
# |
# | 功能特色:
# | 1. 支援多種圖片格式 (JPG, PNG, BMP)。
# | 2. 可調整的分析框，用於局部影像數據分析。
# | 3. 即時計算並顯示分析框內的 RGB 與亮度平均值。
# | 4. 提供多維度的影像調整功能，包含:
# |    - 基礎調整: R, G, B, 亮度, 對比度
# |    - 色彩調整: 色相, 飽和度
# |    - 影像增強: 銳利度, Gamma 校正
# |    - 專業功能: 白平衡色溫調整 (2300K ~ 7500K)
# | 5. 所有調整皆可即時預覽，並可另存新檔。
# |
# | 使用函式庫:
# | - tkinter: 用於建立圖形化使用者介測 (GUI)。
# | - Pillow (PIL): 核心影像處理函式庫，用於讀取、修改、儲存影像。
# | - NumPy: 高效的數值計算函式庫，用於快速計算影像數據。
# =============================================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
# 處理 Pillow 10.0.0 版本後的變更
try:
    from PIL import Image, ImageTk, ImageEnhance, ImageOps, __version__ as PIL_VERSION
    if int(PIL_VERSION.split('.')[0]) >= 10:
        Image.LANCZOS = Image.Resampling.LANCZOS
except (ImportError, AttributeError):
    from PIL import Image, ImageTk, ImageEnhance, ImageOps
import numpy as np
import math

class DraggableRectangle:
    """
    在Canvas上可拖曳的矩形類別。
    用於標示影像分析的區域。
    """
    def __init__(self, canvas, x1, y1, x2, y2, number, on_move_callback, img_w, img_h):
        self.canvas = canvas
        self.number = number
        self.on_move_callback = on_move_callback
        self.img_w = img_w
        self.img_h = img_h

        self.rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline='blue', width=2, tags=f"rect_{number}")
        self.text = self.canvas.create_text(x1 + 15, y1 + 15, text=str(number), fill='cyan', font=('Arial', 12, 'bold'), tags=f"text_{number}")

        self.canvas.tag_bind(self.rect, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(self.rect, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.rect, "<ButtonRelease-1>", self.on_release)
        self.canvas.tag_bind(self.text, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(self.text, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.text, "<ButtonRelease-1>", self.on_release)

        self._drag_data = {"x": 0, "y": 0}

    def on_press(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_drag(self, event):
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        self.canvas.move(self.rect, delta_x, delta_y)
        self.canvas.move(self.text, delta_x, delta_y)
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_release(self, event):
        coords = self.get_coords()
        w = coords[2] - coords[0]
        h = coords[3] - coords[1]
        
        clamped_x1 = max(0, min(coords[0], self.img_w - w))
        clamped_y1 = max(0, min(coords[1], self.img_h - h))
        clamped_x2 = clamped_x1 + w
        clamped_y2 = clamped_y1 + h
        
        self.canvas.coords(self.rect, clamped_x1, clamped_y1, clamped_x2, clamped_y2)
        self.canvas.coords(self.text, clamped_x1 + 15, clamped_y1 + 15)
        
        self.on_move_callback()

    def get_coords(self):
        return self.canvas.coords(self.rect)

    def delete(self):
        self.canvas.delete(self.rect)
        self.canvas.delete(self.text)

class ImageAnalysisTool:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Sam 影像處理小幫手 v2.0")
        self.root.geometry("1800x960+50+50")

        self.original_image = None
        self.image_for_processing = None
        self.processed_image = None
        self.display_image_tk = None
        self.image_on_canvas = None

        self.analysis_boxes = []
        self.DISPLAY_WIDTH = 1080 # 固定寬度
        self.DISPLAY_HEIGHT = 720 # 初始高度，會動態改變

        self.create_menu()
        self.create_widgets()
        
        self.set_controls_state('disabled')

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="開啟圖片", command=self.open_image)
        file_menu.add_command(label="另存新檔", command=self.save_image)
        file_menu.add_separator()
        file_menu.add_command(label="結束", command=self.root.quit)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        left_container = ttk.Frame(paned_window)
        paned_window.add(left_container, weight=3)

        self.right_frame = ttk.Frame(paned_window)
        paned_window.add(self.right_frame, weight=1)

        # 左上: 圖片顯示區 - 放到一個額外的Frame中，避免影響下方Text的大小
        canvas_frame = ttk.Frame(left_container)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        self.canvas = tk.Canvas(canvas_frame, bg='gray20', width=self.DISPLAY_WIDTH, height=self.DISPLAY_HEIGHT)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas_text_hint = self.canvas.create_text(
            self.DISPLAY_WIDTH / 2, self.DISPLAY_HEIGHT / 2, 
            text="請從「檔案」選單開啟圖片", fill="white", font=("Microsoft JhengHei", 20)
        )

        bottom_frame = ttk.LabelFrame(left_container, text="分析數據")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        self.text_results = tk.Text(bottom_frame, height=10, width=100, font=("Consolas", 10), state='disabled')
        text_scrollbar = ttk.Scrollbar(bottom_frame, orient=tk.VERTICAL, command=self.text_results.yview)
        self.text_results.config(yscrollcommand=text_scrollbar.set)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.create_control_panel()
        
    def create_control_panel(self):
        control_canvas = tk.Canvas(self.right_frame)
        control_scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=control_canvas.yview)
        scrollable_frame = ttk.Frame(control_canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: control_canvas.configure(scrollregion=control_canvas.bbox("all"))
        )

        control_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        control_canvas.configure(yscrollcommand=control_scrollbar.set)
        
        control_canvas.pack(side="left", fill="both", expand=True)
        control_scrollbar.pack(side="right", fill="y")
        
        # --- 調整功能總開關 ---
        master_control_frame = ttk.LabelFrame(scrollable_frame, text="調整功能總管")
        master_control_frame.pack(fill=tk.X, padx=10, pady=10)
        self.adjustment_state_var = tk.StringVar(value="關閉")
        
        self.rb_on = ttk.Radiobutton(master_control_frame, text="開啟效果", variable=self.adjustment_state_var, value="開啟", command=self.on_adjustment_toggle)
        self.rb_on.pack(side=tk.LEFT, padx=10)
        self.rb_off = ttk.Radiobutton(master_control_frame, text="關閉效果 (原始影像)", variable=self.adjustment_state_var, value="關閉", command=self.on_adjustment_toggle)
        self.rb_off.pack(side=tk.LEFT, padx=10)

        # --- 分析框設定 ---
        box_frame = ttk.LabelFrame(scrollable_frame, text="分析框設定")
        box_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(box_frame, text="數量:").grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.box_count_var = tk.IntVar(value=8)
        self.box_count_spinbox = ttk.Spinbox(box_frame, from_=1, to=25, textvariable=self.box_count_var, width=10)
        self.box_count_spinbox.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(box_frame, text="寬度:").grid(row=1, column=0, padx=5, pady=2, sticky='w')
        self.box_width_var = tk.IntVar(value=100)
        self.box_width_spinbox = ttk.Spinbox(box_frame, from_=10, to=self.DISPLAY_WIDTH, textvariable=self.box_width_var, width=10)
        self.box_width_spinbox.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(box_frame, text="高度:").grid(row=2, column=0, padx=5, pady=2, sticky='w')
        self.box_height_var = tk.IntVar(value=100)
        self.box_height_spinbox = ttk.Spinbox(box_frame, from_=10, to=self.DISPLAY_HEIGHT, textvariable=self.box_height_var, width=10)
        self.box_height_spinbox.grid(row=2, column=1, padx=5, pady=2)
        
        self.update_boxes_button = ttk.Button(box_frame, text="更新方框設定", command=self.setup_analysis_boxes)
        self.update_boxes_button.grid(row=3, column=0, columnspan=2, pady=5)

        # --- 影像調整滑桿 ---
        def create_slider(parent, text, from_, to, default, resolution, command):
            frame = ttk.Frame(parent)
            label = ttk.Label(frame, text=text, width=10)
            label.pack(side=tk.LEFT)
            var = tk.DoubleVar(value=default)
            scale = ttk.Scale(frame, from_=from_, to=to, orient=tk.HORIZONTAL, variable=var, command=command)
            scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            if resolution == 0:
                var.set(int(default))
                scale.config(command=lambda v, c=command: c(int(float(v))))
            else:
                scale.config(command=lambda v, c=command: c(round(float(v), 2)))
            frame.pack(fill=tk.X, padx=5, pady=2)
            return var
        
        self.basic_frame = ttk.LabelFrame(scrollable_frame, text="基礎調整")
        self.basic_frame.pack(fill=tk.X, padx=10, pady=5,  ipady=5)
        self.r_var = create_slider(self.basic_frame, "R", -127, 127, 0, 0, self.update_display)
        self.g_var = create_slider(self.basic_frame, "G", -127, 127, 0, 0, self.update_display)
        self.b_var = create_slider(self.basic_frame, "B", -127, 127, 0, 0, self.update_display)
        self.brightness_var = create_slider(self.basic_frame, "亮度", -127, 127, 0, 0, self.update_display)
        self.contrast_var = create_slider(self.basic_frame, "對比度", 0, 100, 50, 0, self.update_display)

        self.enhance_frame = ttk.LabelFrame(scrollable_frame, text="影像增強")
        self.enhance_frame.pack(fill=tk.X, padx=10, pady=5, ipady=5)
        self.sharpness_var = create_slider(self.enhance_frame, "銳利度", 0, 100, 50, 0, self.update_display)
        self.gamma_var = create_slider(self.enhance_frame, "Gamma", 0.6, 3.0, 2.2, 0.1, self.update_display)
        
        self.color_frame = ttk.LabelFrame(scrollable_frame, text="色彩調整")
        self.color_frame.pack(fill=tk.X, padx=10, pady=5, ipady=5)
        self.hue_var = create_slider(self.color_frame, "色相", 0, 100, 50, 0, self.update_display)
        self.saturation_var = create_slider(self.color_frame, "飽和度", 0, 100, 50, 0, self.update_display)
        
        self.wb_frame = ttk.LabelFrame(scrollable_frame, text="白平衡 (色溫)")
        self.wb_frame.pack(fill=tk.X, padx=10, pady=5, ipady=5)
        self.white_balance_var = create_slider(self.wb_frame, "色溫(K)", 2300, 7500, 6500, 0, self.update_display)

        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        self.reset_button = ttk.Button(button_frame, text="重設所有調整", command=self.reset_all_sliders)
        self.reset_button.pack()

    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")])
        if not file_path:
            return

        try:
            self.original_image = Image.open(file_path).convert('RGBA')

            background = Image.new('RGB', self.original_image.size, (255, 255, 255))
            background.paste(self.original_image, mask=self.original_image.split()[3])
            
            # --- 等比例縮放 ---
            w_orig, h_orig = background.size
            ratio = w_orig / self.DISPLAY_WIDTH
            new_height = int(h_orig / ratio)
            self.DISPLAY_HEIGHT = new_height
            
            # 更新 Canvas 尺寸
            self.canvas.config(width=self.DISPLAY_WIDTH, height=self.DISPLAY_HEIGHT)
            
            # 使用 resize 進行縮放
            self.image_for_processing = background.resize((self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT), Image.LANCZOS)
            
            # 更新方框尺寸設定的最大值
            self.update_spinbox_limits()
            
            self.set_controls_state('normal')
            self.canvas.delete(self.canvas_text_hint)
            
            self.reset_all_sliders()
            self.setup_analysis_boxes()
            
        except Exception as e:
            messagebox.showerror("開啟失敗", f"無法開啟或處理檔案: {e}")

    def save_image(self):
        if not self.processed_image:
            messagebox.showwarning("警告", "沒有可儲存的圖片。")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG file", "*.png"), ("JPEG file", "*.jpg"), ("BMP file", "*.bmp")])
        if not file_path:
            return

        try:
            self.processed_image.save(file_path)
            messagebox.showinfo("成功", f"圖片已成功儲存至:\n{file_path}")
        except Exception as e:
            messagebox.showerror("儲存失敗", f"儲存檔案時發生錯誤: {e}")

    def set_controls_state(self, state):
        """啟用或禁用右側所有控制項"""
        # 遍歷右側框架中的所有子元件
        for child in self.right_frame.winfo_children():
            # 找到包含所有控制項的捲動框架
            if isinstance(child, tk.Canvas):
                frame_id = child.winfo_children()[0]
                for widget in frame_id.winfo_children():
                    # 遍歷每個 LabelFrame
                    if isinstance(widget, ttk.LabelFrame) or isinstance(widget, ttk.Frame):
                        for sub_widget in widget.winfo_children():
                            try:
                                sub_widget.config(state=state)
                            except tk.TclError:
                                pass
        
        # 如果是啟用，需要根據 radio button 的狀態決定是否啟用滑桿
        if state == 'normal':
            self.on_adjustment_toggle()

    def on_adjustment_toggle(self):
        """根據單選按鈕的狀態，啟用/禁用滑桿區塊並更新圖片"""
        is_enabled = self.adjustment_state_var.get() == "開啟"
        state = 'normal' if is_enabled else 'disabled'
        
        # 控制滑桿區塊的啟用狀態
        adjustment_frames = [self.basic_frame, self.enhance_frame, self.color_frame, self.wb_frame]
        for frame in adjustment_frames:
            for child in frame.winfo_children():
                try:
                    child.config(state=state)
                except tk.TclError:
                    pass
        self.reset_button.config(state=state)

        # 觸發圖片更新
        self.update_display()

    def update_spinbox_limits(self):
        """當圖片尺寸改變時，更新分析框寬高設定的最大值"""
        self.box_width_spinbox.config(to=self.DISPLAY_WIDTH)
        self.box_height_spinbox.config(to=self.DISPLAY_HEIGHT)

    def setup_analysis_boxes(self):
        if self.image_for_processing is None:
            return

        for box in self.analysis_boxes:
            box.delete()
        self.analysis_boxes.clear()

        count = self.box_count_var.get()
        w = self.box_width_var.get()
        h = self.box_height_var.get()
        
        positions = [
            (0.15, 0.15), (0.5, 0.15), (0.85, 0.15),
            (0.15, 0.50), (0.5, 0.50), (0.85, 0.50),
            (0.15, 0.85), (0.5, 0.85), (0.85, 0.85)
        ]
        
        order = [4, 0, 2, 6, 8, 1, 3, 5, 7] 
        
        for i in range(count):
            pos_idx = order[i % len(order)]
            center_x = self.DISPLAY_WIDTH * positions[pos_idx][0]
            center_y = self.DISPLAY_HEIGHT * positions[pos_idx][1]

            x1 = int(center_x - w / 2)
            y1 = int(center_y - h / 2)
            x2 = int(x1 + w)
            y2 = int(y1 + h)

            box = DraggableRectangle(self.canvas, x1, y1, x2, y2, i + 1, self.update_analysis_results, self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT)
            self.analysis_boxes.append(box)
        
        self.update_display()
            
    def update_display(self, _=None):
        if self.image_for_processing is None:
            return

        # 檢查調整功能是否開啟
        if self.adjustment_state_var.get() == "開啟":
            # --- 1. 複製基底圖片，開始處理 ---
            current_image = self.image_for_processing.copy()

            # --- 2. Numpy 數組轉換 ---
            img_np = np.array(current_image).astype(np.float32)

            img_np[..., 0] = np.clip(img_np[..., 0] + self.r_var.get(), 0, 255)
            img_np[..., 1] = np.clip(img_np[..., 1] + self.g_var.get(), 0, 255)
            img_np[..., 2] = np.clip(img_np[..., 2] + self.b_var.get(), 0, 255)
            img_np = np.clip(img_np + self.brightness_var.get(), 0, 255)

            gamma = self.gamma_var.get()
            if gamma != 0:
                inv_gamma = 1.0 / gamma
                table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
                img_np = cv2.LUT(img_np.astype(np.uint8), table).astype(np.float32)

            current_image = Image.fromarray(img_np.astype(np.uint8))

            # --- 3. 使用 Pillow.ImageEnhance ---
            contrast = self.contrast_var.get() / 50.0
            current_image = ImageEnhance.Contrast(current_image).enhance(contrast)

            saturation = self.saturation_var.get() / 50.0
            current_image = ImageEnhance.Color(current_image).enhance(saturation)

            sharpness = self.sharpness_var.get() / 50.0
            current_image = ImageEnhance.Sharpness(current_image).enhance(sharpness)
            
            # --- 4. 白平衡 ---
            temp_k = self.white_balance_var.get()
            if temp_k != 6500:
                r_mult, g_mult, b_mult = self.kelvin_to_rgb_multiplier(temp_k)
                img_np = np.array(current_image).astype(np.float32)
                img_np[..., 0] *= r_mult
                img_np[..., 1] *= g_mult
                img_np[..., 2] *= b_mult
                img_np = np.clip(img_np, 0, 255)
                current_image = Image.fromarray(img_np.astype(np.uint8))
                
            self.processed_image = current_image
        else:
            # 如果功能關閉，直接使用原始處理圖
            self.processed_image = self.image_for_processing.copy()

        # --- 5. 更新 Canvas 上的圖片 (無論是否開啟效果都要執行) ---
        self.display_image_tk = ImageTk.PhotoImage(self.processed_image)
        
        if self.image_on_canvas:
            self.canvas.itemconfig(self.image_on_canvas, image=self.display_image_tk)
        else:
            self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.display_image_tk)
            
        for box in self.analysis_boxes:
            self.canvas.tag_raise(box.rect)
            self.canvas.tag_raise(box.text)
            
        # --- 6. 更新分析數據 ---
        self.update_analysis_results()
        
    def update_analysis_results(self):
        if self.processed_image is None or not self.analysis_boxes:
            return

        image_np = np.array(self.processed_image)

        results_text = "分析框數據 (Avg R, G, B, Brightness):\n"
        results_text += "========================================\n"

        for box in self.analysis_boxes:
            coords = [int(c) for c in box.get_coords()]
            x1, y1, x2, y2 = coords
            
            x1 = max(0, x1); y1 = max(0, y1)
            x2 = min(self.DISPLAY_WIDTH, x2); y2 = min(self.DISPLAY_HEIGHT, y2)

            if x1 >= x2 or y1 >= y2:
                avg_r, avg_g, avg_b, avg_lum = 0, 0, 0, 0
            else:
                roi = image_np[y1:y2, x1:x2]
                avg_colors = np.mean(roi, axis=(0, 1))
                avg_r, avg_g, avg_b = avg_colors[0], avg_colors[1], avg_colors[2]
                avg_lum = 0.2126 * avg_r + 0.7152 * avg_g + 0.0722 * avg_b
            
            results_text += f"BOX #{box.number:<2}: R={avg_r:6.2f}, G={avg_g:6.2f}, B={avg_b:6.2f}, Lum={avg_lum:6.2f}\n"

        self.text_results.config(state='normal')
        self.text_results.delete(1.0, tk.END)
        self.text_results.insert(tk.END, results_text)
        self.text_results.config(state='disabled')

    def reset_all_sliders(self):
        self.r_var.set(0)
        self.g_var.set(0)
        self.b_var.set(0)
        self.brightness_var.set(0)
        self.contrast_var.set(50)
        self.sharpness_var.set(50)
        self.saturation_var.set(50)
        self.hue_var.set(50)
        self.gamma_var.set(1.0)
        self.white_balance_var.set(6500)
        
        self.update_display()

    def kelvin_to_rgb_multiplier(self, temp_k):
        temp = temp_k / 100.0
        
        if temp <= 66: r = 255
        else: r = np.clip(329.698727446 * ((temp - 60) ** -0.1332047592), 0, 255)
            
        if temp <= 66: g = np.clip(99.4708025861 * math.log(temp) - 161.1195681661, 0, 255)
        else: g = np.clip(288.1221695283 * ((temp - 60) ** -0.0755148492), 0, 255)
            
        if temp >= 66: b = 255
        elif temp <= 19: b = 0
        else: b = np.clip(138.5177312231 * math.log(temp - 10) - 305.0447927307, 0, 255)
            
        return r/255.0, g/255.0, b/255.0
        

if __name__ == "__main__":
    try:
        import cv2
    except ImportError:
        print("警告: 偵測到未安裝 OpenCV-Python 函式庫。")
        print("Gamma 調整功能將無法使用。")
        print("請使用 pip 安裝: pip install opencv-python")
        class cv2:
            def LUT(self, src, lut): return src

    root = tk.Tk()
    app = ImageAnalysisTool(root)
    root.mainloop()