import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import struct
import os

class CsvToBinConverter:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("CSV 轉 BIN 轉換器")
        self.window.geometry("400x300")
        
        # 增加狀態標籤
        self.status_label = tk.Label(self.window, text="待轉換")
        self.status_label.pack(pady=10)
        
        self.convert_btn = tk.Button(
            self.window, 
            text="選擇 CSV 檔案並轉換",
            command=self.convert_csv_to_bin
        )
        self.convert_btn.pack(pady=20)
        
    def convert_csv_to_bin(self):
        csv_file = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")]
        )
        if not csv_file:
            return
            
        try:
            # 讀取 CSV 並顯示資料
            df = pd.read_csv(csv_file)
            self.status_label.config(text=f"讀取到 {len(df)} 筆資料")
            
            output_file = os.path.splitext(csv_file)[0] + '.bin'
            
            with open(output_file, 'wb') as f:
                # 將每個數值轉為二進制
                for _, row in df.iterrows():
                    for value in row:
                        try:
                            # 數值轉換
                            if pd.notna(value):  # 檢查非空值
                                if isinstance(value, (int, float)):
                                    f.write(struct.pack('<f', float(value)))
                                elif isinstance(value, str) and value.replace('.','',1).isdigit():
                                    f.write(struct.pack('<f', float(value)))
                        except (ValueError, TypeError) as e:
                            print(f"跳過無效值: {value}, 錯誤: {e}")
            
            # 檢查輸出檔案大小
            file_size = os.path.getsize(output_file)
            self.status_label.config(text=f"轉換完成\n檔案大小: {file_size} bytes")
            
            if file_size > 0:
                messagebox.showinfo("成功", f"已轉換完成\n儲存於: {output_file}\n檔案大小: {file_size} bytes")
            else:
                messagebox.showwarning("警告", "輸出檔案為空")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"轉換失敗: {str(e)}")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = CsvToBinConverter()
    app.run()