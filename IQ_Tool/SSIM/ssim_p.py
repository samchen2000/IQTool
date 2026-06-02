"""
SSIM + PSNR + MSE Tool (Tkinter GUI)
Features:
- Single-pair mode: choose reference image + test image, preview both
- Batch mode: choose folder of reference images + folder of test images (match by filename)
- Calculate SSIM, PSNR, MSE for each pair
- Show Diff map and thumbnails
- Export results to Excel (.xlsx) and PDF report (table + small plots)
- Save CSV results

Dependencies:
pip install opencv-python pillow scikit-image pandas openpyxl matplotlib

To make EXE (Windows):
1) pip install pyinstaller
2) pyinstaller --onefile --windowed SSIM_PSNR_MSE_Tool.py
   (you may need to include data files like icons; test the generated exe)

Usage: run `python SSIM_PSNR_MSE_Tool.py`

"""

import os
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
from skimage.metrics import structural_similarity as compare_ssim
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ----------------- Utility functions -----------------

def read_image_gray(path):
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"無法讀取影像: {path}")
    return img


def read_image_color(path):
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"無法讀取影像: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def mse(imageA, imageB):
    err = np.mean((imageA.astype("float") - imageB.astype("float")) ** 2)
    return float(err)


def psnr_from_mse(mse_val, max_pixel=255.0):
    if mse_val == 0:
        return float('inf')
    return 20 * math.log10(max_pixel) - 10 * math.log10(mse_val)


def compute_metrics(path_ref, path_test, use_color=False):
    # Read grayscale for SSIM and MSE
    img_ref_gray = read_image_gray(path_ref)
    img_test_gray = read_image_gray(path_test)

    # resize test to ref if necessary
    if img_ref_gray.shape != img_test_gray.shape:
        img_test_gray = cv2.resize(img_test_gray, (img_ref_gray.shape[1], img_ref_gray.shape[0]))

    ssim_score, diff = compare_ssim(img_ref_gray, img_test_gray, full=True)
    diff = (diff * 255).astype("uint8")

    m = mse(img_ref_gray, img_test_gray)
    p = psnr_from_mse(m)

    # option: compute color PSNR (per-channel average) if requested
    color_psnr = None
    if use_color:
        try:
            ref_color = read_image_color(path_ref)
            test_color = read_image_color(path_test)
            if ref_color.shape != test_color.shape:
                test_color = cv2.resize(test_color, (ref_color.shape[1], ref_color.shape[0]))
            mse_channels = [mse(ref_color[..., c], test_color[..., c]) for c in range(3)]
            psnr_channels = [psnr_from_mse(x) for x in mse_channels]
            color_psnr = float(np.mean([p for p in psnr_channels if np.isfinite(p)]))
        except Exception:
            color_psnr = None

    return {
        "ssim": float(ssim_score),
        "mse": float(m),
        "psnr": float(p) if np.isfinite(p) else float('inf'),
        "color_psnr": color_psnr,
        "diff_image": diff
    }


# ----------------- GUI -----------------

