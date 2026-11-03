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

    # 【Sam 修正】：使用標準相容的 deltaE_ciede2000 API 替代舊版 color.delta_e
    delta_e = color.deltaE_ciede2000(lab_ref, lab_sample)[0, 0]
    
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
        # 【Sam 新增】：透視變換 4 點座標儲存區 (左上, 右上, 右下, 左下)
        self.pts_4point = []
        self.point_markers = []
        self.create_widgets()

    def create_widgets(self):
        # --- 頂部控制面板 ---
        control_frame = ttk.Frame(self, padding="10")
        control_frame.pack(fill='x')

        ttk.Button(control_frame, text="開啟圖片", command=self.open_image).pack(side='left', padx=5)
        ttk.Button(control_frame, text="分析色卡 (ColorChecker)", command=lambda: self.set_mode('color_chart')).pack(side='left', padx=5)
        ttk.Button(control_frame, text="分析 20 階灰階 (Q13/Q14 Gray Chart)", command=lambda: self.set_mode('density_chart')).pack(side='left', padx=5)
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
        self.clear_canvas_drawings() # 重置繪圖與點位

        if new_mode == 'color_chart':
            self.status_label.config(text="狀態：請依序點擊 ColorChecker 24 四個角 (左上->右上->右下->左下)", foreground="green")
            self.display_message("已進入 ColorChecker 透視分析模式。請在畫布上依序點擊色卡 4 個角落。")
        elif new_mode == 'density_chart':
            self.status_label.config(text="狀態：請依序點擊 20 階灰階圖 4 個角落 (左上->右上->右下->左下)", foreground="orange")
            self.display_message("已進入 20 Step 灰階分析模式。請依序點選 20 階灰階條的 4 個角落。")
        elif new_mode == 'srf_chart':
            self.status_label.config(text="狀態：請框選 SFR 斜邊。", foreground="purple")
            self.display_message("已進入 SFR 銳利度分析模式。請框選斜邊。")
        else:
            self.status_label.config(text="狀態：空閒中", foreground="blue")

    def clear_canvas_drawings(self):
        """清除畫布上的輔助標記線條與點位"""
        self.pts_4point = []
        for marker in self.point_markers:
            self.canvas.delete(marker)
        self.point_markers = []
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

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
        """滑鼠按下事件：依模式進行 4 點點擊或矩形框選"""
        if self.original_img_cv is None:
            return
        
        # 取得 Canvas 上的點擊座標
        click_x = self.canvas.canvasx(event.x)
        click_y = self.canvas.canvasy(event.y)

        # 【Sam 擴充功能】： ColorChecker 24 四點透視點擊邏輯
        if self.mode in ['color_chart', 'density_chart']:
            # 轉換座標至原始圖片解析度
            scale_x = self.original_img_cv.shape[1] / self.current_display_img.width
            scale_y = self.original_img_cv.shape[0] / self.current_display_img.height
            
            orig_x = click_x * scale_x
            orig_y = click_y * scale_y

            self.pts_4point.append((orig_x, orig_y))
            pt_num = len(self.pts_4point)
            
            # 在畫布上記錄點擊視覺標籤 (紅色圓點 + 數字)
            r = 4
            marker = self.canvas.create_oval(click_x-r, click_y-r, click_x+r, click_y+r, fill='red', outline='yellow', width=1.5)
            text_marker = self.canvas.create_text(click_x+10, click_y-5, text=str(pt_num), fill='yellow', font=('Arial', 10, 'bold'))
            self.point_markers.extend([marker, text_marker])

            corner_names = ["左上 (Top-Left)", "右上 (Top-Right)", "右下 (Bottom-Right)", "左下 (Bottom-Left)"]
            self.display_message(f"已選取第 {pt_num} 角落 [{corner_names[pt_num-1]}]: ({int(orig_x)}, {int(orig_y)})")

            # 集滿 4 點後自動啟動透視校正與 24 色塊分析
            if len(self.pts_4point) == 4:
                if self.mode == 'color_chart':
                    self.display_message("4 個角落點選完畢，開始進行 ColorChecker 24 透視校正...")
                    self.analyze_color_chart_perspective()
                elif self.mode == 'density_chart':
                    self.display_message("4 個角落點選完畢，開始進行 20 階灰階 (Step Chart) 分析...")
                    self.analyze_20step_gray_chart_perspective()
            return

        # 其他模式（如矩形框選）
        self.start_x = click_x
        self.start_y = click_y
        
        # 刪除舊的矩形
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        # 創建新的矩形
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=2
        )
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
    def on_mouse_drag(self, event):
        """滑鼠拖曳事件：更新矩形大小"""
        if self.rect_id and self.mode != 'color_chart':
            end_x = self.canvas.canvasx(event.x)
            end_y = self.canvas.canvasy(event.y)
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, end_x, end_y)

    def on_button_release(self, event):
        """滑鼠釋放事件：結束框選並進行分析"""
        if self.mode == 'color_chart':
            return # ColorChecker 使用 4 點點擊，跳過 Drag Release 邏輯

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

        if self.mode == 'density_chart':
            self.analyze_step_chart(roi_img_cv, x1, y1, x2, y2)
        elif self.mode == 'srf_chart':
            self.display_message("SFR 分析模式: 由於演算法複雜度，我們使用基礎銳利度估計。")
            self.analyze_sharpness(roi_img_cv)
        
        self.canvas.delete(self.rect_id)
        self.rect_id = None
        
    # --- 專門分析函數 ---
