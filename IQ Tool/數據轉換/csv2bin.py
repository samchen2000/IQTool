import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import struct
import os

class CsvToBinConverter:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("CSV 轉 BIN 轉換器")
        self.window.geometry("400x200")
        
        # 建立按鈕
        self.convert_btn = tk.Button(
            self.window, 
            text="選擇 CSV 檔案並轉換",
            command=self.convert_csv_to_bin
        )
        self.convert_btn.pack(pady=20)
        
    def convert_csv_to_bin(self):
        # 選擇 CSV 檔案
        csv_file = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")]
        )
        if not csv_file:
            return
            
        try:
            # 讀取 CSV
            df = pd.read_csv(csv_file)
            
            # 建立輸出檔名
            output_file = os.path.splitext(csv_file)[0] + '.bin'
            
            # 轉換為二進制
            with open(output_file, 'wb') as f:
                for _, row in df.iterrows():
                    for value in row:
                        # 假設數值為 float
                        f.write(struct.pack('f', float(value)))
            
            messagebox.showinfo("成功", f"已轉換完成\n儲存於: {output_file}")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"轉換失敗: {str(e)}")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = CsvToBinConverter()
    app.run()