import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.patches import Rectangle
import tkinter as tk
from tkinter import scrolledtext
from skimage.color import rgb2lab
import threading
import math

# ==========================================
# Sam 影像處理小幫手 - 互動式 CCM 調整工具 (升級版)
# ==========================================

def apply_ccm(image_rgb, ccm_matrix):
    """
    對影像應用顏色校正矩陣 (CCM)。

    Args:
        image_rgb: 輸入的 RGB 影像 (H, W, 3)，數值範圍 0-255 (uint8) 或 0.0-1.0 (float)。
        ccm_matrix: 3x3 的變換矩陣 (numpy array)。

    Returns:
        校正後的 RGB 影像 (uint8)。
    """
    img_float = image_rgb.astype(np.float32)
    corrected_float = cv2.transform(img_float, ccm_matrix)
    corrected_clipped = np.clip(corrected_float, 0, 255).astype(np.uint8)
    return corrected_clipped


# ==========================================
# 24色色彩卡生成函數 (ISO/IEC 17321-1)
# ==========================================
def create_24_color_chart_with_labels():
    """
    產生標準 24 色色彩卡 (Macbeth ColorChecker)，並返回顏色資訊。
    
    Returns:
        BGR 格式的色彩卡影像 (uint8) 與 RGB 顏色列表。
        使用 sRGB 色卡資訊
    """
    colors_rgb = [
        # 第 1 行
        (115, 82, 68),      # 1. Deep Skin
        (194, 150, 130),    # 2. Light Skin
        (98, 122, 157),     # 3. Blue Sky
        (87, 108, 67),      # 4. Foliage
        (133, 128, 177),    # 5. Blue Flower
        (103, 189, 170),    # 6. Bluish Green
        
        # 第 2 行
        (214, 126, 44),     # 7. Orange
        (80, 91, 166),      # 8. Purplish-blue
        (193, 90, 99),      # 9. Moderate-red
        (94, 60, 108),      # 10. Purple
        (157, 188, 64),     # 11. Yellow-green
        (224, 163, 46),     # 12. Orange-yellow
        
        # 第 3 行
        (56, 61, 150),      # 13. Blue
        (70, 148, 73),      # 14. Green
        (175, 54, 60),      # 15. Red
        (231, 199, 31),     # 16. Yellow
        (187, 86, 149),     # 17. Magenta
        (8, 133, 161),      # 18. Cyan
        
        # 第 4 行
        (243, 243, 242),    # 19. White (.05*)
        (200, 200, 200),    # 20. Neutral 8 (light gray, .23*)
        (160, 160, 160),    # 21. Neutral 6.5 (gray, .44*)
        (122, 122, 121),    # 22. Neutral 5 (mid gray, .70*)
        (85, 85, 85),       # 23. Neutral 3.5 (dark gray, .1.05*)
        (52, 52, 52),       # 24. Black(1.50*)
    ]      
        
    patch_size = 100
    rows, cols = 4, 6
    height = rows * patch_size
    width = cols * patch_size
    
    img_bgr = np.zeros((height, width, 3), dtype=np.uint8)
    
    for idx, (r, g, b) in enumerate(colors_rgb):
        row = idx // cols
        col = idx % cols
        y1 = row * patch_size
        y2 = y1 + patch_size
        x1 = col * patch_size
        x2 = x1 + patch_size
        img_bgr[y1:y2, x1:x2] = [b, g, r]
    
    return img_bgr , colors_rgb

def get_color_names():
    """獲取24色的名稱"""
    names = [
        "Deep Skin", "Light Skin", "Blue Sky", "Foliage", "Blue Flower", "Bluish Green", 
        "Orange", "Purplish Red", "Moderate-red", "Yellow", "Yellow-green", "Orange-yellow",
        "Blue", "Green", "Red", "Yellow","Magenta", "Cyan", 
        "White", "Neutral 8", "Neutral 6.5", "Neutral 5", "Neutral 3.5", "Black"
    ]
    return names