# ... existing code ...
    def analyze_color_chart(self, roi_img_cv):
        """[舊版 矩形框選備用]"""
        pass

    def analyze_color_chart_perspective(self):
        """
        【Sam 影像處理小幫手 - 四點透視變換與 24 色塊 ROI 視覺化校驗】
        透過 OpenCV cv2.getPerspectiveTransform 將傾斜圖卡透視拉直，
        並在畫布上將 24 個動態 ROI 繪製出來供使用者檢查是否對齊。
        """
        if len(self.pts_4point) != 4:
            self.display_message("錯誤：透視變換需要精確的 4 個點！")
            return

        self.display_message("\n--- ColorChecker 24 (四點透視變換) 分析開始 ---")

        # 1. 取得用戶點選的 4 個頂點 (左上, 右上, 右下, 左下)
        src_pts = np.array(self.pts_4point, dtype=np.float32)

        # 2. 計算目標拉直影像的標準寬度與高度 (以長邊作為標準，預設 6:4 比例)
        width_top = np.linalg.norm(src_pts[1] - src_pts[0])
        width_bottom = np.linalg.norm(src_pts[2] - src_pts[3])
        max_w = int(max(width_top, width_bottom))

        height_left = np.linalg.norm(src_pts[3] - src_pts[0])
        height_right = np.linalg.norm(src_pts[2] - src_pts[1])
        max_h = int(max(height_left, height_right))

        # 強制 6:4 色卡標準比例尺寸
        dst_w = max_w
        dst_h = int(max_w * (4.0 / 6.0))

        # 定義透視目標四角座標
        dst_pts = np.array([
            [0, 0],
            [dst_w - 1, 0],
            [dst_w - 1, dst_h - 1],
            [0, dst_h - 1]
        ], dtype=np.float32)

        # 3. 計算 Perspective Matrix (正向與逆向 Transform 矩陣)
        M_prespective = cv2.getPerspectiveTransform(src_pts, dst_pts)
        M_inv = cv2.getPerspectiveTransform(dst_pts, src_pts)

        # 將原始影像進行透視扭正 Warp Perspective
        warped_card = cv2.warpPerspective(self.original_img_cv, M_prespective, (dst_w, dst_h))

        # 4. 在透視校正圖上劃分 4x6 網格，並計算 24 個色塊採樣區
        rows, cols = 4, 6
        block_w = dst_w / cols
        block_h = dst_h / rows

        # 計算縮放比（將透視後點轉回原始 Display Canvas 用）
        scale_x = self.current_display_img.width / self.original_img_cv.shape[1]
        scale_y = self.current_display_img.height / self.original_img_cv.shape[0]

        analysis_results = []

        for i in range(rows):
            for j in range(cols):
                patch_id = i * cols + j
                ref_rgb = self.REF_COLOR_24[patch_id]

                # 標準透視圖上該色塊的中心座標與採樣範圍 (取中心 40% 避免邊緣失真)
                cx_warped = (j + 0.5) * block_w
                cy_warped = (i + 0.5) * block_h
                sample_w = block_w * 0.4
                sample_h = block_h * 0.4

                x1_w = int(cx_warped - sample_w / 2)
                x2_w = int(cx_warped + sample_w / 2)
                y1_w = int(cy_warped - sample_h / 2)
                y2_w = int(cy_warped + sample_h / 2)

                # 擷取校正圖上的色塊畫素
                patch_img = warped_card[y1_w:y2_w, x1_w:x2_w]
                
                # 計算實際測量值的平均 BGR -> RGB
                if patch_img.size > 0:
                    avg_bgr = np.mean(patch_img, axis=(0, 1))
                    sample_rgb = (avg_bgr[2], avg_bgr[1], avg_bgr[0])
                else:
                    sample_rgb = (0, 0, 0)

                # 計算 Delta E 2000 與 Delta C
                delta_e, delta_c = calculate_delta_e_c(ref_rgb, sample_rgb)

                analysis_results.append({
                    'ID': patch_id + 1,
                    'Ref RGB': ref_rgb,
                    'Sample RGB': tuple(int(c) for c in sample_rgb),
                    'Delta E 2000': delta_e,
                    'Delta C 2000': delta_c
                })

                # --- 5. 【視覺化 ROI 驗證】將透視矩陣逆變換 (M_inv)，在原始 Canvas 上劃出 24 個藍色採樣點/框 ---
                # 原圖座標中的色塊中心
                pt_warped_center = np.array([[[cx_warped, cy_warped]]], dtype=np.float32)
                pt_orig_center = cv2.perspectiveTransform(pt_warped_center, M_inv)[0, 0]

                # 轉換為 GUI Canvas 畫面座標
                canvas_cx = pt_orig_center[0] * scale_x
                canvas_cy = pt_orig_center[1] * scale_y

                # 畫出 24 個 ROI 圓形標示與 Patch ID
                r = 3
                roi_marker = self.canvas.create_oval(
                    canvas_cx - r, canvas_cy - r, canvas_cx + r, canvas_cy + r,
                    outline='#38bdf8', fill='#0284c7', width=1.5
                )
                roi_text = self.canvas.create_text(
                    canvas_cx, canvas_cy - 8,
                    text=f"P{patch_id+1}", fill='#38bdf8', font=('Arial', 7, 'bold')
                )
                self.point_markers.extend([roi_marker, roi_text])

                # 輸出 Log
                self.display_message(
                    f"  色塊 {patch_id+1:02d}: ΔE={delta_e:.2f}, ΔC={delta_c:.2f} "
                    f"(Ref:{ref_rgb}, Sample:{tuple(int(c) for c in sample_rgb)})"
                )

                # 計算灰態 SNR
                if patch_id >= 18:
                    density, snr = analyze_density_snr(patch_img)
                    self.display_message(f"    (灰階 P{patch_id+1}): Y-SNR={snr:.2f}")
                    analysis_results[-1]['Y-SNR'] = snr

        # 將結果加入報表數據
        self.report_data.append({
            'Test Item': 'ColorChecker 24 (Perspective Transform)',
            'Result': analysis_results,
            'Unit': 'Delta E/C'
        })
        self.display_message("✅ ColorChecker 24 透視校正與 24 色塊 ROI 驗證繪製完成！")
        self.status_label.config(text="狀態：ColorChecker 分析完成，請查看畫面上的 24 個 ROI 藍點驗證位置。", foreground="blue")
        
    def analyze_20step_gray_chart_perspective(self):
        """
        【Sam 影像處理小幫手 - 20 Step 灰階階梯圖 (Kodak Q-13) 透視校正與 Y-SNR 分析】
        透過四點透視將長條型灰階卡拉直，切分為 20 個獨立 ROI，
        精確計算每一階的 Y 亮度, Density, 以及 Y-SNR (含 dB)。
        """
        if len(self.pts_4point) != 4:
            self.display_message("錯誤：透視變換需要精確的 4 個點！")
            return

        self.display_message("\n--- 20 Step 灰階階梯圖 (KODAK Q-13) 分析開始 ---")

        # 1. 取得用戶點選的 4 個頂點 (左上, 右上, 右下, 左下)
        src_pts = np.array(self.pts_4point, dtype=np.float32)

        # 2. 計算目標拉直影像的標準長寬
        width_top = np.linalg.norm(src_pts[1] - src_pts[0])
        width_bottom = np.linalg.norm(src_pts[2] - src_pts[3])
        dst_w = int(max(width_top, width_bottom))

        height_left = np.linalg.norm(src_pts[3] - src_pts[0])
        height_right = np.linalg.norm(src_pts[2] - src_pts[1])
        dst_h = int(max(height_left, height_right))

        dst_pts = np.array([
            [0, 0],
            [dst_w - 1, 0],
            [dst_w - 1, dst_h - 1],
            [0, dst_h - 1]
        ], dtype=np.float32)

        # 3. Perspective Homography Matrix
        M_prespective = cv2.getPerspectiveTransform(src_pts, dst_pts)
        M_inv = cv2.getPerspectiveTransform(dst_pts, src_pts)

        warped_card = cv2.warpPerspective(self.original_img_cv, M_prespective, (dst_w, dst_h))

        # 4. 20 個階梯水平均勻分割
        steps = 20
        step_w = dst_w / steps

        scale_x = self.current_display_img.width / self.original_img_cv.shape[1]
        scale_y = self.current_display_img.height / self.original_img_cv.shape[0]

        step_results = []
        labels = ["A", "1", "2", "3", "4", "5", "6", "M", "8", "9", "10", "11", "12", "13", "14", "15", "B", "17", "18", "19"]

        self.display_message("Step | 標籤 | 平均亮度(Y) | Y-Density | Y-SNR (倍數) | Y-SNR (dB)")
        self.display_message("-" * 65)

        for step_idx in range(steps):
            # 取中間 50% 寬度與 50% 高度作為採樣區，避開階梯邊界縫隙
            cx_warped = (step_idx + 0.5) * step_w
            cy_warped = dst_h * 0.5
            sample_w = step_w * 0.5
            sample_h = dst_h * 0.5

            x1_w = int(cx_warped - sample_w / 2)
            x2_w = int(cx_warped + sample_w / 2)
            y1_w = int(cy_warped - sample_h / 2)
            y2_w = int(cy_warped + sample_h / 2)

            patch_bgr = warped_card[y1_w:y2_w, x1_w:x2_w]

            if patch_bgr.size > 0:
                # 計算亮度 Y (Y = 0.299R + 0.587G + 0.114B)
                yuv = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2YUV)
                y_channel = yuv[:, :, 0].astype(np.float64)

                mean_y = np.mean(y_channel)
                std_y = np.std(y_channel)

                # Y-Density (D = -log10(Y/255))
                y_norm = max(mean_y / 255.0, 1e-6)
                density = -np.log10(y_norm)

                # Y-SNR
                snr_ratio = mean_y / std_y if std_y > 0 else 999.0
                snr_db = 20 * np.log10(snr_ratio) if snr_ratio > 0 else 0.0
            else:
                mean_y, density, snr_ratio, snr_db = 0.0, 0.0, 0.0, 0.0

            step_label = labels[step_idx] if step_idx < len(labels) else f"{step_idx+1}"
            step_results.append({
                'Step': step_idx + 1,
                'Label': step_label,
                'Mean Y': mean_y,
                'Density': density,
                'Y-SNR (linear)': snr_ratio,
                'Y-SNR (dB)': snr_db
            })

            # 畫布逆顯示 ROI 採樣中心點
            pt_warped_center = np.array([[[cx_warped, cy_warped]]], dtype=np.float32)
            pt_orig_center = cv2.perspectiveTransform(pt_warped_center, M_inv)[0, 0]

            canvas_cx = pt_orig_center[0] * scale_x
            canvas_cy = pt_orig_center[1] * scale_y

            r = 3
            roi_marker = self.canvas.create_oval(
                canvas_cx - r, canvas_cy - r, canvas_cx + r, canvas_cy + r,
                outline='#10b981', fill='#34d399', width=1.5
            )
            roi_text = self.canvas.create_text(
                canvas_cx, canvas_cy - 8,
                text=f"S{step_idx+1}", fill='#10b981', font=('Arial', 7, 'bold')
            )
            self.point_markers.extend([roi_marker, roi_text])

            self.display_message(
                f"S{step_idx+1:02d} |  {step_label:^4s} |   {mean_y:6.2f}    |   {density:.3f}   |   {snr_ratio:6.2f}     |  {snr_db:5.2f} dB"
            )

        # 寫入報表
        self.report_data.append({
            'Test Item': '20-Step Gray Scale SNR Analysis',
            'Result': step_results,
            'Unit': 'Y-SNR (dB)'
        })
        self.display_message("✅ 20 Step 灰階 Y-SNR 分析與 20 個 ROI 驗證圖點繪製完成！")
        self.status_label.config(text="狀態：20 階灰階分析完成！請查看綠色 ROI 採樣點。", foreground="blue")        
        
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
                    if item['Test Item'] == '20-Step Gray Scale SNR Analysis':
                        writer.writerow([item['Test Item'], '20 階灰階 SNR 分析列表', 'Y-SNR (dB)', '詳細數據如下'])
                        writer.writerow(["Step ID", "標籤", "平均 Y 亮度", "Y-Density", "Y-SNR (Linear)", "Y-SNR (dB)"])
                        for d in item['Result']:
                            writer.writerow([
                                d['Step'], d['Label'], f"{d['Mean Y']:.2f}",
                                f"{d['Density']:.3f}", f"{d['Y-SNR (linear)']:.2f}", f"{d['Y-SNR (dB)']:.2f}"
                            ])
                        writer.writerow([])
                    elif item['Test Item'] == 'ColorChecker 24 (Perspective Transform)':
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
                                d['ID'], str(d['Ref RGB']), str(d['Sample RGB']),
                                f"{d['Delta E 2000']:.2f}", f"{d['Delta C 2000']:.2f}", snr_val
                            ])
                        writer.writerow([])
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