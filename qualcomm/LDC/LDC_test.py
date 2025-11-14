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
    計算幾何失真場和 TV Distortion 值（穩健版）。
    """
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"無法讀取文件: {img_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]

    cols, rows = pattern_size
    # 1. 建立物體點（以實際單位 mm）
    objp = np.zeros((cols * rows, 3), np.float32)
    objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2) * square_size_mm

    # 2. 找角點
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE
    ret, corners = cv2.findChessboardCorners(gray, (cols, rows), flags)
    if not ret:
        raise ValueError("未能成功檢測到足夠的格點角點。請檢查圖像和 '格點尺寸' 設置。")

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
    imgpoints = corners.reshape(-1, 1, 2).astype(np.float32)

    # 嘗試使用 calibrateCamera 計算相機參數，然後以 zero distortion 投影取得 ideal_points
    ideal_points = None
    try:
        objpoints_list = [objp.astype(np.float32)]
        imgpoints_list = [imgpoints]
        retval, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            objpoints_list, imgpoints_list, (w, h), None, None
        )
        if retval and len(rvecs) > 0:
            zero_dist = np.zeros_like(dist_coeffs)
            proj, _ = cv2.projectPoints(objp.astype(np.float32), rvecs[0], tvecs[0], camera_matrix, zero_dist)
            ideal_points = proj.reshape(-1, 2)
    except Exception:
        ideal_points = None

    # fallback: 若 calibrateCamera 失敗，使用 Homography 近似
    if ideal_points is None:
        H, mask = cv2.findHomography(objp[:, :2].astype(np.float32), imgpoints.reshape(-1, 2).astype(np.float32))
        ideal_pts_warped = cv2.perspectiveTransform(objp[:, :2].astype(np.float32).reshape(-1, 1, 2), H)
        ideal_points = ideal_pts_warped.reshape(-1, 2)

    actual_points = imgpoints.reshape(-1, 2)

    # 計算失真向量與 TV 指標
    distortion_vectors = actual_points - ideal_points
    cx, cy = w / 2.0, h / 2.0
    radial_dist_ideal = np.sqrt((ideal_points[:, 0] - cx) ** 2 + (ideal_points[:, 1] - cy) ** 2)

    # 加入 epsilon 保護以避免除以零
    eps = 1e-8
    radial_unit_vector = np.zeros_like(distortion_vectors)
    valid_mask = radial_dist_ideal > eps
    if np.any(valid_mask):
        radial_unit_vector[valid_mask] = (ideal_points[valid_mask] - np.array([cx, cy])) / radial_dist_ideal[valid_mask][:, None]

    radial_distortion = np.sum(distortion_vectors * radial_unit_vector, axis=1)
    max_radial_deviation = np.max(np.abs(radial_distortion)) if radial_distortion.size > 0 else 0.0
    max_idx = int(np.argmax(np.abs(radial_distortion))) if radial_distortion.size > 0 else 0
    r_max = radial_dist_ideal[max_idx] if radial_dist_ideal.size > 0 else 0.0

    if r_max == 0:
        max_tv_distortion = 0.0
    else:
        max_tv_distortion = 100.0 * max_radial_deviation / r_max

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


def plot_distortion(img_path, distortion_data, tv_distortion_val, ax):
    """在給定的 matplotlib Axes 上繪製失真向量與 TV 判定圓。"""
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"無法讀取文件: {img_path}")

    w, h = distortion_data['img_size']
    ideal = distortion_data['ideal_points']
    vectors = distortion_data['vectors']
    cx = distortion_data['cx_px']
    cy = distortion_data['cy_px']
    r_max = distortion_data['r_max']
    max_idx = int(distortion_data['max_idx'])

    U = vectors[:, 0]
    V = vectors[:, 1]
    vector_magnitudes = np.sqrt(U ** 2 + V ** 2)

    ax.clear()
    # BGR -> RGB for plotting
    ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    ax.set_title(f"Geometric Distortion Map & TV Distortion ({tv_distortion_val:.3f}%)", fontsize=10)

    ax.quiver(
        ideal[:, 0], ideal[:, 1], U, V,
        vector_magnitudes,
        angles='xy', scale_units='xy', scale=1,
        cmap='jet', width=0.005, headwidth=5, headlength=7, alpha=0.8
    )

    ax.plot(cx, cy, 'ro', markersize=5, label='Image Center')

    if r_max > 0:
        circle = plt.Circle((cx, cy), r_max, color='r', fill=False, linestyle='--', linewidth=1.5, label=f'TV Max Radius ({r_max:.1f} px)')
        ax.add_artist(circle)
        ax.plot(ideal[max_idx, 0], ideal[max_idx, 1], 'co', markersize=8, label='Max Distortion Point')

    ax.legend(fontsize=7, loc='lower left')
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
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