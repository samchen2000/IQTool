import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.patches import Rectangle
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from skimage.color import rgb2lab
import threading
import math
import os

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
    'user_image': None,  # 用戶打開的圖片
    'user_image_display': None,  # Matplotlib 中用於顯示用戶圖片的 AxesImage
    'color_boxes': [],  # 24 個色塊方框
    'is_manual_mode': False,  # 是否處於手動模式（打開圖片）
    'box_positions': [],  # 存儲 24 個方框的位置和大小
    'selected_box_idx': None,  # 當前選中的方框索引
    'dragging_mode': None,  # 拖拽模式：'move'、'resize' 或 None
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


def detect_color_blocks_kmeans(image_rgb, num_clusters=24):
    """
    使用 K-means 聚類自動檢測24色塊的位置。
    
    Args:
        image_rgb: RGB 格式影像
        num_clusters: 顏色群集數（應為24）
        
    Returns:
        24個色塊的位置信息列表 (x, y, width, height)
    """
    h, w = image_rgb.shape[:2]
    
    # 將影像重塑為像素列表
    pixels = image_rgb.reshape(-1, 3)
    
    # 使用 K-means 聚類
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(
        pixels.astype(np.float32), 
        num_clusters, 
        None, 
        criteria, 
        10, 
        cv2.KMEANS_RANDOM_CENTERS
    )
    
    # 每個像素分配到最近的簇
    labels = labels.flatten()
    
    # 計算每個簇的邊界框
    box_positions = []
    for cluster_id in range(num_clusters):
        mask = (labels == cluster_id)
        if not mask.any():
            continue
            
        y_coords, x_coords = np.where(mask.reshape(h, w))
        if len(y_coords) == 0:
            continue
            
        x_min, x_max = x_coords.min(), x_coords.max()
        y_min, y_max = y_coords.min(), y_coords.max()
        
        box_width = max(x_max - x_min, 10)
        box_height = max(y_max - y_min, 10)
        
        box_positions.append({
            'x': x_min,
            'y': y_min,
            'width': box_width,
            'height': box_height,
            'cluster_id': cluster_id
        })
    
    # 按位置排序（從左到右，從上到下）
    if box_positions:
        box_positions.sort(key=lambda b: (b['y'], b['x']))
    
    return box_positions[:24]  # 只取前24個


def create_initial_boxes(ax_adjusted, num_boxes=24):
    """
    在影像上創建初始24個方框。
    
    Args:
        ax_adjusted: Matplotlib axis
        num_boxes: 方框數量
    """
    global_data['color_boxes'] = []
    global_data['box_positions'] = []
    
    # 獲取軸的寬高
    ax_width = ax_adjusted.get_xlim()[1] - ax_adjusted.get_xlim()[0]
    ax_height = ax_adjusted.get_ylim()[1] - ax_adjusted.get_ylim()[0]
    
    # 4x6 網格
    cols = 6
    rows = 4
    box_width = ax_width / cols * 0.95
    box_height = ax_height / rows * 0.95
    
    for i in range(num_boxes):
        row = i // cols
        col = i % cols
        
        x = col * (ax_width / cols) + (ax_width / cols - box_width) / 2
        y = row * (ax_height / rows) + (ax_height / rows - box_height) / 2
        
        rect = Rectangle((x, y), box_width, box_height, 
                         linewidth=2, edgecolor='cyan', 
                         facecolor='none', picker=True)
        ax_adjusted.add_patch(rect)
        global_data['color_boxes'].append(rect)
        
        global_data['box_positions'].append({
            'x': x,
            'y': y,
            'width': box_width,
            'height': box_height,
            'index': i
        })


