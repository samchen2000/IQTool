# -*- coding: utf-8 -*-

# =============================================================================
# | Sam 影像處理小幫手 - 專業影像分析與調整工具
# |
# | 功能特色:
# | 1. 支援多種圖片格式 (JPG, PNG, BMP)。
# | 2. 可調整的分析框，用於局部影像數據分析。
# | 3. 即時計算並顯示分析框內的 RGB 與亮度平均值。
# | 4. 提供多維度的影像調整功能，包含:
# |    - 基礎調整: R, G, B, 亮度, 對比度
# |    - 色彩調整: 色相, 飽和度
# |    - 影像增強: 銳利度, Gamma 校正
# |    -專業功能: 白平衡色溫調整 (2300K ~ 7500K)
# | 5. 所有調整皆可即時預覽，並可另存新檔。
# |
# | 使用函式庫:
# | - tkinter: 用於建立圖形化使用者介測 (GUI)。
# | - Pillow (PIL): 核心影像處理函式庫，用於讀取、修改、儲存影像。
# | - NumPy: 高效的數值計算函式庫，用於快速計算影像數據。
# =============================================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageEnhance, ImageOps
import numpy as np
import math

class DraggableRectangle:
    """
    在Canvas上可拖曳的矩形類別。
    用於標示影像分析的區域。
    """
    def __init__(self, canvas, x1, y1, x2, y2, number, on_move_callback):
        self.canvas = canvas
        self.number = number
        self.on_move_callback = on_move_callback  # 用於拖動後更新數據的回呼函數

        # 創建矩形和其上方的編號文字
        self.rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline='blue', width=2, tags=f"rect_{number}")
        self.text = self.canvas.create_text(x1 + 15, y1 + 15, text=str(number), fill='cyan', font=('Arial', 12, 'bold'), tags=f"text_{number}")

        # 綁定滑鼠事件，使其可以被拖動
        self.canvas.tag_bind(self.rect, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(self.rect, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.rect, "<ButtonRelease-1>", self.on_release)
        self.canvas.tag_bind(self.text, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(self.text, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.text, "<ButtonRelease-1>", self.on_release)

        self._drag_data = {"x": 0, "y": 0}

    def on_press(self, event):
        """記錄滑鼠點擊的起始位置"""
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_drag(self, event):
        """計算滑鼠移動的距離，並移動矩形和文字"""
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]

        # 移動矩形和文字
        self.canvas.move(self.rect, delta_x, delta_y)
        self.canvas.move(self.text, delta_x, delta_y)

        # 更新拖動的起始位置
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_release(self, event):
        """滑鼠釋放後，觸發回呼函數來更新分析數據"""
        # 確保方框不會超出圖片範圍 (1280x720)
        coords = self.get_coords()
        w = coords[2] - coords[0]
        h = coords[3] - coords[1]
        
        clamped_x1 = max(0, min(coords[0], 1280 - w))
        clamped_y1 = max(0, min(coords[1], 720 - h))
        clamped_x2 = clamped_x1 + w
        clamped_y2 = clamped_y1 + h
        
        self.canvas.coords(self.rect, clamped_x1, clamped_y1, clamped_x2, clamped_y2)
        self.canvas.coords(self.text, clamped_x1 + 15, clamped_y1 + 15)
        
        self.on_move_callback()

    def get_coords(self):
        """獲取當前矩形的座標"""
        return self.canvas.coords(self.rect)

    def delete(self):
        """從Canvas上刪除此矩形和文字"""
        self.canvas.delete(self.rect)
        self.canvas.delete(self.text)

class ImageAnalysisTool:
    """
    主應用程式類別
    """
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Sam 影像處理小幫手")
        self.root.geometry("1920x1000+50+50") # 設定視窗預設大小與位置

        # --- 影像相關變數初始化 ---
        self.original_image = None         # 未經任何處理的原始PIL圖片
        self.image_for_processing = None   # 縮放後，用於所有調整的基底圖片
        self.processed_image = None        # 經過所有效果調整後的PIL圖片
        self.display_image_tk = None       # 用於在Tkinter Canvas上顯示的PhotoImage物件
        self.image_on_canvas = None        # Canvas上的圖片ID

        # --- 分析框相關變數 ---
        self.analysis_boxes = []
        self.DISPLAY_WIDTH = 1280
        self.DISPLAY_HEIGHT = 720

        # --- 初始化UI介面 ---
        self.create_menu()
        self.create_widgets()
        
        # 初始時禁用部分UI元件
        self.set_controls_state('disabled')

    def create_menu(self):
        """建立頂端的選單列"""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="開啟圖片", command=self.open_image)
        file_menu.add_command(label="另存新檔", command=self.save_image)
        file_menu.add_separator()
        file_menu.add_command(label="結束", command=self.root.quit)

    def create_widgets(self):
        """建立主視窗中的所有UI元件"""
        # --- 主要框架結構 ---
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 建立一個可調整左右分割的窗格
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # 左側框架 (包含圖片顯示區和數據顯示區)
        left_container = ttk.Frame(paned_window)
        paned_window.add(left_container, weight=4) # weight=4 表示左側佔較大比例

        # 右側框架 (控制項)
        self.right_frame = ttk.Frame(paned_window)
        paned_window.add(self.right_frame, weight=1) # weight=1 表示右側佔較小比例

        # --- 左上: 圖片顯示區 ---
        self.canvas = tk.Canvas(left_container, bg='gray20', width=self.DISPLAY_WIDTH, height=self.DISPLAY_HEIGHT)
        self.canvas.pack(side=tk.TOP, pady=5)
        # 預留一個置中顯示的提示文字
        self.canvas_text_hint = self.canvas.create_text(
            self.DISPLAY_WIDTH / 2, self.DISPLAY_HEIGHT / 2, 
            text="請從「檔案」選單開啟圖片", 
            fill="white", 
            font=("Microsoft JhengHei", 20)
        )

        # --- 左下: 數據顯示區 ---
        bottom_frame = ttk.LabelFrame(left_container, text="分析數據")
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, pady=5)
        
        self.text_results = tk.Text(bottom_frame, height=10, width=100, font=("Consolas", 10), state='disabled')
        text_scrollbar = ttk.Scrollbar(bottom_frame, orient=tk.VERTICAL, command=self.text_results.yview)
        self.text_results.config(yscrollcommand=text_scrollbar.set)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- 右側: 控制項 ---
        self.create_control_panel()
        
    def create_control_panel(self):
        """在右側框架中建立所有調整工具"""
        control_canvas = tk.Canvas(self.right_frame)
        control_scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=control_canvas.yview)
        scrollable_frame = ttk.Frame(control_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: control_canvas.configure(
                scrollregion=control_canvas.bbox("all")
            )
        )

        control_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        control_canvas.configure(yscrollcommand=control_scrollbar.set)
        
        control_canvas.pack(side="left", fill="both", expand=True)
        control_scrollbar.pack(side="right", fill="y")
        
        # --- 分析框設定 ---
        box_frame = ttk.LabelFrame(scrollable_frame, text="分析框設定")
        box_frame.pack(fill=tk.X, padx=10, pady=5)

        # 數量
        ttk.Label(box_frame, text="數量:").grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.box_count_var = tk.IntVar(value=8)
        self.box_count_spinbox = ttk.Spinbox(box_frame, from_=1, to=25, textvariable=self.box_count_var, width=10, command=self.setup_analysis_boxes)
        self.box_count_spinbox.grid(row=0, column=1, padx=5, pady=2)
        
        # 尺寸
        ttk.Label(box_frame, text="寬度:").grid(row=1, column=0, padx=5, pady=2, sticky='w')
        self.box_width_var = tk.IntVar(value=100)
        self.box_width_spinbox = ttk.Spinbox(box_frame, from_=10, to=self.DISPLAY_WIDTH, textvariable=self.box_width_var, width=10, command=self.resize_analysis_boxes)
        self.box_width_spinbox.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(box_frame, text="高度:").grid(row=2, column=0, padx=5, pady=2, sticky='w')
        self.box_height_var = tk.IntVar(value=100)
        self.box_height_spinbox = ttk.Spinbox(box_frame, from_=10, to=self.DISPLAY_HEIGHT, textvariable=self.box_height_var, width=10, command=self.resize_analysis_boxes)
        self.box_height_spinbox.grid(row=2, column=1, padx=5, pady=2)

        # --- 影像調整滑桿 ---
        # 建立一個輔助函數來創建滑桿，避免重複的程式碼
        def create_slider(parent, text, from_, to, default, resolution, command):
            frame = ttk.Frame(parent)
            label = ttk.Label(frame, text=text, width=10)
            label.pack(side=tk.LEFT)
            var = tk.DoubleVar(value=default)
            scale = ttk.Scale(frame, from_=from_, to=to, orient=tk.HORIZONTAL, variable=var, command=command)
            scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            entry = ttk.Entry(frame, textvariable=var, width=6)
            # entry.pack(side=tk.RIGHT) # 可選: 顯示數值的輸入框
            if resolution == 0: # 整數
                var.set(int(default))
                scale.config(command=lambda v, c=command: c(int(float(v))))
            else:
                scale.config(command=lambda v, c=command: c(round(float(v), 2)))
                
            frame.pack(fill=tk.X, padx=5, pady=2)
            return var
        
        # 基礎調整
        basic_frame = ttk.LabelFrame(scrollable_frame, text="基礎調整")
        basic_frame.pack(fill=tk.X, padx=10, pady=5,  ipady=5)
        self.r_var = create_slider(basic_frame, "R", -127, 127, 0, 0, self.update_display)
        self.g_var = create_slider(basic_frame, "G", -127, 127, 0, 0, self.update_display)
        self.b_var = create_slider(basic_frame, "B", -127, 127, 0, 0, self.update_display)
        self.brightness_var = create_slider(basic_frame, "亮度", -127, 127, 0, 0, self.update_display)
        self.contrast_var = create_slider(basic_frame, "對比度", 0, 100, 50, 0, self.update_display)

        # 影像增強
        enhance_frame = ttk.LabelFrame(scrollable_frame, text="影像增強")
        enhance_frame.pack(fill=tk.X, padx=10, pady=5, ipady=5)
        self.sharpness_var = create_slider(enhance_frame, "銳利度", 0, 100, 50, 0, self.update_display)
        self.gamma_var = create_slider(enhance_frame, "Gamma", 0.6, 3.0, 2.2, 0.1, self.update_display)
        
        # 色彩調整
        color_frame = ttk.LabelFrame(scrollable_frame, text="色彩調整")
        color_frame.pack(fill=tk.X, padx=10, pady=5, ipady=5)
        self.hue_var = create_slider(color_frame, "色相", 0, 100, 50, 0, self.update_display)
        self.saturation_var = create_slider(color_frame, "飽和度", 0, 100, 50, 0, self.update_display)
        
        # 白平衡
        wb_frame = ttk.LabelFrame(scrollable_frame, text="白平衡 (色溫)")
        wb_frame.pack(fill=tk.X, padx=10, pady=5, ipady=5)
        self.white_balance_var = create_slider(wb_frame, "色溫(K)", 2300, 7500, 6500, 0, self.update_display)

        # --- 按鈕 ---
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        self.reset_button = ttk.Button(button_frame, text="重設所有調整", command=self.reset_all_sliders)
        self.reset_button.pack()
        
    def open_image(self):
        """開啟圖片檔案，並進行初始化"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            # 載入圖片並轉換為RGBA格式以處理透明度
            self.original_image = Image.open(file_path).convert('RGBA')

            # 建立一個白色背景，然後將原始圖片貼上去，以消除透明度問題
            background = Image.new('RGB', self.original_image.size, (255, 255, 255))
            background.paste(self.original_image, mask=self.original_image.split()[3]) # 3是Alpha通道
            
            # 使用縮圖功能進行高品質縮放，並確保是RGB格式
            self.image_for_processing = background.copy()
            self.image_for_processing.thumbnail((self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT), Image.LANCZOS)
            
            # 將圖片置中於Canvas
            final_img_w, final_img_h = self.image_for_processing.size
            self.image_x_offset = (self.DISPLAY_WIDTH - final_img_w) // 2
            self.image_y_offset = (self.DISPLAY_HEIGHT - final_img_h) // 2
            
            padded_image = Image.new('RGB', (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT), (51, 51, 51)) # 灰色背景
            padded_image.paste(self.image_for_processing, (self.image_x_offset, self.image_y_offset))
            self.image_for_processing = padded_image
            
            # 啟用UI元件
            self.set_controls_state('normal')
            self.canvas.delete(self.canvas_text_hint) # 移除提示文字
            
            # 重設所有滑桿並更新顯示
            self.reset_all_sliders()
            
            # 建立分析框
            self.setup_analysis_boxes()
            
        except Exception as e:
            messagebox.showerror("開啟失敗", f"無法開啟或處理檔案: {e}")

    def save_image(self):
        """儲存調整後的圖片"""
        if not self.processed_image:
            messagebox.showwarning("警告", "沒有可儲存的圖片。")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG file", "*.png"), ("JPEG file", "*.jpg"), ("BMP file", "*.bmp")]
        )
        if not file_path:
            return

        try:
            self.processed_image.save(file_path)
            messagebox.showinfo("成功", f"圖片已成功儲存至:\n{file_path}")
        except Exception as e:
            messagebox.showerror("儲存失敗", f"儲存檔案時發生錯誤: {e}")
            
    def set_controls_state(self, state):
        """啟用或禁用右側所有控制項"""
        for child in self.right_frame.winfo_children():
            # Toplevel widget is the canvas, its children need to be traversed
            if isinstance(child, tk.Canvas):
                # Find the scrollable frame inside the canvas
                frame_id = child.winfo_children()[0]
                for widget in frame_id.winfo_children():
                    if isinstance(widget, ttk.LabelFrame):
                        for sub_widget in widget.winfo_children():
                            try:
                                sub_widget.config(state=state)
                            except tk.TclError:
                                # Some widgets might not have a 'state' option
                                for sub_sub_widget in sub_widget.winfo_children():
                                    try:
                                        sub_sub_widget.config(state=state)
                                    except tk.TclError:
                                        pass
            else:
                try:
                    child.config(state=state)
                except tk.TclError:
                    pass

    def setup_analysis_boxes(self):
        """根據設定的數量，初始化或重設分析框"""
        if self.image_for_processing is None:
            return

        # 清除舊的方框
        for box in self.analysis_boxes:
            box.delete()
        self.analysis_boxes.clear()

        # 創建新的方框
        count = self.box_count_var.get()
        w = self.box_width_var.get()
        h = self.box_height_var.get()
        
        # 定義九個宮格的中心點位置
        positions = [
            (0.15, 0.15), (0.5, 0.15), (0.85, 0.15), # 上排
            (0.15, 0.50), (0.5, 0.50), (0.85, 0.50), # 中排
            (0.15, 0.85), (0.5, 0.85), (0.85, 0.85)  # 下排
        ]
        
        # 根據數量選取位置 (從中間開始, 然後是角落, 最後是邊緣)
        # 預設8個位置的順序
        order = [4, 0, 2, 6, 8, 1, 3, 5, 7] 
        
        for i in range(count):
            # 從預設順序中獲取位置索引
            pos_idx = order[i % len(order)]
            center_x = self.DISPLAY_WIDTH * positions[pos_idx][0]
            center_y = self.DISPLAY_HEIGHT * positions[pos_idx][1]

            x1 = int(center_x - w / 2)
            y1 = int(center_y - h / 2)
            x2 = int(x1 + w)
            y2 = int(y1 + h)

            box = DraggableRectangle(self.canvas, x1, y1, x2, y2, i + 1, self.update_analysis_results)
            self.analysis_boxes.append(box)
        
        self.update_display()
            
    def resize_analysis_boxes(self):
        """當寬高改變時，重設所有分析框的大小和位置"""
        self.setup_analysis_boxes() # 直接呼叫setup即可
            
    def update_display(self, _=None):
        """
        核心函數：應用所有影像調整，並更新Canvas上的圖片。
        這個函數會被所有滑桿的變動所觸發。
        """
        if self.image_for_processing is None:
            return

        # --- 1. 複製基底圖片，開始處理 ---
        current_image = self.image_for_processing.copy()

        # --- 2. Numpy 數組轉換，用於 R, G, B, 亮度和 Gamma ---
        img_np = np.array(current_image).astype(np.float32)

        # 調整 R, G, B
        r, g, b = self.r_var.get(), self.g_var.get(), self.b_var.get()
        img_np[..., 0] = np.clip(img_np[..., 0] + r, 0, 255)
        img_np[..., 1] = np.clip(img_np[..., 1] + g, 0, 255)
        img_np[..., 2] = np.clip(img_np[..., 2] + b, 0, 255)
        
        # 調整亮度
        brightness = self.brightness_var.get()
        img_np = np.clip(img_np + brightness, 0, 255)

        # 調整 Gamma
        gamma = self.gamma_var.get()
        if gamma != 0:
            inv_gamma = 1.0 / gamma
            # 建立查找表 (LUT) 來加速運算
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            img_np = cv2.LUT(img_np.astype(np.uint8), table).astype(np.float32)

        # 將 numpy 數組轉回 PIL Image
        current_image = Image.fromarray(img_np.astype(np.uint8))

        # --- 3. 使用 Pillow.ImageEnhance 處理其他效果 ---
        # 調整對比度 (滑桿 0-100 -> 效果 0.0-2.0)
        contrast = self.contrast_var.get() / 50.0
        enhancer = ImageEnhance.Contrast(current_image)
        current_image = enhancer.enhance(contrast)

        # 調整飽和度 (滑桿 0-100 -> 效果 0.0-2.0)
        saturation = self.saturation_var.get() / 50.0
        enhancer = ImageEnhance.Color(current_image)
        current_image = enhancer.enhance(saturation)

        # 調整銳利度 (滑桿 0-100 -> 效果 0.0-2.0)
        sharpness = self.sharpness_var.get() / 50.0
        enhancer = ImageEnhance.Sharpness(current_image)
        current_image = enhancer.enhance(sharpness)
        
        # --- 4. 處理色相和白平衡 (較複雜的色彩空間操作) ---
        # 調整色相 (滑桿 0-100 -> 旋轉 -180 到 +180 度)
        # 由於 Pillow 沒有直接的色相調整，此處為示意，可透過轉換到HSV色彩空間實現
        # hue_angle = (self.hue_var.get() - 50) * 3.6 
        # (此處暫時屏蔽，因完整實現較複雜且可能影響效能)
        
        # 調整白平衡
        temp_k = self.white_balance_var.get()
        if temp_k != 6500: # 6500K 是標準日光，視為無效果
            r_mult, g_mult, b_mult = self.kelvin_to_rgb_multiplier(temp_k)
            img_np = np.array(current_image).astype(np.float32)
            img_np[..., 0] *= r_mult
            img_np[..., 1] *= g_mult
            img_np[..., 2] *= b_mult
            img_np = np.clip(img_np, 0, 255)
            current_image = Image.fromarray(img_np.astype(np.uint8))
            
        # --- 5. 更新 Canvas 上的圖片 ---
        self.processed_image = current_image
        self.display_image_tk = ImageTk.PhotoImage(self.processed_image)
        
        if self.image_on_canvas:
            self.canvas.itemconfig(self.image_on_canvas, image=self.display_image_tk)
        else:
            self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.display_image_tk)
            # 確保分析框在圖片上方
            self.canvas.tag_raise("rect")
            self.canvas.tag_raise("text")
            
        # 確保分析框在圖片之上
        for i in range(len(self.analysis_boxes)):
            self.canvas.tag_raise(f"rect_{i+1}")
            self.canvas.tag_raise(f"text_{i+1}")
            
        # --- 6. 更新分析數據 ---
        self.update_analysis_results()
        
    def update_analysis_results(self):
        """計算每個分析框內的影像數據並顯示在文字框中"""
        if self.processed_image is None or not self.analysis_boxes:
            return

        # 將 PIL 圖片轉換為 Numpy 數組以進行快速計算
        image_np = np.array(self.processed_image)

        # 準備要顯示的文字內容
        results_text = "分析框數據 (Avg R, G, B, Brightness):\n"
        results_text += "========================================\n"

        for box in self.analysis_boxes:
            coords = [int(c) for c in box.get_coords()]
            x1, y1, x2, y2 = coords
            
            # 確保座標在圖片範圍內
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(self.DISPLAY_WIDTH, x2)
            y2 = min(self.DISPLAY_HEIGHT, y2)

            if x1 >= x2 or y1 >= y2:
                avg_r, avg_g, avg_b, avg_lum = 0, 0, 0, 0
            else:
                # 截取分析區域
                roi = image_np[y1:y2, x1:x2]
                
                # 計算 R, G, B 平均值
                avg_colors = np.mean(roi, axis=(0, 1))
                avg_r = avg_colors[0]
                avg_g = avg_colors[1]
                avg_b = avg_colors[2]

                # 計算亮度 (Luminance) 平均值 (使用常見的 Rec. 709 標準)
                avg_lum = 0.2126 * avg_r + 0.7152 * avg_g + 0.0722 * avg_b
            
            results_text += f"BOX #{box.number:<2}: R={avg_r:6.2f}, G={avg_g:6.2f}, B={avg_b:6.2f}, Lum={avg_lum:6.2f}\n"

        # 更新下方的文字框
        self.text_results.config(state='normal')
        self.text_results.delete(1.0, tk.END)
        self.text_results.insert(tk.END, results_text)
        self.text_results.config(state='disabled')

    def reset_all_sliders(self):
        """重設所有滑桿到預設值"""
        self.r_var.set(0)
        self.g_var.set(0)
        self.b_var.set(0)
        self.brightness_var.set(0)
        self.contrast_var.set(50)
        self.sharpness_var.set(50)
        self.saturation_var.set(50)
        self.hue_var.set(50)
        self.gamma_var.set(2.2)
        self.white_balance_var.set(6500)
        
        # 重設後要手動觸發一次更新
        self.update_display()

    def kelvin_to_rgb_multiplier(self, temp_k):
        """
        將色溫(K)轉換為RGB乘數。
        這是一個基於物理黑體輻射的近似算法。
        """
        temp = temp_k / 100.0
        
        # 計算 R
        if temp <= 66:
            r = 255
        else:
            r = temp - 60
            r = 329.698727446 * (r ** -0.1332047592)
            r = np.clip(r, 0, 255)
            
        # 計算 G
        if temp <= 66:
            g = temp
            g = 99.4708025861 * math.log(g) - 161.1195681661
        else:
            g = temp - 60
            g = 288.1221695283 * (g ** -0.0755148492)
        g = np.clip(g, 0, 255)
            
        # 計算 B
        if temp >= 66:
            b = 255
        elif temp <= 19:
            b = 0
        else:
            b = temp - 10
            b = 138.5177312231 * math.log(b) - 305.0447927307
            b = np.clip(b, 0, 255)
            
        # 將RGB值正規化，使其可以作為乘數
        # 我們以6500K (標準日光) 為基準 (r=255, g=255, b=255)
        # 由於算法輸出在[0, 255]之間, 我們直接除以255得到乘數
        return r/255.0, g/255.0, b/255.0
        

if __name__ == "__main__":
    # 由於 Gamma 調整使用了 OpenCV 的 LUT，請確保已安裝
    try:
        import cv2
    except ImportError:
        print("警告: 偵測到未安裝 OpenCV-Python 函式庫。")
        print("Gamma 調整功能將無法使用。")
        print("請使用 pip 安裝: pip install opencv-python")
        # 建立一個假的 cv2.LUT 來避免程式崩潰
        class cv2:
            def LUT(self, src, lut):
                # 如果沒有OpenCV，返回原圖
                return src

    root = tk.Tk()
    app = ImageAnalysisTool(root)
    root.mainloop()