## ISP 調整
MT8390 的 ISP 處理分為兩個階段：Pass 1 (感測器介面) 主要負責原始資料（RAW）的預處理，而 Pass 2 (DRAM 到 DRAM) 則專注於紋理、雜訊抑制、色調與色彩引擎的處理
。
以下是整理後的 ISP 影像調整項目詳細列表：
## 1. 感測器預處理模組 (Pass 1)
此階段主要處理感測器端輸出的 RAW 資料。
### - BPC (壞點校正, Bad Pixel Correction)：
    - 目的： 去除亮點與脈衝雜訊。
    - 調整項目： 提供低、中、高三種強度等級；相關參數包括 BPC EN、BPC Strength。
### - OBC (光學黑電平校正, Optical Black Correction)：
    - 目的： 校正黑電平強度並重新縮放至全範圍。
    - 調整項目： 需在調整開始前完成校準，以避免暗處色偏。
### - PDC (相位檢測校正, Phase Detection Correction)：
    - 目的： 針對 RAW 型 PDAF，去除 PD 像素點。
    - 調整項目： PDC_EN 開關及由模組廠提供的 PDC 表。
### - LTM (局部色調映射, Local Tone Mapping)：
    - 目的： 恢復高光細節以獲得更好的動態範圍，並提升高光色彩飽和度。
### - DM (通用解馬賽克, Universal Demosaic)：
    - 目的： 將 Bayer 格式轉換為 RGB，並透過梯度資訊保持邊緣。
    - 調整項目：
        - HF STR (高頻強度)： 調整 HA STR、H1/H2/H3 GN (針對不同頻段的細節增強)。
        - LPF (低通濾波)： 用於減少雜訊，包含 N0 STR 與 N0 OFST。
        - 抑制項： OV_TH (抑制白邊)、UN_TH (抑制黑邊)。
## 2. 雜訊抑制與細節調整模組 (Pass 2)
此階段處理紋理細節、亮度和色彩雜訊。
### - SNR (光譜雜訊抑制, Spectral Noise Reduction)：
    - 目的： 降低亮度雜訊（Luma）與色彩雜訊（Chroma）。
    - 調整項目：
        - Pre-filter： 提供 3x3、5x5、7x7 濾波器選擇。
        - NLM (非局部均值)： 根據邊緣和活動量調整強度，包含 Y NLM EDGE TH、Y NLM ACT TH。
        - 角落雜訊： 使用 SL2 LINK 調整中心到角落的增益。
### - CNR (彩色雜訊抑制, Chroma Noise Reduction)：
    - 目的： 減少亮度脈衝雜訊與低頻彩色雜訊。
    - 調整項目： ACT BLD BASE C (降低色彩雜訊)、CB/CR STD (色彩穩定度)。
    - Median Filter： 調整 LCL TH/LV 與 NCL TH/LV 以平衡細節與雜訊。
### - ABF (自適應邊緣去紫色條紋, Adaptive Blue-purple Fringe Removal)：
    - 目的： 消除飽和區域附近的藍紫色邊緣。
    - 調整項目： BIL_IDX (濾波器大小)、BF_U_OFST (強度) 以及飽和區域閾值 STHRE R/G/B。
### - TNR / MCNR (時域雜訊抑制)：
    - 目的： 改善預覽與錄影品質，支持影像 HDR。
## 3. 色調、對比與邊緣增強 (Pass 2)
### - EE (邊緣增強, Edge Enhancement)：
    - 目的： 提升影像清晰度。
    - 調整項目：
        - **增益調整**： H1~3 GN (細節/紋理/邊緣增強)。
        - **GLUT 表**： 調整 X1~X4 (邊緣反應) 與 Y0~Y5 (對應增益)。
        - **抑制 Overshoot/Undershoot**： 透過 CLIP LUMA UPB/LWB 減少黑白邊。
        - **YCE/CCE**： 加速邊緣過渡，減少油畫感。
### - TNC (色調與對比引擎, Tone and Contrast)：
    - 目的： 改善對比度並提供更佳的色彩表現。
### - AKS (自適應核平滑, Adaptive Kernel Smoothing)：
    - 目的： 改善邊緣平滑度。
    - 調整項目： SMTH LV (平滑等級)、SMTH RNG (範圍) 與 BLND WT (混合權重)。
## 4. 色彩空間調整
### - C3D LUT (3D 色彩域調整)：
    - 特點： 硬體支持 729 個控制點 (9x9x9)。
    - 調整項目： 提供 36 個調整點的 Hue by Hue (色相) 與 Saturation by Hue (飽和度) 調整，並新增 Hue by Luma (亮度關聯色相) 的調整靈活性。
## 5. 其他後處理模組
### - ClearZoom： 結合高保真縮放器與智慧銳化，優化數位變焦品質。
### - HFG (高頻產生器)： 加入高頻亮度雜訊以產生均勻的雜訊模式。
### - CSC (色彩空間轉換)： 負責 YUV 與 RGB 之間的相互轉換。