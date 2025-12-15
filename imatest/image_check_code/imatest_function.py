import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
from skimage import color
import os
import csv
from datetime import datetime

# ==========================================================
# === 核心影像分析算法 (Core Image Analysis Algorithms) ===
# ==========================================================

# 1. MTF50 (銳利度) 替代計算 - 使用 Laplacian Variance
def calculate_sharpness_estimate(gray_img):
    """
    MTF50 替代方案: 使用 Laplacian 變異數作為銳利度快速估計。
    真正的 MTF50 需要 ISO 12233 斜邊圖卡和複雜的演算法。
    
    Args:
        gray_img (np.array): 灰度影像。
        
    Returns:
        float: 銳利度估計值 (Laplacian Variance)。
    """
    if gray_img is None or gray_img.ndim != 2:
        return 0.0
    
    laplacian = cv2.Laplacian(gray_img, cv2.CV_64F)
    # MTF50_Estimate (LW/PH) = K * variance (K為比例常數)
    return laplacian.var() 

# 2. Q14 密度 (Density) 和 SNR 計算
def analyze_density_snr(roi_img):
    """
    分析 Q14 階梯圖 (Step Chart) ROI 區域的 Y 密度和 Y-SNR。
    
    Args:
        roi_img (np.array): 框選的單個階梯 ROI (BGR 格式)。
        
    Returns:
        tuple: (平均 Y 密度, 平均 Y-SNR 估計)
    """
    if roi_img is None:
        return 0.0, 0.0

    # 轉換到 YCbCr 空間，只取 Y (亮度) 通道
    yuv_img = cv2.cvtColor(roi_img, cv2.COLOR_BGR2YUV)
    Y_channel = yuv_img[:, :, 0] # Y: 亮度通道 (0-255)
    
    # 計算 Y 密度 (D = -log10(Y_norm))
    Y_norm = Y_channel.astype(np.float64) / 255.0
    # 避免 log(0)
    Y_norm[Y_norm == 0] = 1e-6 
    Y_density = -np.log10(Y_norm)
    avg_density = np.mean(Y_density)
    
    # 計算 Y-SNR (信噪比) 估計
    # SNR = mean(Y) / std(Y)
    avg_Y = np.mean(Y_channel)
    std_Y = np.std(Y_channel)
    
    # 避免除以 0
    snr_estimate = avg_Y / std_Y if std_Y > 0 else 999.0
    
    return avg_density, snr_estimate

# 3. 色差 Delta E / Delta C 計算
def calculate_delta_e_c(rgb_ref, rgb_sample):
    """
    計算參考 RGB (理想值) 和取樣 RGB (實際值) 之間的 $\Delta E 2000$ 和 $\Delta C$。
    
    Args:
        rgb_ref (tuple): (R, G, B) 參考值 (0-255)。
        rgb_sample (tuple): (R, G, B) 實際測量值 (0-255)。
        
    Returns:
        tuple: ($\Delta E 2000$, $\Delta C 2000$)
    """
    # 轉換為 sRGB (0-1)
    srgb_ref = np.array(rgb_ref) / 255.0
    srgb_sample = np.array(rgb_sample) / 255.0
    
    # 轉換到 Lab 空間 (D65)
    lab_ref = color.rgb2lab(srgb_ref[np.newaxis, np.newaxis, :])
    lab_sample = color.rgb2lab(srgb_sample[np.newaxis, np.newaxis, :])
    
    L_ref, a_ref, b_ref = lab_ref[0, 0, :]
    L_sample, a_sample, b_sample = lab_sample[0, 0, :]

    # 使用 skimage 提供的 $\Delta E 2000$ 算法
    delta_e = color.delta_e(lab_ref, lab_sample, method='cie2000')[0, 0]
    
    # 計算 $\Delta C$ (色度差，忽略亮度 L)
    # C = sqrt(a^2 + b^2)
    C_ref = np.sqrt(a_ref**2 + b_ref**2)
    C_sample = np.sqrt(a_sample**2 + b_sample**2)
    delta_c = np.abs(C_ref - C_sample)
    
    return delta_e, delta_c

# ==========================================================
# === Imatest GUI 主應用程式 (GUI Main Application) ===
# ==========================================================

class ImatestGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sam 影像品質分析助手 v1.0")
        self.geometry("1000x800")
        
        # 影像變數
        self.original_img_cv = None # OpenCV BGR 格式
        self.image_tk = None       # Tkinter 顯示格式
        self.image_path = None
        self.report_data = []      # 報表數據儲存
        
        # 繪圖變數 (用於滑鼠框選)
        self.canvas_img = None     # 畫布上的圖片物件
        self.rect_id = None        # 框選矩形的ID
        self.start_x = None
        self.start_y = None
        
        # 色卡參考值 (ColorChecker 24 - sRGB D65 參考值，這裡使用近似值)
        # 完整的 Imatest 會使用標準化的 CIE L*a*b* 值
        self.REF_COLOR_24 = [
            (115, 82, 68), (194, 150, 130), (98, 122, 157), (87, 108, 67),
            (133, 128, 177), (103, 189, 170), (214, 126, 44), (80, 91, 166),
            (193, 90, 99), (94, 60, 108), (157, 188, 64), (224, 163, 46),
            (56, 61, 150), (70, 148, 73), (175, 54, 60), (231, 199, 31),
            (187, 86, 149), (85, 131, 169), (243, 243, 242), (200, 200, 200),
            (160, 160, 160), (122, 122, 122), (85, 85, 85), (52, 52, 52)
        ] # (R, G, B) 0-255

        self.create_widgets()

    def create_widgets(self):
        # --- 頂部控制面板 ---
        control_frame = ttk.Frame(self, padding="10")
        control_frame.pack(fill='x')

        ttk.Button(control_frame, text="開啟圖片", command=self.open_image).pack(side='left', padx=5)
        ttk.Button(control_frame, text="分析色卡 (ColorChecker)", command=lambda: self.set_mode('color_chart')).pack(side='left', padx=5)
        ttk.Button(control_frame, text="分析密度 (Q14 Step)", command=lambda: self.set_mode('density_chart')).pack(side='left', padx=5)
        ttk.Button(control_frame, text="基礎銳利度 (MTF50估計)", command=self.analyze_sharpness).pack(side='left', padx=5)
        ttk.Button(control_frame, text="生成報表", command=self.generate_report).pack(side='left', padx=5)
        
        self.mode = 'none' # 當前操作模式 (color_chart, density_chart, srf_chart)
        self.status_label = ttk.Label(control_frame, text="狀態：請開啟圖片", foreground="blue")
        self.status_label.pack(side='right', padx=10)

        # --- 影像顯示區 ---
        self.canvas = tk.Canvas(self, bg="gray", cursor="cross")
        self.canvas.pack(fill='both', expand=True, padx=10, pady=10)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # --- 結果顯示區 ---
        self.results_text = tk.Text(self, height=10, state='disabled', wrap='word')
        self.results_text.pack(fill='x', padx=10, pady=5)
        self.display_message("歡迎使用 Sam 影像品質分析助手！")

    def display_message(self, message):
        """用於在結果區顯示訊息"""
        self.results_text.config(state='normal')
        self.results_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.results_text.see(tk.END)
        self.results_text.config(state='disabled')

    def set_mode(self, new_mode):
        """設定當前的操作模式"""
        if self.original_img_cv is None:
            self.status_label.config(text="狀態：請先開啟圖片！", foreground="red")
            return
            
        self.mode = new_mode
        if new_mode == 'color_chart':
            self.status_label.config(text="狀態：請框選 ColorChecker 24 區域。", foreground="green")
            self.display_message("已進入 ColorChecker 分析模式。請在畫布上框選色卡區域。")
        elif new_mode == 'density_chart':
            self.status_label.config(text="狀態：請在 Q14 階梯圖上點擊/框選要分析的位置。", foreground="orange")
            self.display_message("已進入 Q14 密度分析模式。請框選一個或多個階梯區域。")
        elif new_mode == 'srf_chart':
            self.status_label.config(text="狀態：請框選 SFR 斜邊。", foreground="purple")
            self.display_message("已進入 SFR 銳利度分析模式。請框選斜邊。")
        else:
            self.status_label.config(text="狀態：空閒中", foreground="blue")

    # --- GUI 事件處理 ---

    def open_image(self):
        """開啟圖片檔案並顯示"""
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp")]
        )
        if path:
            self.image_path = path
            # 讀取 OpenCV 格式 (用於計算)
            self.original_img_cv = cv2.imread(path)
            if self.original_img_cv is None:
                self.display_message(f"讀取圖片失敗: {path}")
                return

            # 轉換為 RGB (PIL) 並顯示
            img_rgb = cv2.cvtColor(self.original_img_cv, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            
            # 縮放以適應畫布
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            
            # 保持長寬比縮放
            ratio = min(canvas_w / img_pil.width, canvas_h / img_pil.height)
            new_w = int(img_pil.width * ratio)
            new_h = int(img_pil.height * ratio)
            
            self.current_display_img = img_pil.resize((new_w, new_h), Image.LANCZOS)
            self.image_tk = ImageTk.PhotoImage(self.current_display_img)
            
            self.canvas.delete("all")
            # 圖片置中
            self.canvas_img = self.canvas.create_image(
                canvas_w//2, canvas_h//2, anchor=tk.CENTER, image=self.image_tk
            )
            
            self.display_message(f"成功開啟圖片: {os.path.basename(path)}")
            self.set_mode('none') # 重置模式
            self.report_data = [] # 清空報表數據
            
    def on_button_press(self, event):
        """滑鼠按下事件：開始框選"""
        if self.original_img_cv is None:
            return
        
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        
        # 刪除舊的矩形
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        # 創建新的矩形
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=2
        )
        
    def on_mouse_drag(self, event):
        """滑鼠拖曳事件：更新矩形大小"""
        if self.rect_id:
            end_x = self.canvas.canvasx(event.x)
            end_y = self.canvas.canvasy(event.y)
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, end_x, end_y)

    def on_button_release(self, event):
        """滑鼠釋放事件：結束框選並進行分析"""
        if self.rect_id is None or self.original_img_cv is None:
            return

        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        
        # 轉換座標從顯示圖片到原始圖片尺寸
        scale_x = self.original_img_cv.shape[1] / self.current_display_img.width
        scale_y = self.original_img_cv.shape[0] / self.current_display_img.height

        x1 = int(min(self.start_x, end_x) * scale_x)
        y1 = int(min(self.start_y, end_y) * scale_y)
        x2 = int(max(self.start_x, end_x) * scale_x)
        y2 = int(max(self.start_y, end_y) * scale_y)

        # 確保 ROI 是有效的
        if x2 <= x1 or y2 <= y1:
             self.display_message("警告：無效的框選區域。")
             return

        # 擷取原始影像 ROI
        roi_img_cv = self.original_img_cv[y1:y2, x1:x2]

        if self.mode == 'color_chart':
            self.analyze_color_chart(roi_img_cv)
        elif self.mode == 'density_chart':
            self.analyze_step_chart(roi_img_cv, x1, y1, x2, y2)
        elif self.mode == 'srf_chart':
            # 這裡我們只計算基礎銳利度，完整的 SFR 分析需要精確的圖卡檢測
            self.display_message("SFR 分析模式: 由於演算法複雜度，我們使用基礎銳利度估計。")
            self.analyze_sharpness(roi_img_cv)
        
        # 分析完成後，可以選擇保留或刪除框
        self.canvas.delete(self.rect_id)
        self.rect_id = None
        
    # --- 專門分析函數 ---
    
    def analyze_sharpness(self, roi_img=None):
        """計算並顯示 MTF50 估計值"""
        
        img_to_analyze = roi_img if roi_img is not None else self.original_img_cv
        
        if img_to_analyze is None:
            self.display_message("錯誤：沒有可分析的影像！")
            return
            
        gray_img = cv2.cvtColor(img_to_analyze, cv2.COLOR_BGR2GRAY)
        
        sharpness_estimate = calculate_sharpness_estimate(gray_img)
        
        result_text = f"**基礎銳利度 (MTF50 估計/Laplacian Variance): {sharpness_estimate:.2f}**"
        self.display_message(result_text)
        self.report_data.append({
            'Test Item': 'MTF50 Estimate', 
            'Result': f'{sharpness_estimate:.2f}',
            'Unit': 'Variance'
        })
        
        if roi_img is None:
            # 預留功能: 完整的 SFR 分析
            self.display_message("[預留功能]: 完整的 SFRplus/eSFR ISO 分析功能已預留。")

    def analyze_step_chart(self, roi_img, x1, y1, x2, y2):
        """分析 Q14 階梯圖中的單個階梯，計算 Y-Density 和 Y-SNR"""
        
        # 由於我們沒有自動識別 Q14 圖卡的所有 14 階
        # 這裡假設使用者框選的是單獨的一階
        
        density, snr = analyze_density_snr(roi_img)
        
        result_text = (
            f"\n--- 密度/SNR 分析 (ROI: ({x1}, {y1}) - ({x2}, {y2})) ---\n"
            f"  平均 Y-Density: {density:.3f}\n"
            f"  平均 Y-SNR 估計: {snr:.2f}\n"
        )
        self.display_message(result_text)
        self.report_data.append({
            'Test Item': 'Step Chart Analysis', 
            'Result': f'Y-Density: {density:.3f}, Y-SNR: {snr:.2f}',
            'Unit': 'N/A'
        })


    def analyze_color_chart(self, roi_img_cv):
        """
        自動識別 ColorChecker 24 色塊並計算 $\Delta E$ 和 $\Delta C$。
        
        這是一個簡化的自動識別版本，假設色塊排列整齊且ROI足夠準確。
        
        Args:
            roi_img_cv (np.array): 框選的 ColorChecker 24 區域 (BGR 格式)。
        """
        self.display_message("\n--- ColorChecker 24 分析開始 ---")

        rows, cols = 4, 6
        h, w, _ = roi_img_cv.shape
        
        # 計算每個色塊的尺寸
        block_w = w // cols
        block_h = h // rows
        
        analysis_results = []
        
        # 迭代 24 個色塊
        for i in range(rows):
            for j in range(cols):
                patch_id = i * cols + j
                ref_rgb = self.REF_COLOR_24[patch_id]
                
                # 擷取單個色塊 ROI
                x1 = j * block_w
                y1 = i * block_h
                x2 = (j + 1) * block_w
                y2 = (i + 1) * block_h
                
                patch_img = roi_img_cv[y1:y2, x1:x2]
                
                # 為了避免邊緣和高光/陰影影響，取中心一小塊區域進行平均
                center_h = patch_img.shape[0] // 4
                center_w = patch_img.shape[1] // 4
                
                # 取中心 50% 區域
                center_patch = patch_img[center_h:3*center_h, center_w:3*center_w]
                
                # 計算實際測量值的平均 RGB
                avg_bgr = np.mean(center_patch, axis=(0, 1))
                # OpenCV 是 BGR，轉換為 RGB
                sample_rgb = (avg_bgr[2], avg_bgr[1], avg_bgr[0]) 

                # 計算 $\Delta E$ 和 $\Delta C$
                delta_e, delta_c = calculate_delta_e_c(ref_rgb, sample_rgb)
                
                analysis_results.append({
                    'ID': patch_id + 1,
                    'Ref RGB': ref_rgb,
                    'Sample RGB': tuple(int(c) for c in sample_rgb),
                    'Delta E 2000': delta_e,
                    'Delta C 2000': delta_c
                })
                
                self.display_message(
                    f"  色塊 {patch_id+1:02d}: $\Delta E$={delta_e:.2f}, $\Delta C$={delta_c:.2f} "
                    f"(Ref:{ref_rgb}, Sample:{tuple(int(c) for c in sample_rgb)})"
                )
                
                # 額外計算 Y-SNR (針對灰階色塊 19-24)
                if patch_id >= 18: # 19-24 (索引 18-23)
                    density, snr = analyze_density_snr(patch_img)
                    self.display_message(f"    (灰階 {patch_id+1}): Y-SNR={snr:.2f}")
                    analysis_results[-1]['Y-SNR'] = snr
                    
        # 將結果加入報表數據
        self.report_data.append({
            'Test Item': 'ColorChecker Analysis', 
            'Result': analysis_results, 
            'Unit': 'Delta E/C'
        })
        self.display_message("--- ColorChecker 24 分析完成 ---")
        
    def generate_report(self):
        """將所有分析結果匯出為 CSV 報表"""
        if not self.report_data:
            self.display_message("警告：沒有分析數據可生成報表！")
            return

        # 選擇儲存路徑
        default_filename = f"IQ_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_filename,
            filetypes=[("CSV files", "*.csv")]
        )
        
        if not filepath:
            return

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 寫入標頭資訊
                writer.writerow(["影像品質測試報表"])
                writer.writerow(["測試時間", datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(["原始影像", os.path.basename(self.image_path) if self.image_path else "N/A"])
                writer.writerow([])
                
                # 寫入分析結果
                writer.writerow(["測試項目", "結果描述", "單位", "備註"])
                
                for item in self.report_data:
                    if item['Test Item'] == 'ColorChecker Analysis':
                        # 處理 ColorChecker 的複雜結構
                        writer.writerow([
                            item['Test Item'], 
                            f'Average Delta E: {np.mean([d["Delta E 2000"] for d in item["Result"]]):.2f}',
                            'Delta E/C',
                            '詳細數據在下方'
                        ])
                        writer.writerow(["Patch ID", "參考 RGB", "測量 RGB", "Delta E 2000", "Delta C 2000", "Y-SNR (灰階)"])
                        for d in item['Result']:
                            snr_val = f"{d.get('Y-SNR', 'N/A'):.2f}" if d.get('Y-SNR') else "N/A"
                            writer.writerow([
                                d['ID'], 
                                str(d['Ref RGB']), 
                                str(d['Sample RGB']), 
                                f"{d['Delta E 2000']:.2f}", 
                                f"{d['Delta C 2000']:.2f}",
                                snr_val
                            ])
                        writer.writerow([]) # 分隔
                    else:
                        writer.writerow([item['Test Item'], item['Result'], item['Unit'], 'N/A'])
                
            self.display_message(f"✅ 報表成功生成並儲存到: {filepath}")
            
        except Exception as e:
            self.display_message(f"❌ 報表生成失敗: {e}")

# ==========================================================
# === 程式執行入口 (Program Entry Point) ===
# ==========================================================
if __name__ == '__main__':
    # 設置高 DPI 縮放 (可選)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    app = ImatestGUI()
    app.mainloop()