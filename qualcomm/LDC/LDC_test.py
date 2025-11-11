import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

# --- 1. 光學/數學核心計算函數 ---

def calculate_distortion(img_path, pattern_size, square_size_mm):
    """
    計算幾何失真場和 TV Distortion 值。
    
    Args:
        img_path (str): 圖像文件路徑。
        pattern_size (tuple): 檢測的格點內角點數量 (cols, rows)。
        square_size_mm (float): 棋盤格單元格邊長 (用於輸出報告, 不影響像素計算)。

    Returns:
        tuple: (max_tv_distortion, distortion_map_data)
               max_tv_distortion (float): TV 失真百分比。
               distortion_map_data (dict): 包含 ideal_points, actual_points, vectors 等視覺化數據。
    """
    
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"無法讀取文件: {img_path}")
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]
    
    # 1. 檢測格點 (Find Chessboard Corners)
    # objp: 理想的3D點 (Z=0, 為了校準, 但我們只關心像素座標)
    objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)
    
    # 尋找角點
    ret, actual_points = cv2.findChessboardCorners(gray, pattern_size, None)

    if not ret:
        raise ValueError("未能成功檢測到足夠的格點角點。請檢查圖像和 '格點尺寸' 設置。")

    # 精化角點位置
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    actual_points = cv2.cornerSubPix(gray, actual_points, (11, 11), (-1, -1), criteria)
    
    # 2. 確定理想格點位置 (Ideal Grid Position)
    # 使用仿射變換 (Affine Transformation) 或透視變換 (Homography)
    # 找到實際點與理想格點座標系之間的最優映射。
    
    # 由於校準過程複雜，這裡簡化處理：假設 ideal_points 是在實際點上擬合的完美直線網格
    # 理想格點的 (0,0) 點是第一個角點，然後簡單地計算等距點。
    # 更準確的方法是：先用 cv2.calibrateCamera 得到相機矩陣 K 和失真係數 D，然後使用 D=0 重新投影 objp 得到 ideal_points。
    
    # 簡化計算：只進行平面擬合 (更健壯的方法請參考 OpenCV 相機校準文檔)
    
    # 假設理想格點是等間距的，擬合一個平面。
    # 找到四個角點的實際位置，用來計算 Homography
    
    # 理想格點在 normalized 座標下的位置 (用於 Homography)
    ideal_norm = objp[0:pattern_size[0]*pattern_size[1]:pattern_size[0]*pattern_size[1]-1:1][:,:2]
    
    # 實際格點在圖像座標下的位置 (四個角點)
    actual_corners = np.array([
        actual_points[0][0], # 左上
        actual_points[pattern_size[0]-1][0], # 右上
        actual_points[pattern_size[0]*(pattern_size[1]-1)][0], # 左下
        actual_points[pattern_size[0]*pattern_size[1]-1][0]  # 右下
    ], dtype='float32')
    
    # 從理想的 2D 點 (格點索引) 到實際的 2D 點 (像素) 計算 Homography
    H, mask = cv2.findHomography(objp[:,:2].astype(np.float32), actual_points.reshape(-1, 2).astype(np.float32))
    
    # 創建理想的格點索引 (作為輸入)
    ideal_grid_indices = objp[:,:2].astype(np.float32).reshape(-1, 1, 2)
    
    # 使用 Homography 變換來計算理想像素位置 (在沒有失真下的位置)
    ideal_points_warped = cv2.perspectiveTransform(ideal_grid_indices, H)
    ideal_points = ideal_points_warped.reshape(-1, 2)

    actual_points = actual_points.reshape(-1, 2)
    
    # 3. 計算失真向量
    distortion_vectors = actual_points - ideal_points
    
    # 4. 計算 TV 失真
    
    # 圖像中心點 (Principal Point approximation)
    cx, cy = w / 2, h / 2
    
    # 徑向距離 (理想) 和徑向失真 (Radial Distortion)
    radial_dist_ideal = np.sqrt((ideal_points[:, 0] - cx)**2 + (ideal_points[:, 1] - cy)**2)
    
    # 計算失真向量在徑向上的分量 (失真在徑向上的投影)
    # 單位徑向向量 (從中心指向理想點)
    radial_unit_vector = (ideal_points - np.array([cx, cy])) / radial_dist_ideal[:, np.newaxis]
    
    # 徑向失真 $d_r$ = 點積 (失真向量 . 單位徑向向量)
    radial_distortion = np.sum(distortion_vectors * radial_unit_vector, axis=1)
    
    # 找出最大的徑向偏差 $|d_r|$
    max_radial_deviation = np.max(np.abs(radial_distortion))
    
    # 找出該最大偏差對應的理想徑向距離 $r_{\max}$
    max_idx = np.argmax(np.abs(radial_distortion))
    r_max = radial_dist_ideal[max_idx]
    
    if r_max == 0:
        # 避免除以零，通常只發生在中心點
        max_tv_distortion = 0.0
    else:
        # TV Distortion (%) = 100 * |dr_max| / r_max
        max_tv_distortion = 100 * max_radial_deviation / r_max
        
    # 數據包裝
    distortion_map_data = {
        'img_size': (w, h),
        'cx_px': cx,
        'cy_px': cy,
        'ideal_points': ideal_points,
        'actual_points': actual_points,
        'vectors': distortion_vectors,
        'radial_distortion': radial_distortion,
        'r_max': r_max,
        'max_idx': max_idx
    }
    
    return max_tv_distortion, distortion_map_data

