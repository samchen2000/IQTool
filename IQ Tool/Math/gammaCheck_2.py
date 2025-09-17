import tkinter as tk
from tkinter import filedialog, Menu, Text, Scrollbar, Scale, Label, Button, Frame
from PIL import Image, ImageTk
import numpy as np

class DraggableResizableRect:
    """一個可在 Tkinter Canvas 上被拖曳和調整大小的方框類別 (含編號)"""
    def __init__(self, canvas, x1, y1, x2, y2, number, app_callback):
        self.canvas = canvas
        self.app_callback = app_callback
        self.rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline='cyan', width=2, fill='blue', stipple='gray50')
        self.text_id = self.canvas.create_text(x1 + 5, y1 + 5, text=str(number), fill='white', anchor=tk.NW, font=("Arial", 10, "bold"))
        
        for tag in [self.rect_id, self.text_id]:
            self.canvas.tag_bind(tag, "<ButtonPress-1>", self.on_press)
            self.canvas.tag_bind(tag, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(tag, "<ButtonPress-3>", self.on_resize_press)
            self.canvas.tag_bind(tag, "<B3-Motion>", self.on_resize_drag)

        self.drag_data = {"x": 0, "y": 0}
        self.resize_data = {"x": 0, "y": 0}

    def on_press(self, event):
        self.drag_data["x"], self.drag_data["y"] = event.x, event.y
        self.canvas.lift(self.rect_id)
        self.canvas.lift(self.text_id)

    def on_drag(self, event):
        delta_x, delta_y = event.x - self.drag_data["x"], event.y - self.drag_data["y"]
        self.canvas.move(self.rect_id, delta_x, delta_y)
        self.canvas.move(self.text_id, delta_x, delta_y)
        self.drag_data["x"], self.drag_data["y"] = event.x, event.y
        self.app_callback(recalculate_stats=True) # 只移動方框，只需重算統計值

    def on_resize_press(self, event):
        self.resize_data["x"], self.resize_data["y"] = event.x, event.y
        self.canvas.lift(self.rect_id)
        self.canvas.lift(self.text_id)
        
    def on_resize_drag(self, event):
        coords = self.canvas.coords(self.rect_id)
        new_x2, new_y2 = max(coords[0] + 15, event.x), max(coords[1] + 15, event.y)
        self.canvas.coords(self.rect_id, coords[0], coords[1], new_x2, new_y2)
        text_coords = self.canvas.coords(self.text_id)
        self.canvas.coords(self.text_id, coords[0] + 5, coords[1] + 5)
        self.resize_data["x"], self.resize_data["y"] = event.x, event.y
        self.app_callback(recalculate_stats=True)

    def delete(self):
        self.canvas.delete(self.rect_id)
        self.canvas.delete(self.text_id)

class ImageAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("圖片區域分析與調整工具 (v3)")
        self.root.geometry("1080x720")

        # --- 變數初始化 ---
        self.original_image_np = None
        self.adjusted_image_np = None
        self.tk_image = None
        self.image_display_id = None
        self.rects = []
        
        # --- Tkinter 變數 ---
        self.num_rects_to_create = tk.IntVar(value=12)
        self.r_adjust = tk.IntVar(value=0)
        self.g_adjust = tk.IntVar(value=0)
        self.b_adjust = tk.IntVar(value=0)
        self.brightness_adjust = tk.IntVar(value=0)

        # --- 建立選單 ---
        self.menu = Menu(root)
        self.root.config(menu=self.menu)
        file_menu = Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="開啟圖片...", command=self.open_image)
        file_menu.add_command(label="另存調整後的圖片...", command=self.save_adjusted_image)
        file_menu.add_separator()
        file_menu.add_command(label="離開", command=root.quit)

        # --- 主框架 ---
        main_frame = Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- 左側框架 (圖片與數據) ---
        left_frame = Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas_width, self.canvas_height = 600, 450
        self.canvas = tk.Canvas(left_frame, width=self.canvas_width, height=self.canvas_height, bg='gray', relief=tk.SUNKEN, borderwidth=2)
        self.canvas.pack(side=tk.TOP, anchor=tk.NW)

        result_frame = Frame(left_frame)
        result_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, pady=(10, 0))
        self.result_text = Text(result_frame, wrap=tk.WORD, height=15, font=("Consolas", 10))
        self.scrollbar = Scrollbar(result_frame, command=self.result_text.yview)
        self.result_text.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.result_text.insert(tk.END, "請透過 '檔案' -> '開啟圖片...' 來載入一張圖片。")
        self.result_text.config(state=tk.DISABLED)
        
        # --- 右側設定面板 ---
        settings_frame = Frame(main_frame, width=250, padx=10)
        settings_frame.pack(side=tk.RIGHT, fill=tk.Y)
        settings_frame.pack_propagate(False)

        Label(settings_frame, text="設定", font=("Arial", 14, "bold")).pack(pady=10)
        
        # 方框數量調整
        Label(settings_frame, text="方框數量:").pack(anchor=tk.W, pady=(10,0))
        Scale(settings_frame, from_=1, to=25, orient=tk.HORIZONTAL, variable=self.num_rects_to_create).pack(fill=tk.X, pady=5)
        Button(settings_frame, text="更新方框數量", command=self.recreate_interactive_rects).pack(fill=tk.X, pady=(0, 20))

        # 影像調整滑桿
        Label(settings_frame, text="影像調整", font=("Arial", 9, "bold")).pack(pady=10)
        self.create_adjuster_slider(settings_frame, "亮度 (Brightness)", self.brightness_adjust)
        self.create_adjuster_slider(settings_frame, "紅色 (R)", self.r_adjust)
        self.create_adjuster_slider(settings_frame, "綠色 (G)", self.g_adjust)
        self.create_adjuster_slider(settings_frame, "藍色 (B)", self.b_adjust)

    def create_adjuster_slider(self, parent, text, variable):
        """建立一個影像調整滑桿的輔助函式"""
        Label(parent, text=text).pack(anchor=tk.W)
        Scale(
            parent, from_=-127, to=127, orient=tk.HORIZONTAL, variable=variable, 
            command=lambda val: self.apply_image_adjustments(recalculate_stats=True)
        ).pack(fill=tk.X, pady=(0, 10))

    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=(("圖片檔案", "*.jpg *.jpeg *.png *.bmp"), ("所有檔案", "*.*")))
        if not file_path: return

        # 載入圖片並轉為 NumPy 陣列
        image_pil = Image.open(file_path).convert("RGB")
        self.original_image_np = np.array(image_pil)

        # 重置所有調整滑桿
        self.brightness_adjust.set(0)
        self.r_adjust.set(0)
        self.g_adjust.set(0)
        self.b_adjust.set(0)

        # 應用調整（此時為無調整）並顯示圖片
        self.apply_image_adjustments(recreate_rects=True)

    def apply_image_adjustments(self, recalculate_stats=False, recreate_rects=False):
        if self.original_image_np is None: return

        # 使用 int16 作為中介格式以避免溢位
        adjusted_np = self.original_image_np.astype(np.int16)

        # 獲取滑桿值
        b_val = self.brightness_adjust.get()
        r_val = self.r_adjust.get()
        g_val = self.g_adjust.get()
        b_val_color = self.b_adjust.get()

        # 應用調整
        adjusted_np += b_val
        adjusted_np[:, :, 0] += r_val
        adjusted_np[:, :, 1] += g_val
        adjusted_np[:, :, 2] += b_val_color

        # 使用 np.clip 將值限制在 0-255 範圍內，並轉回 uint8
        self.adjusted_image_np = np.clip(adjusted_np, 0, 255).astype(np.uint8)

        # 更新畫布上的圖片
        self.update_canvas_image()
        
        if recreate_rects:
            self.recreate_interactive_rects()
        elif recalculate_stats:
            self.calculate_and_display_stats()

    def update_canvas_image(self):
        """將 NumPy 陣列轉換並顯示在 Canvas 上"""
        adjusted_pil = Image.fromarray(self.adjusted_image_np)
        
        # 縮放圖片以適應 Canvas
        display_image = adjusted_pil.copy()
        display_image.thumbnail((self.canvas_width, self.canvas_height), Image.Resampling.LANCZOS)
        
        self.tk_image = ImageTk.PhotoImage(display_image)
        
        # 計算縮放比例
        orig_w, orig_h = adjusted_pil.size
        disp_w, disp_h = self.tk_image.width(), self.tk_image.height()
        self.scale_factor_x = orig_w / disp_w
        self.scale_factor_y = orig_h / disp_h
        
        if self.image_display_id:
            self.canvas.itemconfig(self.image_display_id, image=self.tk_image)
        else:
            self.image_display_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def save_adjusted_image(self):
        if self.adjusted_image_np is None:
            tk.messagebox.showwarning("無法儲存", "沒有可供儲存的已調整圖片。")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=(("PNG 檔案", "*.png"), ("JPEG 檔案", "*.jpg"), ("BMP 檔案", "*.bmp"), ("所有檔案", "*.*"))
        )
        if not file_path: return

        try:
            img_to_save = Image.fromarray(self.adjusted_image_np)
            img_to_save.save(file_path)
            tk.messagebox.showinfo("成功", f"圖片已成功儲存至:\n{file_path}")
        except Exception as e:
            tk.messagebox.showerror("儲存失敗", f"儲存圖片時發生錯誤:\n{e}")

    def clear_rects(self):
        for rect in self.rects: rect.delete()
        self.rects.clear()

    def recreate_interactive_rects(self):
        if self.tk_image is None: return
        self.clear_rects()
        count = self.num_rects_to_create.get()
        cols = int(np.ceil(np.sqrt(count)))
        rows = int(np.ceil(count / cols))
        img_w, img_h = self.tk_image.width(), self.tk_image.height()
        
        rect_idx = 0
        for i in range(rows):
            for j in range(cols):
                if rect_idx >= count: break
                x1, y1 = (j / cols) * img_w + 10, (i / rows) * img_h + 10
                x2, y2 = min(x1 + 50, img_w - 1), min(y1 + 50, img_h - 1)
                rect = DraggableResizableRect(self.canvas, x1, y1, x2, y2, rect_idx + 1, self.calculate_and_display_stats)
                self.rects.append(rect)
                rect_idx += 1
        self.calculate_and_display_stats()

    def calculate_and_display_stats(self, *args):
        if self.adjusted_image_np is None or not self.rects:
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.config(state=tk.DISABLED)
            return

        results = []
        for i, rect in enumerate(self.rects):
            canvas_coords = self.canvas.coords(rect.rect_id)
            if not canvas_coords: continue
            
            c_x1, c_y1, c_x2, c_y2 = map(int, canvas_coords)
            orig_x1, orig_y1 = int(c_x1 * self.scale_factor_x), int(c_y1 * self.scale_factor_y)
            orig_x2, orig_y2 = int(c_x2 * self.scale_factor_x), int(c_y2 * self.scale_factor_y)

            orig_h, orig_w, _ = self.adjusted_image_np.shape
            orig_x1, orig_y1 = max(0, orig_x1), max(0, orig_y1)
            orig_x2, orig_y2 = min(orig_w, orig_x2), min(orig_h, orig_y2)

            if orig_x1 >= orig_x2 or orig_y1 >= orig_y2:
                avg_r, avg_g, avg_b, avg_lum = 0, 0, 0, 0
            else:
                avg_ium_1 = 0
                roi = self.adjusted_image_np[orig_y1:orig_y2, orig_x1:orig_x2]
                avg_colors = np.mean(roi, axis=(0, 1))
                avg_r, avg_g, avg_b = avg_colors
                avg_lum = 0.2126 * avg_r + 0.7152 * avg_g + 0.0722 * avg_b
                difference = avg_lum - avg_ium_1
            
            result_str = f"方框 {i+1:<2} | Avg RGB: ({avg_r:6.1f}, {avg_g:6.1f}, {avg_b:6.1f}) | 亮度: {avg_lum:6.1f} | {difference:6.1f}"
            results.append(result_str)

        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "\n".join(results))
        self.result_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageAnalyzerApp(root)
    root.mainloop()

