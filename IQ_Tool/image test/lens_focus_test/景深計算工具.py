"""景深與超焦距計算工具。使用方式：python 景深計算工具.py"""

from __future__ import annotations

import math
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk


@dataclass(frozen=True)
class DepthOfField:
    near_limit_mm: float
    far_limit_mm: float
    front_depth_mm: float
    rear_depth_mm: float


def _validate_positive(**values: float) -> None:
    for name, value in values.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} 必須是大於 0 的有限數值")


def calculate_coc_from_pixel(pixel_size_mm: float, multiplier: float) -> float:
    _validate_positive(像素大小=pixel_size_mm, 倍數=multiplier)
    return pixel_size_mm * multiplier


def calculate_hyperfocal_distance(
    focal_length_mm: float, f_number: float, coc_mm: float
) -> float:
    _validate_positive(焦距=focal_length_mm, 光圈值=f_number, 彌散圓直徑=coc_mm)
    return focal_length_mm**2 / (f_number * coc_mm) + focal_length_mm


def calculate_depth_of_field(
    focal_length_mm: float,
    f_number: float,
    coc_mm: float,
    focus_distance_mm: float,
) -> DepthOfField:
    _validate_positive(
        焦距=focal_length_mm,
        光圈值=f_number,
        彌散圓直徑=coc_mm,
        對焦距離=focus_distance_mm,
    )
    if focus_distance_mm <= focal_length_mm:
        raise ValueError("對焦距離必須大於焦距")

    focal_squared = focal_length_mm**2
    aperture_coc = f_number * coc_mm
    distance_from_focal_plane = focus_distance_mm - focal_length_mm
    near_denominator = focal_squared + aperture_coc * distance_from_focal_plane
    far_denominator = focal_squared - aperture_coc * distance_from_focal_plane
    hyperfocal_distance = focal_squared / aperture_coc + focal_length_mm

    near_limit = focus_distance_mm * focal_squared / near_denominator
    far_limit = (
        math.inf
        if focus_distance_mm >= hyperfocal_distance
        else focus_distance_mm * focal_squared / far_denominator
    )
    return DepthOfField(
        near_limit_mm=near_limit,
        far_limit_mm=far_limit,
        front_depth_mm=focus_distance_mm - near_limit,
        rear_depth_mm=far_limit - focus_distance_mm,
    )


def format_distance(distance_mm: float) -> str:
    if math.isinf(distance_mm):
        return "無限遠"
    if distance_mm >= 1000:
        return f"{distance_mm / 1000:,.4f} m（{distance_mm:,.2f} mm）"
    return f"{distance_mm:,.4f} mm"


class DepthOfFieldApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("景深與超焦距計算工具")
        self.root.geometry("720x700")
        self.root.minsize(660, 650)
        self.root.configure(bg="#f3f6fb")

        style = ttk.Style(root)
        style.configure("TLabel", background="#f3f6fb", font=("Microsoft JhengHei UI", 10))
        style.configure("Title.TLabel", font=("Microsoft JhengHei UI", 19, "bold"))
        style.configure("Section.TLabel", font=("Microsoft JhengHei UI", 12, "bold"))
        style.configure("Result.TLabel", font=("Microsoft JhengHei UI", 10))
        style.configure("TButton", font=("Microsoft JhengHei UI", 10, "bold"), padding=8)
        style.configure("TRadiobutton", background="#f3f6fb", font=("Microsoft JhengHei UI", 10))

        container = ttk.Frame(root, padding=24)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="景深與超焦距計算工具", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            container,
            text="輸入鏡頭與 CoC 參數，計算建議對焦距離，並比較指定距離的景深。",
        ).pack(anchor="w", pady=(4, 18))

        inputs = ttk.LabelFrame(container, text="輸入參數", padding=14)
        inputs.pack(fill="x")
        inputs.columnconfigure(1, weight=1)

        self.focal_length = self._add_entry(inputs, "鏡頭焦距 f（mm）", "2.4", 0)
        self.f_number = self._add_entry(inputs, "光圈值 N（例如 f/8 填 8）", "2.8", 1)

        ttk.Label(inputs, text="允許彌散圓直徑 CoC").grid(row=2, column=0, sticky="w", pady=6)
        self.coc_mode = tk.StringVar(value="pixel")
        modes = ttk.Frame(inputs)
        modes.grid(row=2, column=1, sticky="w", pady=6)
        ttk.Radiobutton(
            modes, text="像素大小 × 倍數", variable=self.coc_mode, value="pixel"
        ).pack(side="left", padx=(0, 14))
        ttk.Radiobutton(
            modes, text="直接輸入 CoC", variable=self.coc_mode, value="direct"
        ).pack(side="left")

        self.pixel_size = self._add_entry(inputs, "像素大小（mm）", "0.002", 3)
        self.multiplier = self._add_entry(inputs, "像素倍數", "2", 4)
        self.direct_coc = self._add_entry(inputs, "直接輸入 CoC（mm）", "0.03", 5)
        self.focus_distance = self._add_entry(
            inputs, "比較用對焦距離（mm；留白使用超焦距）", "", 6
        )

        ttk.Button(container, text="計算", command=self.calculate).pack(
            anchor="e", pady=12
        )

        results = ttk.LabelFrame(container, text="計算結果", padding=14)
        results.pack(fill="both", expand=True)
        self.result_text = tk.StringVar(value="輸入參數後按「計算」。")
        ttk.Label(
            results,
            textvariable=self.result_text,
            style="Result.TLabel",
            justify="left",
            wraplength=640,
        ).pack(anchor="nw", fill="both", expand=True)

    @staticmethod
    def _add_entry(
        parent: ttk.LabelFrame, label: str, default: str, row: int
    ) -> tk.StringVar:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5, padx=(0, 14))
        variable = tk.StringVar(value=default)
        ttk.Entry(parent, textvariable=variable, width=22).grid(
            row=row, column=1, sticky="ew", pady=5
        )
        return variable

    def calculate(self) -> None:
        try:
            focal_length = float(self.focal_length.get())
            f_number = float(self.f_number.get())
            if self.coc_mode.get() == "pixel":
                coc = calculate_coc_from_pixel(
                    float(self.pixel_size.get()), float(self.multiplier.get())
                )
            else:
                coc = float(self.direct_coc.get())
                _validate_positive(彌散圓直徑=coc)

            hyperfocal = calculate_hyperfocal_distance(focal_length, f_number, coc)
            approximate_hyperfocal = focal_length**2 / (f_number * coc)
            comparison_distance = (
                hyperfocal
                if not self.focus_distance.get().strip()
                else float(self.focus_distance.get())
            )
            depth = calculate_depth_of_field(
                focal_length, f_number, coc, comparison_distance
            )
        except ValueError as error:
            messagebox.showerror("輸入錯誤", str(error), parent=self.root)
            return

        if math.isinf(depth.far_limit_mm):
            total_depth = "無限大"
        else:
            total_depth = format_distance(depth.front_depth_mm + depth.rear_depth_mm)

        self.result_text.set(
            f"採用 CoC：{coc:.6f} mm\n\n"
            f"最大景深的建議對焦距離（精確超焦距）：{format_distance(hyperfocal)}\n"
            f"簡化超焦距 f²/(N×CoC)：{format_distance(approximate_hyperfocal)}\n"
            f"精確值與簡化值差異：{focal_length:.4f} mm（焦距項）\n\n"
            "最大景深說明：對焦在精確超焦距時，遠景深延伸至無限遠，"
            "因此前景深＋後景深沒有有限的最大值。此時近景深界限為超焦距的一半。\n\n"
            f"比較用對焦距離：{format_distance(comparison_distance)}\n"
            f"近景深界限：{format_distance(depth.near_limit_mm)}\n"
            f"遠景深界限：{format_distance(depth.far_limit_mm)}\n"
            f"前景深：{format_distance(depth.front_depth_mm)}\n"
            f"後景深：{format_distance(depth.rear_depth_mm)}\n"
            f"前景深＋後景深：{total_depth}"
        )


def main() -> None:
    root = tk.Tk()
    DepthOfFieldApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