def rgb_to_lab(rgb_tuple):
    """
    將 RGB (0-255) 轉換為 Lab 色彩空間。
    
    Args:
        rgb_tuple: (R, G, B) 其中值範圍為 0-255
        
    Returns:
        (L, a, b) 其中 L 範圍 0-100, a 和 b 範圍 -128 到 127
    """
    rgb_normalized = np.array(rgb_tuple) / 255.0
    lab = rgb2lab(np.array([[[rgb_normalized[0], rgb_normalized[1], rgb_normalized[2]]]]))
    return lab[0, 0]


# --- 全局變量 ---
global_data = {
    'lab_values': [],
    'color_names': [],
    'text_widget': None,
    'colors_rgb_original': [],  # 保存原始 RGB 顏色
    'current_ccm': np.eye(3),   # 保存當前 CCM 矩陣
    'fig': None,
    'ax': None,
}


def update_lab_display(colors_rgb):
    """計算並更新Lab值顯示"""
    global global_data
    
    global_data['lab_values'] = []
    global_data['color_names'] = get_color_names()
    global_data['colors_rgb_original'] = colors_rgb  # 保存原始顏色
    
    for i, color_rgb in enumerate(colors_rgb):
        lab = rgb_to_lab(color_rgb)
        global_data['lab_values'].append(lab)
    
    update_text_display()


def update_text_display():
    """更新文本框中的Lab值顯示"""
    colors_Lab = [
       # 第 1 行
        (38.02, 11.80, 13.67),      # 1. Deep Skin
        (65.67, 13.67, 16.90),      # 2. Light Skin
        (50.63, 0.37, -21.60),      # 3. Blue Sky
        (43.00, -15.88, 20.45),     # 4. Foliage
        (55.68, 12.76, -25.17),     # 5. Blue Flower
        (70.99, -30.64, 1.54),      # 6. Bluish Green
        
        # 第 2 行
        (61.14, 28.10, 56.13),      # 7. Orange
        (41.12, 17.41, -41.88),     # 8. Purplish-blue
        (51.33, 42.10, 14.89),      # 9. Moderate-red
        (31.10, 24.35, -22.10),     # 10. Purple
        (71.90, -28.10, 56.96),     # 11. Yellow-green
        (71.04, 12.60, 64.92),      # 12. Orange-yellow
        
        # 第 3 行
        (30.35, 26.43, -49.67),     # 13. Blue
        (55.03, -40.14, 32.30),     # 14. Green
        (41.35, 49.30, 24.66),      # 15. Red
        (80.70, -3.66, 77.55),      # 16. Yellow
        (51.14, 48.15, -15.28),     # 17. Magenta
        (51.15, -19.73, -23.37),    # 18. Cyan
        
        # 第 4 行
        (95.82, -0.18, 0.49),       # 19. White (.05*)
        (80.60, -0.00, 0.00),       # 20. Neutral 8 (light gray, .23*)
        (65.87, -0.00, 0.00),       # 21. Neutral 6.5 (gray, .44*)
        (51.19, -0.20, 0.55),       # 22. Neutral 5 (mid gray, .70*)
        (36.15, -0.00, 0.00),       # 23. Neutral 3.5 (dark gray, .1.05*)
        (21.70, -0.00, 0.00),       # 24. Black(1.50*)
    ]

    if global_data['text_widget'] is None:
        return
    
    text_widget = global_data['text_widget']
    text_widget.config(state=tk.NORMAL)
    text_widget.delete('1.0', tk.END)
    
    content = "=" * 75 + "\n"
    content += "24 color - Lab value with CCM Adjusted RGB\n"
    content += "=" * 75 + "\n\n"
    
    # 獲取當前 CCM 矩陣
    current_ccm = global_data['current_ccm'].astype(np.float32)
    
    for i, (lab, name) in enumerate(zip(global_data['lab_values'], global_data['color_names'])):
        lab_org = colors_Lab[i]
        deltaE = math.sqrt(((lab_org[0] - lab[0])**2) + ((lab_org[1] - lab[1])**2) + ((lab_org[2] - lab[2])**2))
        """
        ------------------------------------------
        ΔE	人眼感覺
        < 1	幾乎看不出差異
        1 – 2	非常細微
        2 – 3	仔細看才看得出
        3 – 5	明顯差異
        > 5	明顯色偏
        """
        deltaC_real = math.sqrt((lab[1]**2) + (lab[2]**2))
        deltaC_org = math.sqrt((lab_org[1])**2 + (lab_org[2])**2)
        deltaC = deltaC_real - deltaC_org
        """
        ΔC :
        正值 → 顏色變「更鮮豔」
        負值 → 顏色變「更灰、更淡」
        """
        
        # 動態讀取原始 RGB 值並計算飽和度
        if i < len(global_data['colors_rgb_original']):
            rgb_org = global_data['colors_rgb_original'][i]
            # 計算 CCM 調整後的 RGB 值
            color_float = np.array(rgb_org, dtype=np.float32).reshape(1, 1, 3)
            corrected_color = cv2.transform(color_float, current_ccm)
            corrected_color_clipped = np.clip(corrected_color[0, 0], 0, 255).astype(np.uint8)
            rgb_adjusted = tuple(corrected_color_clipped)
            # 正規化 RGB 值到 0-1 範圍
            r_norm = rgb_adjusted[0] / 255.0
            g_norm = rgb_adjusted[1] / 255.0
            b_norm = rgb_adjusted[2] / 255.0
            
            # 計算飽和度 (HSV 色彩空間中的 S 值)
            rgb_max = max(r_norm, g_norm, b_norm)
            rgb_min = min(r_norm, g_norm, b_norm)
            rgb_delta = rgb_max - rgb_min
            
            if rgb_max == 0:
                sat_value = 0
            else:
                sat_value = (rgb_delta / rgb_max) * 255
        else:
            sat_value = 0
            rgb_adjusted = (0, 0, 0)
            
        content += f"【色塊 #{i+1:2d}】{name:15s}\n"
       # content += f"  原始RGB: ({global_data['colors_rgb_original'][i][0]:3d}, {global_data['colors_rgb_original'][i][1]:3d}, {global_data['colors_rgb_original'][i][2]:3d})  "
       # content += f"調整RGB: ({rgb_adjusted[0]:3d}, {rgb_adjusted[1]:3d}, {rgb_adjusted[2]:3d})\n"
        content += f"  L*: {lab[0]:4.2f}  a*: {lab[1]:4.2f}  b*: {lab[2]:4.2f}  ΔE: {deltaE:4.2f}  ΔC: {deltaC:4.2f}  Sat: {sat_value:4.2f}\n  "
        content += "-" * 75 + "\n"
    text_widget.insert('1.0', content)
    text_widget.config(state=tk.DISABLED)


