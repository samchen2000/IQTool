"""
EMVA1288_AutoReport_Tool.py
自動讀取多資料夾影像，計算 EMVA1288 指標並產出 PDF 報告
支援影像格式：png, bmp, jpg, jpeg
輸出：./results/EMVA1288_Report.pdf 與 CSV 結果檔

使用說明：
  - 將各曝光階影像放入 ./data/exposure_001, exposure_002, ...
    每個 exposure_* 資料夾建議放 2 張 (frame1, frame2)，也支援多張 (程式將使用前兩張估算 temporal variance；若只有 1 張則跳過 temporal variance)
  - 明亮場（PRNU/DSNU）請放在 ./bright_frames/（多張）
  - 暗場請放在 ./dark_frames/（每個曝光時間對應 dark_{texp}ms.png 或多張）
  - 若有光電二極體校正值，放 ./irradiance.csv（單欄，與 exposure_* 的順序對應），否則程式以相對單位代替 irradiance
依賴套件：numpy, opencv-python (cv2), matplotlib, scipy
"""

import os
import glob
import numpy as np
import cv2
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline
from matplotlib.backends.backend_pdf import PdfPages
import csv
import datetime

# ------------------ User Config ------------------
DATA_FOLDER = "./data"
BRIGHT_FOLDER = "./bright_frames"
DARK_FOLDER = "./dark_frames"
RESULTS_FOLDER = "./results"
IRRADIANCE_CSV = "./irradiance.csv"  # 若無，程式會用相對單位
MIN_EXPOSURE_STEPS = 3  # 最少曝光步數保護
# -------------------------------------------------

os.makedirs(RESULTS_FOLDER, exist_ok=True)

def find_exposure_folders(data_folder):
    """Find folders named exposure_XXX under data_folder, sorted by name"""
    pattern = os.path.join(data_folder, "exposure_*")
    folders = sorted([f for f in glob.glob(pattern) if os.path.isdir(f)])
    return folders

