import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import os

def unpack_bg10_to_bg16(input_path, output_path):
    """ 核心轉檔邏輯 """
    try:
        with open(input_path, 'rb') as f:
            raw_data = f.read()

        # 每 5 個 bytes 包含 4 個 10-bit 像素
        num_pixels = (len(raw_data) // 5) * 4
        unpacked = np.zeros(num_pixels, dtype=np.uint16)

        for i in range(0, len(raw_data) - 4, 5):
            # 提取 5 bytes (40 bits)
            b0, b1, b2, b3, b4 = raw_data[i:i+5]

            # MIPI CSI-2 10-bit Unpacking 邏輯
            unpacked[(i // 5) * 4]     = (b0 << 2) | (b1 >> 7)
            unpacked[(i // 5) * 4 + 1] = ((b1 & 0x7F) << 3) | (b2 >> 5)
            unpacked[(i // 5) * 4 + 2] = ((b2 & 0x1F) << 5) | (b3 >> 3)
            unpacked[(i // 5) * 4 + 3] = ((b3 & 0x07) << 8) | b4

        # 儲存為 16-bit Raw 檔案 (Padded)
        unpacked.tofile(output_path)
        return True, len(raw_data), unpacked.nbytes
    except Exception as e:
        return False, str(e), 0

class RAWConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BG10 $\rightarrow$ BG16 RAW 轉檔工具")
        self.root.geometry("500x250")

        # --- 變數儲存 ---
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()

        # --- 介面佈局 ---
        # 輸入檔案部分
        tk.Label(root, text="輸入 BG10 檔案:").grid(row=0, column=0, padx=10, pady=20, sticky="e")
        self.ent_input = tk.Entry(root, textvariable=self.input_path, width=40)
        self.ent_input.grid(row=0, column=1, padx=10, pady=20)
        btn_browse_in = tk.Button(root, text="瀏覽...", command=self.browse_input)
        btn_browse_in.grid(row=0, column=2, padx=10, pady=20)

        # 輸出檔案部分
        tk.Label(root, text="儲存 Padded 檔案:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.ent_output = tk.Entry(root, textvariable=self.output_path, width=40)
        self.ent_output.grid(row=1, column=1, padx=10, pady=10)
        btn_browse_out = tk.Button(root, text="選擇位置...", command=self.browse_output)
        btn_browse_out.grid(row=1, column=2, padx=10, pady=10)

        # 執行按鈕
        self.btn_convert = tk.Button(root, text="開始轉檔", command=self.run_conversion, 
                                     bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), width=20)
        self.btn_convert.grid(row=2, column=0, columnspan=3, pady=30)

    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="選擇 RAW 檔案",
            filetypes=[("RAW files", "*.raw"), ("All files", "*.*")]
        )
        if filename:
            self.input_path.set(filename)
            # 自動建議輸出路徑：原檔名 + _padded.raw
            base, ext = os.path.splitext(filename)
            self.output_path.set(base + "_padded" + ext)

    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="儲存轉檔檔案",
            defaultextension=".raw",
            filetypes=[("RAW files", "*.raw"), ("All files", "*.*")]
        )
        if filename:
            self.output_path.set(filename)

    def run_conversion(self):
        in_p = self.input_path.get()
        out_p = self.output_path.get()

        if not in_p or not out_p:
            messagebox.showwarning("警告", "請先選擇輸入與輸出路徑！")
            return

        # 執行轉檔
        success, info1, info2 = unpack_bg10_to_bg16(in_p, out_p)

        if success:
            messagebox.showinfo("成功", f"轉檔完成！\n\n原始大小: {info1} bytes\n轉換後大小: {info2} bytes\n儲存位置: {out_p}")
        else:
            messagebox.showerror("錯誤", f"轉檔失敗：\n{info1}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RAWConverterApp(root)
    root.mainloop()