class SSIMToolApp:
    def __init__(self, master):
        self.master = master
        master.title("SSIM + PSNR + MSE Tool")
        master.geometry("1000x700")

        # Paths and state
        self.ref_path = None
        self.test_path = None
        self.ref_folder = None
        self.test_folder = None
        self.results = []  # list of dicts

        # Top frame: single pair controls
        top_frame = tk.LabelFrame(master, text="Single Pair Mode", padx=8, pady=8)
        top_frame.pack(fill=tk.X, padx=10, pady=6)

        tk.Button(top_frame, text="選擇參考影像 (Reference)", command=self.choose_ref).grid(row=0, column=0)
        self.lbl_ref = tk.Label(top_frame, text="未選擇")
        self.lbl_ref.grid(row=0, column=1, sticky="w")

        tk.Button(top_frame, text="選擇比較影像 (Test)", command=self.choose_test).grid(row=1, column=0)
        self.lbl_test = tk.Label(top_frame, text="未選擇")
        self.lbl_test.grid(row=1, column=1, sticky="w")

        tk.Button(top_frame, text="計算 (Single)", command=self.compute_single, bg="#4CAF50", fg="white").grid(row=0, column=2, rowspan=2, padx=10)

        # preview thumbnails
        thumb_frame = tk.Frame(top_frame)
        thumb_frame.grid(row=0, column=3, rowspan=2, padx=10)
        self.thumb_ref_label = tk.Label(thumb_frame)
        self.thumb_ref_label.pack(side=tk.LEFT, padx=5)
        self.thumb_test_label = tk.Label(thumb_frame)
        self.thumb_test_label.pack(side=tk.LEFT, padx=5)

        # Middle frame: batch mode
        batch_frame = tk.LabelFrame(master, text="Batch Mode (folder match by filename)", padx=8, pady=8)
        batch_frame.pack(fill=tk.X, padx=10, pady=6)

        tk.Button(batch_frame, text="選擇參考資料夾", command=self.choose_ref_folder).grid(row=0, column=0)
        self.lbl_ref_folder = tk.Label(batch_frame, text="未選擇")
        self.lbl_ref_folder.grid(row=0, column=1, sticky="w")

        tk.Button(batch_frame, text="選擇比較資料夾", command=self.choose_test_folder).grid(row=1, column=0)
        self.lbl_test_folder = tk.Label(batch_frame, text="未選擇")
        self.lbl_test_folder.grid(row=1, column=1, sticky="w")

        tk.Button(batch_frame, text="執行 Batch 計算", command=self.run_batch, bg="#2196F3", fg="white").grid(row=0, column=2, rowspan=2, padx=10)

        # Results frame
        res_frame = tk.LabelFrame(master, text="Results", padx=8, pady=8)
        res_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        # Treeview for results
        cols = ("ref", "test", "ssim", "mse", "psnr", "color_psnr")
        self.tree = ttk.Treeview(res_frame, columns=cols, show='headings')
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor='center')
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.tree.bind('<<TreeviewSelect>>', self.on_select_row)

        # right side: diff preview and buttons
        right_frame = tk.Frame(res_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.Y, padx=8)

        tk.Label(right_frame, text="Diff Map Preview").pack()
        self.diff_label = tk.Label(right_frame)
        self.diff_label.pack()

        tk.Button(right_frame, text="匯出 Excel", command=self.export_excel).pack(fill=tk.X, pady=4)
        tk.Button(right_frame, text="匯出 PDF 報表", command=self.export_pdf).pack(fill=tk.X, pady=4)
        tk.Button(right_frame, text="另存 CSV", command=self.save_csv).pack(fill=tk.X, pady=4)

        # status bar
        self.status = tk.Label(master, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    # ----- GUI actions -----
    def choose_ref(self):
        p = filedialog.askopenfilename(title="選擇參考影像", filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")])
        if p:
            self.ref_path = p
            self.lbl_ref.config(text=os.path.basename(p))
            self.show_thumbnail(p, self.thumb_ref_label)

    def choose_test(self):
        p = filedialog.askopenfilename(title="選擇比較影像", filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")])
        if p:
            self.test_path = p
            self.lbl_test.config(text=os.path.basename(p))
            self.show_thumbnail(p, self.thumb_test_label)

    def choose_ref_folder(self):
        d = filedialog.askdirectory(title="選擇參考資料夾")
        if d:
            self.ref_folder = d
            self.lbl_ref_folder.config(text=d)

    def choose_test_folder(self):
        d = filedialog.askdirectory(title="選擇比較資料夾")
        if d:
            self.test_folder = d
            self.lbl_test_folder.config(text=d)

    def show_thumbnail(self, path, label, size=(150,150)):
        try:
            img = Image.open(path)
            img.thumbnail(size)
            tkimg = ImageTk.PhotoImage(img)
            label.config(image=tkimg)
            label.image = tkimg
        except Exception as e:
            print('thumb error', e)

    def compute_single(self):
        if not self.ref_path or not self.test_path:
            messagebox.showerror("錯誤", "請先選擇參考與比較影像")
            return
        self.status.config(text="計算中...")
        self.master.update()
        try:
            res = compute_metrics(self.ref_path, self.test_path, use_color=True)
            row = {
                'ref': os.path.basename(self.ref_path),
                'test': os.path.basename(self.test_path),
                'ssim': res['ssim'],
                'mse': res['mse'],
                'psnr': res['psnr'],
                'color_psnr': res['color_psnr'],
                'ref_path': self.ref_path,
                'test_path': self.test_path,
                'diff_image': res['diff_image']
            }
            self.results.append(row)
            self.insert_row(row)
            self.status.config(text="Single 計算完成")
        except Exception as e:
            messagebox.showerror("錯誤", str(e))
            self.status.config(text="Error")

    def insert_row(self, row):
        values = (row['ref'], row['test'], f"{row['ssim']:.4f}", f"{row['mse']:.1f}", f"{row['psnr']:.2f}", f"{row['color_psnr']:.2f} if row['color_psnr'] else 'N/A' ")
        self.tree.insert('', tk.END, values=values)

    def run_batch(self):
        if not self.ref_folder or not self.test_folder:
            messagebox.showerror("錯誤", "請先選擇兩個資料夾")
            return
        self.status.config(text="Batch 計算中...")
        self.master.update()

        ref_files = {os.path.basename(f): os.path.join(self.ref_folder, f) for f in os.listdir(self.ref_folder) if f.lower().endswith(('.png','.jpg','.jpeg','.bmp'))}
        test_files = {os.path.basename(f): os.path.join(self.test_folder, f) for f in os.listdir(self.test_folder) if f.lower().endswith(('.png','.jpg','.jpeg','.bmp'))}

        common = sorted(set(ref_files.keys()).intersection(set(test_files.keys())))
        if not common:
            messagebox.showinfo("資訊", "兩個資料夾中沒有相同檔名的影像")
            self.status.config(text="No matching files")
            return

        for name in common:
            try:
                refp = ref_files[name]
                testp = test_files[name]
                res = compute_metrics(refp, testp, use_color=True)
                row = {
                    'ref': name,
                    'test': name,
                    'ssim': res['ssim'],
                    'mse': res['mse'],
                    'psnr': res['psnr'],
                    'color_psnr': res['color_psnr'],
                    'ref_path': refp,
                    'test_path': testp,
                    'diff_image': res['diff_image']
                }
                self.results.append(row)
                self.insert_row(row)
            except Exception as e:
                print('batch error on', name, e)

        self.status.config(text=f"Batch 完成: {len(common)} 組")

    def on_select_row(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        vals = item['values']
        # find matching results entry
        for r in self.results:
            if r['ref'] == vals[0] and r['test'] == vals[1]:
                # show diff image
                diff = r.get('diff_image')
                if diff is not None:
                    pil = Image.fromarray(diff)
                    pil = pil.resize((300,300))
                    tkimg = ImageTk.PhotoImage(pil)
                    self.diff_label.config(image=tkimg)
                    self.diff_label.image = tkimg
                # show thumbnails
                try:
                    self.show_thumbnail(r['ref_path'], self.thumb_ref_label)
                    self.show_thumbnail(r['test_path'], self.thumb_test_label)
                except Exception:
                    pass
                break

    # Export functions
    def export_excel(self):
        if not self.results:
            messagebox.showinfo("資訊", "沒有結果可匯出")
            return
        path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel','*.xlsx')])
        if not path:
            return
        df = pd.DataFrame(self.results)
        # drop image arrays before saving
        df2 = df.drop(columns=['diff_image','ref_path','test_path'], errors='ignore')
        df2.to_excel(path, index=False)
        messagebox.showinfo('完成', f'已匯出到 {path}')

    def save_csv(self):
        if not self.results:
            messagebox.showinfo("資訊", "沒有結果可保存")
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
        if not path:
            return
        df = pd.DataFrame(self.results)
        df2 = df.drop(columns=['diff_image','ref_path','test_path'], errors='ignore')
        df2.to_csv(path, index=False)
        messagebox.showinfo('完成', f'已保存為 {path}')

    def export_pdf(self):
        if not self.results:
            messagebox.showinfo("資訊", "沒有結果可匯出")
            return
        path = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF','*.pdf')])
        if not path:
            return

        df = pd.DataFrame(self.results)
        df2 = df[['ref','test','ssim','mse','psnr','color_psnr']]

        # create a simple matplotlib table report
        fig, ax = plt.subplots(figsize=(11, max(6, 0.4*len(df2)+1)))
        ax.axis('off')
        ax.set_title('SSIM/PSNR/MSE Report - ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # round numbers for nicer output
        display_df = df2.copy()
        display_df['ssim'] = display_df['ssim'].map(lambda x: f"{x:.4f}")
        display_df['mse'] = display_df['mse'].map(lambda x: f"{x:.1f}")
        display_df['psnr'] = display_df['psnr'].map(lambda x: f"{x:.2f}")
        display_df['color_psnr'] = display_df['color_psnr'].map(lambda x: f"{x:.2f}" if pd.notnull(x) else 'N/A')

        table = ax.table(cellText=display_df.values, colLabels=display_df.columns, loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.2)

        plt.savefig(path, bbox_inches='tight')
        plt.close(fig)
        messagebox.showinfo('完成', f'PDF 已匯出到 {path}')


# ----------------- Run App -----------------

if __name__ == '__main__':
    root = tk.Tk()
    app = SSIMToolApp(root)
    root.mainloop()
