"""
程式名稱: Interactive Lens Refraction Simulator (Snell's Law)
作者: Sam 影像處理小幫手
描述: 本程式基於司乃耳定律 (Snell's Law)，透過 Tkinter 視覺化介面與 Matplotlib 即時繪製，
      提供互動式的透鏡光路追蹤與幾何光學學習工具。

光學原理:
  - 司乃耳定律: n1 * sin(theta1) = n2 * sin(theta2)
  - 向量形式折射公式:
    v_refract = (n1/n2) * v_in + [(n1/n2)*cos(theta1) - sqrt(1 - (n1/n2)^2 * (1 - cos(theta1)^2))] * N
"""

import math
import tkinter as tk
from tkinter import ttk
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

# 設定 Matplotlib 支援中文顯示
matplotlib.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'Arial']
matplotlib.rcParams['axes.unicode_minus'] = False


class LensRefractionSimulator:

  def __init__(self, root):
    self.root = root
    self.root.title("司乃耳定律與透鏡光路互動學習系統")
    self.root.geometry("1100x700")

    # ------------------------------------------------------------------
    # 預設光學與幾何參數
    # ------------------------------------------------------------------
    self.n_air = 1.0  # 空氣折射率 (n1)
    self.n_glass = 1.5168  # 預設 BK7 玻璃折射率 (n2)
    self.r1 = 100.0  # 前曲率半徑 (R1, 正值為凸面)
    self.r2 = -100.0  # 後曲率半徑 (R2, 負值為凸面)
    self.lens_thickness = 30.0  # 透鏡中心厚度 (mm)
    self.num_rays = 7  # 平行入射光線數量
    self.ray_spacing = 8.0  # 光線間距 (mm)

    # [擴充預留] 色散參數 (Dispersion / Cauchy Equation coefficients)
    # self.enable_dispersion = False
    # self.wavelengths = {'R': 656.3, 'G': 587.6, 'B': 486.1} # nm
    # self.n_glass_rgb = {'R': 1.514, 'G': 1.5168, 'B': 1.522}

    # [擴充預留] 非球面修正參數 (Aspheric coefficients: k, A4, A6...)
    # self.enable_aspheric = False
    # self.k_conic = 0.0

    # 初始化 UI 與 繪圖區域
    self._setup_ui()
    self.update_simulation()

  def _setup_ui(self):
    """建立 Tkinter 使用者介面配置"""
    # 主容器: 左側為控制面板，右側為繪圖區
    control_frame = ttk.LabelFrame(self.root, text="光學參數設定", padding=15)
    control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

    plot_frame = ttk.Frame(self.root)
    plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    # ------------------------------------------------------------------
    # 控制項：材質選擇 (折射率 n2)
    # ------------------------------------------------------------------
    ttk.Label(control_frame, text="1. 選擇鏡片材質 (n2):").pack(
        anchor=tk.W, pady=(0, 2)
    )
    self.material_combobox = ttk.Combobox(
        control_frame,
        state="readonly",
        values=[
            "Crown Glass (BK7) - n=1.517",
            "Flint Glass (F2) - n=1.620",
            "Plastic (PMMA) - n=1.492",
            "Diamond - n=2.417",
            "Custom (自訂)",
        ],
    )
    self.material_combobox.current(0)
    self.material_combobox.pack(fill=tk.X, pady=(0, 10))
    self.material_combobox.bind(
        "<<ComboboxSelected>>", self._on_material_change
    )

    # 數值滑桿：自訂折射率
    ttk.Label(control_frame, text="介面折射率 (n2):").pack(anchor=tk.W)
    self.slider_n2 = ttk.Scale(
        control_frame,
        from_=1.1,
        to=2.5,
        value=1.5168,
        command=lambda e: self.update_simulation(),
    )
    self.slider_n2.pack(fill=tk.X, pady=(0, 15))

    # ------------------------------------------------------------------
    # 控制項：透鏡曲率 (R1, R2)
    # ------------------------------------------------------------------
    ttk.Label(control_frame, text="2. 前曲率半徑 R1 (mm):").pack(anchor=tk.W)
    self.slider_r1 = ttk.Scale(
        control_frame,
        from_=30,
        to=200,
        value=100,
        command=lambda e: self.update_simulation(),
    )
    self.slider_r1.pack(fill=tk.X, pady=(0, 10))

    ttk.Label(control_frame, text="3. 後曲率半徑 R2 (mm):").pack(anchor=tk.W)
    self.slider_r2 = ttk.Scale(
        control_frame,
        from_=-200,
        to=-30,
        value=-100,
        command=lambda e: self.update_simulation(),
    )
    self.slider_r2.pack(fill=tk.X, pady=(0, 15))

    # ------------------------------------------------------------------
    # 控制項：光線設定
    # ------------------------------------------------------------------
    ttk.Label(control_frame, text="4. 入射平行光束數量:").pack(anchor=tk.W)
    self.slider_rays = ttk.Scale(
        control_frame,
        from_=1,
        to=15,
        value=7,
        command=lambda e: self.update_simulation(),
    )
    self.slider_rays.pack(fill=tk.X, pady=(0, 15))

    # ------------------------------------------------------------------
    # 資訊顯示面板
    # ------------------------------------------------------------------
    self.info_label = ttk.Label(
        control_frame,
        text="",
        font=("Consolas", 9),
        justify=tk.LEFT,
        relief=tk.SUNKEN,
        padding=5,
    )
    self.info_label.pack(fill=tk.X, pady=(10, 0))

    # [擴充預留] 進階功能按鈕區
    # self._setup_extension_ui(control_frame)

    # ------------------------------------------------------------------
    # Matplotlib 畫布內嵌
    # ------------------------------------------------------------------
    self.fig = Figure(figsize=(7, 5), dpi=100)
    self.ax = self.fig.add_subplot(111)
    self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
    self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

  def _on_material_change(self, event):
    """材質切換事件處理"""
    mat = self.material_combobox.get()
    if "BK7" in mat:
      self.slider_n2.set(1.5168)
    elif "F2" in mat:
      self.slider_n2.set(1.6200)
    elif "PMMA" in mat:
      self.slider_n2.set(1.4920)
    elif "Diamond" in mat:
      self.slider_n2.set(2.4170)
    self.update_simulation()

  def _snell_refract_vector(self, ray_dir, normal, n1, n2):
    """基於司乃耳定律 (Snell's Law) 的三維/二維向量折射計算

    :param ray_dir: 入射光線單位向量 (2D)
    :param normal: 界面法線單位向量 (2D, 指向入射介質或依幾何定義)
    :param n1: 入射介質折射率
    :param n2: 折射介質折射率
    :return: (refracted_dir, is_total_reflection) 折射光線單位向量與全反射標記
    """
    eta = n1 / n2
    cos_i = -np.dot(normal, ray_dir)

    # 若法線方向與入射相反，修正法線方向
    if cos_i < 0:
      normal = -normal
      cos_i = -cos_i

    sin2_t = eta**2 * (1.0 - cos_i**2)

    # 判斷是否發生全反射 (Total Internal Reflection)
    if sin2_t > 1.0:
      # 全反射狀況，返還反射向量
      reflect_dir = ray_dir + 2.0 * cos_i * normal
      return reflect_dir, True

    cos_t = math.sqrt(1.0 - sin2_t)
    refract_dir = eta * ray_dir + (eta * cos_i - cos_t) * normal
    return refract_dir / np.linalg.norm(refract_dir), False

  def update_simulation(self):
    """執行光路追蹤演算法並更新圖表"""
    # 讀取介面參數
    n2 = self.slider_n2.get()
    r1 = self.slider_r1.get()
    r2 = self.slider_r2.get()
    num_rays = int(self.slider_rays.get())

    self.ax.clear()

    # 1. 幾何定位：定義前曲面中心與後曲面中心
    c1_x = r1
    c2_x = self.lens_thickness + r2

    # 繪製透鏡外廓 (畫出雙曲面透鏡)
    y_vals = np.linspace(-40, 40, 200)

    # 前曲面 X 坐標: (x - c1_x)^2 + y^2 = R1^2
    x_surf1 = []
    for y in y_vals:
      if abs(y) < abs(r1):
        x = c1_x - np.sign(r1) * math.sqrt(r1**2 - y**2)
      else:
        x = 0
      x_surf1.append(x)

    # 後曲面 X 坐標: (x - c2_x)^2 + y^2 = R2^2
    x_surf2 = []
    for y in y_vals:
      if abs(y) < abs(r2):
        x = c2_x - np.sign(r2) * math.sqrt(r2**2 - y**2)
      else:
        x = self.lens_thickness
      x_surf2.append(x)

    # 填滿與繪製透鏡主體
    self.ax.plot(x_surf1, y_vals, "b-", linewidth=1.5, label="前透鏡界面 (R1)")
    self.ax.plot(x_surf2, y_vals, "b-", linewidth=1.5, label="後透鏡界面 (R2)")
    self.ax.fill_betweenx(
        y_vals, x_surf1, x_surf2, color="skyblue", alpha=0.3
    )

    # 2. 光路追蹤 (Ray Tracing Pipeline)
    ray_heights = np.linspace(
        -self.ray_spacing * (num_rays - 1) / 2,
        self.ray_spacing * (num_rays - 1) / 2,
        num_rays,
    )

    focus_x_list = []  # 收集焦點位置

    for y0 in ray_heights:
      # --- 階段 A: 空氣 -> 第一介面 (前曲面) ---
      p0 = np.array([-50.0, y0])
      ray_dir0 = np.array([1.0, 0.0])  # 平行光入射

      # 計算與曲面 1 的交點
      if abs(y0) >= abs(r1):
        continue  # 超過透鏡孔徑，忽略
      x1 = c1_x - np.sign(r1) * math.sqrt(r1**2 - y0**2)
      p1 = np.array([x1, y0])

      # 前曲面法線向量 (指向圓心外部)
      normal1 = (p1 - np.array([c1_x, 0.0])) / r1

      # 第一階段司乃耳折射 (空氣 n1 -> 玻璃 n2)
      ray_dir1, tir1 = self._snell_refract_vector(
          ray_dir0, normal1, self.n_air, n2
      )

      # --- 階段 B: 玻璃內部 -> 第二介面 (後曲面) ---
      # 解二次方程式求光線與球面 2 的交點 P2
      # 直線: P = P1 + t * ray_dir1 ; 圓心: (c2_x, 0)
      oc = p1 - np.array([c2_x, 0.0])
      a = np.dot(ray_dir1, ray_dir1)
      b = 2.0 * np.dot(oc, ray_dir1)
      c = np.dot(oc, oc) - r2**2
      discriminant = b**2 - 4 * a * c

      if discriminant < 0:
        continue  # 光線未撞擊後曲面

      t = (-b + np.sign(r2) * math.sqrt(discriminant)) / (2 * a)
      p2 = p1 + t * ray_dir1

      # 後曲面法線向量
      normal2 = (p2 - np.array([c2_x, 0.0])) / r2

      # 第二階段司乃耳折射 (玻璃 n2 -> 空氣 n1)
      ray_dir2, tir2 = self._snell_refract_vector(
          ray_dir1, normal2, n2, self.n_air
      )

      # --- 階段 C: 出射光線路徑與焦點估計 ---
      p3 = p2 + ray_dir2 * 120.0  # 延伸射出光線

      # 計算該光線與光軸 (Y=0) 的交點 (焦距估計)
      if abs(ray_dir2[1]) > 1e-5:
        t_axis = -p2[1] / ray_dir2[1]
        x_focus = p2[0] + t_axis * ray_dir2[0]
        if x_focus > p2[0]:  # 焦點在透鏡後方
          focus_x_list.append(x_focus)

      # 繪製單條光線路徑 (入射 -> 內部 -> 出射)
      self.ax.plot(
          [p0[0], p1[0], p2[0], p3[0]],
          [p0[1], p1[1], p2[1], p3[1]],
          "r-",
          alpha=0.7,
          linewidth=1.2,
      )

    # 3. 造鏡者公式 (Lensmaker's Equation) 理論薄透鏡焦距算式:
    # 1/f = (n - 1) * [ 1/R1 - 1/R2 + ((n-1)*d)/(n*R1*R2) ]
    try:
      inv_f = (n2 - 1.0) * (
          1.0 / r1 - 1.0 / r2 + ((n2 - 1.0) * self.lens_thickness) / (n2 * r1 * r2)
      )
      f_theory = 1.0 / inv_f if inv_f != 0 else float("inf")
    except ZeroDivisionError:
      f_theory = float("inf")

    avg_focus_x = np.mean(focus_x_list) if focus_x_list else 0.0

    # 圖表裝飾與資訊更新
    self.ax.axhline(0, color="black", linestyle="--", alpha=0.5, label="光軸 (Optical Axis)")
    self.ax.set_xlim(-60, 180)
    self.ax.set_ylim(-50, 50)
    self.ax.set_aspect("equal")
    self.ax.set_title("司乃耳定律 (Snell's Law) 透鏡折射與光路追蹤模擬")
    self.ax.set_xlabel("光軸位置 X (mm)")
    self.ax.set_ylabel("高度 Y (mm)")
    self.ax.legend(loc="upper right", fontsize=8)
    self.ax.grid(True, linestyle=":", alpha=0.6)

    self.canvas.draw()

    # 更新右下角資訊
    self.info_label.config(
        text=f"【光學計算數據】\n"
        f"介質折射率 n2: {n2:.4f}\n"
        f"前曲率 R1: {r1:.1f} mm | 後曲率 R2: {r2:.1f} mm\n"
        f"理論焦距 (Lensmaker): {f_theory:.2f} mm\n"
        f"實測近軸焦點位置: {avg_focus_x:.2f} mm"
    )

  # ==================================================================
  # [預留擴充功能槽] 供未來擴充進階影像與光學演算法
  # ==================================================================
  def _extension_simulate_chromatic_aberration(self):
    """[預留] 模擬縱向色差 (Chromatic Aberration)

    實作思路: 分別針對 R (656nm)、G (587nm)、B (486nm) 的折射率做 Ray Tracing，
    並在圖上畫出紅、綠、藍三色光線匯聚在不同焦點的現象。
    """
    pass

  def _extension_simulate_spherical_aberration(self):
    """[預留] 計算並繪製球面像差 (Spherical Aberration) 曲線

    實作思路: 計算不同高度 (y0) 的入射光線其焦點 X 座標的偏移量 (Delta F)。
    """
    pass

  def _extension_aspheric_surface(self, y, r, k, a4=0, a6=0):
    """[預留] 非球面 (Aspheric Surface) 幾何表面計算方程式

    x(y) = (y^2 / r) / (1 + sqrt(1 - (1+k)*(y/r)^2)) + A4*y^4 + A6*y^6
    """
    pass


