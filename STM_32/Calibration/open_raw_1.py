import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
from PIL import Image, ImageTk  # 處理縮圖
import rawpy


class RawParamGui:

    def __init__(self, root):
        self.root = root
        self.root.title("RAW 原始像素提取與預覽工具 (參數已修正版)")
        self.root.geometry("950x550")  # 設定合適的視窗大小

        # 初始化變數
        self.file_path = tk.StringVar()
        self.wb_var = tk.StringVar(value="camera")  # 白平衡預設
        self.half_size_var = tk.BooleanVar(value=False)  # 半亮度預設
        self.output_space_var = tk.StringVar(value="sRGB")  # 色彩空間預設
        self.tk_img = None  # 用於保存圖片記憶體，防止被回收

        self.create_widgets()

    def create_widgets(self):
        # 使用左右分欄佈局
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        # ================= 左側：控制面板 =================
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # 1. 檔案選擇區
        file_frame = ttk.LabelFrame(left_panel, text=" 1. 檔案來源 ", padding=10)
        file_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(
            file_frame, text="瀏覽檔案...", command=self.select_file
        ).pack(side="left", padx=5)
        ttk.Entry(
            file_frame, textvariable=self.file_path, width=35, state="readonly"
        ).pack(side="left", fill="x", expand=True, padx=5)

        # 2. 參數設定區
        param_frame = ttk.LabelFrame(
            left_panel, text=" 2. RAW 讀取與解碼設定 ", padding=10
        )
        param_frame.pack(fill="x", pady=(0, 10))

        # 白平衡
        ttk.Label(param_frame, text="白平衡模式:").grid(
            row=0, column=0, sticky="w", pady=5
        )
        ttk.Radiobutton(
            param_frame, text="相機內定 (Camera)", variable=self.wb_var, value="camera"
        ).grid(row=0, column=1, sticky="w", padx=5)
        ttk.Radiobutton(
            param_frame, text="自動計算 (Auto)", variable=self.wb_var, value="auto"
        ).grid(row=0, column=2, sticky="w", padx=5)

        # 色彩空間
        ttk.Label(param_frame, text="輸出色彩空間:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        space_combo = ttk.Combobox(
            param_frame,
            textvariable=self.output_space_var,
            values=["sRGB", "AdobeRGB", "ProPhoto", "WideGamut"],
            state="readonly",
            width=15,
        )
        space_combo.grid(row=1, column=1, sticky="w", padx=5)

        # 採樣加速
        ttk.Label(param_frame, text="效能優化:").grid(
            row=2, column=0, sticky="w", pady=5
        )
        ttk.Checkbutton(
            param_frame,
            text="使用半亮度降採樣 (解碼快2倍，用於快速預覽)",
            variable=self.half_size_var,
        ).grid(row=2, column=1, columnspan=2, sticky="w", padx=5)

        # 執行按鈕
        ttk.Button(
            left_panel, text="開始解析並生成預覽", command=self.process_raw
        ).pack(fill="x", pady=10)

        # 3. 結果顯示區
        result_frame = ttk.LabelFrame(
            left_panel, text=" 3. 原始 Bayer 像素值 (左上角第一個點) ", padding=10
        )
        result_frame.pack(fill="both", expand=True)

        self.txt_output = tk.Text(result_frame, wrap="word", height=12, width=45)
        self.txt_output.pack(fill="both", expand=True)

        # ================= 右側：即時縮圖預覽區 =================
        right_panel = ttk.LabelFrame(
            main_frame, text=" 即時照片縮圖預覽 ", padding=10, width=380
        )
        # 📌 關鍵修正：將 fill="vertical" 修改為標準的 fill="y"
        right_panel.pack(side="right", fill="y", expand=False)
        right_panel.pack_propagate(False)  # 固定元件寬度為 380

        # 用於顯示圖片的 Label
        self.preview_label = ttk.Label(
            right_panel,
            text="尚未載入影像\n\n請在左側選擇檔案\n並點擊執行按鈕",
            anchor="center",
            justify="center",
        )
        self.preview_label.pack(fill="both", expand=True)

    def select_file(self):
        filetypes = [
            (
                "所有相機 RAW 格式",
                "*.cr2 *.CR2 *.cr3 *.CR3 *.nef *.NEF *.arw *.ARW *.dng *.DNG *.orf *.ORF *.rw2 *.RW2 *.pef *.PEF *.raw *.RAW",
            ),
            ("Canon 影像檔 (*.cr2, *.cr3)", "*.cr2 *.CR2 *.cr3 *.CR3"),
            ("Sony 影像檔 (*.arw)", "*.arw *.ARW"),
            ("Nikon 影像檔 (*.nef)", "*.nef *.NEF"),
            ("通用 Adobe RAW (*.dng)", "*.dng *.DNG"),
            ("所有檔案 (*.*)", "*.*"),
        ]

        path = filedialog.askopenfilename(
            title="選擇相機 RAW 檔案", filetypes=filetypes
        )
        if path:
            self.file_path.set(path)

    def process_raw(self):
        path = self.file_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("錯誤", "請先選擇有效的 RAW 檔案！")
            return

        self.txt_output.delete("1.0", tk.END)
        self.txt_output.insert(tk.END, f"正在讀取檔案: {os.path.basename(path)}...\n")
        self.preview_label.config(text="正在解碼影像，請稍候...", image="")
        self.root.update()

        try:
            with rawpy.imread(path) as raw:
                # 提取原始 Bayer 像素值
                bayer_pattern = raw.raw_image_visible
                color_desc = raw.color_desc.decode("utf-8")

                # 提取四個通道
                ch_R = bayer_pattern[0::2, 0::2]
                ch_GR = bayer_pattern[0::2, 1::2]
                ch_GB = bayer_pattern[1::2, 0::2]
                ch_B = bayer_pattern[1::2, 1::2]

                # 色彩空間對照與 WideGamutRGB 修正
                space_map = {
                    "sRGB": rawpy.ColorSpace.sRGB,
                    "AdobeRGB": rawpy.ColorSpace.Adobe,
                    "ProPhoto": rawpy.ColorSpace.ProPhoto,
                    "WideGamut": rawpy.ColorSpace.WideGamutRGB,
                }
                out_space = space_map.get(self.output_space_var.get())

                # 使用使用者設定進行解碼
                rgb_image = raw.postprocess(
                    use_camera_wb=self.wb_var.get() == "camera",
                    half_size=self.half_size_var.get(),
                    output_color=out_space,
                )

                # 生成預覽縮圖
                img = Image.fromarray(rgb_image)
                img.thumbnail((350, 450))
                self.tk_img = ImageTk.PhotoImage(img)

                # 更新介面預覽圖
                self.preview_label.config(text="", image=self.tk_img)

                # 更新左側純文字結果 (📌 同步修正了參數倒置的 Bug)
                self.txt_output.insert(tk.END, "【讀取成功】\n")
                self.txt_output.insert(tk.END, f"影像原始解析度: {bayer_pattern.shape}\n")
                self.txt_output.insert(tk.END, f"Bayer 陣列描述: {color_desc}\n\n")
                self.txt_output.insert(
                    tk.END, "--- 提取物理通道數值 (左上角第[0,0]點) ---\n"
                )
                self.txt_output.insert(
                    tk.END, f"紅色通道 (R)   數值: {ch_R[0, 0]}\n"
                )
                self.txt_output.insert(
                    tk.END, f"綠色通道 (GR)  數值: {ch_GR[0, 0]}\n"
                )
                self.txt_output.insert(
                    tk.END, f"綠色通道 (GB)  數值: {ch_GB[0, 0]}\n"
                )
                self.txt_output.insert(
                    tk.END, f"藍色通道 (B)   數值: {ch_B[0, 0]}\n\n"
                )
                self.txt_output.insert(tk.END, "--- 啟用之解碼設定 ---\n")
                self.txt_output.insert(
                    tk.END, f"- 色彩空間: {self.output_space_var.get()}\n"
                )

        except Exception as e:
            self.preview_label.config(text="影像載入失敗", image="")
            messagebox.showerror(
                "錯誤", f"無法解析此 RAW 檔案。\n\n錯誤原因:\n{str(e)}"
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = RawParamGui(root)
    root.mainloop()
