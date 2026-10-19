由於 LSC 涉及影像處理與參數調校，我建議使用 PyQt6 (或 PySide6) 作為 GUI 框架，因為它對佈局的控制力較強，且適合開發工具類軟體；影像處理則使用 OpenCV 與 NumPy。

專案指南：Lens Shading Correction (LSC) 校正工具
本文件說明如何使用 Python 建立一個具有圖形介面的 LSC 校正程式。LSC 的核心目標是消除影像邊緣亮度不足（Vignetting）的現象。

## 1. 技術棧 (Tech Stack)
語言: Python 3.x
GUI 框架: PyQt6 (提供專業的視窗介面)
影像處理: OpenCV (讀取與處理影像), NumPy (矩陣運算)
數據可視化: Matplotlib (用於顯示 Gain Map 分佈圖)
## 2. 視窗介面佈局設計 (UI Layout)
建議將介面分為 「左側控制面板」 與 「右側預覽區域」。

介面結構圖
```txt
+-----------------------------------------------------------------------+
| [頂部工具欄]  - 開啟檔案 | 保存影像 | 重設參數                           |
+-----------------------+-----------------------------------------------+
| < 左側：控制面板 >       | < 右側：影像顯示區 >                            |
|                       |                                               |
| 1. 增益圖設定 (Gain Map) | +-----------------------+  +-----------------------+ |
|    - 中心增益 (Center)  |  |    原始影像 (Original)  |  |   校正後影像 (Correct) | |
|    - 邊緣增益 (Edge)    |  +-----------------------+  +-----------------------+ |
|    - 衰減半徑 (Radius)  |                                               |
|                       |                                               |
| 2. 運算設定             |                                               |
|    - 運算模式 (線性/二次) |                                               |
|                       |                                               |
| 3. 狀態顯示             |                                               |
|    - 處理時間: 0.1s     |                                               |
+-----------------------+-----------------------------------------------+

```

功能模組分工
| 位置	| 組件|	功能實現 |
| ---- | ---- | ---- |
頂部 | QPushButton	| 觸發 QFileDialog 讀取圖片 $\rightarrow$ 載入至 NumPy 陣列。
左側 | QSlider / QDoubleSpinBox | 即時調整 $\text{Gain}$ 參數 $\rightarrow$ 觸發 update_image() 函數。
右側 | QLabel (顯示圖片) | 將 OpenCV 的 BGR 格式轉換為 QPixmap 顯示。
後台 | LSC Engine | 根據參數生成 $\text{Gain Map} \rightarrow$ 執行元素乘法 $\rightarrow$ 輸出結果。


## 3. 核心功能實現邏輯

### A. LSC 數學模型 (簡化版)   
### LSC 的基本原理是將影像 $I(x,y)$ 乘以一個增益圖 $G(x,y)$： 
## $Corrected_Image(x,y)=I(x,y)×G(x,y)$

### 其中 $\text{Gain Map}$ 通常基於距離中心的距離 $r$ 來計算： 
## $G(r)=1+k⋅(r 2)$ 
(k 為係數，r 為像素點到影像中心的歸一化距離)

### B. 程式實作流程
載入影像: 使用 cv2.imread()。  
生成 Gain Map:  
建立一個與影像等大的矩陣。  
計算每個像素點 $(x,y)$ 到中心 $(cx, cy)$ 的歐幾里得距離。  
根據 Slider 的參數（如 $\text{Edge Gain}$）對距離進行權重映射。  
套用校正: 使用 np.multiply() 將原圖與 Gain Map 相乘。  
數值截斷 (Clipping): 使用 np.clip(result, 0, 255) 防止數值溢位 $\rightarrow$ 轉回 uint8。

## 4. 建議的代碼結構 (Python Scaffold)
```python
import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QSlider, QLabel, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap

class LSCWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lens Shading Correction Tool")
        self.image = None
        self.initUI()

    def initUI(self):
        # 1. 主佈局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # 2. 左側控制面板
        control_panel = QVBoxLayout()
        self.btn_open = QPushButton("開啟影像")
        self.btn_open.clicked.connect(self.load_image)
        
        self.slider_gain = QSlider(Qt.Orientation.Horizontal)
        self.slider_gain.setRange(100, 200) # 1.0 ~ 2.0
        self.slider_gain.valueChanged.connect(self.apply_lsc)

        control_panel.addWidget(self.btn_open)
        control_panel.addWidget(QLabel("邊緣增益 (Edge Gain):"))
        control_panel.addWidget(self.slider_gain)
        
        # 3. 右側顯示區
        self.img_display = QLabel("請載入影像")
        self.img_display.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(control_panel, 1)
        layout.addWidget(self.img_display, 4)

    def load_image(self):
        # 使用 QFileDialog 讀取路徑 -> cv2.imread
        pass

    def generate_gain_map(self, h, w, gain_factor):
        # 實現 Gain Map 生成邏輯 (使用 NumPy)
        # 1. 建立中心坐標
        # 2. 計算距離矩陣
        # 3. 回傳 gain_map
        pass

    def apply_lsc(self):
        if self.image is None: return
        # 1. 獲取 Slider 數值
        # 2. generate_gain_map()
        # 3. np.multiply(self.image, gain_map)
        # 4. 更新 self.img_display
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LSCWindow()
    win.show()
    sys.exit(app.exec())

```
## 5. 開發步驟建議 (Roadmap)
### 1.第一階段 (核心算法): 先不寫 UI，用一個 .py 腳本實現：讀取圖 $\rightarrow$ 產生 Gain Map $\rightarrow$ 乘法 $\rightarrow$ 儲存圖。
### 2. 第二階段 (基礎 UI): 建立視窗，實現「開啟檔案」與「顯示影像」的功能。
### 3. 第三階段 (動態聯動): 將 Slider 的數值與 apply_lsc 函數綁定，實現即時預覽（Real-time Preview）。
### 4. 第四階段 (進階優化):
- 加入 ** Gain Map 視覺化** (顯示一張黑白圖代表增益分佈)。
- 支援 多項式擬合 (Polynomial Fitting) 讓校正更精準。
- 支援 Save as TIFF/PNG 以保留精度。