def create_lab_window():
    """建立顯示Lab值的窗口"""
    root = tk.Tk()
    root.title("24 色色彩卡 Lab 值分析")
    root.geometry("750x850")
    
    title_label = tk.Label(root, text="24 色色彩卡 - L*a*b 色彩空間數據", font=("Consolas", 14, "bold"))
    title_label.pack(pady=10)
    
    text_widget = scrolledtext.ScrolledText(root, width=85, height=45, font=("Courier", 10))
    text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    global_data['text_widget'] = text_widget
    
    # 窗口建立後，立即更新顯示 Lab 值
    update_text_display()
    
    root.mainloop()


# --- 檔案路徑設定 ---
IMAGE_PATH = 'sample.jpg'

# --- 讀取影像或使用 24 色色彩卡 ---
img_bgr = cv2.imread(IMAGE_PATH)

if img_bgr is None:
    print("\n已改用 24 色色彩卡進行演示。\n")
    img_bgr, colors_rgb = create_24_color_chart_with_labels()
else:
    colors_rgb = None

# 將 BGR 轉換為 RGB 以便 Matplotlib 正確顯示和 CCM 計算
img_rgb_original = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

# 計算Lab值並開啟顯示窗口
if colors_rgb:
    update_lab_display(colors_rgb)
    # 在後台執行緒中開啟 Lab 值分析窗口
    lab_thread = threading.Thread(target=create_lab_window, daemon=True)
    lab_thread.start()
    print("24 color blocks Lab value automatically calculated")
    print("已開啟 Lab 分析視窗 (獨立窗口)")
    print()

# --- 初始化 Matplotlib 介面 ---
fig, (ax_original, ax_adjusted) = plt.subplots(1, 2, figsize=(16, 8))
plt.subplots_adjust(left=0.10, right=0.95, bottom=0.50)

