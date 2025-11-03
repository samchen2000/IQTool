"""
af_demo.py
示範：簡易 CAF (contrast-based) 與 模擬 PDAF (phase-correlation disparity)
說明（中文註解充足），教育用途。

需要套件：
  pip install numpy matplotlib pillow opencv-python

此程式做以下事：
 1) 讀入影像（或用內建的測試圖）
 2) 產生不同模糊程度的 focus-stack（模擬不同焦距位置）
 3) 對每張圖計算對比指標（Variance of Laplacian） -> 示範 CAF
 4) 以 hill-climb（鄰近搜尋）演示 CAF 的搜尋行為
 5) 模擬 PDAF：用左右小位移的影像當作左右半孔徑影像，使用 phase-correlation 估位移，
    並展示位移量 (disparity) 隨模糊程度的變化（需要再校準以映射到 lens steps）
"""

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageFilter
import sys

# 嘗試使用 cv2 做 subpixel shift，如果沒有則 fallback 到整數位移的簡單方法
try:
    import cv2
    _HAS_CV2 = True
except Exception:
    _HAS_CV2 = False

def load_image_gray(path=None, size=(512,512)):
    """載入灰階圖片。若未提供 path，會自動產生一張測試用圖（含細節與紋理）。"""
    if path:
        img = Image.open(path).convert('L')
        img = img.resize(size, Image.LANCZOS)
    else:
        # 建一張 synthetic test image (checker + text + gaussian noise)
        img = Image.new('L', size, color=128)
        arr = np.array(img, dtype=np.float32)
        # checker
        cx, cy = size[0]//8, size[1]//8
        for y in range(size[1]):
            for x in range(size[0]):
                if ((x//cx) + (y//cy)) % 2 == 0:
                    arr[y,x] += 40
        # add text using PIL
        img = Image.fromarray(np.clip(arr,0,255).astype(np.uint8))
        # add a small sharp detail rectangle
        for y in range(60, 120):
            for x in range(200, 300):
                arr[y,x] = 255 if ( (x+y) % 6 < 3 ) else 0
        arr += np.random.normal(0, 4, size)  # gentle noise
        img = Image.fromarray(np.clip(arr,0,255).astype(np.uint8))
    return img

def gaussian_blur_pil(img_pil, sigma):
    """用 PIL GaussianBlur 做模糊（sigma 可小於1，但 PIL 的參數為 radius）"""
    # PIL ImageFilter.GaussianBlur 的參數是 radius ≈ sigma
    return img_pil.filter(ImageFilter.GaussianBlur(radius=sigma))

def var_laplacian(np_img):
    """計算 Variance of Laplacian 當作 focus metric。
    np_img: 2D float image (0..255)
    """
    # 直接用簡單的 discrete Laplacian kernel
    K = np.array([[0,1,0],[1,-4,1],[0,1,0]], dtype=np.float32)
    # convolution (valid) using FFT-based conv for simplicity
    f = np.fft.rfft2(np_img)
    kpad = np.zeros_like(np_img)
    kh, kw = K.shape
    kpad[:kh, :kw] = K[::-1, ::-1]  # flip kernel
    Fk = np.fft.rfft2(kpad)
    conv = np.fft.irfft2(f * Fk)
    lap = conv
    return float(lap.var())

def phase_correlation_shift(img1, img2):
    """用 phase correlation 計算 img2 相對 img1 的平移 (dy, dx)。
    使用 FFT cross-power spectrum。
    影像請先轉為 float，並視需要 windowing。
    """
    a = np.array(img1, dtype=np.float32)
    b = np.array(img2, dtype=np.float32)
    # remove mean
    a -= a.mean()
    b -= b.mean()
    # windowing could be helpful in實務上，但此處省略以簡潔示範
    # FFT
    fa = np.fft.fft2(a)
    fb = np.fft.fft2(b)
    R = fa * np.conj(fb)
    denom = np.abs(R)
    # 防止除以零
    denom[denom == 0] = 1e-9
    R /= denom
    r = np.fft.ifft2(R)
    r_abs = np.abs(r)
    # 取得峰值位置
    maxpos = np.unravel_index(np.argmax(r_abs), r_abs.shape)
    shift_y = maxpos[0]
    shift_x = maxpos[1]
    # 將 wrap-around 轉成負值表示
    h, w = a.shape
    if shift_y > h//2:
        shift_y -= h
    if shift_x > w//2:
        shift_x -= w
    return (float(shift_y), float(shift_x))

def shift_image(img_pil, dx, dy):
    """用 cv2 做 subpixel shift（若可用），否則用 PIL 的 transform（較差但可用）。"""
    if _HAS_CV2:
        arr = np.array(img_pil, dtype=np.float32)
        h, w = arr.shape
        M = np.array([[1,0,dx],[0,1,dy]], dtype=np.float32)
        shifted = cv2.warpAffine(arr, M, (w,h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        return Image.fromarray(np.clip(shifted,0,255).astype(np.uint8))
    else:
        # PIL transform expects (a,b,c,d,e,f) inverse mapping
        w, h = img_pil.size
        # inverse transform matrix for shift is (1, 0, -dx, 0, 1, -dy)
        return img_pil.transform((w,h), Image.AFFINE, (1,0,-dx,0,1,-dy), resample=Image.BILINEAR)

def hill_climb_caf(img_pil, search_range=(0.5,6.0), steps=30, start_idx=None):
    """示範 CAF 的 hill-climb 使用：
       - 先建立 focus stack（使用 Gaussian blur）
       - 計算 metric（var laplacian）
       - 以 hill-climb 找到局部最大 (模擬相機要做的搜尋)
    回傳：best_sigma, metrics_list, sigmas_list
    """
    sigmas = np.linspace(search_range[0], search_range[1], steps)
    metrics = []
    stack = []
    for s in sigmas:
        b = gaussian_blur_pil(img_pil, s)
        stack.append(b)
        arr = np.array(b, dtype=np.float32)
        metrics.append(var_laplacian(arr))
    metrics = np.array(metrics)
    # 若沒有給初始 index，從中間開始
    if start_idx is None:
        idx = len(sigmas)//2
    else:
        idx = start_idx
    # hill-climb（鄰域搜尋直到到達局部最大）
    while True:
        left = metrics[idx-1] if idx-1 >=0 else -np.inf
        right = metrics[idx+1] if idx+1 < len(metrics) else -np.inf
        cur = metrics[idx]
        if left > cur and left >= right:
            idx -= 1
        elif right > cur and right >= left:
            idx += 1
        else:
            break
    best_sigma = sigmas[idx]
    return best_sigma, sigmas, metrics

def demo_all(path=None):
    img = load_image_gray(path)
    plt.figure(figsize=(8,8))
    plt.imshow(img, cmap='gray')
    plt.title("Input image (grayscale)")
    plt.axis('off')
    plt.show()

    # CAF demo: focus stack & metrics
    best_sigma, sigmas, metrics = hill_climb_caf(img, search_range=(0.5,6.0), steps=40)
    print(f"[CAF] hill-climb 找到局部最大對應 sigma ≈ {best_sigma:.3f}")

    plt.figure()
    plt.plot(sigmas, metrics, marker='o')
    plt.xlabel("blur sigma (simulated)")
    plt.ylabel("focus metric (Var Laplacian)")
    plt.title("CAF: focus metric vs blur (示範)")
    plt.grid(True)
    plt.show()

    # PDAF demo (simulation)
    # 我們用「左右微位移」當作左右子孔徑成像（簡化模擬）
    # 真實系統會有 aperture-based PSF 差異；這裡只示意 disparity-測量流程
    disp_list = []
    blur_list = np.linspace(0.5, 6.0, 20)
    for s in blur_list:
        b = gaussian_blur_pil(img, s)  # 模擬 defocus (較大 s => more defocus)
        # 模擬左右子孔徑影像：對同一模糊圖作左右微移（量會和 defocus 有關）
        # 這裡用一個簡單模型：disparity ≈ alpha * s （非實際光學公式，需要校準）
        alpha = 0.6  # 模擬的比例常數（示範用）
        dx = alpha * s  # x shift magnitude
        left = shift_image(b, -dx/2.0, 0)
        right = shift_image(b,  dx/2.0, 0)
        # 以 phase-correlation 計算 shift (右相對左)
        shift = phase_correlation_shift(np.array(left, dtype=np.float32), np.array(right, dtype=np.float32))
        # shift 是 (dy, dx)
        disp_list.append(shift[1])  # 用水平位移
    disp_list = np.array(disp_list)
    plt.figure()
    plt.plot(blur_list, disp_list, marker='x')
    plt.xlabel("simulated blur sigma")
    plt.ylabel("measured disparity (pixels)")
    plt.title("Simulated PDAF: disparity vs defocus (需校準 mapping)")
    plt.grid(True)
    plt.show()
    print("[PDAF 模擬] 注意：真實系統需校準 disparity -> lens motor steps 的 mapping；此處僅示範量測流程")

if __name__ == "__main__":
    # 若有 command-line arg，當作 image path
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = None
    demo_all(path)
