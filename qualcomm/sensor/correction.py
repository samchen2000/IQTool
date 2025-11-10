import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import time
import os

class ISP_CalibrationTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ISP 自動化校正工具 (Tkinter)")
        self.geometry("800x500")
        self.resizable(False, False)
        self.create_widgets()

    def create_widgets(self):
        # 左側功能區
        frame_left = tk.Frame(self, width=250, bg="#e6e6e6", relief=tk.RIDGE, borderwidth=2)
        frame_left.pack(side="left", fill="y")

        tk.Label(frame_left, text="校正流程控制", bg="#e6e6e6", font=("微軟正黑體", 12, "bold")).pack(pady=10)

        ttk.Button(frame_left, text="① 載入 Sensor 設定檔", command=self.load_sensor_ini).pack(pady=5, fill='x', padx=10)
        ttk.Button(frame_left, text="② GainMap 校正", command=lambda: self.run_process("GainMap")).pack(pady=5, fill='x', padx=10)
        ttk.Button(frame_left, text="③ DCC Map 校正", command=lambda: self.run_process("DCC")).pack(pady=5, fill='x', padx=10)
        ttk.Button(frame_left, text="④ Sharpness 驗證", command=lambda: self.run_process("Sharpness")).pack(pady=5, fill='x', padx=10)
        ttk.Button(frame_left, text="⑤ 一鍵自動化執行", command=self.run_all).pack(pady=15, fill='x', padx=10)

        ttk.Separator(frame_left, orient='horizontal').pack(fill='x', padx=5, pady=10)
        ttk.Button(frame_left, text="匯出報告", command=self.export_report).pack(pady=10, fill='x', padx=10)
        ttk.Button(frame_left, text="離開", command=self.quit).pack(pady=10, fill='x', padx=10)

        # 右側Log區
        frame_right = tk.Frame(self, bg="#ffffff", relief=tk.SUNKEN, borderwidth=2)
        frame_right.pack(side="right", fill="both", expand=True)

        tk.Label(frame_right, text="執行 Log：", bg="#ffffff", font=("微軟正黑體", 11, "bold")).pack(anchor='w', pady=5, padx=10)
        self.text_log = tk.Text(frame_right, wrap='word', font=("Consolas", 10))
        self.text_log.pack(fill='both', expand=True, padx=10, pady=5)
        self.log("🟢 系統已啟動，請載入 sensor.ini")

    def log(self, text):
        self.text_log.insert(tk.END, f"{time.strftime('%H:%M:%S')}  {text}\n")
        self.text_log.see(tk.END)
        self.text_log.update_idletasks()

    def load_sensor_ini(self):
        file_path = filedialog.askopenfilename(title="選擇 sensor_*.ini 檔案", filetypes=[("INI files", "*.ini")])
        if file_path:
            self.sensor_ini = file_path
            self.log(f"✅ 已載入 Sensor 設定檔: {os.path.basename(file_path)}")
        else:
            self.log("⚠️ 尚未選擇設定檔")

    def run_process(self, step):
        thread = threading.Thread(target=self._execute_step, args=(step,))
        thread.start()

    def _execute_step(self, step):
        steps = {
            "GainMap": "開始 GainMap 校正...",
            "DCC": "執行 DCC Map 校正...",
            "Sharpness": "進行 Sharpness 驗證..."
        }
        self.log(f"🚀 {steps[step]}")
        time.sleep(1.5)  # 模擬處理時間

        # 模擬運算結果
        for i in range(3):
            time.sleep(0.8)
            self.log(f"  ➤ 處理中 {'.' * (i+1)}")

        result = "通過" if step != "DCC" else "需調整"
        self.log(f"✅ {step} 校正結果：{result}")

    def run_all(self):
        self.log("⚙️ 一鍵執行自動化校正流程開始...")
        steps = ["GainMap", "DCC", "Sharpness"]
        for s in steps:
            self._execute_step(s)
        self.log("🎉 所有步驟完成，可匯出報告。")

    def export_report(self):
        report_path = filedialog.asksaveasfilename(title="儲存報告", defaultextension=".txt",
                                                  filetypes=[("Text Files", "*.txt")])
        if report_path:
            log_text = self.text_log.get("1.0", tk.END)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(log_text)
            self.log(f"📁 報告已輸出: {os.path.basename(report_path)}")
            messagebox.showinfo("報告輸出", "報告已成功儲存！")

if __name__ == "__main__":
    app = ISP_CalibrationTool()
    app.mainloop()