# 左邊顯示原始影像
ax_original.imshow(img_rgb_original)
ax_original.set_title("Original Color Chart", fontsize=14, fontweight='bold')
ax_original.axis('off')

# 右邊顯示動態調整影像
img_display = ax_adjusted.imshow(img_rgb_original)
ax_adjusted.set_title("Adjusted Color Chart (CCM)", fontsize=14, fontweight='bold')
ax_adjusted.axis('off')

# --- 定義初始 CCM 矩陣 ---
initial_ccm = np.array([
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0]
])

# --- 建立滑桿和數值顯示 ---
axcolor = 'lightgoldenrodyellow'
sliders = []
text_entries = []

labels = ['R_r', 'R_g', 'R_b', 'G_r', 'G_g', 'G_b', 'B_r', 'B_g', 'B_b']

for i in range(3):
    for j in range(3):
        idx = i * 3 + j
        
        # 滑桿軸
        sax = plt.axes([0.15 + j * 0.27, 0.32 - i * 0.10, 0.20, 0.03], facecolor=axcolor)
        if idx == 0 :    
            slider = Slider(sax, labels[idx], 0, 2.0, valinit=initial_ccm[i, j], valstep=0.01)
        elif idx == 1 :
            slider = Slider(sax, labels[idx], -1.0, 1.0, valinit=initial_ccm[i, j], valstep=0.01)
        elif idx == 2 :
            slider = Slider(sax, labels[idx], -1.0, 1.0, valinit=initial_ccm[i, j], valstep=0.01)
        elif idx == 3 :
            slider = Slider(sax, labels[idx], -1.0, 1.0, valinit=initial_ccm[i, j], valstep=0.01)
        elif idx == 4 :
            slider = Slider(sax, labels[idx], 0, 2.0, valinit=initial_ccm[i, j], valstep=0.01)    
        elif idx == 5 :
            slider = Slider(sax, labels[idx], -1.0, 1.0, valinit=initial_ccm[i, j], valstep=0.01)  
        elif idx == 6 :
            slider = Slider(sax, labels[idx], -1.0, 1.0, valinit=initial_ccm[i, j], valstep=0.01)   
        elif idx == 7 :
            slider = Slider(sax, labels[idx], -1.0, 1.0, valinit=initial_ccm[i, j], valstep=0.01)  
        elif idx == 8 :
            slider = Slider(sax, labels[idx], 0, 2.0, valinit=initial_ccm[i, j], valstep=0.01)                 
        else :
            slider = Slider(sax, labels[idx], -1.0, 1.0, valinit=initial_ccm[i, j], valstep=0.01)
        print(idx)
        sliders.append(slider)
        
        # 數值顯示文本框軸
        tax = plt.axes([0.36 + j * 0.27, 0.32 - i * 0.10, 0.03, 0.1])
        tax.axis('off')
        text_box = plt.text(0.5, 0.5, f'{initial_ccm[i, j]:.2f}', 
                           ha='center', va='center', fontsize=11, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='black', linewidth=1.5),
                           transform=tax.transAxes)
        text_entries.append(text_box)

# --- 建立 ΔE 統計資訊顯示框 ---
# 平均 ΔE 顯示框
avg_deltaE_ax = plt.axes([0.15, 0.42, 0.25, 0.04])
avg_deltaE_ax.axis('off')
avg_deltaE_box = plt.text(0.5, 0.5, 'Avg ΔE: 0.00', 
                          ha='center', va='center', fontsize=12, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', edgecolor='blue', linewidth=2),
                          transform=avg_deltaE_ax.transAxes)

# 最大 ΔE 顯示框
max_deltaE_ax = plt.axes([0.30, 0.42, 0.25, 0.04])
max_deltaE_ax.axis('off')
max_deltaE_box = plt.text(0.5, 0.5, 'Max ΔE: 0.00', 
                          ha='center', va='center', fontsize=12, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', edgecolor='red', linewidth=2),
                          transform=max_deltaE_ax.transAxes)

# --- 建立 ΔC 統計資訊顯示框 ---
# 平均 ΔC 顯示框
avg_deltaC_ax = plt.axes([0.45, 0.42, 0.25, 0.04])
avg_deltaC_ax.axis('off')
avg_deltaC_box = plt.text(0.5, 0.5, 'Avg ΔC: 0.00', 
                          ha='center', va='center', fontsize=12, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', edgecolor='blue', linewidth=2),
                          transform=avg_deltaC_ax.transAxes)

