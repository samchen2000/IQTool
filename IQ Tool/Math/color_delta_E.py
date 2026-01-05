import cv2
import numpy as np
from skimage.color import rgb2lab, deltaE_cie2000
import matplotlib.pyplot as plt

# --- 1. 標準色塊的定義 (ColorChecker Classic 24色) ---
# 這裡使用標準 ColorChecker 24 色塊在 D65 光源下的 L*a*b* 參考值。
# 數值依據標準規範，實際應用中應使用儀器測量結果或標準文件。
# 數組順序：深棕 (Dark Skin) -> 淺綠 (Blue Sky) -> ... -> 黑 (Black)
# 為簡潔起見，這裡只列出前 6 個色塊作為示範：
REFERENCE_LAB = np.array([
    [37.95, 13.55, 14.06],  # 1. Dark Skin (深棕)
    [66.52, 17.58, 17.65],  # 2. Light Skin (淺棕)
    [31.25, 23.31, -2.49],  # 3. Blue Sky (天空藍)
    [54.38, -5.92, -26.39], # 4. Foliage (葉綠)
    [41.51, 40.23, -2.55],  # 5. Blue Flower (花藍)
    [49.49, -15.65, -23.59]  # 6. Bluish Green (藍綠)
    # ... 其他 18 個色塊
])

class ColorAccuracyAnalyzer:
    """
    影像色彩準確性分析器 (基於 Delta E 2000)
    """
    def __init__(self, reference_lab=REFERENCE_LAB):
        """
        初始化分析器
        :param reference_lab: 標準 L*a*b* 參考值
        """
        self.reference_lab = reference_lab
        print("初始化 ColorAccuracyAnalyzer，準備計算 Delta E...")

    def extract_patch_colors(self, image_path, roi_coords):
        """
        從影像中擷取指定區域 (ROI) 的平均顏色
        :param image_path: 待測影像路徑 (例如：拍攝 ColorChecker 的照片)
        :param roi_coords: 色塊的 ROI 座標列表 [(x1, y1, x2, y2), ...]
                           注意：需手動調整座標以精確框選色塊
        :return: 擷取的平均 L*a*b* 值 (NumPy array)
        """
        # 使用 OpenCV 讀取影像 (預設為 BGR 格式)
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            raise FileNotFoundError(f"無法讀取影像：{image_path}")

        # 轉換為 RGB 格式
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        # 儲存擷取的顏色
        measured_rgb_list = []

        # 擷取每個色塊的平均顏色
        for (x1, y1, x2, y2) in roi_coords:
            # 裁剪出 ROI 區域
            patch = img_rgb[y1:y2, x1:x2] 
            
            # 計算該區域所有像素的平均值
            avg_rgb = np.mean(patch, axis=(0, 1))
            measured_rgb_list.append(avg_rgb)
        
        # 將 RGB 轉換為 L*a*b* 格式
        # 注意：rgb2lab 期望輸入為 0-1 範圍的浮點數
        measured_rgb = np.array(measured_rgb_list) / 255.0
        measured_lab = rgb2lab(measured_rgb)
        
        return measured_lab

    def calculate_delta_e(self, measured_lab):
        """
        計算每個色塊的 Delta E 2000
        :param measured_lab: 待測影像擷取的 L*a*b* 值
        :return: 每個色塊的 Delta E 2000 列表
        """
        if len(measured_lab) != len(self.reference_lab):
            print("警告：待測色塊數量與參考值數量不匹配。")
            # 確保只計算共同部分的 Delta E
            n = min(len(measured_lab), len(self.reference_lab))
            measured_lab = measured_lab[:n]
            reference_lab = self.reference_lab[:n]
        else:
            reference_lab = self.reference_lab
            
        # 使用 scikit-image 的 deltaE_cie2000 函數進行計算
        # 這是 Delta E 2000 的標準實現
        delta_e_values = deltaE_cie2000(reference_lab, measured_lab)
        
        return delta_e_values

    def plot_results(self, delta_e_values):
        """
        視覺化 Delta E 結果
        :param delta_e_values: Delta E 數值列表
        """
        num_patches = len(delta_e_values)
        avg_delta_e = np.mean(delta_e_values)
        
        plt.figure(figsize=(10, 5))
        plt.bar(range(num_patches), delta_e_values, color='skyblue')
        plt.axhline(y=avg_delta_e, color='r', linestyle='-', label=f'平均 $\\Delta E_{{00}}$: {avg_delta_e:.2f}')
        plt.axhline(y=5.0, color='g', linestyle='--', label='可接受上限 ($\le 5$)')
        
        plt.title('ColorChecker $\\Delta E_{{00}}$ 色彩準確性分析')
        plt.xlabel('色塊編號')
        plt.ylabel('$\\Delta E_{{00}}$ 數值')
        plt.xticks(range(num_patches), [f'P{i+1}' for i in range(num_patches)])
        plt.legend()
        plt.grid(axis='y', linestyle='--')
        plt.show()