def open_image_file():
    """打開圖片文件對話框並加載圖片"""
    root = tk.Tk()
    root.withdraw()  # 隱藏 Tkinter 主窗口
    
    file_path = filedialog.askopenfilename(
        title="選擇圖片",
        filetypes=[
            ("圖片文件", "*.jpg *.jpeg *.png *.bmp"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("BMP", "*.bmp"),
            ("所有文件", "*.*")
        ]
    )
    
    root.destroy()
    
    if not file_path:
        return False
    
    # 讀取圖片
    img_bgr = cv2.imread(file_path)
    if img_bgr is None:
        messagebox.showerror("錯誤", "無法讀取圖片文件")
        return False
    
    # 轉換為 RGB
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    # 取得右側顯示區域的大小（假設為 400x400）
    target_height = 400
    target_width = 400
    
    # 調整圖片尺寸以適應顯示區域，保持縱橫比
    h, w = img_rgb.shape[:2]
    scale = min(target_width / w, target_height / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    img_rgb_resized = cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    global_data['user_image'] = img_rgb_resized
    global_data['is_manual_mode'] = True
    
    return True


def load_user_image_to_plot(ax_adjusted):
    """將用戶圖片加載到 Matplotlib 中"""
    if global_data['user_image'] is None:
        return False
    
    # 清除現有的方框
    for rect in global_data['color_boxes']:
        rect.remove()
    global_data['color_boxes'] = []
    global_data['box_positions'] = []
    
    # 清除現有的圖片顯示
    if global_data['user_image_display'] is not None:
        global_data['user_image_display'].remove()
    
    # 顯示新圖片
    global_data['user_image_display'] = ax_adjusted.imshow(global_data['user_image'])
    ax_adjusted.set_title("User Image - Click to Select Box", fontsize=12, fontweight='bold')
    
    # 自動檢測24色塊
    try:
        box_positions = detect_color_blocks_kmeans(global_data['user_image'], 24)
        
        # 創建方框
        for pos in box_positions:
            rect = Rectangle((pos['x'], pos['y']), pos['width'], pos['height'],
                            linewidth=2, edgecolor='cyan', 
                            facecolor='none', picker=True)
            ax_adjusted.add_patch(rect)
            global_data['color_boxes'].append(rect)
            global_data['box_positions'].append(pos)
    except Exception as e:
        print(f"自動檢測失敗: {e}")
        # 使用預設網格
        create_initial_boxes(ax_adjusted, 24)
    
    return True


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
fig, (ax_original, ax_adjusted) = plt.subplots(1, 2, figsize=(16, 10))
plt.subplots_adjust(left=0.10, right=0.95, bottom=0.60)

# 左邊顯示原始影像
ax_original.imshow(img_rgb_original)
ax_original.set_title("Original Color Chart", fontsize=14, fontweight='bold')
ax_original.axis('off')

# 右邊顯示動態調整影像
img_display = ax_adjusted.imshow(img_rgb_original)
ax_adjusted.set_title("Adjusted Color Chart (CCM)", fontsize=14, fontweight='bold')
ax_adjusted.axis('off')

# 存儲 img_display 的引用
global_data['img_display'] = img_display
global_data['ax_adjusted'] = ax_adjusted

# --- 建立菜單栏 ---
def on_open_image():
    """打開圖片菜單回調"""
    if open_image_file():
        load_user_image_to_plot(ax_adjusted)
        fig.canvas.draw_idle()

# 獲取 Tkinter 根窗口（來自 Matplotlib 後端）
manager = fig.canvas.manager
if manager and hasattr(manager, 'window'):
    root_window = manager.window
    
    # 建立菜單欄
    menubar = tk.Menu(root_window)
    root_window.config(menu=menubar)
    
    # File 菜單
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Open Image (JPEG/PNG/BMP)", command=on_open_image)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root_window.quit)

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
buttons_inc = []
buttons_dec = []
input_boxes = []
add_ccm_boxes = []

labels = ['R_r', 'R_g', 'R_b', 'G_r', 'G_g', 'G_b', 'B_r', 'B_g', 'B_b']

# 定義每個滑桿的範圍
slider_ranges = [
    (0, 2.0),      # 0: R_r
    (-1.0, 1.0),   # 1: R_g
    (-1.0, 1.0),   # 2: R_b
    (-1.0, 1.0),   # 3: G_r
    (0, 2.0),      # 4: G_g
    (-1.0, 1.0),   # 5: G_b
    (-1.0, 1.0),   # 6: B_r
    (-1.0, 1.0),   # 7: B_g
    (0, 2.0),      # 8: B_b
]

# 全局變量以追蹤輸入框焦點
focused_input_idx = None

def update_ccm_sum_display():
    """更新 CCM 每行的加總顯示"""
    # 計算每行的加總
    # Row 0: R_r + R_g + R_b (indices 0, 1, 2)
    # Row 1: G_r + G_g + G_b (indices 3, 4, 5)
    # Row 2: B_r + B_g + B_b (indices 6, 7, 8)
    
    row_sums = [
        sliders[0].val + sliders[1].val + sliders[2].val,  # R row
        sliders[3].val + sliders[4].val + sliders[5].val,  # G row
        sliders[6].val + sliders[7].val + sliders[8].val,  # B row
    ]
    
    # 更新三個 add_ccm_boxes
    for row_idx, total in enumerate(row_sums):
        if row_idx < len(add_ccm_boxes):
            add_ccm_boxes[row_idx].set_text(f'Add: {total:.2f}')

for i in range(3):
    for j in range(3):
        idx = i * 3 + j
        
        # 滑桿軸
        sax = plt.axes([0.15 + j * 0.27, 0.32 - i * 0.10, 0.20, 0.03], facecolor=axcolor)
        slider_range = slider_ranges[idx]
        slider = Slider(sax, labels[idx], slider_range[0], slider_range[1], valinit=initial_ccm[i, j], valstep=0.01)
        print(idx)
        sliders.append(slider)
        
        # 數值顯示文本框軸
        #tax = plt.axes([0.36 + j * 0.27, 0.32 - i * 0.10, 0.03, 0.1])
        #tax.axis('off')
        #text_box = plt.text(0.5, 0.5, f'{initial_ccm[i, j]:.2f}', 
        #                   ha='center', va='center', fontsize=11, fontweight='bold',
        #                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='black', linewidth=1.5),
        #                   transform=tax.transAxes)
        #text_entries.append(text_box)
        
        # 減少按鍵
        dec_ax = plt.axes([0.15 + j * 0.27, 0.27 - i * 0.10, 0.04, 0.03])
        btn_dec = Button(dec_ax, '-', color='lightcoral', hovercolor='red')
        buttons_dec.append(btn_dec)
        
        # 輸入框
        input_ax = plt.axes([0.22 + j * 0.27, 0.27 - i * 0.10, 0.08, 0.03])
        input_ax.axis('off')
        input_box = plt.text(0.5, 0.5, f'{initial_ccm[i, j]:.2f}', 
                            ha='center', va='center', fontsize=10,
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', edgecolor='gray', linewidth=1),
                            transform=input_ax.transAxes,
                            picker=True)
        input_boxes.append({'text': input_box, 'ax': input_ax, 'idx': idx})
        
        # 增加按鍵
        inc_ax = plt.axes([0.31 + j * 0.27, 0.27 - i * 0.10, 0.04, 0.03])
        btn_inc = Button(inc_ax, '+', color='lightgreen', hovercolor='green')
        buttons_inc.append(btn_inc)
    
    # Rr+Rg+Rb , Gr+Gg+Gb , Br+Bg+Bb 加總 (每行一個，所以在 j 循環外)
    #CCM 每一行（Row）的總和應該等於 1 
    add_ccm_ax = plt.axes([0.87, 0.12 + (i/10), 0.25, 0.04])
    add_ccm_ax.axis('off')
    add_ccm_box = plt.text(0.3, 0.3, ' Add : 1.00', 
                      ha='center', va='center', fontsize=10, fontweight='bold',
                      bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', edgecolor='blue', linewidth=2),
                      transform=add_ccm_ax.transAxes)
    add_ccm_boxes.append(add_ccm_box)

# --- 建立 ΔE 統計資訊顯示框 ---
# 平均 ΔE 顯示框
avg_deltaE_ax = plt.axes([0.15, 0.50, 0.25, 0.04])
avg_deltaE_ax.axis('off')
avg_deltaE_box = plt.text(0.5, 0.5, 'Avg ΔE: 0.00', 
                          ha='center', va='center', fontsize=12, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', edgecolor='blue', linewidth=2),
                          transform=avg_deltaE_ax.transAxes)

# 最大 ΔE 顯示框
max_deltaE_ax = plt.axes([0.30, 0.50, 0.25, 0.04])
max_deltaE_ax.axis('off')
max_deltaE_box = plt.text(0.5, 0.5, 'Max ΔE: 0.00', 
                          ha='center', va='center', fontsize=12, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', edgecolor='red', linewidth=2),
                          transform=max_deltaE_ax.transAxes)

# --- 建立 ΔC 統計資訊顯示框 ---
# 平均 ΔC 顯示框
avg_deltaC_ax = plt.axes([0.45, 0.50, 0.25, 0.04])
avg_deltaC_ax.axis('off')
avg_deltaC_box = plt.text(0.5, 0.5, 'Avg ΔC: 0.00', 
                          ha='center', va='center', fontsize=12, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', edgecolor='blue', linewidth=2),
                          transform=avg_deltaC_ax.transAxes)

# 最大 ΔC 顯示框
max_deltaC_ax = plt.axes([0.60, 0.50, 0.25, 0.04])
max_deltaC_ax.axis('off')
max_deltaC_box = plt.text(0.5, 0.5, 'Max ΔC: 0.00', 
                          ha='center', va='center', fontsize=12, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', edgecolor='red', linewidth=2),
                          transform=max_deltaC_ax.transAxes)

# 平均HSV
avg_saturation_ax = plt.axes([0.75, 0.50, 0.25, 0.04])
avg_saturation_ax.axis('off')
avg_saturation_box = plt.text(0.5, 0.5, 'Avg SAT: 0.00', 
                          ha='center', va='center', fontsize=12, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', edgecolor='red', linewidth=2),
                          transform=avg_saturation_ax.transAxes)

# --- 更新函數 ---
def create_button_callbacks():
    """建立按鍵回調函數"""
    
    def make_increment_callback(idx):
        def on_inc_clicked(event):
            slider_range = slider_ranges[idx]
            current_val = sliders[idx].val
            new_val = min(current_val + 0.05, slider_range[1])
            sliders[idx].set_val(new_val)
            update_ccm_sum_display()
        return on_inc_clicked
    
    def make_decrement_callback(idx):
        def on_dec_clicked(event):
            slider_range = slider_ranges[idx]
            current_val = sliders[idx].val
            new_val = max(current_val - 0.05, slider_range[0])
            sliders[idx].set_val(new_val)
            update_ccm_sum_display()
        return on_dec_clicked
    
    for idx, btn_inc in enumerate(buttons_inc):
        btn_inc.on_clicked(make_increment_callback(idx))
    
    for idx, btn_dec in enumerate(buttons_dec):
        btn_dec.on_clicked(make_decrement_callback(idx))

# 建立按鍵回調
create_button_callbacks()

# 初始化 CCM 行加總顯示
update_ccm_sum_display()

# --- 用戶圖片方框交互功能 ---
box_drag_data = {'start_x': None, 'start_y': None, 'box_idx': None}

def on_box_pick_event(event):
    """點擊方框時選中"""
    if not global_data['is_manual_mode']:
        return
    
    for i, rect in enumerate(global_data['color_boxes']):
        if event.artist == rect:
            global_data['selected_box_idx'] = i
            rect.set_edgecolor('red')
            rect.set_linewidth(3)
            fig.canvas.draw_idle()
            return

def on_mouse_press(event):
    """滑鼠按下事件"""
    if not global_data['is_manual_mode']:
        return
    if event.inaxes != global_data['ax_adjusted']:
        return
    
    box_drag_data['start_x'] = event.xdata
    box_drag_data['start_y'] = event.ydata

def on_mouse_release(event):
    """滑鼠釋放事件"""
    if not global_data['is_manual_mode']:
        return
    if event.inaxes != global_data['ax_adjusted']:
        return
    
    box_drag_data['start_x'] = None
    box_drag_data['start_y'] = None

def on_mouse_motion(event):
    """滑鼠移動事件 - 用於調整方框"""
    if not global_data['is_manual_mode']:
        return
    if event.inaxes != global_data['ax_adjusted']:
        return
    if box_drag_data['start_x'] is None:
        return
    
    if global_data['selected_box_idx'] is not None:
        box_idx = global_data['selected_box_idx']
        dx = event.xdata - box_drag_data['start_x']
        dy = event.ydata - box_drag_data['start_y']
        
        # 使用 Shift 鍵調整大小，否則移動
        if event.key == 'shift':
            # 調整大小
            global_data['color_boxes'][box_idx].set_width(
                max(10, global_data['color_boxes'][box_idx].get_width() + dx)
            )
            global_data['color_boxes'][box_idx].set_height(
                max(10, global_data['color_boxes'][box_idx].get_height() + dy)
            )
            global_data['box_positions'][box_idx]['width'] = global_data['color_boxes'][box_idx].get_width()
            global_data['box_positions'][box_idx]['height'] = global_data['color_boxes'][box_idx].get_height()
        else:
            # 移動
            global_data['color_boxes'][box_idx].set_xy(
                (global_data['color_boxes'][box_idx].get_xy()[0] + dx,
                 global_data['color_boxes'][box_idx].get_xy()[1] + dy)
            )
            global_data['box_positions'][box_idx]['x'] = global_data['color_boxes'][box_idx].get_xy()[0]
            global_data['box_positions'][box_idx]['y'] = global_data['color_boxes'][box_idx].get_xy()[1]
        
        box_drag_data['start_x'] = event.xdata
        box_drag_data['start_y'] = event.ydata
        
        # 更新 Lab 顯示
        update_manual_mode_display()
        fig.canvas.draw_idle()

def update_manual_mode_display():
    """在手動模式下更新 Lab 顯示"""
    if not global_data['is_manual_mode'] or global_data['user_image'] is None:
        return
    
    # 清除舊的 Lab 值
    global_data['lab_values'] = []
    global_data['colors_rgb_original'] = []
    
    # 從每個方框中提取平均顏色
    user_image = global_data['user_image']
    
    for box_pos in global_data['box_positions']:
        x = int(box_pos['x'])
        y = int(box_pos['y'])
        w = int(box_pos['width'])
        h = int(box_pos['height'])
        
        # 確保邊界在影像範圍內
        x = max(0, min(x, user_image.shape[1] - 1))
        y = max(0, min(y, user_image.shape[0] - 1))
        w = min(w, user_image.shape[1] - x)
        h = min(h, user_image.shape[0] - y)
        
        # 提取方框內的像素
        roi = user_image[y:y+h, x:x+w]
        if roi.size == 0:
            avg_color = (128, 128, 128)
        else:
            avg_color = tuple(roi.reshape(-1, 3).mean(axis=0).astype(int))
        
        global_data['colors_rgb_original'].append(avg_color)
        lab = rgb_to_lab(avg_color)
        global_data['lab_values'].append(lab)
    
    # 更新顯示
    update_text_display()

# --- 輸入框編輯功能 ---
input_editing_data = {'idx': None, 'text': ''}

def on_pick_event(event):
    """點擊輸入框時觸發"""
    global focused_input_idx
    
    # 檢查是否點擊了輸入框
    for i, input_box_info in enumerate(input_boxes):
        if event.artist == input_box_info['text']:
            focused_input_idx = i
            input_editing_data['idx'] = input_box_info['idx']
            input_editing_data['text'] = str(sliders[input_box_info['idx']].val)
            # 暫時改變顏色表示選中
            input_box_info['text'].set_bbox(dict(boxstyle='round,pad=0.3', facecolor='lightcyan', edgecolor='blue', linewidth=2))
            fig.canvas.draw_idle()
            break

def on_key_event(event):
    """鍵盤輸入事件處理"""
    if input_editing_data['idx'] is None:
        return
    
    idx = input_editing_data['idx']
    text = input_editing_data['text']
    slider_range = slider_ranges[idx]
    
    if event.key == 'backspace':
        input_editing_data['text'] = text[:-1] if text else ''
    elif event.key == 'escape':
        input_editing_data['idx'] = None
        # 恢復顏色
        for input_box_info in input_boxes:
            if input_box_info['idx'] == idx:
                input_box_info['text'].set_bbox(dict(boxstyle='round,pad=0.3', facecolor='lightyellow', edgecolor='gray', linewidth=1))
        fig.canvas.draw_idle()
        return
    elif event.key == 'enter':
        # 確認輸入
        try:
            new_val = float(input_editing_data['text'])
            # 限制在範圍內
            new_val = max(slider_range[0], min(new_val, slider_range[1]))
            sliders[idx].set_val(new_val)
        except ValueError:
            pass
        
        input_editing_data['idx'] = None
        # 恢復顏色
        for input_box_info in input_boxes:
            if input_box_info['idx'] == idx:
                input_box_info['text'].set_bbox(dict(boxstyle='round,pad=0.3', facecolor='lightyellow', edgecolor='gray', linewidth=1))
        fig.canvas.draw_idle()
        return
    elif event.character and (event.character.isdigit() or event.character in '.-+'):
        input_editing_data['text'] += event.character
    
    # 更新輸入框顯示
    for input_box_info in input_boxes:
        if input_box_info['idx'] == idx:
            input_box_info['text'].set_text(input_editing_data['text'])
            break
    
    fig.canvas.draw_idle()

# 連接事件處理
fig.canvas.mpl_connect('pick_event', on_pick_event)
fig.canvas.mpl_connect('pick_event', on_box_pick_event)  # 方框選擇
fig.canvas.mpl_connect('button_press_event', on_mouse_press)  # 滑鼠按下
fig.canvas.mpl_connect('button_release_event', on_mouse_release)  # 滑鼠釋放
fig.canvas.mpl_connect('motion_notify_event', on_mouse_motion)  # 滑鼠移動
fig.canvas.mpl_connect('key_press_event', on_key_event)

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
    
    # 更新輸入框顯示
    for input_box_info in input_boxes:
        idx = input_box_info['idx']
        input_box_info['text'].set_text(f'{sliders[idx].val:.2f}')
    
    # 應用 CCM
    if global_data['is_manual_mode'] and global_data['user_image'] is not None:
        # 手動模式：對用戶圖片應用 CCM
        corrected_img = apply_ccm(global_data['user_image'], new_ccm)
        global_data['user_image_display'].set_data(corrected_img)
    else:
        # 標準模式：對 24 色卡應用 CCM
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
    
    # 更新 CCM 行加總顯示
    update_ccm_sum_display()
    
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