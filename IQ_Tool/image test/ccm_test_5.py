import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, TextBox
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
plt.rcParams['font.sans-serif'] = [
    'Microsoft JhengHei',
    'Segoe UI Emoji',
    'SimHei',
    'Arial Unicode MS',
]

# 2. 修正負號 '-' 顯示為方框的問題
#plt.rcParams['axes.unicode_minus'] = False

def apply_ccm(image_rgb, ccm_matrix):
    """對影像應用顏色校正矩陣 (CCM)"""
    img_float = image_rgb.astype(np.float32)
    corrected_float = cv2.transform(img_float, ccm_matrix)
    corrected_clipped = np.clip(corrected_float, 0, 255).astype(np.uint8)
    return corrected_clipped

# ==========================================
# 24色色彩卡生成函數 (ISO/IEC 17321-1)
# ==========================================
def create_24_color_chart_with_labels():
    """產生標準 24 色色彩卡 (Macbeth ColorChecker)"""
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
        (85, 85, 85),       # 23. Neutral 3.5 (dark gray, 1.05*)
        (52, 52, 52),       # 24. Black(1.50*)
    ]      
        
    patch_size = 150
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
    """獲取 24 色的標準名稱"""
    return [
        "Deep Skin", "Light Skin", "Blue Sky", "Foliage", "Blue Flower", "Bluish Green", 
        "Orange", "Purplish Red", "Moderate-red", "Purple", "Yellow-green", "Orange-yellow",
        "Blue", "Green", "Red", "Yellow", "Magenta", "Cyan", 
        "White", "Neutral 8", "Neutral 6.5", "Neutral 5", "Neutral 3.5", "Black"
    ]

# 標準參考色度 Lab 值 (1-24)
STANDARD_COLORS_LAB = [
    (38.02, 11.80, 13.67),   (65.67, 13.67, 16.90),   (50.63, 0.37, -21.60),
    (43.00, -15.88, 20.45),  (55.68, 12.76, -25.17),  (70.99, -30.64, 1.54),
    (61.14, 28.10, 56.13),   (41.12, 17.41, -41.88),  (51.33, 42.10, 14.89),
    (31.10, 24.35, -22.10),  (71.90, -28.10, 56.96),  (71.04, 12.60, 64.92),
    (30.35, 26.43, -49.67),  (55.03, -40.14, 32.30),  (41.35, 49.30, 24.66),
    (80.70, -3.66, 77.55),   (51.14, 48.15, -15.28),  (51.15, -19.73, -23.37),
    (95.82, -0.18, 0.49),    (80.60, 0.00, 0.00),     (65.87, 0.00, 0.00),
    (51.19, -0.20, 0.55),    (36.15, 0.00, 0.00),     (21.70, 0.00, 0.00),
]

def rgb_to_lab(rgb_tuple):
    """將 RGB (0-255) 轉換為 Lab 色彩空間"""
    rgb_normalized = np.array(rgb_tuple) / 255.0
    lab = rgb2lab(np.array([[[rgb_normalized[0], rgb_normalized[1], rgb_normalized[2]]]]))
    return lab[0, 0]

# --- 全局狀態變量 ---
global_data = {
    'lab_values': [],
    'color_names': get_color_names(),
    'text_widget': None,
    'colors_rgb_original': [],  # 保存圖框擷取到的原始 RGB
    'patch_ids': [],            # 記錄每個框對應的色塊編號 (1-24)
    'current_ccm': np.eye(3),
    'fig': None,
    'ax_adjusted': None,
    'user_image': None,
    'user_image_display': None,
    'color_boxes': [],          # Rectangle 物件列表
    'box_labels': [],           # 繪製在圖框上的文字標籤 (#1, #2 等)
    'is_manual_mode': False,
    'box_positions': [],        # 存儲 [{'x', 'y', 'width', 'height', 'patch_id'}]
    'selected_box_idx': None,
    'default_box_w': 35,
    'default_box_h': 35,
    'default_box_count': 24
}

