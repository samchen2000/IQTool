import tkinter as tk
from tkinter import filedialog, Menu, Text, Scrollbar, Scale, Label, Button
from PIL import Image, ImageTk
import numpy as np

class DraggableResizableRect:
    """一個可在 Tkinter Canvas 上被拖曳和調整大小的方框類別 (含編號)"""
    def __init__(self, canvas, x1, y1, x2, y2, number, app_callback):
        self.canvas = canvas
        self.app_callback = app_callback
        
        # 建立方框
        self.rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2, 
            outline='cyan', 
            width=2, 
            fill='blue', 
            stipple='gray50' # 使用更明顯的半透明效果
        )
        
        # 建立編號文字
        self.text_id = self.canvas.create_text(
            x1 + 5, y1 + 5, 
            text=str(number), 
            fill='white', 
            anchor=tk.NW,
            font=("Arial", 10, "bold")
        )
        
        # 綁定滑鼠事件
        self.canvas.tag_bind(self.rect_id, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(self.rect_id, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.rect_id, "<ButtonPress-3>", self.on_resize_press)
        self.canvas.tag_bind(self.rect_id, "<B3-Motion>", self.on_resize_drag)
        # 同時綁定文字，讓點擊文字也能觸發
        self.canvas.tag_bind(self.text_id, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(self.text_id, "<B1-Motion>", self.on_drag)

        self.drag_data = {"x": 0, "y": 0}
        self.resize_data = {"x": 0, "y": 0}

    def on_press(self, event):
        """紀錄滑鼠左鍵點擊位置 (用於移動)"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        # 確保方框和文字在最上層
        self.canvas.lift(self.rect_id)
        self.canvas.lift(self.text_id)

    def on_drag(self, event):
        """計算滑鼠左鍵拖曳的位移並移動方框與文字"""
        delta_x = event.x - self.drag_data["x"]
        delta_y = event.y - self.drag_data["y"]
        
        # 移動方框和文字
        self.canvas.move(self.rect_id, delta_x, delta_y)
        self.canvas.move(self.text_id, delta_x, delta_y)
        
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.app_callback()

    def on_resize_press(self, event):
        """紀錄滑鼠右鍵點擊位置 (用於調整大小)"""
        self.resize_data["x"] = event.x
        self.resize_data["y"] = event.y
        self.canvas.lift(self.rect_id)
        self.canvas.lift(self.text_id)
        
    def on_resize_drag(self, event):
        """計算滑鼠右鍵拖曳的位移並調整方框大小"""
        coords = self.canvas.coords(self.rect_id)
        # 限制新座標不小於左上角座標
        new_x2 = max(coords[0] + 15, event.x) # 確保最小寬度
        new_y2 = max(coords[1] + 15, event.y) # 確保最小高度
        
        self.canvas.coords(self.rect_id, coords[0], coords[1], new_x2, new_y2)
        
        self.resize_data["x"] = event.x
        self.resize_data["y"] = event.y
        self.app_callback()
    
    def delete(self):
        """從畫布上刪除方框和文字"""
        self.canvas.delete(self.rect_id)
        self.canvas.delete(self.text_id)


class ImageAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("圖片區域分析工具 (v2)")
        self.root.geometry("1200x800") # 加寬視窗以容納設定面板

        # --- 變數初始化 ---
        self.original_image = None
        self.tk_image = None
        self.rects = []
        self.num_rects_to_create = tk.IntVar(value=12) # 預設方框數量

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
        
        # --- 左側框架 (圖片顯示) ---
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas_width, self.canvas_height = 800, 600
        self.canvas = tk.Canvas(left_frame, width=self.canvas_width, height=self.canvas_height, bg='gray', relief=tk.SUNKEN, borderwidth=2)
        self.canvas.pack(side=tk.TOP, anchor=tk.NW)

        # --- 結果顯示框 ---
        result_frame = tk.Frame(left_frame)
        result_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, pady=(10, 0))
        self.result_text = Text(result_frame, wrap=tk.WORD, height=15, font=("Consolas", 10))
        self.scrollbar = Scrollbar(result_frame, command=self.result_text.yview)
        self.result_text.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.result_text.insert(tk.END, "請透過 '檔案' -> '開啟圖片...' 來載入一張圖片。")
        self.result_text.config(state=tk.DISABLED)
        
        # --- 右側設定面板 ---
        settings_frame = tk.Frame(main_frame, width=200, padx=10)
        settings_frame.pack(side=tk.RIGHT, fill=tk.Y)
        settings_frame.pack_propagate(False) # 防止框架縮小

        Label(settings_frame, text="設定", font=("Arial", 14, "bold")).pack(pady=10)
        
        Label(settings_frame, text="方框數量:").pack(anchor=tk.W)
        self.rect_count_slider = Scale(
            settings_frame, 
            from_=1, 
            to=25, 
            orient=tk.HORIZONTAL, 
            variable=self.num_rects_to_create
        )
        self.rect_count_slider.pack(fill=tk.X, pady=5)
        
        Button(
            settings_frame, 
            text="更新方框數量", 
            command=self.recreate_interactive_rects
        ).pack(fill=tk.X, pady=10)


    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=(("圖片檔案", "*.jpg *.jpeg *.png *.bmp"), ("所有檔案", "*.*")))
        if not file_path:
            return

        self.original_image = Image.open(file_path).convert("RGB")
        
        # 縮放圖片以適應 Canvas
        display_image = self.original_image.copy()
        display_image.thumbnail((self.canvas_width, self.canvas_height), Image.Resampling.LANCZOS)
        
        self.tk_image = ImageTk.PhotoImage(display_image)
        
        # 計算縮放比例
        orig_w, orig_h = self.original_image.size
        disp_w, disp_h = self.tk_image.width(), self.tk_image.height()
        self.scale_factor_x = orig_w / disp_w
        self.scale_factor_y = orig_h / disp_h
        
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        
        self.recreate_interactive_rects()

    def clear_rects(self):
        """清除畫布上所有方框物件"""
        for rect in self.rects:
            rect.delete()
        self.rects.clear()

    def recreate_interactive_rects(self):
        """根據滑桿設定的數量，重新建立方框"""
        if not self.tk_image:
            return
            
        self.clear_rects()
        
        count = self.num_rects_to_create.get()
        # 嘗試以接近正方形的方式排列方框
        cols = int(np.ceil(np.sqrt(count)))
        rows = int(np.ceil(count / cols))
        
        img_w, img_h = self.tk_image.width(), self.tk_image.height()
        
        rect_idx = 0
        for i in range(rows):
            for j in range(cols):
                if rect_idx >= count:
                    break
                
                x1 = (j / cols) * img_w + 10
                y1 = (i / rows) * img_h + 10
                x2 = x1 + 50
                y2 = y1 + 50
                
                # 確保方框在圖片範圍內
                x2 = min(x2, img_w - 1)
                y2 = min(y2, img_h - 1)
                
                rect = DraggableResizableRect(self.canvas, x1, y1, x2, y2, rect_idx + 1, self.calculate_and_display_stats)
                self.rects.append(rect)
                rect_idx += 1
                
        self.calculate_and_display_stats()

    def calculate_and_display_stats(self):
        if not self.original_image or not self.rects:
            # 如果沒有圖片或方框，清空文字顯示區
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.config(state=tk.DISABLED)
            return

        image_np = np.array(self.original_image)
        results = []

        for i, rect in enumerate(self.rects):
            canvas_coords = self.canvas.coords(rect.rect_id)
            c_x1, c_y1, c_x2, c_y2 = map(int, canvas_coords)

            orig_x1 = int(c_x1 * self.scale_factor_x)
            orig_y1 = int(c_y1 * self.scale_factor_y)
            orig_x2 = int(c_x2 * self.scale_factor_x)
            orig_y2 = int(c_y2 * self.scale_factor_y)

            orig_w, orig_h = self.original_image.size
            orig_x1, orig_y1 = max(0, orig_x1), max(0, orig_y1)
            orig_x2, orig_y2 = min(orig_w, orig_x2), min(orig_h, orig_y2)

            if orig_x1 >= orig_x2 or orig_y1 >= orig_y2:
                avg_r, avg_g, avg_b, avg_lum = 0, 0, 0, 0
            else:
                roi = image_np[orig_y1:orig_y2, orig_x1:orig_x2]
                avg_colors = np.mean(roi, axis=(0, 1))
                avg_r, avg_g, avg_b = avg_colors
                avg_lum = 0.2126 * avg_r + 0.7152 * avg_g + 0.0722 * avg_b
            
            result_str = (
                f"方框 {i+1:<2} | "
                f"Avg RGB: ({avg_r:6.1f}, {avg_g:6.1f}, {avg_b:6.1f}) | "
                f"亮度: {avg_lum:6.1f}"
            )
            results.append(result_str)

        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "\n".join(results))
        self.result_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageAnalyzerApp(root)
    root.mainloop()