# --- 2. 視覺化函數 ---

def plot_distortion(img_path, distortion_data, tv_distortion_val, ax):
    """
    在 Matplotlib Axes 上繪製失真場和 TV 判定線。
    """
    
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # Matplotlib 讀取 RGB
    h, w = img.shape[:2]
    
    ideal = distortion_data['ideal_points']
    vectors = distortion_data['vectors']
    cx, cy = distortion_data['cx_px'], distortion_data['cy_px']
    r_max = distortion_data['r_max']
    max_idx = distortion_data['max_idx']
    
    ax.clear()
    ax.imshow(img)
    ax.set_title(f"Geometric Distortion Map & TV Distortion ({tv_distortion_val:.3f}%)", fontsize=10)
    
    # 繪製失真場向量 (Quiver Plot)
    # U, V 是向量的 X, Y 分量
    U = vectors[:, 0]
    V = vectors[:, 1]
    
    # 繪製向量，顏色深度表示向量大小
    vector_magnitudes = np.sqrt(U**2 + V**2)
    
    Q = ax.quiver(
        ideal[:, 0], ideal[:, 1], U, V, 
        vector_magnitudes, # 用於顏色映射
        angles='xy', scale_units='xy', scale=1, 
        cmap='jet', width=0.005, headwidth=5, headlength=7, alpha=0.8
    )
    
    # 繪製中心點
    ax.plot(cx, cy, 'ro', markersize=5, label='Image Center')
    
    # 繪製 TV 判定線：以 r_max 為半徑的圓
    # 該圓通過最大徑向失真點的理想位置
    if r_max > 0:
        # 繪製 TV 失真判定圓
        circle = plt.Circle((cx, cy), r_max, color='r', fill=False, linestyle='--', linewidth=1.5, label=f'TV Max Radius ({r_max:.1f} px)')
        ax.add_artist(circle)
        
        # 標記最大失真點
        ax.plot(ideal[max_idx, 0], ideal[max_idx, 1], 'co', markersize=8, label='Max Distortion Point')
    
    ax.legend(fontsize=7, loc='lower left')
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0) # 圖像座標系 Y 軸反轉
    ax.set_aspect('equal', adjustable='box')
    ax.tick_params(labelsize=8)
    ax.figure.canvas.draw_idle()

# --- 3. GUI 介面類別 ---

