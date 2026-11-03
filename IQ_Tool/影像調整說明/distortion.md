"""
程式名稱: Lens Optical Distortion & Correction Framework
作者: Sam 影像處理小幫手
描述: 本程式示範基於徑向畸變模型 (Radial Distortion Model) 的影像幾何變形模擬。
      內含完整的影像處理管線，並預留了進階光學校正（如色差與暗角補償）的擴充介面。
"""

import cv2
import numpy as np


class LensOpticsSimulator:

  def __init__(self, k1: float = -0.2, k2: float = 0.05):
    """初始化光學鏡頭模擬器參數

    :param k1: 二階徑向畸變係數 (負數代表桶形畸變，正數代表枕形畸變)
    :param k2: 四階徑向畸變係數 (用於微調邊緣畸變曲線)
    """
    self.k1 = k1
    self.k2 = k2

    # [擴充預留] 可在此初始化色差補償或邊緣亮度衰減（暗角）參數
    # self.chromatic_shift = [1.01, 1.0, 0.99]  # R, G, B 通道微調係數
    # self.vignetting_coeff = 0.85

  def simulate_radial_distortion(self, image: np.ndarray) -> np.ndarray:
    """步驟一：模擬鏡頭產生的光學畸變 (以徑向畸變為主)"""
    h, w = image.shape[:2]
    # 計算影像中心點坐標
    cx, cy = w / 2.0, h / 2.0

    # 建立網格坐標
    y_indices, x_indices = np.indices((h, w), dtype=np.float32)

    # 將坐標平移至以中心為原點，並進行歸一化
    x_norm = (x_indices - cx) / cx
    y_norm = (y_indices - cy) / cy

    # 計算距離平方 r^2
    r2 = x_norm**2 + y_norm**2

    # 套用徑向畸變多項式模型: x_distorted = x * (1 + k1*r^2 + k2*r^4)
    radial_factor = 1.0 + self.k1 * r2 + self.k2 * (r2**2)

    x_distorted = x_norm * radial_factor * cx + cx
    y_distorted = y_norm * radial_factor * cy + cy

    # 使用重取樣 (Remap) 將原圖進行幾何變形映射
    distorted_image = cv2.remap(
        image,
        x_distorted,
        y_distorted,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0),
    )

    return distorted_image

  # ==========================================
  # [預留擴充功能] 未來可在此新增進階光學修正方法
  # ==========================================
  def _apply_chromatic_aberration_correction(self, image: np.ndarray) -> np.ndarray:
    """[預留] 模擬或修正倍率色差 (Lateral Chromatic Aberration)

    實作思路: 將影像拆分為 B, G, R 三個通道，對 R 與 B 通道進行微幅的縮放或平移，
    以模擬或消除邊緣色散。
    """
    # 程式碼尚未實作，留待日後擴充
    pass

  def _apply_vignetting_correction(self, image: np.ndarray) -> np.ndarray:
    """[預留] 模擬或補償鏡頭邊緣失光 (Vignetting / 畫面四角變暗)

    實作思路: 產生一個以中心向外遞減的 2D 亮度衰減遮罩 (Cos^4 定律)，與影像相乘。
    """
    # 程式碼尚未實作，留待日後擴充
    pass

  def process(self, image: np.ndarray) -> np.ndarray:
    """執行完整的光學畸變模擬與校正管線"""
    # 1. 執行光學畸變模擬
    distorted = self.simulate_radial_distortion(image)

    # [擴充預留] 若未來啟用色差或暗角處理，可在此調用
    # distorted = self._apply_chromatic_aberration_correction(distorted)
    # distorted = self._apply_vignetting_correction(distorted)

    return distorted


# ==========================================
# 程式使用範例 (Usage Example)
# ==========================================
if __name__ == "__main__":
  # 建立一個測試用的棋盤格紋或幾何圖形畫布，方便觀察畸變效果
  test_canvas = np.ones((600, 600, 3), dtype=np.uint8) * 240
  # 畫幾條基準線與網格
  for i in range(0, 600, 50):
    cv2.line(test_canvas, (i, 0), (i, 600), (200, 200, 200), 1)
    cv2.line(test_canvas, (0, i), (600, i), (200, 200, 200), 1)
  cv2.circle(test_canvas, (300, 300), 150, (0, 0, 255), 2)

  # 實例化光學模擬器 (設定負係數模擬明顯的桶形畸變)
  optics_sim = LensOpticsSimulator(k1=-0.3, k2=0.1)

  # 執行處理
  result_frame = optics_sim.process(test_canvas)

  print(
      "光學鏡頭畸變模擬管線執行完畢！可根據專案需求在類別中擴充"
      " _apply_vignetting_correction。"
  )