# 最大 ΔC 顯示框
max_deltaC_ax = plt.axes([0.60, 0.42, 0.25, 0.04])
max_deltaC_ax.axis('off')
max_deltaC_box = plt.text(0.5, 0.5, 'Max ΔC: 0.00', 
                          ha='center', va='center', fontsize=12, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', edgecolor='red', linewidth=2),
                          transform=max_deltaC_ax.transAxes)

# 平均HSV
avg_saturation_ax = plt.axes([0.75, 0.42, 0.25, 0.04])
avg_saturation_ax.axis('off')
avg_saturation_box = plt.text(0.5, 0.5, 'Avg SAT: 0.00', 
                          ha='center', va='center', fontsize=12, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', edgecolor='red', linewidth=2),
                          transform=avg_saturation_ax.transAxes)

# --- 更新函數 ---
def update(val):
    """滑桿更新回調"""
    global global_data
    
    new_ccm = np.array([
        [sliders[0].val, sliders[1].val, sliders[2].val],
        [sliders[3].val, sliders[4].val, sliders[5].val],
        [sliders[6].val, sliders[7].val, sliders[8].val]
    ])
    
    # 保存當前 CCM 矩陣到全局變量
    global_data['current_ccm'] = new_ccm.copy()
    
    # 更新數值顯示
    for idx, text_box in enumerate(text_entries):
        text_box.set_text(f'{sliders[idx].val:.2f}')
    
    # 應用 CCM
    corrected_img = apply_ccm(img_rgb_original, new_ccm)
    img_display.set_data(corrected_img)
    
    # 動態更新 Lab 值
    if global_data['colors_rgb_original']:
        # 重新計算調整後的 RGB 顏色的 Lab 值
        global_data['lab_values'] = []
        ccm_matrix = new_ccm.astype(np.float32)
        
        # 參考色 Lab 值
        colors_Lab = [
           # 第 1 行
            (38.02, 11.80, 13.67),      # 1. Deep Skin
            (65.67, 13.67, 16.90),      # 2. Light Skin
            (50.63, 0.37, -21.60),      # 3. Blue Sky
            (43.00, -15.88, 20.45),     # 4. Foliage
            (55.68, 12.76, -25.17),     # 5. Blue Flower
            (70.99, -30.64, 1.54),      # 6. Bluish Green
            
            # 第 2 行
            (61.14, 28.10, 56.13),      # 7. Orange
            (41.12, 17.41, -41.88),     # 8. Purplish-blue
            (51.33, 42.10, 14.89),      # 9. Moderate-red
            (31.10, 24.35, -22.10),     # 10. Purple
            (71.90, -28.10, 56.96),     # 11. Yellow-green
            (71.04, 12.60, 64.92),      # 12. Orange-yellow
            
            # 第 3 行
            (30.35, 26.43, -49.67),     # 13. Blue
            (55.03, -40.14, 32.30),     # 14. Green
            (41.35, 49.30, 24.66),      # 15. Red
            (80.70, -3.66, 77.55),      # 16. Yellow
            (51.14, 48.15, -15.28),     # 17. Magenta
            (51.15, -19.73, -23.37),    # 18. Cyan
            
            # 第 4 行
            (95.82, -0.18, 0.49),       # 19. White (.05*)
            (80.60, -0.00, 0.00),       # 20. Neutral 8 (light gray, .23*)
            (65.87, -0.00, 0.00),       # 21. Neutral 6.5 (gray, .44*)
            (51.19, -0.20, 0.55),       # 22. Neutral 5 (mid gray, .70*)
            (36.15, -0.00, 0.00),       # 23. Neutral 3.5 (dark gray, .1.05*)
            (21.70, -0.00, 0.00),       # 24. Black(1.50*)
        ]
        
        deltaE_values = []
        for idx, color_rgb in enumerate(global_data['colors_rgb_original']):
            # 將 RGB 顏色轉換為 numpy 陣列並應用 CCM
            color_float = np.array(color_rgb, dtype=np.float32).reshape(1, 1, 3)
            corrected_color = cv2.transform(color_float, ccm_matrix)
            corrected_color_clipped = np.clip(corrected_color[0, 0], 0, 255).astype(np.uint8)
            
            # 計算調整後顏色的 Lab 值
            lab = rgb_to_lab(tuple(corrected_color_clipped))
            global_data['lab_values'].append(lab)
            
            # 計算 ΔE
            lab_org = colors_Lab[idx]
            deltaE = math.sqrt(((lab_org[0] - lab[0])**2) + ((lab_org[1] - lab[1])**2) + ((lab_org[2] - lab[2])**2))
            deltaE_values.append(deltaE)
            
        deltaC_values = []
        for idx, color_rgb in enumerate(global_data['colors_rgb_original']):
            # 將 RGB 顏色轉換為 numpy 陣列並應用 CCM
            color_float = np.array(color_rgb, dtype=np.float32).reshape(1, 1, 3)
            corrected_color = cv2.transform(color_float, ccm_matrix)
            corrected_color_clipped = np.clip(corrected_color[0, 0], 0, 255).astype(np.uint8)
            
            # 計算調整後顏色的 Lab 值
            lab = rgb_to_lab(tuple(corrected_color_clipped))
            global_data['lab_values'].append(lab)
            
            # 計算 ΔE
            lab_org = colors_Lab[idx]
            deltaC = math.sqrt(((lab_org[1] - lab[1])**2) + ((lab_org[2] - lab[2])**2))
            deltaC_values.append(deltaC)        
        
        # 計算平均 ΔE 和最大 ΔE
        avg_deltaE = np.mean(deltaE_values)
        max_deltaE = np.max(deltaE_values)
        
        # 計算平均 ΔC 和最大 ΔC
        avg_deltaC = np.mean(deltaC_values)
        max_deltaC = np.max(deltaC_values)
        
        # 計算 24 色卡調整後的飽和度平均值
        saturation_values = []
        for idx, color_rgb in enumerate(global_data['colors_rgb_original']):
            # 將 RGB 顏色轉換為 numpy 陣列並應用 CCM
            color_float = np.array(color_rgb, dtype=np.float32).reshape(1, 1, 3)
            corrected_color = cv2.transform(color_float, ccm_matrix)
            corrected_color_clipped = np.clip(corrected_color[0, 0], 0, 255).astype(np.uint8)
            
            # 正規化調整後的 RGB 值到 0-1 範圍
            r_norm = corrected_color_clipped[0] / 255.0
            g_norm = corrected_color_clipped[1] / 255.0
            b_norm = corrected_color_clipped[2] / 255.0
            
            # 計算飽和度 (HSV 色彩空間中的 S 值)
            rgb_max = max(r_norm, g_norm, b_norm)
            rgb_min = min(r_norm, g_norm, b_norm)
            rgb_delta = rgb_max - rgb_min
            
            if rgb_max == 0:
                sat_value = 0
            else:
                sat_value = (rgb_delta / rgb_max) * 255
            
            saturation_values.append(sat_value)
        
        # 計算平均飽和度
        avg_saturation = np.mean(saturation_values)
        
        # 更新顯示框
        avg_deltaE_box.set_text(f'Avg ΔE: {avg_deltaE:.2f}')
        max_deltaE_box.set_text(f'Max ΔE: {max_deltaE:.2f}')
        avg_deltaC_box.set_text(f'Avg ΔC: {avg_deltaC:.2f}')
        max_deltaC_box.set_text(f'Max ΔC: {max_deltaC:.2f}')
        avg_saturation_box.set_text(f'Avg SAT: {avg_saturation:.2f}')
        
        # 更新 Lab 顯示視窗
        update_text_display()
    
    fig.canvas.draw_idle()

# 綁定所有滑桿
for slider in sliders:
    slider.on_changed(update)

# --- 重置按鈕 ---
resetax = plt.axes([0.8, 0.025, 0.1, 0.04])
button = Button(resetax, 'Reset Identity', color=axcolor, hovercolor='0.975')

def reset(event):
    idx = 0
    for i in range(3):
        for j in range(3):
            sliders[idx].set_val(initial_ccm[i, j])
            idx += 1

button.on_clicked(reset)

# --- 顯示 Matplotlib 圖表 ---
plt.show()