def read_images_from_folder(folder, max_read=10):
    """Read image files from folder; support png, bmp, jpg, jpeg"""
    exts = ("*.png", "*.bmp", "*.jpg", "*.jpeg", "*.tif", "*.tiff")
    files = []
    for e in exts:
        files.extend(sorted(glob.glob(os.path.join(folder, e))))
    files = files[:max_read]
    imgs = []
    for f in files:
        img = cv2.imread(f, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        imgs.append(img.astype(np.float32))
    return imgs, files

def load_irradiance(csv_path, n):
    if os.path.exists(csv_path):
        vals = []
        with open(csv_path, newline='') as cf:
            rdr = csv.reader(cf)
            for row in rdr:
                if not row: continue
                try:
                    vals.append(float(row[0]))
                except:
                    continue
        vals = np.array(vals, dtype=float)
        if len(vals) >= n:
            return vals[:n]
        else:
            print("警告：irradiance.csv 長度小於曝光步數，將使用相對單位代替。")
    # fallback: relative units 1..n
    return np.linspace(1.0, float(n), n)

def compute_temporal_stats(img1, img2):
    """Compute mean and temporal variance from two images"""
    mean1 = np.mean(img1)
    mean2 = np.mean(img2)
    mean = 0.5 * (mean1 + mean2)
    var = np.mean((img1 - img2)**2) / 2.0
    std = np.sqrt(var)
    return mean, std

def calc_nonuniformity_from_files(file_list, max_imgs=200):
    imgs = []
    for f in sorted(file_list)[:max_imgs]:
        img = cv2.imread(f, cv2.IMREAD_GRAYSCALE).astype(np.float32)
        imgs.append(img)
    if len(imgs) == 0:
        return None, None, None
    avg_img = np.mean(imgs, axis=0)
    mean_val = np.mean(avg_img)
    # DSNU measured as std of (avg_img - mean of single frame) normalized by mean
    dsnu = np.std(avg_img - imgs[0].mean()) / mean_val * 100.0
    prnu = np.std(avg_img) / mean_val * 100.0
    return avg_img, dsnu, prnu

def dark_current_from_dark_folder(dark_folder, exposure_times_ms=None):
    """If dark files named dark_{texp}ms.* exist, compute mean vs texp slope (DN/ms)"""
    if exposure_times_ms is None:
        # try to infer unique exposure times from filenames
        files = sorted(glob.glob(os.path.join(dark_folder, "*")))
        exposures = []
        for f in files:
            bn = os.path.basename(f).lower()
            if "dark_" in bn and "ms" in bn:
                try:
                    t = bn.split("dark_")[1].split("ms")[0]
                    exposures.append((int(t), f))
                except:
                    continue
        if not exposures:
            # fallback: compute mean of all dark files and report as single point
            dark_imgs = [cv2.imread(f, cv2.IMREAD_GRAYSCALE).astype(np.float32) for f in files if cv2.imread(f, cv2.IMREAD_GRAYSCALE) is not None]
            if not dark_imgs:
                return None, None, None
            mean_dark = np.mean([np.mean(im) for im in dark_imgs])
            return (np.array([0.0]), np.array([mean_dark])), None, None
        exposures = sorted(exposures, key=lambda x: x[0])
        times = []
        means = []
        for t, f in exposures:
            img = cv2.imread(f, cv2.IMREAD_GRAYSCALE).astype(np.float32)
            times.append(float(t))
            means.append(np.mean(img))
        times = np.array(times)
        means = np.array(means)
        # linear fit
        slope, intercept = np.polyfit(times, means, 1)
        return (times, means), slope, intercept
    else:
        # user provided exposure times
        times = []
        means = []
        for t in exposure_times_ms:
            path = os.path.join(dark_folder, f"dark_{int(t)}ms.*")
            files = []
            for ext in ("png","bmp","jpg","jpeg","tif","tiff"):
                files.extend(sorted(glob.glob(os.path.join(dark_folder, f"dark_{int(t)}ms."+ext))))
            if not files:
                continue
            img = cv2.imread(files[0], cv2.IMREAD_GRAYSCALE).astype(np.float32)
            times.append(float(t))
            means.append(np.mean(img))
        if not times:
            return None, None, None
        times = np.array(times); means = np.array(means)
        slope, intercept = np.polyfit(times, means, 1)
        return (times, means), slope, intercept

def generate_report(results, pdf_path):
    """Generate PDF report using matplotlib PdfPages"""
    with PdfPages(pdf_path) as pdf:
        # Summary page
        fig = plt.figure(figsize=(8.27, 11.69))  # A4 in inches
        fig.clf()
        txt = f"EMVA1288 自動報告\n生成時間: {datetime.datetime.now().isoformat()}\n\n"
        for k, v in results['summary'].items():
            txt += f"{k}: {v}\n"
        plt.axis('off')
        plt.text(0.01, 0.99, txt, va='top', wrap=True, fontsize=10)
        pdf.savefig(fig); plt.close(fig)

        # Characteristic Curve
        fig, ax = plt.subplots(figsize=(8,6))
        ax.plot(results['irradiance'], results['mean_values'], marker='o', linestyle='-')
        ax.set_xscale('linear')
        ax.set_xlabel('Irradiance (relative units)')
        ax.set_ylabel('Mean Output (DN)')
        ax.set_title('Characteristic Curve')
        ax.grid(True)
        pdf.savefig(fig); plt.close(fig)

        # SNR curves
        fig, ax = plt.subplots(figsize=(8,6))
        ax.semilogx(results['irradiance'], results['SNRp'], linestyle='-', marker='o', label='SNRp (Input)')
        ax.semilogx(results['irradiance'], results['SNRy'], linestyle='--', marker='o', label='SNRy (Output)')
        ax.set_xlabel('Irradiance (relative units)')
        ax.set_ylabel('SNR')
        ax.set_title('SNR Curves')
        ax.legend()
        ax.grid(True)
        pdf.savefig(fig); plt.close(fig)

        # PRNU map and histogram
        if results.get('prnu_map') is not None:
            fig, ax = plt.subplots(figsize=(8,6))
            ax.imshow(results['prnu_map'], cmap='gray')  # showing mean image
            ax.set_title('Average Bright Field (for PRNU)')
            ax.axis('off')
            pdf.savefig(fig); plt.close(fig)

            fig, ax = plt.subplots(figsize=(8,6))
            ax.hist(results['prnu_hist'].ravel(), bins=100)
            ax.set_title('PRNU Histogram (pixel values of average bright image)')
            pdf.savefig(fig); plt.close(fig)

        # Dark current plot if available
        if results.get('dark_times') is not None and results.get('dark_means') is not None:
            fig, ax = plt.subplots(figsize=(8,6))
            ax.plot(results['dark_times'], results['dark_means'], marker='o', linestyle='-')
            ax.set_xlabel('Exposure time (ms)')
            ax.set_ylabel('Mean dark signal (DN)')
            ax.set_title('Dark Current vs Exposure Time')
            ax.grid(True)
            pdf.savefig(fig); plt.close(fig)

        # Save a CSV summary page as text figure
        fig = plt.figure(figsize=(8.27, 11.69))
        fig.clf()
        lines = ["Detailed numeric results:"]
        for k, v in results['detailed'].items():
            lines.append(f"{k}: {v}")
        plt.axis('off')
        plt.text(0.01, 0.99, "\n".join(lines), va='top', wrap=True, fontsize=9)
        pdf.savefig(fig); plt.close(fig)

    print(f"PDF report saved to: {pdf_path}")

def save_csv_summary(results, csv_path):
    with open(csv_path, 'w', newline='') as cf:
        wr = csv.writer(cf)
        wr.writerow(['metric','value'])
        for k, v in results['detailed'].items():
            wr.writerow([k, v])
    print(f"CSV summary saved to: {csv_path}")

def run_all():
    exposure_folders = find_exposure_folders(DATA_FOLDER)
    if len(exposure_folders) < MIN_EXPOSURE_STEPS:
        print(f"錯誤：找不到足夠曝光階資料夾 (需要至少 {MIN_EXPOSURE_STEPS})，在 {DATA_FOLDER} 中找到 {len(exposure_folders)} 個。")
        return

    n = len(exposure_folders)
    irradiance = load_irradiance(IRRADIANCE_CSV, n)

    mean_values = []
    std_values = []
    exposure_names = []

    for idx, ef in enumerate(exposure_folders):
        imgs, files = read_images_from_folder(ef, max_read=10)
        if len(imgs) >= 2:
            mean, std = compute_temporal_stats(imgs[0], imgs[1])
        elif len(imgs) == 1:
            mean = np.mean(imgs[0])
            std = np.nan
        else:
            print(f"警告：曝光資料夾 {ef} 無影像，跳過")
            continue
        mean_values.append(mean)
        std_values.append(std)
        exposure_names.append(os.path.basename(ef))

    mean_values = np.array(mean_values)
    std_values = np.array(std_values)
    irradiance = np.array(irradiance[:len(mean_values)])

    # SNRy and SNRp
    SNRy = mean_values / std_values
    # Fit spline to get d(mu_p)/d(mu_y) -> using mu_y -> mu_p relation
    try:
        spline = UnivariateSpline(mean_values, irradiance, s=0)
        dp_dy = spline.derivative()(mean_values)
        SNRp = SNRy * np.abs(dp_dy)
    except Exception as e:
        print("警告：spline 擬合失敗，SNRp 將使用相對估計。", e)
        dp_dy = np.gradient(irradiance, mean_values)
        SNRp = SNRy * np.abs(dp_dy)

    # Dynamic Range (using SNRp, SNRp >=1 definition)
    try:
        SNR1_idx = np.where(SNRp >= 1)[0][0]
        DR = 20 * np.log10(SNRp[-1] / SNRp[SNR1_idx])
    except Exception:
        DR = np.nan

    # PRNU/DSNU from bright frames
    bright_files = []
    for ext in ("png","bmp","jpg","jpeg","tif","tiff"):
        bright_files.extend(sorted(glob.glob(os.path.join(BRIGHT_FOLDER, "*."+ext))))
    prnu_map, DSNU, PRNU = calc_nonuniformity_from_files(bright_files, max_imgs=500)

    # PRNU histogram data
    prnu_hist = None
    if prnu_map is not None:
        prnu_hist = prnu_map.flatten()

    # Dark current
    dark_info, dark_slope, dark_intercept = dark_current_from_dark_folder(DARK_FOLDER)
    dark_times = None; dark_means = None
    if dark_info is not None and isinstance(dark_info, tuple):
        dark_times, dark_means = dark_info

    # Compile results
    summary = {
        "Exposure steps": len(mean_values),
        "PRNU (%)": f"{PRNU:.4f}" if PRNU is not None else "N/A",
        "DSNU (%)": f"{DSNU:.4f}" if DSNU is not None else "N/A",
        "Dynamic Range (dB)": f"{DR:.2f}" if not np.isnan(DR) else "N/A",
        "Dark current (DN/ms)": f"{dark_slope:.6f}" if dark_slope is not None else "N/A"
    }
    detailed = {
        "mean_values_first": mean_values[0] if len(mean_values)>0 else np.nan,
        "mean_values_last": mean_values[-1] if len(mean_values)>0 else np.nan,
        "std_values_first": std_values[0] if len(std_values)>0 else np.nan,
        "std_values_last": std_values[-1] if len(std_values)>0 else np.nan,
        "PRNU_percent": PRNU,
        "DSNU_percent": DSNU,
        "DynamicRange_dB": DR,
        "Dark_slope_DN_per_ms": dark_slope
    }

    results = {
        "summary": summary,
        "detailed": detailed,
        "irradiance": irradiance,
        "mean_values": mean_values,
        "std_values": std_values,
        "SNRy": SNRy,
        "SNRp": SNRp,
        "prnu_map": prnu_map,
        "prnu_hist": prnu_hist,
        "dark_times": dark_times,
        "dark_means": dark_means
    }

    # Save PDF report
    pdf_path = os.path.join(RESULTS_FOLDER, "EMVA1288_Report.pdf")
    generate_report(results, pdf_path)
    csv_path = os.path.join(RESULTS_FOLDER, "EMVA1288_Summary.csv")
    save_csv_summary(results, csv_path)
    # Save numeric arrays as npz
    np.savez(os.path.join(RESULTS_FOLDER, "EMVA1288_numeric.npz"),
             irradiance=irradiance, mean_values=mean_values, std_values=std_values,
             SNRy=SNRy, SNRp=SNRp)

if __name__ == "__main__":
    run_all()
