import numpy as np
import cv2
import matplotlib.pyplot as plt
from scipy.fftpack import fft

def calculate_sfr(image_roi):
    """
    計算簡易的 SFR (MTF) 曲線
    image_roi: 傳入一個包含斜邊的灰階影像區域 (ROI)
    """
    
    # 1. 影像線性化 (預留功能：如果影像有 Gamma，需先轉回線性空間)
    # image_linear = np.power(image_roi / 255.0, 2.2) 
    image_linear = image_roi.astype(float) / 255.0

    # 2. 取得 ESF (Edge Spread Function)
    # 在實際演算法中，我們會進行「超取樣(Oversampling)」來增加精確度
    # 這裡我們簡化處理，直接取每一行的平均值
    esf = np.mean(image_linear, axis=0)

    # 3. 取得 LSF (Line Spread Function) - 對 ESF 求導數
    lsf = np.diff(esf)

    # --- 預留功能：Windowing (窗函數) ---
    # 為了減少 FFT 的頻譜洩漏，通常會施加 Hamming 或 Hann Window
    # window = np.hamming(len(lsf))
    # lsf = lsf * window
    # ----------------------------------

    # 4. 計算 MTF (對 LSF 進行 FFT)
    n = len(lsf)
    mtf = np.abs(fft(lsf, n=n*2)) # 補零增加頻譜解析度
    mtf = mtf[:n] # 取正頻率部分
    
    # 5. 正規化：讓 DC 分量 (頻率 0) 為 1
    if mtf[0] != 0:
        mtf = mtf / mtf[0]

    return mtf

# --- 測試模擬數據 ---
def generate_test_edge(width=100, blur_sigma=2):
    """ 生成一個模糊的斜邊影像作為測試 """
    edge = np.zeros((100, width))
    edge[:, width//2:] = 1.0
    # 使用高斯模糊模擬鏡頭的點擴散函數 (PSF)
    edge_blurred = cv2.GaussianBlur(edge, (0, 0), sigmaX=blur_sigma)
    return (edge_blurred * 255).astype(np.uint8)

# 主程式
if __name__ == "__main__":
    # 產生測試影像
    roi = generate_test_edge(width=128, blur_sigma=3)
    
    # 計算 SFR
    mtf_curve = calculate_sfr(roi)
    
    # 繪圖
    plt.figure(figsize=(10, 5))
    
    plt.subplot(1, 2, 1)
    plt.title("Test ROI (Slanted Edge)")
    plt.imshow(roi, cmap='gray')
    
    plt.subplot(1, 2, 2)
    plt.title("MTF (SFR) Curve")
    plt.plot(mtf_curve)
    plt.xlabel("Spatial Frequency (cycles/pixel)")
    plt.ylabel("Modulation")
    plt.grid(True)
    plt.ylim(0, 1.1)
    plt.xlim(0, len(mtf_curve)//2) # 通常只看到 Nyquist 頻率
    
    plt.tight_layout()
    plt.show()