def update_text_display():
    """更新 Tkinter 視窗中的數據報表"""
    if global_data['text_widget'] is None:
        return
    
    text_widget = global_data['text_widget']
    text_widget.config(state=tk.NORMAL)
    text_widget.delete('1.0', tk.END)
    
    content = "=" * 80 + "\n"
    content += "  CCM Color Checker Lab Analysis Report\n"
    content += "=" * 80 + "\n\n"
    
    current_ccm = global_data['current_ccm'].astype(np.float32)
    names = global_data['color_names']
    
    for i, (rgb_org, patch_id) in enumerate(zip(global_data['colors_rgb_original'], global_data['patch_ids'])):
        # 獲取對應的標準參考值
        target_idx = max(0, min(patch_id - 1, 23))
        ref_lab = STANDARD_COLORS_LAB[target_idx]
        name = names[target_idx]
        
        # 計算 CCM 調整後的 RGB
        color_float = np.array(rgb_org, dtype=np.float32).reshape(1, 1, 3)
        corrected_color = cv2.transform(color_float, current_ccm)
        corrected_clipped = np.clip(corrected_color[0, 0], 0, 255).astype(np.uint8)
        rgb_adjusted = tuple(corrected_clipped)
        
        # 計算調整後的 Lab
        lab = rgb_to_lab(rgb_adjusted)
        
        deltaE = math.sqrt(((ref_lab[0] - lab[0])**2) + ((ref_lab[1] - lab[1])**2) + ((ref_lab[2] - lab[2])**2))
        deltaC = math.sqrt((lab[1]**2 + lab[2]**2)) - math.sqrt((ref_lab[1]**2 + ref_lab[2]**2))
        
        r_norm, g_norm, b_norm = rgb_adjusted[0]/255.0, rgb_adjusted[1]/255.0, rgb_adjusted[2]/255.0
        rgb_max = max(r_norm, g_norm, b_norm)
        rgb_min = min(r_norm, g_norm, b_norm)
        sat_value = ((rgb_max - rgb_min) / rgb_max * 255) if rgb_max > 0 else 0
        
        content += f"【圖框 #{i+1:02d} -> 色卡 #{patch_id:02d}】{name:15s}\n"
        content += f"  原RGB: {rgb_org}  ->  校正RGB: {rgb_adjusted}\n"
        content += f"  L*: {lab[0]:4.1f}  a*: {lab[1]:4.1f}  b*: {lab[2]:4.1f} | ΔE: {deltaE:4.2f}  ΔC: {deltaC:+4.2f}  Sat: {sat_value:4.1f}\n"
        content += "-" * 80 + "\n"
        
    text_widget.insert('1.0', content)
    text_widget.config(state=tk.DISABLED)

def clear_all_boxes():
    """清除目前所有的方框與其文字標籤"""
    for rect in global_data['color_boxes']:
        try:
            rect.remove()
        except:
            pass
    for txt in global_data['box_labels']:
        try:
            txt.remove()
        except:
            pass
    global_data['color_boxes'] = []
    global_data['box_labels'] = []
    global_data['box_positions'] = []
    global_data['selected_box_idx'] = None

def create_custom_boxes(ax, num_boxes=24, box_w=None, box_h=None):
    """依照指定的數量與寬高在畫面上建立圖框與文字標籤"""
    clear_all_boxes()
    if global_data['user_image'] is None:
        return
        
    img_h, img_w = global_data['user_image'].shape[:2]
    
    if box_w is None:
        box_w = global_data['default_box_w']
    if box_h is None:
        box_h = global_data['default_box_h']
        
    global_data['default_box_w'] = box_w
    global_data['default_box_h'] = box_h
    
    # 計算網格排列 (盡量接近 3:2 或 6:4)
    if num_boxes <= 6:
        cols, rows = num_boxes, 1
    elif num_boxes <= 12:
        cols, rows = 6, 2
    elif num_boxes <= 18:
        cols, rows = 6, 3
    else:
        cols = 6
        rows = math.ceil(num_boxes / cols)
        
    x_step = img_w / (cols + 1)
    y_step = img_h / (rows + 1)
    
    for i in range(num_boxes):
        r = i // cols
        c = i % cols
        cx = (c + 1) * x_step
        cy = (r + 1) * y_step
        x = max(0, min(cx - box_w / 2, img_w - box_w))
        y = max(0, min(cy - box_h / 2, img_h - box_h))
        patch_id = (i % 24) + 1  # 預設編號 1-24
        
        rect = Rectangle((x, y), box_w, box_h, linewidth=2, edgecolor='cyan', facecolor='none', picker=True)
        ax.add_patch(rect)
        global_data['color_boxes'].append(rect)
        
        # 建立方框上的標籤
        txt = ax.text(x + 2, y + 2, f"#{patch_id}", color='yellow', fontsize=9, fontweight='bold',
                      bbox=dict(boxstyle='square,pad=0.1', facecolor='black', alpha=0.6, edgecolor='none'))
        global_data['box_labels'].append(txt)
        
        global_data['box_positions'].append({
            'x': x, 'y': y, 'width': box_w, 'height': box_h, 'patch_id': patch_id
        })
        
    update_manual_mode_display()
    if global_data['fig']:
        global_data['fig'].canvas.draw_idle()