# --- 2. 影像測試示範 ---
def run_color_test(image_file):
    """
    執行色彩準確性測試的主函數
    """
    # ⚠️ 這是最關鍵且最需要手動調整的部分！ 
    # 這裡的座標 (x1, y1, x2, y2) 必須精確框選影像中的色塊。
    # 假設我們拍攝了一張 ColorChecker 24 色卡，並只測試前 6 個色塊的座標：
    # 請根據您的實際測試圖卡影像調整以下座標
    try:
        # 範例座標，您需要根據實際影像調整
        # (這裡假設 ColorChecker 是一個 6x4 的矩陣，我們只取第一行)
        coords = [
            (50, 50, 150, 150),   # Patch 1
            (160, 50, 260, 150),  # Patch 2
            (270, 50, 370, 150),  # Patch 3
            (380, 50, 480, 150),  # Patch 4
            (490, 50, 590, 150),  # Patch 5
            (600, 50, 700, 150)   # Patch 6
            # 實際測試應包含 24 個色塊的座標
        ]
        
        # 初始化分析器
        analyzer = ColorAccuracyAnalyzer()
        
        # 擷取顏色
        measured_lab = analyzer.extract_patch_colors(image_file, coords)
        print("\n✅ 擷取的 L*a*b* 值 (部分)：")
        print(measured_lab)
        
        # 計算 Delta E
        delta_e_values = analyzer.calculate_delta_e(measured_lab)
        
        print("\n✅ 計算結果：")
        for i, de in enumerate(delta_e_values):
            # 依照會議系統的標準，Delta E <= 5 為可接受
            status = "PASS" if de <= 5.0 else "FAIL" 
            print(f"  色塊 {i+1} ($\mathbf{{\\Delta E_{{00}}}}$): {de:.2f} ({status})")
            
        print(f"\n✨ **整體平均 $\\Delta E_{{00}}$:** {np.mean(delta_e_values):.2f}")
        
        # 視覺化結果 
        analyzer.plot_results(delta_e_values)
        
    except FileNotFoundError as e:
        print(f"錯誤：{e}。請確認圖片路徑是否正確，並準備一張 ColorChecker 圖片進行測試。")
    except Exception as e:
        print(f"發生錯誤：{e}")

# --- 執行部分 ---
if __name__ == "__main__":
    # ⚠️ 請將 'test_colorchecker.png' 替換為您的實際影像路徑
    # 執行前請確保您已安裝所需的函式庫：
    # pip install opencv-python numpy scikit-image matplotlib
    test_image_path = 'test_colorchecker.png' 
    print(f"--- 開始分析影像：{test_image_path} ---")
    
    # 預留功能：可在此處切換不同的參考標準，例如：
    # analyzer_medical = ColorAccuracyAnalyzer(REFERENCE_LAB_MEDICAL)
    
    run_color_test(test_image_path)