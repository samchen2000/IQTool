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
        self.curve_points = self._make_gamma_curve(self.gamma_value)
        self.dragging_point = None

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

        lbl_gamma_text = tk.Label(control_frame, text="Gamma 快速曲線 (0.2 ~ 4.0):", font=("Arial", 11), bg="#f0f0f0")
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
        curve_frame = tk.LabelFrame(self.root, text="手動曲線調整", font=("Arial", 11, "bold"))
        curve_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=10)

        toolbar = tk.Frame(curve_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=(5, 0))
        tk.Button(toolbar, text="重設為 Gamma 曲線", command=self.reset_gamma_curve).pack(side=tk.LEFT)
        tk.Label(
            toolbar,
            text="拖曳節點調整；雙擊曲線新增節點；右鍵點擊節點刪除",
            font=("Arial", 9),
        ).pack(side=tk.LEFT, padx=10)

        self.canvas = tk.Canvas(curve_frame, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.pack(pady=5)
        self.canvas.bind("<Button-1>", self.start_curve_drag)
        self.canvas.bind("<B1-Motion>", self.drag_curve_point)
        self.canvas.bind("<ButtonRelease-1>", self.stop_curve_drag)
        self.canvas.bind("<Double-Button-1>", self.add_curve_point)
        self.canvas.bind("<Button-3>", self.remove_curve_point)
        self.draw_gamma_curve()

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
        self.curve_points = self._make_gamma_curve(self.gamma_value)
        self.refresh_curve_and_image()

    @staticmethod
    def _make_gamma_curve(gamma):
        return [(x, x ** gamma) for x in (0.0, 0.25, 0.5, 0.75, 1.0)]

    def reset_gamma_curve(self):
        self.curve_points = self._make_gamma_curve(self.gamma_value)
        self.refresh_curve_and_image()

    def _plot_bounds(self):
        margin = 35
        return margin, margin, self.canvas_width - margin, self.canvas_height - margin

    def _point_to_canvas(self, point):
        left, top, right, bottom = self._plot_bounds()
        x, y = point
        return left + x * (right - left), bottom - y * (bottom - top)

    def _canvas_to_point(self, event):
        left, top, right, bottom = self._plot_bounds()
        x = min(1.0, max(0.0, (event.x - left) / (right - left)))
        y = min(1.0, max(0.0, (bottom - event.y) / (bottom - top)))
        return x, y

    def _nearest_curve_point(self, event):
        nearest_index = min(
            range(len(self.curve_points)),
            key=lambda index: (
                self._point_to_canvas(self.curve_points[index])[0] - event.x
            ) ** 2 + (
                self._point_to_canvas(self.curve_points[index])[1] - event.y
            ) ** 2,
        )
        point_x, point_y = self._point_to_canvas(self.curve_points[nearest_index])
        if (point_x - event.x) ** 2 + (point_y - event.y) ** 2 <= 14 ** 2:
            return nearest_index
        return None

    def start_curve_drag(self, event):
        self.dragging_point = self._nearest_curve_point(event)

    def drag_curve_point(self, event):
        if self.dragging_point is None or self.dragging_point in (0, len(self.curve_points) - 1):
            return

        x, y = self._canvas_to_point(event)
        previous_x, previous_y = self.curve_points[self.dragging_point - 1]
        next_x, next_y = self.curve_points[self.dragging_point + 1]
        min_gap = 0.02
        x = min(next_x - min_gap, max(previous_x + min_gap, x))
        y = min(next_y, max(previous_y, y))
        self.curve_points[self.dragging_point] = (x, y)
        self.refresh_curve_and_image()

    def stop_curve_drag(self, _event):
        self.dragging_point = None

    def add_curve_point(self, event):
        left, top, right, bottom = self._plot_bounds()
        if not (left <= event.x <= right and top <= event.y <= bottom):
            return

        x, y = self._canvas_to_point(event)
        if not 0.0 < x < 1.0:
            return
        insert_at = next(
            index for index, point in enumerate(self.curve_points) if point[0] > x
        )
        previous_x, previous_y = self.curve_points[insert_at - 1]
        next_x, next_y = self.curve_points[insert_at]
        min_gap = 0.02
        if x - previous_x < min_gap or next_x - x < min_gap:
            return

        y = min(next_y, max(previous_y, y))
        self.curve_points.insert(insert_at, (x, y))
        self.refresh_curve_and_image()

    def remove_curve_point(self, event):
        point_index = self._nearest_curve_point(event)
        if point_index is not None and point_index not in (0, len(self.curve_points) - 1):
            self.curve_points.pop(point_index)
            self.refresh_curve_and_image()

    def refresh_curve_and_image(self):
        if hasattr(self, "canvas"):
            self.draw_gamma_curve()
        if self.original_image is not None and hasattr(self, "lbl_orig"):
            self.update_images()

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

        # Map every input channel through the same piecewise-linear curve shown below.
        curve_x = [point[0] * 255 for point in self.curve_points]
        curve_y = [point[1] * 255 for point in self.curve_points]
        lut = np.uint8(np.clip(np.interp(np.arange(256), curve_x, curve_y), 0, 255))
        img_adj_np = lut[np.array(self.original_image)]

        # 3. 處理調整後影像顯示
        img_adj = Image.fromarray(img_adj_np)
        img_adj_resized = img_adj.copy()
        img_adj_resized.thumbnail(display_size)
        self.adj_tk = ImageTk.PhotoImage(img_adj_resized)
        self.lbl_adj.config(image=self.adj_tk, text="")

    def draw_gamma_curve(self):
        """Draw the editable tone curve and its control points."""
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

        sample_x = np.linspace(0.0, 1.0, 121)
        control_x = [point[0] for point in self.curve_points]
        control_y = [point[1] for point in self.curve_points]
        sample_y = np.interp(sample_x, control_x, control_y)
        points = [
            (margin + x * plot_w, (h - margin) - y * plot_h)
            for x, y in zip(sample_x, sample_y)
        ]
        for i in range(len(points) - 1):
            self.canvas.create_line(points[i], points[i + 1], fill="#1f77b4", width=3)

        for index, point in enumerate(self.curve_points):
            px, py = self._point_to_canvas(point)
            radius = 5
            self.canvas.create_oval(
                px - radius,
                py - radius,
                px + radius,
                py + radius,
                fill="#d9534f" if index in (0, len(self.curve_points) - 1) else "#1f77b4",
                outline="white",
                width=1,
            )
        self.canvas.create_text(
            w - margin - 55,
            margin + 10,
            text=f"基準 γ={self.gamma_value:.2f}",
            font=("Arial", 9, "bold"),
            fill="#d9534f",
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = GammaTestApp(root)
    root.mainloop()