def open_image_file():
    """打開圖片文件並載入"""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="選擇圖片",
        filetypes=[("圖片文件", "*.jpg *.jpeg *.png *.bmp"), ("所有文件", "*.*")]
    )
    root.destroy()
    if not file_path:
        return False
    
    try:
        image_data = np.fromfile(file_path, dtype=np.uint8)
        img_bgr = cv2.imdecode(image_data, cv2.IMREAD_COLOR) if image_data.size else None
    except Exception as exc:
        messagebox.showerror("錯誤", f"讀取失敗：\n{exc}")
        return False

    if img_bgr is None:
        messagebox.showerror("錯誤", "無法解碼圖片文件！")
        return False
    
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    # 適度縮放至 600x600 保持清晰度與適中運算速度
    target_dim = 600
    h, w = img_rgb.shape[:2]
    scale = min(target_dim / w, target_dim / h, 1.0)
    new_w, new_h = int(w * scale), int(h * scale)
    
    global_data['user_image'] = cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
    global_data['is_manual_mode'] = True
    return True

def load_user_image_to_plot(ax_adjusted):
    """將圖片與圖框呈現於畫面上"""
    if global_data['user_image'] is None:
        return False
    
    clear_all_boxes()
    if global_data['user_image_display'] is not None:
        global_data['user_image_display'].remove()
        
    global_data['user_image_display'] = ax_adjusted.imshow(global_data['user_image'])
    ax_adjusted.set_title("User Image - Drag to Move, Shift+Drag to Resize", fontsize=11, fontweight='bold')
    
    # 建立預設圖框
    create_custom_boxes(ax_adjusted, global_data['default_box_count'])
    return True

def update_manual_mode_display():
    """從使用者圖片中的圖框擷取色彩並觸發計算"""
    if not global_data['is_manual_mode'] or global_data['user_image'] is None:
        return
    
    user_img = global_data['user_image']
    img_h, img_w = user_img.shape[:2]
    
    global_data['colors_rgb_original'] = []
    global_data['patch_ids'] = []
    
    for box in global_data['box_positions']:
        x = int(max(0, min(box['x'], img_w - 1)))
        y = int(max(0, min(box['y'], img_h - 1)))
        w = int(max(2, min(box['width'], img_w - x)))
        h = int(max(2, min(box['height'], img_h - y)))
        
        roi = user_img[y:y+h, x:x+w]
        if roi.size == 0:
            avg_color = (128, 128, 128)
        else:
            avg_color = tuple(roi.reshape(-1, 3).mean(axis=0).astype(int))
            
        global_data['colors_rgb_original'].append(avg_color)
        global_data['patch_ids'].append(box.get('patch_id', 1))
        
    update(None)

def create_lab_window():
    """建立顯示 Lab 值與色差分析的獨立 Tkinter 視窗"""
    root = tk.Tk()
    root.title("CCM 色彩品質與 Lab 分析報告")
    root.geometry("820x800")
    
    top_frame = tk.Frame(root)
    top_frame.pack(fill=tk.X, padx=10, pady=6)
    
    title_label = tk.Label(top_frame, text="24 色色彩卡 / ROI 圖框取樣 - 色彩空間數據", font=("Consolas", 12, "bold"))
    title_label.pack(side=tk.LEFT)
    
    btn_open = tk.Button(top_frame, text="📁 開啟圖片 (Open Image)", font=("Microsoft JhengHei", 9, "bold"),
                         bg="#C8E6C9", activebackground="#A5D6A7", command=lambda: on_open_image())
    btn_open.pack(side=tk.RIGHT, padx=5)
    
    btn_close = tk.Button(top_frame, text="✖ 還原色卡 (Reset)", font=("Microsoft JhengHei", 9),
                          bg="#FFCDD2", activebackground="#EF9A9A", command=lambda: on_close_image())
    btn_close.pack(side=tk.RIGHT, padx=5)
    
    text_widget = scrolledtext.ScrolledText(root, width=95, height=42, font=("Courier", 10))
    text_widget.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
    
    global_data['text_widget'] = text_widget
    update_text_display()
    root.mainloop()