class DistortionAnalyzerApp:
    def __init__(self, master):
        self.master = master
        master.title("光學幾何失真分析器 (Geometric Distortion Analyzer)")

        self.img_path = None
        self.tv_distortion = None
        self.distortion_map_data = None
        self.current_image = None
        
        # 設置參數
        self.pattern_cols = tk.IntVar(value=9)
        self.pattern_rows = tk.IntVar(value=6)
        self.square_size_mm = tk.DoubleVar(value=10.0) # 僅用於報告輸出
        
        # 初始化介面
        self.create_widgets()

    def create_widgets(self):
        # 頂部控制面板
        control_frame = ttk.Frame(self.master, padding="10")
        control_frame.pack(fill='x')

        ttk.Label(control_frame, text="格點尺寸 (Cols x Rows):").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Entry(control_frame, textvariable=self.pattern_cols, width=5).grid(row=0, column=1, padx=2, pady=5)
        ttk.Label(control_frame, text="x").grid(row=0, column=2, padx=2, pady=5)
        ttk.Entry(control_frame, textvariable=self.pattern_rows, width=5).grid(row=0, column=3, padx=2, pady=5)

        ttk.Label(control_frame, text="單元格大小 (mm):").grid(row=0, column=4, padx=5, pady=5, sticky='w')
        ttk.Entry(control_frame, textvariable=self.square_size_mm, width=8).grid(row=0, column=5, padx=2, pady=5)

        # 按鈕
        ttk.Button(control_frame, text="開啟圖檔", command=self.open_file).grid(row=0, column=6, padx=10, pady=5)
        self.process_button = ttk.Button(control_frame, text="計算並繪圖", command=self.process_image, state=tk.DISABLED)
        self.process_button.grid(row=0, column=7, padx=10, pady=5)
        self.report_button = ttk.Button(control_frame, text="輸出報表", command=self.output_report, state=tk.DISABLED)
        self.report_button.grid(row=0, column=8, padx=10, pady=5)
        
        # 底部顯示區域
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 左側: 圖像預覽
        preview_frame = ttk.LabelFrame(main_frame, text="原始圖像預覽", padding="5")
        preview_frame.pack(side=tk.LEFT, fill='y', padx=5)
        self.image_label = ttk.Label(preview_frame)
        self.image_label.pack(padx=5, pady=5)
        
        # 右側: Matplotlib 繪圖區
        plot_frame = ttk.LabelFrame(main_frame, text="失真圖視覺化", padding="5")
        plot_frame.pack(side=tk.RIGHT, fill='both', expand=True, padx=5, pady=5)
        
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.ax.axis('off') # 初始不顯示軸
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        # 狀態欄
        self.status_bar = ttk.Label(self.master, text="等待開啟圖檔...", relief=tk.SUNKEN, anchor='w')
        self.status_bar.pack(side=tk.BOTTOM, fill='x')

    def open_file(self):
        # 支援的格式
        f_types = [('Image Files', '*.png;*.jpg;*.bmp;*.jpeg')]
        self.img_path = filedialog.askopenfilename(filetypes=f_types)
        
        if self.img_path:
            self.status_bar.config(text=f"已載入: {self.img_path}")
            self.process_button.config(state=tk.NORMAL)
            self.report_button.config(state=tk.DISABLED)
            
            # 顯示預覽圖 (縮放)
            img_pil = Image.open(self.img_path)
            img_pil.thumbnail((250, 250)) # 縮略圖大小
            self.current_image = ImageTk.PhotoImage(img_pil)
            self.image_label.config(image=self.current_image)
            self.master.update()

    def process_image(self):
        if not self.img_path:
            messagebox.showerror("錯誤", "請先選擇圖檔。")
            return
            
        try:
            cols = self.pattern_cols.get()
            rows = self.pattern_rows.get()
            sq_size = self.square_size_mm.get()
            
            self.status_bar.config(text="正在計算失真場和 TV 失真...")
            
            # 執行核心計算
            self.tv_distortion, self.distortion_map_data = calculate_distortion(
                self.img_path, (cols, rows), sq_size
            )
            
            # 繪製結果
            plot_distortion(self.img_path, self.distortion_map_data, self.tv_distortion, self.ax)
            
            self.status_bar.config(text=f"計算完成! TV Distortion: {self.tv_distortion:.3f}%")
            self.report_button.config(state=tk.NORMAL)
            
        except FileNotFoundError as e:
            messagebox.showerror("文件錯誤", str(e))
        except ValueError as e:
            messagebox.showerror("格點檢測錯誤", str(e))
        except Exception as e:
            messagebox.showerror("運行時錯誤", f"發生未知錯誤: {e}")
            self.status_bar.config(text="計算失敗。")

    def output_report(self):
        if self.tv_distortion is None:
            messagebox.showwarning("警告", "請先執行計算。")
            return
            
        report_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')])
        
        if report_path:
            try:
                # 提取關鍵數據
                w, h = self.distortion_map_data['img_size']
                cx, cy = self.distortion_map_data['cx_px'], self.distortion_map_data['cy_px']
                r_max = self.distortion_map_data['r_max']
                max_rad_dev = self.tv_distortion * r_max / 100 # 最大徑向偏差 (像素)
                
                # 寫入報告
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write("========== 光學幾何失真分析報告 ==========\n")
                    f.write(f"報告日期: {self.master.winfo_id()}\n") # 使用一個 ID 或時間戳
                    f.write(f"分析文件: {self.img_path}\n")
                    f.write("-" * 50 + "\n")
                    
                    f.write("--- 1. 輸入參數 ---\n")
                    f.write(f"格點尺寸: {self.pattern_cols.get()} x {self.pattern_rows.get()} 內角點\n")
                    f.write(f"單元格大小: {self.square_size_mm.get():.2f} mm\n")
                    f.write(f"圖像尺寸: {w} x {h} 像素\n")
                    f.write(f"近似中心點: ({cx:.1f}, {cy:.1f}) 像素\n")
                    f.write("-" * 50 + "\n")
                    
                    f.write("--- 2. TV 失真結果 ---\n")
                    f.write(f"** TV 失真值: {self.tv_distortion:.3f} % **\n")
                    f.write(f"最大徑向偏差: {max_rad_dev:.3f} 像素\n")
                    f.write(f"最大偏差點的理想徑向距離: {r_max:.1f} 像素\n")
                    f.write("\n")
                    
                    f.write("--- 3. 原始失真數據 (部分前10點) ---\n")
                    f.write("理想位置(X, Y) | 實際位置(X, Y) | 失真向量(dX, dY) | 徑向失真(dr)\n")
                    f.write("-" * 80 + "\n")
                    
                    ideal = self.distortion_map_data['ideal_points']
                    actual = self.distortion_map_data['actual_points']
                    vectors = self.distortion_map_data['vectors']
                    radial_dist = self.distortion_map_data['radial_distortion']
                    
                    for i in range(min(10, len(ideal))):
                        f.write(
                            f"({ideal[i, 0]:.2f}, {ideal[i, 1]:.2f}) | "
                            f"({actual[i, 0]:.2f}, {actual[i, 1]:.2f}) | "
                            f"({vectors[i, 0]:.3f}, {vectors[i, 1]:.3f}) | "
                            f"{radial_dist[i]:.3f}\n"
                        )
                    f.write("...\n")
                    f.write("-" * 50 + "\n")
                    
                    f.write("========== 報告結束 ==========\n")

                messagebox.showinfo("成功", f"報告已保存至: {report_path}")
            except Exception as e:
                messagebox.showerror("寫入錯誤", f"無法寫入文件: {e}")

# --- 4. 運行程式 ---

if __name__ == '__main__':
    root = tk.Tk()
    # 設置主題，使介面更現代
    style = ttk.Style(root)
    style.theme_use('clam')
    app = DistortionAnalyzerApp(root)
    root.mainloop()