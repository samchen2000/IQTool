from pathlib import Path

import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np


LAYOUT_SECTIONS = ("controls", "image_comparison", "gamma_curve")


def load_layout_config(config_path=None):
    """Load enabled sections and their display order from the Markdown table."""
    if config_path is None:
        config_path = Path(__file__).with_name("gamma_adjust_layout.md")

    content = Path(config_path).read_text(encoding="utf-8")
    rows = content.splitlines()
    header_index = None

    for index, line in enumerate(rows):
        cells = [cell.strip().lower() for cell in line.strip().strip("|").split("|")]
        if cells == ["section", "enabled", "order"]:
            header_index = index
            break

    if header_index is None:
        raise ValueError("版面設定缺少 Markdown 表格標頭：section | enabled | order")

    settings = {}
    orders = set()
    for line in rows[header_index + 1:]:
        stripped_line = line.strip()
        if not stripped_line.startswith("|"):
            if settings:
                break
            continue

        cells = [cell.strip() for cell in stripped_line.strip("|").split("|")]
        if all(cell and set(cell) <= {"-", ":"} for cell in cells):
            continue
        if len(cells) != 3:
            raise ValueError(f"版面設定表格欄位數錯誤：{line}")

        section, enabled_text, order_text = cells
        if section not in LAYOUT_SECTIONS:
            raise ValueError(f"不支援的版面區塊：{section}")
        if section in settings:
            raise ValueError(f"版面區塊重複設定：{section}")

        enabled_text = enabled_text.lower()
        if enabled_text not in ("true", "false"):
            raise ValueError(f"{section} 的 enabled 必須是 true 或 false")
        try:
            order = int(order_text)
        except ValueError as error:
            raise ValueError(f"{section} 的 order 必須是整數") from error
        if order < 1:
            raise ValueError(f"{section} 的 order 必須大於 0")
        if order in orders:
            raise ValueError(f"版面順序重複：{order}")

        settings[section] = (enabled_text == "true", order)
        orders.add(order)

    missing_sections = set(LAYOUT_SECTIONS) - settings.keys()
    if missing_sections:
        raise ValueError(f"版面設定缺少區塊：{', '.join(sorted(missing_sections))}")

    return [
        section
        for section, (enabled, _) in sorted(settings.items(), key=lambda item: item[1][1])
        if enabled
    ]


class GammaTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ISP IQ 實驗室：Gamma 測試與驗證 AP")
        self.root.geometry("1100x780")
        self.root.minsize(900, 700)

        self.original_image = None
        self.gamma_value = 1.0
        self.canvas_width = 450
        self.canvas_height = 160

        section_builders = {
            "controls": self._build_control_panel,
            "image_comparison": self._build_image_comparison,
            "gamma_curve": self._build_gamma_curve,
        }
        for section in load_layout_config():
            section_builders[section]()

    def _build_control_panel(self):
        control_frame = tk.Frame(self.root, pady=10, padx=10, bg="#f0f0f0")
        control_frame.pack(side=tk.TOP, fill=tk.X)

        btn_load = tk.Button(control_frame, text="載入影像檔案", command=self.load_image, font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", padx=10, pady=3)
        btn_load.pack(side=tk.LEFT, padx=10)

        lbl_gamma_text = tk.Label(control_frame, text="Gamma 值調整 (0.2 ~ 4.0):", font=("Arial", 11), bg="#f0f0f0")
        lbl_gamma_text.pack(side=tk.LEFT, padx=15)

        # 數值滑桿 (支援 0.2 至 4.0，解析度 0.05)
        self.slider_gamma = tk.Scale(control_frame, from_=0.2, to=4.0, resolution=0.05, 
                                     orient=tk.HORIZONTAL, length=350, command=self.on_gamma_change, font=("Arial", 10), bg="#f0f0f0")
        self.slider_gamma.set(1.0)
        self.slider_gamma.pack(side=tk.LEFT, padx=5)

        # 數值顯示標籤
        self.lbl_gamma_val = tk.Label(control_frame, text="1.00", font=("Arial", 12, "bold"), width=5, fg="#d9534f", bg="#f0f0f0")
        self.lbl_gamma_val.pack(side=tk.LEFT, padx=5)

    def _build_image_comparison(self):
        image_frame = tk.Frame(self.root, pady=10)
        image_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10)

        orig_frame = tk.LabelFrame(image_frame, text=" 原始影像 (Linear / Default) ", font=("Arial", 11, "bold"))
        orig_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.lbl_orig = tk.Label(orig_frame, text="尚未載入圖片\n請點擊上方按鈕載入測試圖卡", font=("Arial", 10), fg="gray")
        self.lbl_orig.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        adj_frame = tk.LabelFrame(image_frame, text=" Gamma 調整後預覽 (Adjusted) ", font=("Arial", 11, "bold"))
        adj_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        self.lbl_adj = tk.Label(adj_frame, text="尚未載入圖片", font=("Arial", 10), fg="gray")
        self.lbl_adj.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _build_gamma_curve(self):
        curve_frame = tk.LabelFrame(self.root, text=" Gamma 轉換曲線 (Tone Curve: V_out = V_in ^ Gamma) ", font=("Arial", 11, "bold"))
        curve_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=10)

        self.canvas = tk.Canvas(curve_frame, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.pack(pady=5)

        self.draw_gamma_curve(1.0)

    def load_image(self):
        """ 開啟檔案對話框並載入圖片 """
        file_path = filedialog.askopenfilename(filetypes=[
            ("Image Files", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"),
            ("All Files", "*.*")
        ])
        if file_path:
            try:
                self.original_image = Image.open(file_path).convert("RGB")
                self.update_images()
            except Exception as e:
                print(f"圖片載入失敗: {e}")

    def on_gamma_change(self, val):
        """ 當滑桿數值改變時觸發 """
        self.gamma_value = float(val)
        self.lbl_gamma_val.config(text=f"{self.gamma_value:.2f}")
        
        # 即時更新影像與曲線
        if self.original_image is not None and hasattr(self, "lbl_orig"):
            self.update_images()
        if hasattr(self, "canvas"):
            self.draw_gamma_curve(self.gamma_value)

    def update_images(self):
        """ 重新計算 Gamma 並更新畫面顯示 """
        if self.original_image is None or not hasattr(self, "lbl_orig"):
            return

        # 限制顯示大小以適應介面排版 (最大約 480x320)
        display_size = (480, 320)

        # 1. 處理原圖顯示
        img_orig_resized = self.original_image.copy()
        img_orig_resized.thumbnail(display_size)
        self.orig_tk = ImageTk.PhotoImage(img_orig_resized)
        self.lbl_orig.config(image=self.orig_tk, text="")

        # 2. 使用 NumPy 進行高效 Gamma 轉換: V_out = 255 * (V_in / 255) ^ gamma
        img_np = np.array(self.original_image, dtype=np.float32) / 255.0
        # 加上 np.clip 避免數值溢位
        img_adj_np = np.power(np.clip(img_np, 0.0, 1.0), self.gamma_value)
        img_adj_np = np.uint8(np.clip(img_adj_np * 255.0, 0, 255))

        # 3. 處理調整後影像顯示
        img_adj = Image.fromarray(img_adj_np)
        img_adj_resized = img_adj.copy()
        img_adj_resized.thumbnail(display_size)
        self.adj_tk = ImageTk.PhotoImage(img_adj_resized)
        self.lbl_adj.config(image=self.adj_tk, text="")

    def draw_gamma_curve(self, gamma):
        """ 在 Canvas 上動態繪製 Gamma 曲線 """
        self.canvas.delete("all")
        w = self.canvas_width
        h = self.canvas_height
        margin = 35

        plot_w = w - 2 * margin
        plot_h = h - 2 * margin

        # 畫 X, Y 軸
        self.canvas.create_line(margin, h - margin, w - margin, h - margin, fill="#666666", width=2) # X 軸
        self.canvas.create_line(margin, margin, margin, h - margin, fill="#666666", width=2) # Y 軸

        # 座標軸標籤與刻度
        self.canvas.create_text(w - margin + 10, h - margin + 5, text="In", font=("Arial", 9, "bold"))
        self.canvas.create_text(margin - 15, margin, text="Out", font=("Arial", 9, "bold"))
        self.canvas.create_text(margin, h - margin + 15, text="0", font=("Arial", 8))
        self.canvas.create_text(w - margin, h - margin + 15, text="1.0", font=("Arial", 8))
        self.canvas.create_text(margin - 15, h - margin, text="0", font=("Arial", 8))
        self.canvas.create_text(margin - 15, margin, text="1.0", font=("Arial", 8))

        # 畫對角線參考線 (Gamma = 1.0 的線性對照)
        self.canvas.create_line(margin, h - margin, w - margin, margin, fill="#cccccc", dash=(4, 4))

        # 計算並繪製當前 Gamma 曲線
        points = []
        steps = 60
        for i in range(steps + 1):
            x_val = i / steps  # 0.0 ~ 1.0
            y_val = x_val ** gamma  # 核心公式
            
            px = margin + x_val * plot_w
            py = (h - margin) - y_val * plot_h
            points.append((px, py))

        # 連接曲線線段
        for i in range(len(points) - 1):
            self.canvas.create_line(points[i], points[i+1], fill="#1f77b4", width=3)

        # 顯示當前 Gamma 數值在畫布右上角
        self.canvas.create_text(w - margin - 40, margin + 10, text=f"γ = {gamma:.2f}", font=("Arial", 11, "bold"), fill="#d9534f")

if __name__ == "__main__":
    root = tk.Tk()
    app = GammaTestApp(root)
    root.mainloop()