# --- 初始化影像與後台視窗 ---
img_bgr, colors_rgb = create_24_color_chart_with_labels()
img_rgb_original = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
global_data['colors_rgb_original'] = colors_rgb
global_data['patch_ids'] = list(range(1, 25))

lab_thread = threading.Thread(target=create_lab_window, daemon=True)
lab_thread.start()

# --- 建立 Matplotlib 介面 ---
fig, (ax_original, ax_adjusted) = plt.subplots(1, 2, figsize=(16, 10))
plt.subplots_adjust(left=0.08, right=0.96, top=0.92, bottom=0.56)
global_data['fig'] = fig
global_data['ax_adjusted'] = ax_adjusted

ax_original.imshow(img_rgb_original)
ax_original.set_title("Standard 24 ColorChart (Reference)", fontsize=13, fontweight='bold')
ax_original.axis('off')

img_display = ax_adjusted.imshow(img_rgb_original)
ax_adjusted.set_title("Adjusted Image (CCM Corrected)", fontsize=13, fontweight='bold')
ax_adjusted.axis('off')
global_data['img_display'] = img_display

# --- 選單與按鈕回調功能 ---
def on_open_image(event=None):
    if open_image_file():
        load_user_image_to_plot(ax_adjusted)
        fig.canvas.draw_idle()

def on_close_image(event=None):
    global_data['user_image'] = None
    global_data['user_image_display'] = None
    global_data['is_manual_mode'] = False
    clear_all_boxes()
    
    if global_data['img_display'] is not None:
        global_data['img_display'].remove()
    global_data['img_display'] = ax_adjusted.imshow(img_rgb_original)
    ax_adjusted.set_title("Adjusted Image (CCM Corrected)", fontsize=13, fontweight='bold')
    
    global_data['colors_rgb_original'] = colors_rgb
    global_data['patch_ids'] = list(range(1, 25))
    update(None)
    fig.canvas.draw_idle()

# 頂部顯眼按鈕 (位於右側 Adjusted Image 上方)
#ax_top_open = plt.axes([0.66, 0.935, 0.14, 0.038])
#btn_top_open = Button(ax_top_open, '📁 Open Image', color='#C8E6C9', hovercolor='#A5D6A7')
#btn_top_open.on_clicked(on_open_image)

#ax_top_close = plt.axes([0.81, 0.935, 0.14, 0.038])
#btn_top_close = Button(ax_top_close, '✖ Close Image', color='#FFCDD2', hovercolor='#EF9A9A')
#btn_top_close.on_clicked(on_close_image)

# 原生選單列 (兼容 Tkinter 與 Qt 後端)
try:
    manager = fig.canvas.manager
    if manager and hasattr(manager, 'window'):
        root_window = manager.window
        if hasattr(root_window, 'tk'):
            menubar = tk.Menu(root_window)
            root_window.config(menu=menubar)
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="File", menu=file_menu)
            file_menu.add_command(label="Open Image", command=on_open_image)
            file_menu.add_command(label="Close Image", command=on_close_image)
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=root_window.quit)
        elif hasattr(root_window, 'menuBar'):
            file_menu = root_window.menuBar().addMenu("File")
            file_menu.addAction("Open Image", on_open_image)
            file_menu.addAction("Close Image", on_close_image)
            file_menu.addSeparator()
            file_menu.addAction("Exit", root_window.close)
except Exception as e:
    print(f"原生選單列建立提示: {e}")

# ==========================================
# 下方控制面板：CCM 滑桿與按鈕
# ==========================================
initial_ccm = np.eye(3)
axcolor = 'lightgoldenrodyellow'
sliders = []
buttons_inc, buttons_dec = [], []
input_boxes = []
add_ccm_boxes = []

labels = ['R_r', 'R_g', 'R_b', 'G_r', 'G_g', 'G_b', 'B_r', 'B_g', 'B_b']
slider_ranges = [
    (0, 3.0), (-2.0, 2.0), (-2.0, 2.0),
    (-2.0, 2.0), (0, 3.0), (-2.0, 2.0),
    (-2.0, 2.0), (-2.0, 2.0), (0, 3.0)
]

def update_ccm_sum_display():
    row_sums = [
        sliders[0].val + sliders[1].val + sliders[2].val,
        sliders[3].val + sliders[4].val + sliders[5].val,
        sliders[6].val + sliders[7].val + sliders[8].val,
    ]
    for row_idx, total in enumerate(row_sums):
        if row_idx < len(add_ccm_boxes):
            add_ccm_boxes[row_idx].set_text(f'Add: {total:.2f}')