# ==================================================================
# 主程式進入點
# ==================================================================
if __name__ == "__main__":
  root = tk.Tk()
  app = LensRefractionSimulator(root)
  root.mainloop()
#====================================================================================================#
#系統功能與特色重點
#1. 向量化司乃耳定律引擎 (_snell_refract_vector)：
#   採用 2D 向量矩陣運算，不僅能正確處理正向折射，還自動支援光線從高折射率介質射出時的全反射（Total Internal Reflection）邊界情況。
#2. 真實厚透鏡雙界面追蹤：
#   光線進入第一曲面（空氣 $\to$ 玻璃）發生一次偏折，穿過透鏡內部後撞擊第二曲面（玻璃 $\to$ 空氣）發生第二次偏折，精準呈現光學系統的實況。
#3. 理論與實測焦點對照：
#   計算並顯示造鏡者公式（Lensmaker's Equation）算出的理論焦距，同時透過光路追蹤求出真實光線與光軸的實際焦點，可直觀觀察到「球面像差」帶來的焦點不重合現象。
#4. 預留擴充模組介面：
#   程式碼中預留了 _extension_simulate_chromatic_aberration（色差）與 _extension_aspheric_surface（非球面方程式）等函式草稿，方便其他團隊成員或學習者直接加入高階光學計算。
#====================================================================================================#