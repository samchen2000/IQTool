"""
Delta E*a*b Viewer
==================
GUI 工具:讀取 Imatest Master CSV,計算並視覺化 ΔE*a*b、ΔE*94、ΔE00
"""

import sys
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QPushButton, QLabel, QFileDialog,
                              QTextEdit, QSplitter, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QImage
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# ============================================================
# 色彩轉換函式
# ============================================================

def lab_to_xyz(L, a, b):
    """CIELAB → XYZ (D65)"""
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0
    def f_inv(t):
        delta = 6.0 / 29.0
        return t**3 if t > delta else 3 * delta**2 * (t - 4.0/29.0)
    return Xn * f_inv(fx), Yn * f_inv(fy), Zn * f_inv(fz)


def lab_to_display_rgb(L, a, b):
    """CIELAB → sRGB (0~1)"""
    X, Y, Z = lab_to_xyz(L, a, b)
    M = np.array([
        [3.2406255, -1.5372080, -0.4986286],
        [-0.9689307,  1.8757561,  0.0415175],
        [0.0557101, -0.2040211,  1.0569959]
    ])
    rgb = np.clip(M @ np.array([X, Y, Z]), 0, 1)
    def gamma(c):
        return 12.92 * c if c <= 0.0031308 else 1.055 * c**(1/2.4) - 0.055
    return np.array([gamma(c) for c in rgb])


# ============================================================
# Delta E 計算
# ============================================================

def delta_e_ab(L1, a1, b1, L2, a2, b2):
    """CIE76 ΔE*a*b"""
    return np.sqrt((L1-L2)**2 + (a1-a2)**2 + (b1-b2)**2)


def delta_e_94(L1, a1, b1, L2, a2, b2):
    """CIE94 ΔE"""
    C1, C2 = np.sqrt(a1**2 + b1**2), np.sqrt(a2**2 + b2**2)
    dL, dC = L1 - L2, C1 - C2
    da, db = a1 - a2, b1 - b2
    dH2 = da**2 + db**2 - dC**2
    SL, SC, SH = 1.0, 1 + 0.045*C1, 1 + 0.015*C1
    return np.sqrt((dL/SL)**2 + (dC/SC)**2 + dH2/SH**2)


