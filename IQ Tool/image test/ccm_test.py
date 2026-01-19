import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.patches import Rectangle
import tkinter as tk
from tkinter import scrolledtext
from skimage.color import rgb2lab
import threading

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
        (80, 91, 166),      # 8. Purplish Red
        (193, 90, 99),      # 9. Red
        (94, 60, 108),      # 10. Yellow (dark)
        (157, 188, 64),     # 11. Green
        (224, 163, 46),     # 12. Red-Yellow
        
        # 第 3 行
        (230, 126, 34),     # 13. Orange-Red
        (74, 144, 226),     # 14. Blue
        (56, 61, 150),      # 15. Purple
        (70, 148, 73),      # 16. Green-Yellow
        (175, 54, 60),      # 17. Red
        (118, 187, 178),    # 18. Cyan
        
        # 第 4 行
        (255, 255, 255),    # 19. White
        (200, 200, 200),    # 20. Neutral 8 (light gray)
        (160, 160, 160),    # 21. Neutral 6.5 (gray)
        (122, 122, 122),    # 22. Neutral 5 (mid gray)
        (85, 85, 85),       # 23. Neutral 3.5 (dark gray)
        (52, 52, 52),       # 24. Black
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
    
    return img_bgr, colors_rgb


def get_color_names():
    """獲取24色的名稱"""
    names = [
        "Deep Skin", "Light Skin", "Blue Sky", "Foliage",
        "Blue Flower", "Bluish Green", "Orange", "Purplish Red",
        "Red", "Yellow", "Green", "Red-Yellow",
        "Orange-Red", "Blue", "Purple", "Green-Yellow",
        "Red", "Cyan", "White", "Neutral 8",
        "Neutral 6.5", "Neutral 5", "Neutral 3.5", "Black"
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
    if global_data['text_widget'] is None:
        return
    
    text_widget = global_data['text_widget']
    text_widget.config(state=tk.NORMAL)
    text_widget.delete('1.0', tk.END)
    
    content = "=" * 75 + "\n"
    content += "24 色色彩卡 - Lab 值數據\n"
    content += "=" * 75 + "\n\n"
    
    for i, (lab, name) in enumerate(zip(global_data['lab_values'], global_data['color_names'])):
        content += f"【色塊 #{i+1:2d}】{name:15s}\n"
        content += f"    L*: {lab[0]:7.2f}    a*: {lab[1]:7.2f}    b*: {lab[2]:7.2f}\n"
        content += "-" * 75 + "\n"
    
    text_widget.insert('1.0', content)
    text_widget.config(state=tk.DISABLED)


def create_lab_window():
    """建立顯示Lab值的窗口"""
    root = tk.Tk()
    root.title("24 色色彩卡 Lab 值分析")
    root.geometry("750x850")
    
    title_label = tk.Label(root, text="24 色色彩卡 - L*a*b 色彩空間數據", font=("Arial", 14, "bold"))
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
    print("✓ 已自動計算 24 色塊的 Lab 值")
    print("✓ 已開啟 Lab 分析視窗 (獨立窗口)")
    print()

# --- 初始化 Matplotlib 介面 ---
fig, ax = plt.subplots(figsize=(13, 9))
plt.subplots_adjust(left=0.15, bottom=0.50)

# 顯示初始影像
img_display = ax.imshow(img_rgb_original)
ax.set_title("24 色色彩卡 - 互動式 CCM 調整工具", fontsize=14, fontweight='bold')
ax.axis('off')

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
        sax = plt.axes([0.15 + j * 0.27, 0.42 - i * 0.10, 0.20, 0.03], facecolor=axcolor)
        slider = Slider(sax, labels[idx], -1.0, 1.0, valinit=initial_ccm[i, j], valstep=0.01)
        sliders.append(slider)
        
        # 數值顯示文本框軸
        tax = plt.axes([0.36 + j * 0.27, 0.42 - i * 0.10, 0.06, 0.03])
        tax.axis('off')
        text_box = plt.text(0.5, 0.5, f'{initial_ccm[i, j]:.2f}', 
                           ha='center', va='center', fontsize=11, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='black', linewidth=1.5),
                           transform=tax.transAxes)
        text_entries.append(text_box)

# --- 更新函數 ---
def update(val):
    """滑桿更新回調"""
    global global_data
    
    new_ccm = np.array([
        [sliders[0].val, sliders[1].val, sliders[2].val],
        [sliders[3].val, sliders[4].val, sliders[5].val],
        [sliders[6].val, sliders[7].val, sliders[8].val]
    ])
    
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
        
        for color_rgb in global_data['colors_rgb_original']:
            # 將 RGB 顏色轉換為 numpy 陣列並應用 CCM
            color_float = np.array(color_rgb, dtype=np.float32).reshape(1, 1, 3)
            corrected_color = cv2.transform(color_float, ccm_matrix)
            corrected_color_clipped = np.clip(corrected_color[0, 0], 0, 255).astype(np.uint8)
            
            # 計算調整後顏色的 Lab 值
            lab = rgb_to_lab(tuple(corrected_color_clipped))
            global_data['lab_values'].append(lab)
        
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