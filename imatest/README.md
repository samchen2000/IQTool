

## ISO 8600-5:2020
Optics and photonics — Medical endoscopes and endotherapy devices
Part 5: Determination of optical resolution of rigid endoscopes with optics

Imatest 軟體是一個非常強大的工具套件，用於衡量、測試和比較各種相機和影像系統的效能。  
它可以測試的項目非常廣泛，涵蓋了從鏡頭到感光元件，再到最終影像處理的各個環節。
以下為 Imatest 軟體可以測試的主要項目及其詳細說明：
## 📷 Imatest 影像品質測試項目詳解
### 1. 銳利度與解析度 (Sharpness and Resolution)這是 Imatest 最常用且最重要的功能之一，用於評估影像系統捕捉細節的能力。
- 測試方法/圖卡:SFRplus/eSFR ISO: 使用斜邊 (Slanted Edge) 方法，符合 ISO 12233 標準，  
用於測量空間頻率響應 (Spatial Frequency Response, SFR)。
- 星形圖 (Star Chart) 或正弦波/楔形圖:  
用於視覺或特定的空間頻率測試。
- 關鍵指標:  
-- MTF (Modulation Transfer Function, 調變傳遞函數):  
反映系統在不同空間頻率下傳輸對比度的能力。  
-- MTF50:  
對比度下降到 50% 的空間頻率，是衡量系統銳利度的最常見指標。數值越高，影像越銳利。  
-- MTF-L/H/P:  
用於區分不同方向（水平、垂直、對角）的銳利度。  
-- OECF (Opto-Electronic Conversion Function, 光電轉換函數):  
描述系統如何將輸入光線轉換為數位輸出的特性，與銳利度分析結合使用。
### 2. 噪聲與動態範圍 (Noise and Dynamic Range)噪聲是影響影像品質的重要因素，特別是在低光環境下。動態範圍則決定了影像能同時捕捉的亮部和暗部細節範圍。  
- 測試方法/圖卡:灰階圖卡 (Grayscale Charts):   
例如 X-Rite ColorChecker SG 或各種密度階梯圖 (Step Chart)。  
關鍵指標:  
SNR (Signal-to-Noise Ratio, 信噪比):   
衡量影像中訊號強度與噪聲強度的比值。SNR 越高，影像越清晰。  
視覺噪聲 (Visual Noise): 考慮了人眼對不同顏色和空間頻率噪聲的敏感度，通常以 $V_{N}$ 表示。  
動態範圍 (Dynamic Range, DR): 系統能區分的最亮和最暗區域之間的亮度範圍。通常以 $\text{dB}$ 或光圈數 (stops) 表示。最大可接受信噪比下的動態範圍 (DR-SNR): 在特定 SNR 閾值下計算的動態範圍。
### 3. 色彩準確度 (Color Accuracy)色彩準確度評估系統再現真實世界顏色的能力。  
測試方法/圖卡:  
ColorChecker 24 (經典色卡): 或 ColorChecker SG (半光澤圖卡)。  
關鍵指標:  
色差 ($\Delta E$):   
衡量實際顏色與理想顏色之間的差異。$\Delta E$ 數值越小，色彩越準確。$\Delta E\ 2000$ (CIE $\text{DE}2000$): 目前最常用的色差公式。色彩飽和度 (Saturation): 影像中顏色的鮮豔程度。白平衡誤差 (White Balance Error): 系統對中性灰的再現準確度。
### 4. 畸變 (Distortion) 與視野 (Field of View, FOV)用於分析鏡頭的幾何失真和覆蓋範圍。  
測試方法/圖卡:  
點陣圖 (Dot Pattern) 或網格圖 (Grid Charts)。  
關鍵指標:  
徑向畸變 (Radial Distortion): 影像中直線彎曲的程度（例如桶形 $\text{Barrel}$ 或枕形 $\text{Pincushion}$ 畸變）。以百分比表示。  
切向畸變 (Tangential Distortion):   
由於鏡頭組件未完美對齊引起的失真。  
視野 (FOV):  
鏡頭能捕捉的場景範圍，通常以角度（$\text{degrees}$）或水平/垂直距離表示。  
### 5. 亮度與色度均勻性 (Lightfall/Vignetting and Color Uniformity)評估影像邊緣和角落與中心區域的亮度/顏色差異。  
測試方法/圖卡:  
均勻光照下的平面圖卡 (Uniformly-lit flat field)。  
關鍵指標:  
漸暈/光衰減 (Vignetting/Lightfall):   
影像邊緣相對於中心區域的亮度下降程度。通常以中心亮度的百分比表示。  
色度均勻性 (Color Uniformity):   
影像不同區域之間顏色的穩定性，通常用色度坐標（如 $L^*a^*b^*$）的差異來衡量。  
### 6. 橫向色差 (Lateral Chromatic Aberration, LCA)由於不同波長的光線穿過鏡頭時折射角不同，導致影像邊緣出現彩色邊緣。  
測試方法/圖卡:  
斜邊圖卡 (Slanted Edge Charts)。  
關鍵指標:  
LCA (以畫素或焦距的百分比表示):   
衡量不同顏色通道 (R/G/B) 影像之間的空間位移。位移越大，色邊越明顯。