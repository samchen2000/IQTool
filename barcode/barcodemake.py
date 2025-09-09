import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import barcode
import qrcode
import os
from io import BytesIO

# 條碼類型定義
barcode_types = {
    "一維碼": [
        "ean8", "ean13", "upca", "upce", "isbn10", "isbn13",
        "issn", "jan", "pzn", "gtin", "codabar", "code128", "code39",
    ],
    "二維碼": ["qr", ],
    "PDF417": ["pdf417"],
}

# 輔助函式：根據類型獲取條碼類
def get_barcode_class(name):
    if name == "qr":
        return qrcode
    elif name == "pdf417":
        return barcode.PDF417
    else:
        return getattr(barcode, name.upper(), None)

# 主應用程式類別
class BarcodeGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("條碼產生器")
        self.root.geometry("800x600")

        # 框架：分為左中右三個區塊
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 建立三個分區框架
        self.left_frame = tk.Frame(main_frame, width=250, bd=2, relief="groove")
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        self.middle_frame = tk.Frame(main_frame, width=500, bd=2, relief="groove")
        self.middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 初始化 GUI
        self.create_widgets()

    def create_widgets(self):
        # 左側控制區塊
        tk.Label(self.left_frame, text="條碼設定", font=("Arial", 14, "bold")).pack(pady=10)

        # 條碼類型選擇
        tk.Label(self.left_frame, text="選擇條碼類型：").pack(pady=(10, 2))
        self.barcode_type_var = tk.StringVar()
        self.barcode_type_combo = ttk.Combobox(self.left_frame, textvariable=self.barcode_type_var, state="readonly")
        
        # 將所有條碼類型扁平化到一個清單中
        all_types = []
        for group in barcode_types.values():
            all_types.extend(group)
        self.barcode_type_combo['values'] = all_types
        self.barcode_type_combo.set("ean13") # 預設值
        self.barcode_type_combo.bind("<<ComboboxSelected>>", self.on_type_change)
        self.barcode_type_combo.pack(pady=(0, 10), padx=5)

        # 條碼數據輸入
        tk.Label(self.left_frame, text="條碼數據：").pack(pady=(10, 2))
        self.data_entry = tk.Entry(self.left_frame, width=30)
        self.data_entry.pack(pady=(0, 10), padx=5)
        
        # 參數提示
        self.hint_label = tk.Label(self.left_frame, text="", fg="gray")
        self.hint_label.pack(pady=(0, 10))

        # 調整參數
        tk.Label(self.left_frame, text="調整條碼尺寸").pack(pady=(10, 2))
        
        tk.Label(self.left_frame, text="寬度 (Module Width, e.g., 0.29):").pack(pady=(5, 2))
        self.width_entry = tk.Entry(self.left_frame, width=10)
        self.width_entry.insert(0, "0.29")
        self.width_entry.pack(pady=(0, 10))

        tk.Label(self.left_frame, text="高度 (e.g., 10):").pack(pady=(5, 2))
        self.height_entry = tk.Entry(self.left_frame, width=10)
        self.height_entry.insert(0, "10")
        self.height_entry.pack(pady=(0, 10))

        # 按鈕
        self.generate_button = tk.Button(self.left_frame, text="產生條碼", command=self.generate_barcode)
        self.generate_button.pack(pady=20)

        self.save_button = tk.Button(self.left_frame, text="儲存條碼", command=self.save_barcode)
        self.save_button.pack(pady=10)
        
        # 右側顯示區塊
        tk.Label(self.middle_frame, text="條碼顯示區", font=("Arial", 14, "bold")).pack(pady=10)
        self.barcode_canvas = tk.Canvas(self.middle_frame, bg="white", highlightthickness=1, highlightbackground="black")
        self.barcode_canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 條碼文字碼顯示
        self.text_label = tk.Label(self.middle_frame, text="", font=("Arial", 12))
        self.text_label.pack(pady=5)
        
        self.on_type_change() # 初始提示

    def on_type_change(self, event=None):
        selected_type = self.barcode_type_var.get()
        hint_text = ""
        
        if selected_type == "ean8":
            hint_text = "EAN8: 7位數字，最後一位為校驗碼。"
        elif selected_type == "ean13":
            hint_text = "EAN13: 12位數字，最後一位為校驗碼。"
        elif selected_type == "code128":
            hint_text = "Code128: 支援所有 ASCII 字元。"
        elif selected_type == "upca":
            hint_text = "UPC-A: 11位數字，最後一位為校驗碼。"
        elif selected_type == "upce":
            hint_text = "UPC-E: 壓縮型 UPC，6位數字，最後一位為校驗碼。"
        elif selected_type == "isbn10":
            hint_text = "ISBN10: 9位數字，最後一位為校驗碼（可為X）。"
        elif selected_type == "isbn13":
            hint_text = "ISBN13: 12位數字，最後一位為校驗碼。"
        elif selected_type == "issn":
            hint_text = "ISSN: 7位數字，最後一位為校驗碼（可為X）。"
        elif selected_type == "jan":
            hint_text = "JAN: 12位數字，最後一位為校驗碼。"
        elif selected_type == "pzn":
            hint_text = "PZN: 7位數字，最後一位為校驗碼。"
        elif selected_type == "gtin":
            hint_text = "GTIN: 13位數字，最後一位為校驗碼。"
        elif selected_type == "codabar":
            hint_text = "Codabar: 支援數字和部分特殊字元。"
        elif selected_type == "code39":
            hint_text = "Code39: 支援數字、字母和部分特殊字元。"
        elif selected_type == "qr":
            hint_text = "QR Code: 可儲存數字、字母、二進位資料，甚至中文。 "
        elif selected_type == "pdf417":
            hint_text = "PDF417: 堆疊式條碼，可儲存數字、字母、二進位資料，甚至中文。"
        else:
            hint_text = "請輸入條碼數據。"
        
        self.hint_label.config(text=hint_text)
        
    def generate_barcode(self):
        data = self.data_entry.get().strip()
        selected_type = self.barcode_type_var.get()
        
        if not data:
            self.show_message("請輸入條碼數據。", "red")
            return

        try:
            # 獲取寬度和高度參數
            module_width = float(self.width_entry.get())
            module_height = float(self.height_entry.get())

            if selected_type == "qr":
                # 生成 QR Code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=int(module_width * 10),  # 調整大小
                    border=4,
                )
                qr.add_data(data)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
                
                # 調整 QR Code 高度
                current_width, current_height = img.size
                new_height = int(current_height * module_height / 10)
                if new_height > 0:
                    img = img.resize((current_width, new_height))
                
                self.generated_image = img
                self.display_image(img)
                self.text_label.config(text="") # QR碼不顯示文字
                
            elif selected_type == "pdf417":
                # 生成 PDF417
                pdf417 = barcode.PDF417(data)
                self.generated_image = pdf417.render(writer=barcode.writer.ImageWriter())
                self.display_image(self.generated_image)
                self.text_label.config(text="")
            else:
                # 生成一維條碼
                barcode_class = get_barcode_class(selected_type)
                if barcode_class:
                    options = {
                        "module_width": module_width,
                        "module_height": module_height,
                        "write_text": True,
                        "text_distance": 5,
                        "font_size": 12,
                        "quiet_zone": 6,
                    }
                    barcode_instance = barcode_class(data, writer=barcode.writer.ImageWriter())
                    self.generated_image = barcode_instance.render(options)
                    self.display_image(self.generated_image)
                    self.text_label.config(text=data)
                    
            self.show_message("條碼已成功生成！", "green")

        except Exception as e:
            self.show_message(f"產生條碼失敗: {e}", "red")

    def display_image(self, pil_image):
        """將 PIL 圖片顯示到 Canvas 上"""
        self.barcode_canvas.delete("all")
        canvas_width = self.barcode_canvas.winfo_width()
        canvas_height = self.barcode_canvas.winfo_height()
        
        # 調整圖片大小以適應畫布
        img_width, img_height = pil_image.size
        ratio_w = canvas_width / img_width
        ratio_h = canvas_height / img_height
        ratio = min(ratio_w, ratio_h)
        
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        if new_width > 0 and new_height > 0:
            resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(resized_image)
            self.barcode_canvas.create_image(canvas_width/2, canvas_height/2, image=self.tk_image, anchor=tk.CENTER)

    def save_barcode(self):
        if not hasattr(self, 'generated_image'):
            self.show_message("請先產生一個條碼。", "red")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG file", "*.png"),
                ("JPEG file", "*.jpg"),
                ("BMP file", "*.bmp"),
            ]
        )
        
        if file_path:
            try:
                self.generated_image.save(file_path)
                self.show_message(f"條碼已儲存至 {file_path}", "green")
            except Exception as e:
                self.show_message(f"儲存失敗: {e}", "red")
    
    def show_message(self, message, color):
        # 暫時性的提示訊息
        status_label = tk.Label(self.root, text=message, fg=color)
        status_label.pack(side=tk.BOTTOM, fill=tk.X)
        self.root.after(3000, status_label.destroy)

if __name__ == "__main__":
    root = tk.Tk()
    app = BarcodeGeneratorApp(root)
    root.mainloop()