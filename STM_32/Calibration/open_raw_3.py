import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2  # 用於高效的 Bayer Demosaic 轉換
import numpy as np
from PIL import Image, ImageTk


class PureRawGui:

    def __init__(self, root):
        self.root = root
        self.root.title("工業級純 RAW (BGGR 16bit) 解析與預覽工具")
        self.root.geometry("1000x600")

        # 固定影像參數
        self.WIDTH = 3264
        self.HEIGHT = 2448
        self.EXPECTED_SIZE = self.WIDTH * self.HEIGHT * 2  # 15,980,544 Bytes

        # 介面控制變數
        self.file_path = tk.StringVar()
        self.tk_img = None  # 防止圖片被回收

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
        file_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(
            file_frame, text="瀏覽檔案...", command=self.select_file
        ).pack(side="left", padx=5)
        ttk.Entry(
            file_frame, textvariable=self.file_path, state="readonly"
        ).pack(side="left", fill="x", expand=True, padx=5)

        # 2. 檔案格式資訊展示 (固定規格)
        info_frame = ttk.LabelFrame(
            left_panel, text=" 2. 目標影像規格 ", padding=10
        )
        info_frame.pack(fill="x", pady=(0, 10))

        specs = [
            ("解析度 (Resolution):", f"{self.WIDTH} x {self.HEIGHT}"),
            ("色彩排列 (Pattern):", "BGGR (Bayer)"),
            ("資料深度 (Bit Depth):", "16-bit (uint16)"),
            ("預期大小 (Expected):", f"{self.EXPECTED_SIZE:,} Bytes"),
        ]
        for idx, (label, val) in enumerate(specs):
            ttk.Label(info_frame, text=label, font=("Arial", 9, "bold")).grid(
                row=idx, column=0, sticky="w", pady=2, padx=5
            )
            ttk.Label(info_frame, text=val).grid(
                row=idx, column=1, sticky="w", pady=2, padx=5
            )

        # 執行按鈕
        ttk.Button(
            left_panel, text="載入檔案並解碼顯示", command=self.process_pure_raw
        ).pack(fill="x", pady=10)

        # 3. 數值輸出區
        result_frame = ttk.LabelFrame(
            left_panel, text=" 3. 物理通道數據提取 (左上角 2x2) ", padding=10
        )
        result_frame.pack(fill="both", expand=True)

        self.txt_output = tk.Text(result_frame, wrap="word", height=12, width=45)
        self.txt_output.pack(fill="both", expand=True)

        # ================= 右側：影像顯示區 =================
        right_panel = ttk.LabelFrame(
            main_frame, text=" 影像即時預覽 (彩色還原) ", padding=10, width=500
        )
        right_panel.pack(side="right", fill="both", expand=False)
        right_panel.pack_propagate(False)

        self.preview_label = ttk.Label(
            right_panel,
            text="尚未載入影像\n\n請選擇 3264x2448 的 RAW 檔\n並點擊解碼按鈕",
            anchor="center",
            justify="center",
        )
        self.preview_label.pack(fill="both", expand=True)

    def select_file(self):
        filetypes = [
            ("純 RAW 數據檔案 (*.raw, *.bin)", "*.raw *.bin *.RAW *.BIN"),
            ("所有檔案 (*.*)", "*.*"),
        ]
        path = filedialog.askopenfilename(
            title="選擇 3264x2448 16bit RAW 檔案", filetypes=filetypes
        )
        if path:
            self.file_path.set(path)

    def process_pure_raw(self):
        path = self.file_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("錯誤", "請先選取有效的 RAW 檔案！")
            return

        self.txt_output.delete("1.0", tk.END)
        self.preview_label.config(text="正在進行 Bayer 色彩還原，請稍候...", image="")
        self.root.update()

        try:
            # 1. 驗證檔案大小
            actual_size = os.path.getsize(path)
            if actual_size != self.EXPECTED_SIZE:
                raise ValueError(
                    f"檔案大小不符！\n實際：{actual_size:,} Bytes\n預期：{self.EXPECTED_SIZE:,} Bytes"
                )

            # 2. 讀取二進位資料並重塑矩陣
            raw_data = np.fromfile(path, dtype=np.uint16)
            bayer_matrix = raw_data.reshape((self.HEIGHT, self.WIDTH))

            # 3. 提取 BGGR 四通道物理數值 (2x2 切片)
            ch_B = bayer_matrix[0::2, 0::2]
            ch_GR = bayer_pattern_0_1 = bayer_matrix[0::2, 1::2]
            ch_GB = bayer_pattern_1_0 = bayer_matrix[1::2, 0::2]
            ch_R = bayer_matrix[1::2, 1::2]

            # 4. 色彩還原 (Demosaic): 將 BGGR 轉為標準 RGB 影像
            # 由於 OpenCV 的 Bayer 格式定義是以左上角兩個像素決定，這裡使用 COLOR_BayerBG2RGB
            rgb_image = cv2.cvtColor(bayer_matrix, cv2.COLOR_BayerBG2RGB)

            # 5. 影像亮度優化 (Auto-Gain)
            # 16-bit 數據直接轉 8-bit 通常會極暗（因為通常數據只佔用了 10-14 bits 空間）
            # 我們將數據做直方圖拉伸，使其在螢幕上可視
            img_min = rgb_image.min()
            img_max = rgb_image.max()
            if img_max > img_min:
                # 正規化到 0-255 範圍
                normalized_img = (
                    (rgb_image - img_min) / (img_max - img_min) * 255
                ).astype(np.uint8)
            else:
                normalized_img = (rgb_image // 256).astype(np.uint8)

            # 6. 生成 Tkinter 縮圖
            img = Image.fromarray(normalized_img)
            img.thumbnail((480, 520))  # 縮放至適合預覽視窗的大小
            self.tk_img = ImageTk.PhotoImage(img)

            # 7. 更新介面顯示
            self.preview_label.config(text="", image=self.tk_img)

            self.txt_output.insert(tk.END, "【RAW 檔案讀取成功】\n\n")
            self.txt_output.insert(
                tk.END,
                f"影像物理最大值: {img_max}\n影像物理最小值: {img_min}\n\n",
            )
            self.txt_output.insert(
                tk.END, "--- 提取物理通道數值 (座標 0,0 處) ---\n"
            )
            self.txt_output.insert(tk.END, f"藍色通道 (B)  數值: {ch_B}\n")
            self.txt_output.insert(tk.END, f"綠色通道 (GR) 數值: {ch_GR}\n")
            self.txt_output.insert(tk.END, f"綠色通道 (GB) 數值: {ch_GB}\n")
            self.txt_output.insert(tk.END, f"紅色通道 (R)  數值: {ch_R}\n")

        except Exception as e:
            self.preview_label.config(text="影像載入失敗", image="")
            messagebox.showerror("解析錯誤", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = PureRawGui(root)
    root.mainloop()
