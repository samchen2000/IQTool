import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2  # 用於高效的 Bayer Demosaic 轉換
import numpy as np
from PIL import Image, ImageTk


class PureRawGui:

    def __init__(self, root):
        self.root = root
        self.root.title("工業級純 RAW (RGGB 16bit) 解析與預覽工具")
        self.root.geometry("1000x600")

        # 固定影像參數
        self.WIDTH = 3264
        self.HEIGHT = 2448
        self.EXPECTED_SIZE = self.WIDTH * self.HEIGHT * 2  # 15,980,544 Bytes

        # 介面控制變數
        self.file_path = tk.StringVar()
        self.tk_img = None  # 防止圖片被回收
        self.normalized_base_img = None # 儲存基準 8bit RGB 影像
        self.bayer_matrix = None # 儲存原始 16bit Bayer 矩陣

        # 滑桿數值顯示變數
        self.slider_R_val_var = tk.StringVar(value="1.00")
        self.slider_G_val_var = tk.StringVar(value="1.00")
        self.slider_B_val_var = tk.StringVar(value="1.00")
        self.slider_bright_val_var = tk.StringVar(value="0")
        self.avg_r_var = tk.StringVar(value="--")
        self.avg_g_var = tk.StringVar(value="--")
        self.avg_b_var = tk.StringVar(value="--")

        # 點擊座標相關
        self.adjusted_img_full = None # 儲存調整後的全尺寸影像
        self.thumbnail_size = (0, 0) # 儲存縮圖的實際尺寸

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
            ("色彩排列 (Pattern):", "RGGB (Bayer)"),
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
        self.preview_label.bind("<Button-1>", self.on_image_click)
        
         # 4. 控制面板：調整 R, G, B 與亮度
        ctrl_frame = ttk.LabelFrame(right_panel, text=" 4. 影像即時調整面板 (8-bit 預覽優化) ", padding=10)
        ctrl_frame.pack(fill="x", side="bottom", pady=(5,0))
        
        # 滑桿定義 - R Gain
        ttk.Label(ctrl_frame, text="紅光增益 (R Gain):").grid(row=0, column=0, sticky="w", pady=2)
        self.slider_R = ttk.Scale(ctrl_frame, from_=0.5, to=3.0, value=1.0, orient="horizontal", command=self.apply_image_adjustments)
        self.slider_R.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Label(ctrl_frame, textvariable=self.slider_R_val_var, width=5).grid(row=0, column=2)
        
        # 滑桿定義 - G Gain
        ttk.Label(ctrl_frame, text="綠光增益 (G Gain):").grid(row=1, column=0, sticky="w", pady=2)
        self.slider_G = ttk.Scale(ctrl_frame, from_=0.5, to=3.0, value=1.0, orient="horizontal", command=self.apply_image_adjustments)
        self.slider_G.grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Label(ctrl_frame, textvariable=self.slider_G_val_var, width=5).grid(row=1, column=2)
        
        # 滑桿定義 - B Gain
        ttk.Label(ctrl_frame, text="藍光增益 (B Gain):").grid(row=2, column=0, sticky="w", pady=2)
        self.slider_B = ttk.Scale(ctrl_frame, from_=0.5, to=3.0, value=1.0, orient="horizontal", command=self.apply_image_adjustments)
        self.slider_B.grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Label(ctrl_frame, textvariable=self.slider_B_val_var, width=5).grid(row=2, column=2)
        
        # 滑桿定義 - 亮度 Offset
        ttk.Label(ctrl_frame, text="整體亮度調校:").grid(row=3, column=0, sticky="w", pady=2)
        self.slider_bright = ttk.Scale(ctrl_frame, from_=-100, to=100, value=0, orient="horizontal", command=self.apply_image_adjustments)
        self.slider_bright.grid(row=3, column=1, sticky="ew", padx=5)
        ttk.Label(ctrl_frame, textvariable=self.slider_bright_val_var, width=5).grid(row=3, column=2)
        
        ctrl_frame.columnconfigure(1, weight=1)
        self.preview_label.pack(fill="both", expand=True)

        # 5. 即時影像數據分析
        analysis_frame = ttk.LabelFrame(right_panel, text=" 5. 即時影像數據分析 ", padding=10)
        analysis_frame.pack(fill="x", side="bottom")

        ttk.Label(analysis_frame, text="平均 R:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(analysis_frame, textvariable=self.avg_r_var, width=8).grid(row=0, column=1, sticky="w")
        ttk.Label(analysis_frame, text="平均 G:").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Label(analysis_frame, textvariable=self.avg_g_var, width=8).grid(row=0, column=3, sticky="w")
        ttk.Label(analysis_frame, text="平均 B:").grid(row=0, column=4, sticky="w", padx=5)
        ttk.Label(analysis_frame, textvariable=self.avg_b_var, width=8).grid(row=0, column=5, sticky="w")
        analysis_frame.columnconfigure(1, weight=1)
        analysis_frame.columnconfigure(3, weight=1)
        analysis_frame.columnconfigure(5, weight=1)

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
    def apply_image_adjustments(self, _=None):
        """根據滑桿設定即時變更 R, G, B 增益與亮度"""
        if self.normalized_base_img is None:
            return
    
        # 獲取滑桿數值
        r_gain = self.slider_R.get()
        g_gain = self.slider_G.get()
        b_gain = self.slider_B.get()
        brightness = self.slider_bright.get()

        # 更新滑桿數值標籤
        self.slider_R_val_var.set(f"{r_gain:.2f}")
        self.slider_G_val_var.set(f"{g_gain:.2f}")
        self.slider_B_val_var.set(f"{b_gain:.2f}")
        self.slider_bright_val_var.set(f"{int(brightness)}")
    
        # 分離 8bit 通道
        r_ch, g_ch, b_ch = cv2.split(self.normalized_base_img)
    
        # 調整各通道增益與整體亮度偏移量 (使用 np.clip 防止 8bit 溢位超過 255 或低於 0)
        r_adjusted = np.clip(r_ch * r_gain + brightness, 0, 255).astype(np.uint8)
        g_adjusted = np.clip(g_ch * g_gain + brightness, 0, 255).astype(np.uint8)
        b_adjusted = np.clip(b_ch * b_gain + brightness, 0, 255).astype(np.uint8)
    
        # 合併回彩色影像
        adjusted_img = cv2.merge([r_adjusted, g_adjusted, b_adjusted])
        self.adjusted_img_full = adjusted_img.copy() # 儲存全尺寸影像供點擊查詢

        # 計算並更新整體影像的平均 RGB
        self.avg_r_var.set(f"{np.mean(self.adjusted_img_full[:, :, 2]):.2f}") # OpenCV is BGR
        self.avg_g_var.set(f"{np.mean(self.adjusted_img_full[:, :, 1]):.2f}")
        self.avg_b_var.set(f"{np.mean(self.adjusted_img_full[:, :, 0]):.2f}")
    
        # 轉換為 Tkinter 縮圖元件
        img = Image.fromarray(adjusted_img)
        img.thumbnail((500, 480))
        self.tk_img = ImageTk.PhotoImage(img)
    
        # 更新畫布
        self.thumbnail_size = (self.tk_img.width(), self.tk_img.height())
        self.preview_label.config(text="", image=self.tk_img)
        
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
            self.bayer_matrix = raw_data.reshape((self.HEIGHT, self.WIDTH))

            # 3. 提取 RGGB 四通道物理數值 (2x2 切片)
            # [ R  GR ]
            # [ GB  B ]
            ch_R = self.bayer_matrix[0::2, 0::2]    # 偶數行, 偶數列
            ch_GR = self.bayer_matrix[0::2, 1::2]   # 偶數行, 奇數列
            ch_GB = self.bayer_matrix[1::2, 0::2]   # 奇數行, 偶數列
            ch_B = self.bayer_matrix[1::2, 1::2]    # 奇數行, 奇數列

            # 4. 色彩還原 (Demosaic): 將 BGGR 轉為標準 RGB 影像
            # 由於 OpenCV 的 Bayer 格式定義是以左上角兩個像素決定，這裡使用 COLOR_BayerRG2RGB
            rgb_image = cv2.cvtColor(self.bayer_matrix, cv2.COLOR_BayerRG2RGB)

            # 5. 影像亮度優化 (Auto-Gain)
            # 16-bit 數據直接轉 8-bit 通常會極暗（因為通常數據只佔用了 10-14 bits 空間）
            # 我們將數據做直方圖拉伸，使其在螢幕上可視
            img_min = rgb_image.min()
            img_max = rgb_image.max()
            if img_max > img_min:
                # 將正規化後的 8-bit 影像存為基準影像
                self.normalized_base_img = (
                    (rgb_image - img_min) / (img_max - img_min) * 255
                ).astype(np.uint8)
            else:
                self.normalized_base_img = (rgb_image // 256).astype(np.uint8)

            # 6. 重設滑桿數值並觸發第一次影像渲染
            self.slider_R.set(1.0)
            self.slider_G.set(1.0)
            self.slider_B.set(1.0)
            self.slider_bright.set(0)
            self.apply_image_adjustments()

            self.txt_output.insert(tk.END, "【RAW 檔案讀取成功】\n\n")
            # 7. 更新介面顯示
            self.txt_output.insert(
                tk.END,
                f"影像物理最大值: {img_max}\n影像物理最小值: {img_min}\n\n",
            )
            self.txt_output.insert(
                tk.END, "--- 提取物理通道數值 (座標 0,0 處) ---\n"
            )
            self.txt_output.insert(tk.END, f"紅色通道 (R)  數值: {ch_R[0, 0]}\n")
            self.txt_output.insert(tk.END, f"綠色通道 (GR) 數值: {ch_GR[0, 0]}\n")
            self.txt_output.insert(tk.END, f"綠色通道 (GB) 數值: {ch_GB[0, 0]}\n")
            self.txt_output.insert(tk.END, f"藍色通道 (B)  數值: {ch_B[0, 0]}\n")

        except Exception as e:
            self.preview_label.config(text="影像載入失敗", image="")
            messagebox.showerror("解析錯誤", str(e))

    def on_image_click(self, event):
        """處理預覽圖上的滑鼠點擊事件"""
        if self.bayer_matrix is None or self.adjusted_img_full is None:
            return

        # 1. 計算圖片在 Label 中的偏移量 (因為圖片是置中的)
        label_w = self.preview_label.winfo_width()
        label_h = self.preview_label.winfo_height()
        thumb_w, thumb_h = self.thumbnail_size

        offset_x = (label_w - thumb_w) // 2
        offset_y = (label_h - thumb_h) // 2

        # 2. 獲取在縮圖上的實際點擊座標
        click_x = event.x - offset_x
        click_y = event.y - offset_y

        # 3. 邊界檢查，確保點擊在圖片範圍內
        if not (0 <= click_x < thumb_w and 0 <= click_y < thumb_h):
            return

        # 4. 將縮圖座標轉換回原始影像座標
        orig_x = int(click_x * (self.WIDTH / thumb_w))
        orig_y = int(click_y * (self.HEIGHT / thumb_h))

        # 5. 獲取像素值
        # 原始 16-bit Bayer 值
        raw_val = self.bayer_matrix[orig_y, orig_x]
        # 調整後 8-bit RGB 值 (注意 OpenCV 順序是 BGR)
        b, g, r = self.adjusted_img_full[orig_y, orig_x]

        # 6. 在文字區顯示結果
        info = f"\n--- 點擊座標資訊 ---\n" \
               f"原始座標 (X, Y): ({orig_x}, {orig_y})\n" \
               f"預覽圖 RGB (8-bit): ({r}, {g}, {b})\n" \
               f"原始 Bayer 值 (16-bit): {raw_val}\n"
        self.txt_output.insert(tk.END, info)
        self.txt_output.see(tk.END) # 自動捲動到最下方

if __name__ == "__main__":
    root = tk.Tk()
    app = PureRawGui(root)
    root.mainloop()
