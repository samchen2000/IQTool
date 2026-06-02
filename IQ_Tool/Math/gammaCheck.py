import tkinter as tk
from tkinter import filedialog, Menu, Text, Scrollbar
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import os

class DraggableResizableRect:
    """一個可在 Tkinter Canvas 上被拖曳和調整大小的方框類別"""
    def __init__(self, canvas, x1, y1, x2, y2, app_callback):
        self.canvas = canvas
        self.app_callback = app_callback
        self.id = self.canvas.create_rectangle(x1, y1, x2, y2, outline='cyan', width=2, fill='blue', stipple='gray25')
        
        # 綁定滑鼠事件
        self.canvas.tag_bind(self.id, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(self.id, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.id, "<ButtonPress-3>", self.on_resize_press)
        self.canvas.tag_bind(self.id, "<B3-Motion>", self.on_resize_drag)
        
        self.drag_data = {"x": 0, "y": 0}
        self.resize_data = {"x": 0, "y": 0}

    def on_press(self, event):
        """紀錄滑鼠左鍵點擊位置 (用於移動)"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_drag(self, event):
        """計算滑鼠左鍵拖曳的位移並移動方框"""
        delta_x = event.x - self.drag_data["x"]
        delta_y = event.y - self.drag_data["y"]
        
        self.canvas.move(self.id, delta_x, delta_y)
        
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.app_callback() # 通知主程式更新數據

    def on_resize_press(self, event):
        """紀錄滑鼠右鍵點擊位置 (用於調整大小)"""
        self.resize_data["x"] = event.x
        self.resize_data["y"] = event.y
        
    def on_resize_drag(self, event):
        """計算滑鼠右鍵拖曳的位移並調整方框大小"""
        coords = self.canvas.coords(self.id)
        # 限制新座標不小於左上角座標
        new_x2 = max(coords[0] + 5, event.x)
        new_y2 = max(coords[1] + 5, event.y)
        
        self.canvas.coords(self.id, coords[0], coords[1], new_x2, new_y2)
        
        self.resize_data["x"] = event.x
        self.resize_data["y"] = event.y
        self.app_callback() # 通知主程式更新數據

class ImageAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("圖片區域分析工具")
        self.root.geometry("1000x800")

        # --- 變數初始化 ---
        self.original_image = None
        self.tk_image = None
        self.image_display_id = None
        self.scale_factor_x = 1.0
        self.scale_factor_y = 1.0
        self.rects = []
        self.canvas_width = 800
        self.canvas_height = 600

        # --- 建立選單 ---
        self.menu = Menu(root)
        self.root.config(menu=self.menu)
        file_menu = Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="開啟圖片...", command=self.open_image)
        file_menu.add_separator()
        file_menu.add_command(label="離開", command=root.quit)

        # --- 建立主要框架 ---
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- 圖片顯示框架 (Canvas) ---
        self.canvas = tk.Canvas(main_frame, width=self.canvas_width, height=self.canvas_height, bg='gray', relief=tk.SUNKEN, borderwidth=2)
        self.canvas.pack(side=tk.TOP, anchor=tk.NW)

        # --- 結果顯示框 (Text with Scrollbar) ---
        result_frame = tk.Frame(main_frame)
        result_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.result_text = Text(result_frame, wrap=tk.WORD, height=15, font=("Consolas", 10))
        self.scrollbar = Scrollbar(result_frame, command=self.result_text.yview)
        self.result_text.config(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.result_text.insert(tk.END, "請透過 '檔案' -> '開啟圖片...' 來載入一張圖片。")
        self.result_text.config(state=tk.DISABLED)

    def open_image(self):
        """開啟圖片檔案，並在 Canvas 上顯示"""
        file_path = filedialog.askopenfilename(
            title="選擇圖片檔案",
            filetypes=(("圖片檔案", "*.jpg *.jpeg *.png *.bmp"), ("所有檔案", "*.*"))
        )
        if not file_path:
            return

        # 載入並處理圖片
        self.original_image = Image.open(file_path).convert("RGB")
        
        # 計算縮放比例
        orig_w, orig_h = self.original_image.size
        self.scale_factor_x = orig_w / self.canvas_width
        self.scale_factor_y = orig_h / self.canvas_height
        
        # 縮放圖片以適應 Canvas
        display_image = self.original_image.copy()
        display_image.thumbnail((self.canvas_width, self.canvas_height), Image.Resampling.LANCZOS)
        
        self.tk_image = ImageTk.PhotoImage(display_image)
        
        # 清除舊的圖片和方框
        self.canvas.delete("all")
        
        # 在 Canvas 左上角顯示新圖片
        self.image_display_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        
        # 建立 12 個可移動方框
        self.create_interactive_rects()
        self.calculate_and_display_stats()


    def create_interactive_rects(self):
        """在圖片上建立12個預設的方框"""
        self.rects.clear()
        cols, rows = 4, 3
        img_w, img_h = self.tk_image.width(), self.tk_image.height()
        
        for i in range(rows):
            for j in range(cols):
                x1 = (j / cols) * img_w + 10
                y1 = (i / rows) * img_h + 10
                x2 = x1 + 50
                y2 = y1 + 50
                rect = DraggableResizableRect(self.canvas, x1, y1, x2, y2, self.calculate_and_display_stats)
                self.rects.append(rect)

    def calculate_and_display_stats(self):
        """計算每個方框內的影像數據並顯示在文字框中"""
        if not self.original_image or not self.rects:
            return

        # 將原始圖片轉換為 NumPy 陣列以利快速計算
        image_np = np.array(self.original_image)
        results = []

        for i, rect in enumerate(self.rects):
            # 獲取方框在 Canvas 上的座標
            canvas_coords = self.canvas.coords(rect.id)
            c_x1, c_y1, c_x2, c_y2 = map(int, canvas_coords)

            # 將 Canvas 座標轉換回原始圖片的座標
            # 必須考慮圖片縮放後可能存在的黑邊 (在此簡化為直接縮放)
            orig_x1 = int(c_x1 * self.scale_factor_x)
            orig_y1 = int(c_y1 * self.scale_factor_y)
            orig_x2 = int(c_x2 * self.scale_factor_x)
            orig_y2 = int(c_y2 * self.scale_factor_y)

            # 確保座標在圖片範圍內
            orig_w, orig_h = self.original_image.size
            orig_x1 = max(0, orig_x1)
            orig_y1 = max(0, orig_y1)
            orig_x2 = min(orig_w, orig_x2)
            orig_y2 = min(orig_h, orig_y2)

            # 如果方框無效 (例如寬高為0)，則跳過
            if orig_x1 >= orig_x2 or orig_y1 >= orig_y2:
                avg_r, avg_g, avg_b, avg_lum = 0, 0, 0, 0
            else:
                # 使用 NumPy 切片選取 ROI (Region of Interest)
                roi = image_np[orig_y1:orig_y2, orig_x1:orig_x2]
                
                # 計算平均 RGB
                avg_colors = np.mean(roi, axis=(0, 1))
                avg_r, avg_g, avg_b = avg_colors[0], avg_colors[1], avg_colors[2]

                # 計算亮度 (Luminance) - 使用標準 Rec. 709 公式
                avg_lum = 0.2126 * avg_r + 0.7152 * avg_g + 0.0722 * avg_b
            
            # 格式化輸出字串
            result_str = (
                f"圖框 {i+1:<2} | "
                f"Avg RGB: ({avg_r:6.1f}, {avg_g:6.1f}, {avg_b:6.1f}) | "
                f"亮度: {avg_lum:6.1f}"
            )
            results.append(result_str)

        # 更新顯示文字框
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "\n".join(results))
        self.result_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageAnalyzerApp(root)
    root.mainloop()