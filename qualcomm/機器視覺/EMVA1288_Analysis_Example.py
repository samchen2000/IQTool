import numpy as np
import cv2
import glob
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline

# === EMVA1288 測試分析範例 ===
# 1. 將每曝光階的兩張影像放在 data/exposure_001, exposure_002/... 目錄下
# 2. 修改 irradiance_values 為對應校正值（光電二極體校正結果）
# 3. 程式自動計算 µy, σy, SNR, 動態範圍, PRNU, DSNU, 暗電流

irradiance_values = np.linspace(1e2, 1e6, 50)  # 示例
data_folder = "./data/"

mean_values, std_values = [], []

for i in range(len(irradiance_values)):
    files = sorted(glob.glob(f"{data_folder}/exposure_{i+1:03d}/*.png"))
    imgs = [cv2.imread(f, cv2.IMREAD_GRAYSCALE).astype(np.float32) for f in files]
    mean1, mean2 = np.mean(imgs[0]), np.mean(imgs[1])
    var = np.mean((imgs[0] - imgs[1])**2) / 2
    mean_values.append((mean1 + mean2) / 2)
    std_values.append(np.sqrt(var))

mean_values = np.array(mean_values)
std_values = np.array(std_values)

plt.figure(); plt.plot(irradiance_values, mean_values, 'o-')
plt.xlabel('Irradiance (ph/cm²)'); plt.ylabel('Mean Output (DN)')
plt.title('Characteristic Curve'); plt.grid(True); plt.show()

SNRy = mean_values / std_values
spline = UnivariateSpline(mean_values, irradiance_values, s=0)
dp_dy = spline.derivative()(mean_values)
SNRp = SNRy * np.abs(dp_dy)

plt.figure()
plt.semilogx(irradiance_values, SNRp, 'r-', label='SNRp (Input)')
plt.semilogx(irradiance_values, SNRy, 'b--', label='SNRy (Output)')
plt.xlabel('Irradiance (ph/cm²)'); plt.ylabel('SNR')
plt.title('SNR Curves'); plt.legend(); plt.grid(True); plt.show()

SNR1_idx = np.where(SNRp >= 1)[0][0]
DR = 20 * np.log10(SNRp[-1] / SNRp[SNR1_idx])
print(f"Dynamic Range: {DR:.2f} dB")

def calc_nonuniformity(img_files):
    imgs = [cv2.imread(f, cv2.IMREAD_GRAYSCALE).astype(np.float32) for f in img_files]
    avg_img = np.mean(imgs, axis=0)
    mean_val = np.mean(avg_img)
    dsnu = np.std(avg_img - np.mean(imgs[0])) / mean_val * 100
    prnu = np.std(avg_img) / mean_val * 100
    return dsnu, prnu

dark_files = glob.glob('./dark/*.png')
light_files = glob.glob('./bright/*.png')
DSNU, PRNU = calc_nonuniformity(light_files)
print(f'DSNU: {DSNU:.3f} %, PRNU: {PRNU:.3f} %')

def dark_current_test(dark_folder, exposure_times):
    mean_darks = []
    for t in exposure_times:
        img = cv2.imread(f"{dark_folder}/dark_{t}ms.png", cv2.IMREAD_GRAYSCALE).astype(np.float32)
        mean_darks.append(np.mean(img))
    slope, _ = np.polyfit(exposure_times, mean_darks, 1)
    return slope

exposure_times = [10, 50, 100, 200, 400, 800]
dark_rate = dark_current_test('./dark_frames', exposure_times)
print(f'Dark Current: {dark_rate:.3f} DN/s')
