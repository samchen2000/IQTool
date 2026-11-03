"""
程式名稱: Lens Flare & Bloom Simulation Tool
作者: Sam 影像處理小幫手
描述: 本程式示範如何在數位影像中實作基於亮度閥值的強光光暈 (Bloom) 效果。
      內含完整的影像處理管線，並預留了進階光學效果擴充介面。
"""

import cv2
import numpy as np


class LensFlareSimulator:

  def __init__(self, threshold_val=200, blur_ksize=51, intensity=0.6):
    """初始化光暈模擬器參數

    :param threshold_val: 決定畫面中哪些高亮度區域會產生光暈 (0-255)
    :param blur_ksize: 高斯模糊核心大小 (必須為奇數)，決定光暈的擴散範圍
    :param intensity: 光暈疊加到原圖上的強度權重
    """
    self.threshold_val = threshold_val
    self.blur_ksize = blur_ksize
    self.intensity = intensity

    # [擴充預留] 可在此初始化鏡頭鬼影(Ghosting)或星芒(Starburst)的設定
    # self.enable_ghosting = False
    # self.enable_starburst = False

  def extract_bright_regions(self, image: np.ndarray) -> np.ndarray:
    """步驟一：萃取影像中的高光區域（模擬強光源）"""
    # 轉換為灰階以計算亮度，或直接在通道上處理
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 套用閥值，保留高光部分
    _, bright_mask = cv2.threshold(
        gray, self.threshold_val, 255, cv2.THRESH_BINARY
    )

    # 將遮罩套用到原圖，保留高光色彩
    bright_spots = cv2.bitwise_and(image, image, mask=bright_mask)
    return bright_spots

  def apply_bloom_effect(self, bright_spots: np.ndarray) -> np.ndarray:
    """步驟二：對高光區域進行大範圍模糊，模擬光線在鏡頭內部的散射光暈"""
    # 使用高斯模糊製造擴散的光暈效果
    bloom_layer = cv2.GaussianBlur(
        bright_spots, (self.blur_ksize, self.blur_ksize), 0
    )
    return bloom_layer

  # ==========================================
  # [預留擴充功能] 未來可在此新增進階光學模擬方法
  # ==========================================
  def _apply_ghosting_effect(self, image: np.ndarray) -> np.ndarray:
    """[預留] 模擬鏡片間多重反射產生的幾何鬼影

    實作思路: 偵測中心對稱點，將高光區域按比例縮小、反轉並降低透明度疊加。
    """
    # 程式碼尚未實作，留待日後擴充
    pass

  def _apply_starburst_effect(self, image: np.ndarray) -> np.ndarray:
    """[預留] 模擬縮光圈產生的繞射星芒效果

    實作思路: 使用多方向的線性濾鏡 (Line Kernels) 對高光點進行放射狀模糊。
    """
    # 程式碼尚未實作，留待日後擴充
    pass

  def process(self, image: np.ndarray) -> np.ndarray:
    """執行完整的光暈影像處理管線"""
    # 1. 萃取高光
    brights = self.extract_bright_regions(image)

    # 2. 生成光暈層
    bloom = self.apply_bloom_effect(brights)

    # [擴充預留] 若未來啟用鬼影或星芒，可在此調用
    # if self.enable_ghosting:
    #     bloom = cv2.add(bloom, self._apply_ghosting_effect(image))

    # 3. 將光暈層以加權方式與原圖融合 (Screen Blend 效果的簡易替代)
    output = cv2.addWeighted(image, 1.0, bloom, self.intensity, 0)

    return output


# ==========================================
# 程式使用範例 (Usage Example)
# ==========================================
if __name__ == "__main__":
  # 建立一個測試用黑色畫布並在中央畫一個極亮的白色圓圈模擬太陽
  test_img = np.zeros((500, 500, 3), dtype=np.uint8)
  cv2.circle(test_img, (250, 250), 30, (255, 255, 255), -1)

  # 實例化光暈模擬器
  simulator = LensFlareSimulator(
      threshold_val=200, blur_ksize=75, intensity=0.8
  )

  # 執行處理
  result_img = simulator.process(test_img)

  print("光學光暈影像模擬處理完畢！可根據需求進一步擴充 _apply_ghosting_effect。")
