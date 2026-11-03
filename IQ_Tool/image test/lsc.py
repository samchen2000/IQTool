import cv2
import numpy as np
import matplotlib.pyplot as plt

def generate_lens_shading_gain_map(height, width, k=1.2, gamma=2.0, center_offset=(0, 0)):
    """
    【Sam 影像處理小幫手 - 函數說明】
    計算 2D Lens Shading 補償增益圖 (Gain Map)。
    """
    # 1. 建立影像 X, Y 座標網格
    y_indices, x_indices = np.indices((height, width), dtype=np.float32)

    # 2. 計算光學中心 (預留非對稱偏移量 dx, dy)
    cx = (width / 2.0) + center_offset[0]
    cy = (height / 2.0) + center_offset[1]

    # 3. 計算各點至光學中心之歐式距離 r
    dx = x_indices - cx
    dy = y_indices - cy
    dist_sq = dx**2 + dy**2

    # 4. 正規化半徑 (Normalized Radius, 範圍 0.0 ~ 1.0)
    max_dist_sq = (width / 2.0)**2 + (height / 2.0)**2
    r_norm = np.sqrt(dist_sq / max_dist_sq)

    # 5. 多項式增益模型計算: Gain(r) = 1 + k * (r^gamma)
    gain_map = 1.0 + k * (r_norm ** gamma)

    return gain_map


def simulate_synthetic_vignetting(image_bgr, shading_intensity=1.4, gamma=2.0):
    """
    【Sam 預留模組 - 人為暗角模擬器】
    對無暗角之原始影像添加物理光學暗角衰減效果，用於教學與測試對比。
    """
    if shading_intensity <= 0:
        return image_bgr.copy()
        
    h, w, c = image_bgr.shape
    # 生成衰減係數 ( Gain 的倒數即為 Attenuation )
    gain_map = generate_lens_shading_gain_map(h, w, k=shading_intensity, gamma=gamma)
    attenuation_map = 1.0 / gain_map

    degraded_img = image_bgr.astype(np.float32)
    for ch in range(c):
        degraded_img[:, :, ch] *= attenuation_map

    return np.clip(degraded_img, 0, 255).astype(np.uint8)


def apply_lens_shading_correction(image_bgr, k=1.2, gamma=2.0, channel_gains=(1.0, 1.0, 1.0)):
    """
    對輸入 BGR 影像進行 Lens Shading 畫素補償。
    """
    h, w, c = image_bgr.shape
    base_gain_map = generate_lens_shading_gain_map(h, w, k=k, gamma=gamma)
    img_float = image_bgr.astype(np.float32)
    corrected_img = np.zeros_like(img_float)

    for ch in range(3):
        ch_gain = base_gain_map * channel_gains[ch]
        corrected_img[:, :, ch] = img_float[:, :, ch] * ch_gain

    # 【預留擴充功能 - 備用區】
    # ---------------------------------------------------------------------
    # 1. 預留：過曝截斷預防 (Clipping Avoidance / Soft Knee Mapping)
    # corrected_img = np.clip(corrected_img, 0, 255)
    # ---------------------------------------------------------------------

    corrected_img = np.clip(corrected_img, 0, 255).astype(np.uint8)
    return corrected_img, base_gain_map


if __name__ == "__main__":
    print("🤖 Sam 影像處理小幫手 - 正在執行 Lens Shading 校正模擬...")

    # 創建立完美無瑕的原始畫質圖片
    clean_image = np.full((400, 400, 3), 180, dtype=np.uint8)

    # 1. 人為加入衰減強度為 1.4 的嚴重暗角
    raw_vignette_image = simulate_synthetic_vignetting(clean_image, shading_intensity=1.4)

    # 2. 使用演算法進行補償校正
    corrected_image, gain_map = apply_lens_shading_correction(raw_vignette_image, k=1.4, gamma=2.0)
    print("✅ 校正完成！可於控制面板即時觀察數值變化。")