for i in range(3):
    for j in range(3):
        idx = i * 3 + j
        sax = plt.axes([0.10 + j * 0.28, 0.44 - i * 0.08, 0.17, 0.025], facecolor=axcolor)
        slider = Slider(sax, labels[idx], slider_ranges[idx][0], slider_ranges[idx][1], valinit=initial_ccm[i, j], valstep=0.01)
        sliders.append(slider)
        
        dec_ax = plt.axes([0.10 + j * 0.28, 0.41 - i * 0.08, 0.03, 0.025])
        buttons_dec.append(Button(dec_ax, '-', color='lightcoral', hovercolor='red'))
        
        input_ax = plt.axes([0.15 + j * 0.28, 0.41 - i * 0.08, 0.07, 0.025])
        input_ax.axis('off')
        input_box = plt.text(0.5, 0.5, f'{initial_ccm[i, j]:.2f}', ha='center', va='center', fontsize=9,
                             bbox=dict(boxstyle='round,pad=0.2', facecolor='lightyellow', edgecolor='gray'))
        input_boxes.append({'text': input_box, 'ax': input_ax, 'idx': idx})
        
        inc_ax = plt.axes([0.24 + j * 0.28, 0.41 - i * 0.08, 0.03, 0.025])
        buttons_inc.append(Button(inc_ax, '+', color='lightgreen', hovercolor='green'))
        
    add_ccm_ax = plt.axes([0.91, 0.43 - (i * 0.08), 0.07, 0.03])
    add_ccm_ax.axis('off')
    add_ccm_box = plt.text(0.5, 0.5, 'Add: 1.00', ha='center', va='center', fontsize=9, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcyan', edgecolor='blue'))
    add_ccm_boxes.append(add_ccm_box)

# 統計數據指標框
stat_positions = [0.10, 0.26, 0.42, 0.58, 0.74]
stat_axes = [plt.axes([pos, 0.49, 0.13, 0.03]) for pos in stat_positions]
for ax in stat_axes: ax.axis('off')

avg_deltaE_box = plt.text(0.5, 0.5, 'Avg ΔE: 0.00', ha='center', va='center', fontsize=10, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', edgecolor='blue'), transform=stat_axes[0].transAxes)
max_deltaE_box = plt.text(0.5, 0.5, 'Max ΔE: 0.00', ha='center', va='center', fontsize=10, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.3', facecolor='lightpink', edgecolor='red'), transform=stat_axes[1].transAxes)
avg_deltaC_box = plt.text(0.5, 0.5, 'Avg ΔC: 0.00', ha='center', va='center', fontsize=10, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', edgecolor='blue'), transform=stat_axes[2].transAxes)
max_deltaC_box = plt.text(0.5, 0.5, 'Max ΔC: 0.00', ha='center', va='center', fontsize=10, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.3', facecolor='lightpink', edgecolor='red'), transform=stat_axes[3].transAxes)
avg_saturation_box = plt.text(0.5, 0.5, 'Avg SAT: 0.00', ha='center', va='center', fontsize=10, fontweight='bold',
                              bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', edgecolor='orange'), transform=stat_axes[4].transAxes)

# ==========================================
# 升級：底部圖框數量、大小與 24 色塊設定控制區
# ==========================================

# 1. 數量控制項
ax_box_cnt_lbl = plt.axes([0.05, 0.09, 0.07, 0.03]); ax_box_cnt_lbl.axis('off')
ax_box_cnt_lbl.text(0.5, 0.5, 'Box Count:', ha='center', va='center', fontsize=9, fontweight='bold')
ax_box_cnt = plt.axes([0.12, 0.09, 0.04, 0.03])
txt_box_cnt = TextBox(ax_box_cnt, '', initial=str(global_data['default_box_count']))

ax_btn_gen = plt.axes([0.17, 0.09, 0.06, 0.03])
btn_gen_boxes = Button(ax_btn_gen, 'Apply Grid', color='lightgreen', hovercolor='lime')

# 2. 大小控制項 (寬 W 與 高 H)
ax_w_lbl = plt.axes([0.25, 0.09, 0.02, 0.03]); ax_w_lbl.axis('off')
ax_w_lbl.text(0.5, 0.5, 'W:', ha='center', va='center', fontsize=9, fontweight='bold')
ax_box_w = plt.axes([0.27, 0.09, 0.04, 0.03])
txt_box_w = TextBox(ax_box_w, '', initial=str(global_data['default_box_w']))

ax_h_lbl = plt.axes([0.32, 0.09, 0.02, 0.03]); ax_h_lbl.axis('off')
ax_h_lbl.text(0.5, 0.5, 'H:', ha='center', va='center', fontsize=9, fontweight='bold')
ax_box_h = plt.axes([0.34, 0.09, 0.04, 0.03])
txt_box_h = TextBox(ax_box_h, '', initial=str(global_data['default_box_h']))

ax_btn_sz_sel = plt.axes([0.39, 0.09, 0.07, 0.03])
btn_sz_sel = Button(ax_btn_sz_sel, 'Set Selected', color=axcolor, hovercolor='gold')

ax_btn_sz_all = plt.axes([0.47, 0.09, 0.06, 0.03])
btn_sz_all = Button(ax_btn_sz_all, 'Set All', color=axcolor, hovercolor='gold')

# 3. 指定色塊編號 (1-24)
ax_patch_lbl = plt.axes([0.55, 0.09, 0.10, 0.03]); ax_patch_lbl.axis('off')
ax_patch_lbl.text(0.5, 0.5, 'Patch ID (1-24):', ha='center', va='center', fontsize=9, fontweight='bold')
ax_patch_id = plt.axes([0.65, 0.09, 0.04, 0.03])
txt_patch_id = TextBox(ax_patch_id, '', initial='1')

ax_btn_set_patch = plt.axes([0.70, 0.09, 0.08, 0.03])
btn_set_patch = Button(ax_btn_set_patch, 'Assign Patch', color='lightcoral', hovercolor='red')

# 4. 重設矩陣按鈕
ax_reset = plt.axes([0.83, 0.09, 0.08, 0.03])
btn_reset = Button(ax_reset, 'Reset CCM', color='lightgray', hovercolor='white')

# 5. 底部相片開啟與操作列
ax_btn_open = plt.axes([0.05, 0.03, 0.11, 0.035])
btn_open_bottom = Button(ax_btn_open, '📁 Open Image', color='#C8E6C9', hovercolor='#81C784')
btn_open_bottom.on_clicked(on_open_image)

ax_btn_close = plt.axes([0.17, 0.03, 0.11, 0.035])
btn_close_bottom = Button(ax_btn_close, '✖ Close Image', color='#FFCDD2', hovercolor='#E57373')
btn_close_bottom.on_clicked(on_close_image)

ax_tip = plt.axes([0.30, 0.03, 0.65, 0.035])
ax_tip.axis('off')
ax_tip.text(0.0, 0.5, '💡 提示：點擊「Open Image」開啟相片；點選圖框拖曳移動 / 按住 Shift 縮放；輸入 Patch ID 可綁定色塊。', fontsize=9, color='#444444', va='center')

# --- 控件回調事件實作 ---

def on_apply_count(event):
    """依照輸入的數量重新產生網格圖框"""
    if not global_data['is_manual_mode']:
        messagebox.showinfo("提示", "請先開啟自訂圖片以建立圖框！")
        return
    try:
        count = int(txt_box_cnt.text.strip())
        if not (1 <= count <= 24):
            messagebox.showwarning("警告", "圖框數量請介於 1 到 24 之間！")
            return
        w = int(txt_box_w.text.strip())
        h = int(txt_box_h.text.strip())
        create_custom_boxes(global_data['ax_adjusted'], count, w, h)
    except ValueError:
        messagebox.showerror("錯誤", "數量與尺寸請輸入整數數值！")

btn_gen_boxes.on_clicked(on_apply_count)

def on_set_size_selected(event):
    """套用寬高至目前選中的圖框"""
    sel_idx = global_data['selected_box_idx']
    if sel_idx is None or sel_idx >= len(global_data['color_boxes']):
        messagebox.showinfo("提示", "請先使用滑鼠在右圖中點選要調整的圖框！")
        return
    try:
        w = max(4, int(txt_box_w.text.strip()))
        h = max(4, int(txt_box_h.text.strip()))
        global_data['color_boxes'][sel_idx].set_width(w)
        global_data['color_boxes'][sel_idx].set_height(h)
        global_data['box_positions'][sel_idx]['width'] = w
        global_data['box_positions'][sel_idx]['height'] = h
        update_manual_mode_display()
        fig.canvas.draw_idle()
    except ValueError:
        messagebox.showerror("錯誤", "寬高請輸入有效的整數！")

btn_sz_sel.on_clicked(on_set_size_selected)

def on_set_size_all(event):
    """套用寬高至所有圖框"""
    if not global_data['color_boxes']:
        return
    try:
        w = max(4, int(txt_box_w.text.strip()))
        h = max(4, int(txt_box_h.text.strip()))
        for i, rect in enumerate(global_data['color_boxes']):
            rect.set_width(w)
            rect.set_height(h)
            global_data['box_positions'][i]['width'] = w
            global_data['box_positions'][i]['height'] = h
        update_manual_mode_display()
        fig.canvas.draw_idle()
    except ValueError:
        messagebox.showerror("錯誤", "寬高請輸入有效的整數！")

btn_sz_all.on_clicked(on_set_size_all)

def on_assign_patch(event):
    """將輸入的 24 色卡色塊編號 (1-24) 指派給目前選取的圖框"""
    sel_idx = global_data['selected_box_idx']
    if sel_idx is None or sel_idx >= len(global_data['box_positions']):
        messagebox.showinfo("提示", "請先使用滑鼠點選圖中欲綁定的圖框！")
        return
    try:
        patch_id = int(txt_patch_id.text.strip())
        if not (1 <= patch_id <= 24):
            messagebox.showwarning("警告", "色塊編號請輸入 1 至 24！")
            return
        
        global_data['box_positions'][sel_idx]['patch_id'] = patch_id
        global_data['box_labels'][sel_idx].set_text(f"#{patch_id}")
        update_manual_mode_display()
        fig.canvas.draw_idle()
    except ValueError:
        messagebox.showerror("錯誤", "色塊編號請輸入有效數字！")

btn_set_patch.on_clicked(on_assign_patch)

def on_reset_ccm(event):
    for i in range(9):
        sliders[i].set_val(initial_ccm[i//3, i%3])

btn_reset.on_clicked(on_reset_ccm)

# --- 滑鼠選取與拖曳調整事件 ---
box_drag_state = {'start_x': None, 'start_y': None}

def on_mouse_press(event):
    if not global_data['is_manual_mode'] or event.inaxes != global_data['ax_adjusted']:
        return
    if event.xdata is None or event.ydata is None:
        return
        
    box_drag_state['start_x'] = event.xdata
    box_drag_state['start_y'] = event.ydata
    
    # 判斷點擊了哪個方框
    for i, rect in enumerate(global_data['color_boxes']):
        x, y = rect.get_xy()
        w, h = rect.get_width(), rect.get_height()
        if x <= event.xdata <= x + w and y <= event.ydata <= y + h:
            # 清除舊選取
            if global_data['selected_box_idx'] is not None and global_data['selected_box_idx'] < len(global_data['color_boxes']):
                global_data['color_boxes'][global_data['selected_box_idx']].set_edgecolor('cyan')
                global_data['color_boxes'][global_data['selected_box_idx']].set_linewidth(2)
            
            # 設定新選取
            global_data['selected_box_idx'] = i
            rect.set_edgecolor('red')
            rect.set_linewidth(3)
            
            # 同步更新輸入框上的當前數值
            pos = global_data['box_positions'][i]
            txt_box_w.set_val(str(int(pos['width'])))
            txt_box_h.set_val(str(int(pos['height'])))
            txt_patch_id.set_val(str(pos.get('patch_id', 1)))
            
            fig.canvas.draw_idle()
            return

def on_mouse_release(event):
    box_drag_state['start_x'] = None
    box_drag_state['start_y'] = None

def on_mouse_motion(event):
    if not global_data['is_manual_mode'] or event.inaxes != global_data['ax_adjusted']:
        return
    if box_drag_state['start_x'] is None or global_data['selected_box_idx'] is None:
        return
        
    idx = global_data['selected_box_idx']
    dx = event.xdata - box_drag_state['start_x']
    dy = event.ydata - box_drag_state['start_y']
    rect = global_data['color_boxes'][idx]
    lbl = global_data['box_labels'][idx]
    
    if event.key == 'shift':
        # Shift 按住：調整尺寸
        new_w = max(5, rect.get_width() + dx)
        new_h = max(5, rect.get_height() + dy)
        rect.set_width(new_w)
        rect.set_height(new_h)
        global_data['box_positions'][idx]['width'] = new_w
        global_data['box_positions'][idx]['height'] = new_h
        txt_box_w.set_val(str(int(new_w)))
        txt_box_h.set_val(str(int(new_h)))
    else:
        # 平移圖框與文字標籤
        new_x = rect.get_xy()[0] + dx
        new_y = rect.get_xy()[1] + dy
        rect.set_xy((new_x, new_y))
        lbl.set_position((new_x + 2, new_y + 2))
        global_data['box_positions'][idx]['x'] = new_x
        global_data['box_positions'][idx]['y'] = new_y
        
    box_drag_state['start_x'] = event.xdata
    box_drag_state['start_y'] = event.ydata
    
    update_manual_mode_display()
    fig.canvas.draw_idle()

fig.canvas.mpl_connect('button_press_event', on_mouse_press)
fig.canvas.mpl_connect('button_release_event', on_mouse_release)
fig.canvas.mpl_connect('motion_notify_event', on_mouse_motion)

# --- CCM 微調按鈕回調 ---
def make_increment_callback(i):
    def on_inc(event):
        sliders[i].set_val(min(sliders[i].val + 0.01, slider_ranges[i][1]))
    return on_inc

def make_decrement_callback(i):
    def on_dec(event):
        sliders[i].set_val(max(sliders[i].val - 0.01, slider_ranges[i][0]))
    return on_dec

for i in range(9):
    buttons_inc[i].on_clicked(make_increment_callback(i))
    buttons_dec[i].on_clicked(make_decrement_callback(i))

# --- CCM 矩陣更新與色彩評估 ---
def update(val):
    new_ccm = np.array([
        [sliders[0].val, sliders[1].val, sliders[2].val],
        [sliders[3].val, sliders[4].val, sliders[5].val],
        [sliders[6].val, sliders[7].val, sliders[8].val]
    ])
    global_data['current_ccm'] = new_ccm.copy()
    
    for idx_box, info in enumerate(input_boxes):
        info['text'].set_text(f"{sliders[info['idx']].val:.2f}")
        
    if global_data['is_manual_mode'] and global_data['user_image'] is not None:
        corrected_img = apply_ccm(global_data['user_image'], new_ccm)
        global_data['user_image_display'].set_data(corrected_img)
    else:
        corrected_img = apply_ccm(img_rgb_original, new_ccm)
        img_display.set_data(corrected_img)
        
    # 色彩差與統計計算
    if global_data['colors_rgb_original']:
        deltaE_list, deltaC_list, sat_list = [], [], []
        ccm_f = new_ccm.astype(np.float32)
        
        for rgb_org, patch_id in zip(global_data['colors_rgb_original'], global_data['patch_ids']):
            target_idx = max(0, min(patch_id - 1, 23))
            ref_lab = STANDARD_COLORS_LAB[target_idx]
            
            c_f = np.array(rgb_org, dtype=np.float32).reshape(1, 1, 3)
            c_corr = cv2.transform(c_f, ccm_f)
            rgb_corr = np.clip(c_corr[0, 0], 0, 255).astype(np.uint8)
            
            lab = rgb_to_lab(tuple(rgb_corr))
            dE = math.sqrt(((ref_lab[0] - lab[0])**2) + ((ref_lab[1] - lab[1])**2) + ((ref_lab[2] - lab[2])**2))
            dC = math.sqrt(lab[1]**2 + lab[2]**2) - math.sqrt(ref_lab[1]**2 + ref_lab[2]**2)
            
            deltaE_list.append(dE)
            deltaC_list.append(abs(dC))
            
            r_n, g_n, b_n = rgb_corr[0]/255.0, rgb_corr[1]/255.0, rgb_corr[2]/255.0
            mx, mn = max(r_n, g_n, b_n), min(r_n, g_n, b_n)
            sat = ((mx - mn) / mx * 255) if mx > 0 else 0
            sat_list.append(sat)
            
        avg_deltaE_box.set_text(f'Avg ΔE: {np.mean(deltaE_list):.2f}')
        max_deltaE_box.set_text(f'Max ΔE: {np.max(deltaE_list):.2f}')
        avg_deltaC_box.set_text(f'Avg ΔC: {np.mean(deltaC_list):.2f}')
        max_deltaC_box.set_text(f'Max ΔC: {np.max(deltaC_list):.2f}')
        avg_saturation_box.set_text(f'Avg SAT: {np.mean(sat_list):.2f}')
        
        update_text_display()
        
    update_ccm_sum_display()
    fig.canvas.draw_idle()

for slider in sliders:
    slider.on_changed(update)

update_ccm_sum_display()
update(None)

plt.show()