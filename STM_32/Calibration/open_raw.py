import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
from PIL import Image, ImageTk  # 引入 Pillow 處理縮圖
import rawpy


class RawParamGui:

    def __init__(self, root):
        self.root = root
        self.root.title("RAW 原始像素數值提取器")
        self.root.geometry("550x500")

        # 初始化變數
        self.file_path = tk.StringVar()
        self.wb_var = tk.StringVar(value="camera")  # 白平衡預設
        self.half_size_var = tk.BooleanVar(value=False)  # 半亮度預設
        self.output_space_var = tk.StringVar(value="sRGB")  # 色彩空間預設

        self.create_widgets()

    def create_widgets(self):
        # --- 檔案選擇區 ---
        file_frame = ttk.LabelFrame(self.root, text=" 1. 檔案來源 ", padding=10)
        file_frame.pack(fill="x", padx=15, pady=10)

        ttk.Button(file_frame, text="瀏覽檔案...", command=self.select_file).pack(
            side="left", padx=5
        )
        ttk.Entry(
            file_frame, textvariable=self.file_path, width=45, state="readonly"
        ).pack(side="left", padx=5)

        # --- 參數設定區 ---
        param_frame = ttk.LabelFrame(self.root, text=" 2. RAW 讀取與解碼設定 ", padding=10)
        param_frame.pack(fill="x", padx=15, pady=10)

        # 設定選項 A: 白平衡 (White Balance)
        ttk.Label(param_frame, text="白平衡模式:").grid(
            row=0, column=0, sticky="w", pady=5
        )
        ttk.Radiobutton(
            param_frame, text="相機內定 (Camera)", variable=self.wb_var, value="camera"
        ).grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(
            param_frame, text="自動計算 (Auto)", variable=self.wb_var, value="auto"
        ).grid(row=0, column=2, sticky="w")

        # 設定選項 B: 色彩空間 (Color Space)
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
        space_combo.grid(row=1, column=1, sticky="w")

        # 設定選項 C: 採樣加速 (Half Size)
        ttk.Label(param_frame, text="效能優化:").grid(
            row=2, column=0, sticky="w", pady=5
        )
        ttk.Checkbutton(
            param_frame,
            text="使用半亮度降採樣 (解碼速度快2倍，用於快速預覽)",
            variable=self.half_size_var,
        ).grid(row=2, column=1, columnspan=2, sticky="w")

        # --- 執行按鈕 ---
        ttk.Button(
            self.root, text="開始解析並提取像素值", command=self.process_raw
        ).pack(pady=15)

        # --- 結果顯示區 ---
        result_frame = ttk.LabelFrame(self.root, text=" 3. 解析結果 (左上角 2x2 區塊) ", padding=10)
        result_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.txt_output = tk.Text(result_frame, wrap="word", height=12)
        self.txt_output.pack(fill="both", expand=True)

    def select_file(self):
        # 限制只能選擇常見的 RAW 格式
        filetypes = (
            (
                "RAW 影像檔案",
                "*.CR2 *.CR3 *.NEF *.ARW *.DNG *.ORF *.RW2 *.PEF *.raw *.RAW",
            ),
            ("所有檔案", "*.*"),
        )
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
        self.root.update()

        try:
            with rawpy.imread(path) as raw:
                # 提取原始 2D Bayer 矩陣（未經過白平衡與色彩變換）
                bayer_pattern = raw.raw_image_visible
                color_desc = raw.color_desc.decode("utf-8")

                # 根據常見的 RGGB 排列進行 2x2 切片提取
                ch_R = bayer_pattern[0::2, 0::2]
                ch_GR = bayer_pattern[0::2, 1::2]
                ch_GB = bayer_pattern[1::2, 0::2]
                ch_B = bayer_pattern[1::2, 1::2]

                # 讀取使用者在 GUI 設定的解碼參數
                use_camera_wb = self.wb_var.get() == "camera"
                use_auto_wb = self.wb_var.get() == "auto"
                half_size = self.half_size_var.get()

                space_map = {
                    "sRGB": rawpy.ColorSpace.sRGB,
                    "AdobeRGB": rawpy.ColorSpace.Adobe,
                    "ProPhoto": rawpy.ColorSpace.ProPhoto,
                    #"WideGamut": rawpy.ColorSpace.WideGamut,
                    "WideGamut": rawpy.ColorSpace.WideGamutRGB, # 修正項
                }
                out_space = space_map.get(self.output_space_var.get())

                # 模擬完整解碼（若後續需要轉成標準 RGB 圖片顯示可用）
                # rgb_image = raw.postprocess(use_camera_wb=use_camera_wb, use_auto_wb=use_auto_wb, half_size=half_size, output_color=out_space)
                
                # 將原始矩陣渲染成標準 RGB 陣列
                rgb_image = raw.postprocess(
                    use_camera_wb=self.wb_var.get() == "camera",
                    half_size=self.half_size_var.get(),
                    output_color=out_space,
                )
                # 2. 生成縮圖並顯示在 Tkinter 視窗上
                img = Image.fromarray(rgb_image)
                img.thumbnail((350, 450)) # 限制大小
                self.tk_img = ImageTk.PhotoImage(img) # 綁定影像
                self.preview_label.config(text="", image=self.tk_img)
        except Exception as e:
                messagebox.showerror("錯誤", str(e))
            
                # 顯示輸出結果
                self.txt_output.insert(tk.END, "【讀取成功】\n")
                self.txt_output.insert(tk.END, f"影像原始解析度: {bayer_pattern.shape}\n")
                self.txt_output.insert(tk.END, f"Bayer 陣列描述: {color_desc}\n\n")
                self.txt_output.insert(
                    tk.END, "--- 提取物理通道數值 (座標 0,0 處) ---\n"
                )
                self.txt_output.insert(tk.END, f"紅色通道 (R)   數值: {ch_R[0, 0]}\n")
                self.txt_output.insert(tk.END, f"綠色通道 (GR)  數值: {ch_GR[0, 0]}\n")
                self.txt_output.insert(tk.END, f"綠色通道 (GB)  數值: {ch_GB[0, 0]}\n")
                self.txt_output.insert(tk.END, f"藍色通道 (B)   數值: {ch_B[0, 0]}\n\n")
                self.txt_output.insert(tk.END, "--- 啟用之解碼設定選項 ---\n")
                self.txt_output.insert(
                    tk.END, f"- 白平衡: {'相機內定' if use_camera_wb else '自動計算'}\n"
                )
                self.txt_output.insert(tk.END, f"- 色彩空間: {self.output_space_var.get()}\n")
                self.txt_output.insert(
                    tk.END, f"- 半亮度解碼: {'開啟 (降低解析度加速)' if half_size else '關閉 (全解析度)'}\n"
                )

        except Exception as e:
            messagebox.showerror("重度錯誤", f"無法解析此 RAW 檔案。\n原因: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = RawParamGui(root)
    root.mainloop()
