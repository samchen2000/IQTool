import os
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageTk


class AdvancedRawTool:

    def __init__(self, root):
        self.root = root
        self.root.title("工業級 RAW (3264x2448 BGGR 16bit) 進階分析工具")
        self.root.geometry("1150x700")

        # 固定影像規格
        self.WIDTH = 3264
        self.HEIGHT = 2448
        self.EXPECTED_SIZE = self.WIDTH * self.HEIGHT * 2

        # 核心數據變數
        self.file_path = tk.StringVar()
        self.bayer_matrix = None  # 儲存原始 16bit 矩陣
        self.normalized_base_img = None  # 儲存基準 8bit RGB 影像
        self.tk_img = None  # 防止圖片記憶體被回收

        # 統計數據儲存
        self.stats_data = {}

        self.create_widgets()

    def create_widgets(self):
        # 左右主要分欄
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        # ================= 左側：控制與數值面板 =================
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # 1. 檔案選擇
        file_frame = ttk.LabelFrame(left_panel, text=" 1. 選擇 RAW 檔案 ", padding=10)
        file_frame.pack(fill="x", pady=(0, 5))

        ttk.Button(
            file_frame, text="瀏覽檔案...", command=self.select_file
        ).pack(side="left", padx=5)
        ttk.Entry(
            file_frame, textvariable=self.file_path, state="readonly"
        ).pack(side="left", fill="x", expand=True, padx=5)

        # 執行按鈕
        ttk.Button(
            left_panel, text="載入檔案並分析解碼", command=self.process_raw_data
        ).pack(fill="x", pady=5)

        # 2. 數據匯出功能區
        export_frame = ttk.LabelFrame(left_panel, text=" 2. 數據匯出功能 ", padding=10)
        export_frame.pack(fill="x", pady=(0, 5))

        ttk.Button(
            export_frame, text="匯出統計資料報告 (CSV)", command=self.export_stats
        ).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(
            export_frame, text="匯出 4 通道像素矩陣 (CSV.zip)", command=self.export_matrices
        ).pack(side="left", fill="x", expand=True, padx=5)

        # 3. 統計與數值輸出文字框
        result_frame = ttk.LabelFrame(left_panel, text=" 3. 分析報告與統計資料 ", padding=10)
        result_frame.pack(fill="both", expand=True)

        self.txt_output = tk.Text(result_frame, wrap="word", height=20, width=50)
        self.txt_output.pack(fill="both", expand=True)

        # ================= 右側：影像預覽與調整面板 =================
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side="right", fill="both", expand=False)
        right_panel.pack_propagate(False)  # 關鍵：固定 Frame 大小，防止被內部元件撐開

        # 影像框架
        img_frame = ttk.LabelFrame(right_panel, text=" 影像即時預覽 (彩色還原) ", padding=10)
        img_frame.pack(fill="x", pady=(0, 5))

        self.preview_label = ttk.Label(
            img_frame,
            text="尚未載入影像\n\n請在左側選擇檔案並點擊「載入檔案並分析解碼」",
            anchor="center",
            justify="center",
        )
        self.preview_label.pack(fill="both", expand=True)

        # 4. 控制面板：調整 R, G, B 與亮度
        ctrl_frame = ttk.LabelFrame(right_panel, text=" 4. 影像即時調整面板 (8-bit 預覽優化) ", padding=10)
        ctrl_frame.pack(fill="x", side="bottom")

        # 滑桿定義 - R Gain
        ttk.Label(ctrl_frame, text="紅光增益 (R Gain):").grid(row=0, column=0, sticky="w", pady=2)
        self.slider_R = ttk.Scale(ctrl_frame, from_=0.5, to=3.0, value=1.0, orient="horizontal")
        self.slider_R.grid(row=0, column=1, sticky="ew", padx=5)

        # 滑桿定義 - G Gain
        ttk.Label(ctrl_frame, text="綠光增益 (G Gain):").grid(row=1, column=0, sticky="w", pady=2)
        self.slider_G = ttk.Scale(ctrl_frame, from_=0.5, to=3.0, value=1.0, orient="horizontal")
        self.slider_G.grid(row=1, column=1, sticky="ew", padx=5)

        # 滑桿定義 - B Gain
        ttk.Label(ctrl_frame, text="藍光增益 (B Gain):").grid(row=2, column=0, sticky="w", pady=2)
        self.slider_B = ttk.Scale(ctrl_frame, from_=0.5, to=3.0, value=1.0, orient="horizontal")
        self.slider_B.grid(row=2, column=1, sticky="ew", padx=5)

        # 滑桿定義 - 亮度 Offset
        ttk.Label(ctrl_frame, text="整體亮度調校:").grid(row=3, column=0, sticky="w", pady=2)
        self.slider_bright = ttk.Scale(ctrl_frame, from_=-100, to=100, value=0, orient="horizontal")
        self.slider_bright.grid(row=3, column=1, sticky="ew", padx=5)

        ctrl_frame.columnconfigure(1, weight=1)

        # 應用調整按鈕
        ttk.Button(ctrl_frame, text=" 重新渲染影像參數 ", command=self.apply_image_adjustments).grid(
            row=4, column=0, columnspan=2, pady=(8, 0), sticky="ew"
        )

    def select_file(self):
        filetypes = [
            ("純 RAW 數據檔案 (*.raw, *.bin)", "*.raw *.bin *.RAW *.BIN"),
            ("所有檔案 (*.*)", "*.*"),
        ]
        path = filedialog.askopenfilename(title="選擇 3264x2448 16bit RAW 檔案", filetypes=filetypes)
        if path:
            self.file_path.set(path)

    def process_raw_data(self):
        path = self.file_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("錯誤", "請先選取有效的 RAW 檔案！")
            return

        self.txt_output.delete("1.0", tk.END)
        self.preview_label.config(text="正在分析計算各通道統計指標，請稍候...", image="")
        self.root.update()

        try:
            # 1. 驗證檔案大小
            actual_size = os.path.getsize(path)
            if actual_size != self.EXPECTED_SIZE:
                raise ValueError(f"檔案大小不符！\n實際：{actual_size:,} Bytes\n預期：{self.EXPECTED_SIZE:,} Bytes")

            # 2. 讀取並重塑
            raw_data = np.fromfile(path, dtype=np.uint16)
            self.bayer_matrix = raw_data.reshape((self.HEIGHT, self.WIDTH))

            # 3. 提取 4 通道資料
            channels = {
                "B": self.bayer_matrix[0::2, 0::2],
                "GR": self.bayer_matrix[0::2, 1::2],
                "GB": self.bayer_matrix[1::2, 0::2],
                "R": self.bayer_matrix[1::2, 1::2],
            }

            # 4. 計算統計資訊 (含 SNR)
            self.stats_data = {}
            for name, data in channels.items():
                mean_val = float(np.mean(data))
                std_val = float(np.std(data))
                # 避免標準差為 0 導致 log 錯誤
                snr_val = 20 * np.log10(mean_val / std_val) if std_val > 0 else 0.0

                self.stats_data[name] = {
                    "Mean (平均值)": round(mean_val, 2),
                    "Std Dev (標準差)": round(std_val, 2),
                    "SNR (訊噪比 dB)": round(snr_val, 2),
                    "Max (最大值)": int(np.max(data)),
                    "Min (最小值)": int(np.min(data)),
                }

            # 5. 生成色彩還原基準彩色圖 (Demosaic & Auto-Gain)
            rgb_image = cv2.cvtColor(self.bayer_matrix, cv2.COLOR_BayerBG2RGB)
            img_min, img_max = rgb_image.min(), rgb_image.max()

            if img_max > img_min:
                self.normalized_base_img = ((rgb_image - img_min) / (img_max - img_min) * 255).astype(np.uint8)
            else:
                self.normalized_base_img = (rgb_image // 256).astype(np.uint8)

            # 6. 重設調整滑桿並渲染
            self.slider_R.set(1.0)
            self.slider_G.set(1.0)
            self.slider_B.set(1.0)
            self.slider_bright.set(0)
            self.apply_image_adjustments()

            # 7. 印出文字報告
            self.print_report_to_gui()

        except Exception as e:
            self.preview_label.config(text="數據載入失敗", image="")
            messagebox.showerror("解析錯誤", str(e))

    def print_report_to_gui(self):
        self.txt_output.insert(tk.END, "====== 📊 RAW 統計資料報告 ======\n\n")
        for ch_name, metrics in self.stats_data.items():
            self.txt_output.insert(tk.END, f"【通道 {ch_name}】\n")
            for k, v in metrics.items():
                self.txt_output.insert(tk.END, f"    {k}: {v}\n")
            self.txt_output.insert(tk.END, "\n")

        self.txt_output.insert(tk.END, "====== 🔍 物理左上角像素矩陣 (2x2) ======\n")
        self.txt_output.insert(tk.END, f" B  (0,0): {self.bayer_matrix[0, 0]}   | GR (0,1): {self.bayer_matrix[0, 1]}\n")
        self.txt_output.insert(tk.END, f" GB (1,0): {self.bayer_matrix[1, 0]}   | R  (1,1): {self.bayer_matrix[1, 1]}\n")

    def apply_image_adjustments(self):
        """根據滑桿設定即時變更 R, G, B 增益與亮度"""
        if self.normalized_base_img is None:
            return

        # 獲取滑桿數值
        r_gain = self.slider_R.get()
        g_gain = self.slider_G.get()
        b_gain = self.slider_B.get()
        brightness = self.slider_bright.get()

        # 分離 8bit 通道
        r_ch, g_ch, b_ch = cv2.split(self.normalized_base_img)

        # 調整各通道增益與整體亮度偏移量 (使用 np.clip 防止 8bit 溢位超過 255 或低於 0)
        r_adjusted = np.clip(r_ch * r_gain + brightness, 0, 255).astype(np.uint8)
        g_adjusted = np.clip(g_ch * g_gain + brightness, 0, 255).astype(np.uint8)
        b_adjusted = np.clip(b_ch * b_gain + brightness, 0, 255).astype(np.uint8)

        # 合併回彩色影像
        adjusted_img = cv2.merge([r_adjusted, g_adjusted, b_adjusted])

        # 轉換為 Tkinter 縮圖元件
        img = Image.fromarray(adjusted_img)
        img.thumbnail((500, 480))
        self.tk_img = ImageTk.PhotoImage(img)

        # 更新畫布
        self.preview_label.config(text="", image=self.tk_img)

    def export_stats(self):
        """匯出通道統計資料為 CSV"""
        if not self.stats_data:
            messagebox.showwarning("警告", "請先載入並分析 RAW 檔案。")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV 檔案", "*.csv")], title="儲存統計報告"
        )
        if save_path:
            try:
                df = pd.DataFrame(self.stats_data).T
                df.index.name = "Channel"
                df.to_csv(save_path, encoding="utf-8-sig")
                messagebox.showinfo("成功", "統計報告已順利匯出！")
            except Exception as e:
                messagebox.showerror("匯出失敗", str(e))

    def export_matrices(self):
        """因為 3264x2448 的二維矩陣極大，單個 Excel 會超出欄位極限且執行極慢，

        在此採用將 4 個通道分別導出為獨立 CSV 檔案，並自動打包壓縮成一個 ZIP 檔方案。
        """
        if self.bayer_matrix is None:
            messagebox.showwarning("警告", "請先載入並分析 RAW 檔案。")
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".zip", filetypes=[("ZIP 壓縮檔", "*.zip")], title="儲存像素二維矩陣壓縮檔"
        )
        if save_path:
            self.txt_output.insert(tk.END, "\n正在導出龐大的像素矩陣，請勿關閉程式...\n")
            self.root.update()
            try:
                # 建立四個通道的二維矩陣
                channels = {
                    "Matrix_B.csv": self.bayer_matrix[0::2, 0::2],
                    "Matrix_GR.csv": self.bayer_matrix[0::2, 1::2],
                    "Matrix_GB.csv": self.bayer_matrix[1::2, 0::2],
                    "Matrix_R.csv": self.bayer_matrix[1::2, 1::2],
                }
                # 寫入壓縮檔中，避免在硬碟產生大量零散大檔案
                with zipfile.ZipFile(save_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for filename, matrix_data in channels.items():
                        # 使用 pandas 快速轉換為不帶行列索引的純數值矩陣
                        df = pd.DataFrame(matrix_data)
                        csv_string = df.to_csv(header=False, index=False)
                        zipf.writestr(filename, csv_string)

                self.txt_output.insert(tk.END, "【矩陣匯出成功】\n")
                messagebox.showinfo("成功", "四通道的完整 2D 像素矩陣已壓縮匯出成功！")
            except Exception as e:
                messagebox.showerror("匯出失敗", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedRawTool(root)
    root.mainloop()