def delta_e_00(L1, a1, b1, L2, a2, b2):
    """CIEDE2000 ΔE"""
    kL = kC = kH = 1.0
    C1, C2 = np.sqrt(a1**2 + b1**2), np.sqrt(a2**2 + b2**2)
    C_avg = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(C_avg**7 / (C_avg**7 + 25**7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.sqrt(a1p**2 + b1**2), np.sqrt(a2p**2 + b2**2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    if C1p * C2p == 0: dhp = 0
    elif abs(h2p - h1p) <= 180: dhp = h2p - h1p
    elif h2p - h1p > 180: dhp = h2p - h1p - 360
    else: dhp = h2p - h1p + 360
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dhp / 2))
    Lp_avg = (L1 + L2) / 2
    Cp_avg = (C1p + C2p) / 2
    if C1p * C2p == 0: hp_avg = h1p + h2p
    elif abs(h1p - h2p) <= 180: hp_avg = (h1p + h2p) / 2
    elif h1p + h2p < 360: hp_avg = (h1p + h2p + 360) / 2
    else: hp_avg = (h1p + h2p - 360) / 2
    T = (1 - 0.17*np.cos(np.radians(hp_avg-30))
           + 0.24*np.cos(np.radians(2*hp_avg))
           + 0.32*np.cos(np.radians(3*hp_avg+6))
           - 0.20*np.cos(np.radians(4*hp_avg-63)))
    SL = 1 + 0.015*(Lp_avg-50)**2 / np.sqrt(20+(Lp_avg-50)**2)
    SC = 1 + 0.045*Cp_avg
    SH = 1 + 0.015*Cp_avg*T
    d_theta = 30*np.exp(-((hp_avg-275)/25)**2)
    RC = 2*np.sqrt(Cp_avg**7/(Cp_avg**7+25**7))
    RT = -np.sin(np.radians(2*d_theta))*RC
    return np.sqrt((dLp/(kL*SL))**2 + (dCp/(kC*SC))**2 +
                   (dHp/(kH*SH))**2 + RT*(dCp/(kC*SC))*(dHp/(kH*SH)))


# ============================================================
# CSV 解析
# ============================================================

class CSVParser:
    @staticmethod
    def parse(filename):
        patches = []
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # 定位 CIELAB 區段
        idx = None
        for i, line in enumerate(lines):
            if 'CIELAB and xyY values for reference and input patches' in line:
                idx = i + 2
                break
        if idx is None:
            return patches

        for i in range(idx, len(lines)):
            line = lines[i].strip()
            if not line or line.startswith(','): continue
            if 'Color errors' in line or 'Additional color' in line: break

            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 7: continue
            try:
                patch_num = int(parts[0])
                Lr, ar, br = float(parts[1]), float(parts[2]), float(parts[3])
                Li, ai, bi = float(parts[4]), float(parts[5]), float(parts[6])

                dE_ab = delta_e_ab(Lr, ar, br, Li, ai, bi)
                dE_94 = delta_e_94(Lr, ar, br, Li, ai, bi)
                dE_00 = delta_e_00(Lr, ar, br, Li, ai, bi)
                dC    = np.sqrt(ai**2+bi**2) - np.sqrt(ar**2+br**2)

                row = col = None
                if len(parts) >= 16:
                    try:
                        row, col = int(parts[14]), int(parts[15])
                    except: pass

                patches.append({
                    'patch': patch_num, 'L_ref': Lr, 'a_ref': ar, 'b_ref': br,
                    'L_input': Li, 'a_input': ai, 'b_input': bi,
                    'dE_ab': dE_ab, 'dE_94': dE_94, 'dE_00': dE_00,
                    'dC': dC, 'row': row, 'col': col
                })
            except (ValueError, IndexError):
                continue
        return patches


# ============================================================
# GUI 主程式
# ============================================================

class DeltaEViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ΔE Viewer - Imatest CSV Analyzer")
        self.setGeometry(50, 50, 1400, 900)
        self.patches = []
        self.csv_filename = ""
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # --- 頂部控制列 ---
        ctrl = QHBoxLayout()
        title = QLabel("ΔE Analyzer — 色彩差異視覺化工具")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        ctrl.addWidget(title); ctrl.addStretch()

        self.file_label = QLabel("📄 未載入檔案")
        ctrl.addWidget(self.file_label)

        load_btn = QPushButton("📂 載入 CSV")
        load_btn.clicked.connect(self.load_file)
        ctrl.addWidget(load_btn)

        save_btn = QPushButton("💾 匯出報告")
        save_btn.clicked.connect(self.export_report)
        ctrl.addWidget(save_btn)
        main_layout.addLayout(ctrl)

        # --- 主內容 (Splitter) ---
        splitter = QSplitter(Qt.Horizontal)

        # 左:Matplotlib 畫布
        plot_w = QWidget()
        plot_l = QVBoxLayout(plot_w)
        self.figure = Figure(figsize=(8, 8), facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        plot_l.addWidget(self.canvas)
        splitter.addWidget(plot_w)

        # 右:側邊面板
        side = QWidget()
        side_l = QVBoxLayout(side)

        grp1 = QGroupBox("📋 Color Checker 佈局")
        v1 = QVBoxLayout()
        self.checker_label = QLabel("載入 CSV 後顯示色塊")
        self.checker_label.setAlignment(Qt.AlignCenter)
        self.checker_label.setMinimumHeight(180)
        self.checker_label.setStyleSheet("background:#f5f5f5;border:1px solid #aaa;")
        v1.addWidget(self.checker_label)
        grp1.setLayout(v1); side_l.addWidget(grp1)

        grp2 = QGroupBox("📊 各色塊 ΔE 數值")
        v2 = QVBoxLayout()
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setFont(QFont("Consolas", 9))
        v2.addWidget(self.detail_text)
        grp2.setLayout(v2); side_l.addWidget(grp2)

        splitter.addWidget(side)
        splitter.setSizes([900, 450])
        main_layout.addWidget(splitter)

        # --- 底部統計 ---
        bg = QGroupBox("📈 摘要統計  (Δ Input-Ref)")
        bl = QVBoxLayout()
        self.summary_label = QLabel("請載入 CSV 檔案以開始分析")
        self.summary_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.summary_label.setStyleSheet(
            "background:#fffce6;padding:12px;border:1px solid #ddd;")
        bl.addWidget(self.summary_label)
        bg.setLayout(bl); main_layout.addWidget(bg)

        self.statusBar().showMessage("就緒")
        self.show_empty_plot()

    def show_empty_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, "ΔE*a*b Vision\n\nplease load CSV file",
                ha='center', va='center', transform=ax.transAxes,
                fontsize=16, color='#888')
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values(): s.set_visible(False)
        self.canvas.draw()

    # ====== 檔案操作 ======
    def load_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "開啟 Imatest CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not filename: return

        self.csv_filename = filename
        name = filename.replace('\\','/').split('/')[-1]
        self.file_label.setText(f"📄 {name}")
        self.statusBar().showMessage(f"載入中 {name}...")

        self.patches = CSVParser.parse(filename)
        if self.patches:
            self.refresh_all()
            self.statusBar().showMessage(f"已載入 {len(self.patches)} 個色塊: {name}")
        else:
            self.statusBar().showMessage("❌ 找不到有效的色塊資料")
            self.summary_label.setText("❌ CSV 內無有效色塊資料")

    def export_report(self):
        if not self.patches:
            self.statusBar().showMessage("⚠ 請先載入資料再匯出")
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "儲存報告", "delta_e_report.txt",
            "Text Files (*.txt);;CSV Files (*.csv)")
        if not filename: return

        dE_ab = [p['dE_ab'] for p in self.patches]
        dE_94 = [p['dE_94'] for p in self.patches]
        dE_00 = [p['dE_00'] for p in self.patches]
        dC    = [abs(p['dC']) for p in self.patches]

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*70+"\nDELTA E 分析報告\n")
            f.write(f"來源:{self.csv_filename}\n"+"="*70+"\n\n")
            f.write("摘要統計\n"+"-"*70+"\n")
            f.write(f"{'':10}{'Mean':>10}{'Max':>10}{'Min':>10}\n")
            for name, vals in [('ΔE*ab',dE_ab),('ΔE*94',dE_94),
                               ('ΔE00',dE_00),('|ΔC|',dC)]:
                f.write(f"{name:10}{np.mean(vals):>10.3f}"
                        f"{np.max(vals):>10.3f}{np.min(vals):>10.3f}\n")
            f.write("\n各色塊明細\n"+"-"*70+"\n")
            f.write(f"{'Patch':<7}{'ΔE*ab':<10}{'ΔE*94':<10}{'ΔE00':<10}{'ΔC':<10}\n")
            f.write("-"*70+"\n")
            for p in self.patches:
                f.write(f"{p['patch']:<7}{p['dE_ab']:<10.3f}"
                       f"{p['dE_94']:<10.3f}{p['dE_00']:<10.3f}{p['dC']:<10.3f}\n")
        self.statusBar().showMessage(f"✅ 報告已儲存:{filename}")

    # ====== 更新顯示 ======
    def refresh_all(self):
        self.plot_ab_diagram()
        self.update_color_checker()
        self.update_details()
        self.update_summary()

    def plot_ab_diagram(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # 產生 sRGB 色彩背景 (L*=70)
        a_grid = np.linspace(-70, 85, 200)
        b_grid = np.linspace(-65, 105, 200)
        A, B = np.meshgrid(a_grid, b_grid)
        colors = np.zeros(A.shape + (3,))
        for i in range(A.shape[0]):
            for j in range(A.shape[1]):
                colors[i,j] = lab_to_display_rgb(70, A[i,j], B[i,j])
        ax.imshow(colors, extent=[-70,85,-65,105],
                  origin='lower', aspect='auto', alpha=0.5)

        # 繪製每個色塊
        for p in self.patches:
            ar, br = p['a_ref'], p['b_ref']
            ai, bi = p['a_input'], p['b_input']

            ref_rgb = lab_to_display_rgb(p['L_ref'], ar, br)
            ax.scatter(ar, br, marker='s', s=180, c=[ref_rgb],
                       edgecolors='black', linewidths=1.5, zorder=4)

            in_rgb = lab_to_display_rgb(p['L_input'], ai, bi)
            ax.scatter(ai, bi, marker='o', s=180, c=[in_rgb],
                       edgecolors='black', linewidths=1.5, zorder=4)

            ax.plot([ar, ai], [br, bi], 'k-', alpha=0.6,
                    linewidth=1, zorder=2)

            ax.annotate(str(p['patch']), xy=(ai, bi),
                       xytext=(7,4), textcoords='offset points',
                       fontsize=10, fontweight='bold', zorder=5)

        # 圖例
        ax.scatter([], [], marker='s', s=150, c='white',
                  edgecolors='black', linewidths=1.5, label='Reference')
        ax.scatter([], [], marker='o', s=150, c='lightgray',
                  edgecolors='black', linewidths=1.5, label='Camera (Input)')

        ax.set_xlabel("a*", fontsize=13, fontweight='bold')
        ax.set_ylabel("b*", fontsize=13, fontweight='bold')
        ax.set_title("2D a*b* Chromaticity Diagram — ΔE 視覺化",
                     fontsize=14, fontweight='bold')
        ax.set_xlim(-70, 85); ax.set_ylim(-65, 105)
        ax.axhline(0, color='gray', ls='--', lw=0.6, alpha=0.6)
        ax.axvline(0, color='gray', ls='--', lw=0.6, alpha=0.6)
        ax.grid(True, alpha=0.25, color='white', lw=0.5)
        ax.legend(loc='upper left', fontsize=10, framealpha=0.9)

        # 統計文字框
        dE_ab = [p['dE_ab'] for p in self.patches]
        stats = (f"ΔE*ab: mean = {np.mean(dE_ab):.2f}, max = {np.max(dE_ab):.2f}\n"
                f"Patches: {len(self.patches)}")
        ax.text(0.98, 0.02, stats, transform=ax.transAxes,
                ha='right', va='bottom', fontsize=10,
                bbox=dict(boxstyle='round,pad=0.5',
                         facecolor='white', alpha=0.85, edgecolor='gray'))
        self.figure.tight_layout()
        self.canvas.draw()

    def update_color_checker(self):
        rows = [p['row'] for p in self.patches if p['row']]
        cols = [p['col'] for p in self.patches if p['col']]
        if not rows or not cols: return
        max_row, max_col = max(rows), max(cols)
        cell = 28
        img = np.ones((max_row*cell, max_col*cell, 3)) * 0.85
        for p in self.patches:
            if p['row'] and p['col']:
                rgb = lab_to_display_rgb(p['L_input'], p['a_input'], p['b_input'])
                y1 = (p['row']-1)*cell; x1 = (p['col']-1)*cell
                img[y1:y1+cell, x1:x1+cell] = rgb
        h, w = img.shape[:2]
        q_img = QImage((img*255).astype(np.uint8).copy(),
                       w, h, 3*w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(q_img).scaled(
            self.checker_label.width()-10,
            self.checker_label.height()-10,
            Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.checker_label.setPixmap(pix)

    def update_details(self):
        dE_ab = [p['dE_ab'] for p in self.patches]
        dE_94 = [p['dE_94'] for p in self.patches]
        dE_00 = [p['dE_00'] for p in self.patches]
        text = (f"{'Patch':<7}{'ΔE*ab':<9}{'ΔE*94':<9}{'ΔE00':<9}"
               f"{'Row':<5}{'Col':<5}\n"+"-"*44+"\n")
        for p in self.patches:
            rs = str(p['row']) if p['row'] else '-'
            cs = str(p['col']) if p['col'] else '-'
            text += (f"{p['patch']:<7}{p['dE_ab']:<9.2f}"
                    f"{p['dE_94']:<9.2f}{p['dE_00']:<9.2f}"
                    f"{rs:<5}{cs:<5}\n")
        text += "-"*44+"\n"
        text += (f"{'Mean':<7}{np.mean(dE_ab):<9.2f}"
                f"{np.mean(dE_94):<9.2f}{np.mean(dE_00):<9.2f}\n")
        text += (f"{'Max':<7}{np.max(dE_ab):<9.2f}"
                f"{np.max(dE_94):<9.2f}{np.max(dE_00):<9.2f}\n")
        self.detail_text.setText(text)

    def update_summary(self):
        dE_ab = [p['dE_ab'] for p in self.patches]
        dE_94 = [p['dE_94'] for p in self.patches]
        dE_00 = [p['dE_00'] for p in self.patches]
        dC    = [abs(p['dC']) for p in self.patches]
        summary = (
            f"  ΔE*a*b : mean = {np.mean(dE_ab):6.2f}  max = {np.max(dE_ab):6.2f}  |  "
            f"ΔE*94 : mean = {np.mean(dE_94):6.2f}  max = {np.max(dE_94):6.2f}  |  "
            f"ΔE00 : mean = {np.mean(dE_00):6.2f}  max = {np.max(dE_00):6.2f}  |  "
            f"|ΔC| : mean = {np.mean(dC):6.2f}  max = {np.max(dC):6.2f}"
        )
        self.summary_label.setText(summary)


# ============================================================
# 入口
# ============================================================

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = DeltaEViewer()
    window.show()
    sys.exit(app.exec_())
