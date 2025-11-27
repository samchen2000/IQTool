## PAGE 4 — 目錄

Purpose（目的）

Usage limitation（使用限制）

Overview（總覽）

Environment setup（環境架設）

Calibration input images（校正輸入影像）

Calibration process（校正流程）

Tuning（調整參數）

Calibration validation（校正驗證）

✅ PAGE 5 — Purpose（目的）

本文件描述：

相機畸變校正的流程

校正場景的搭建方式

非魚眼鏡頭（non-fisheye）的拍攝與配置方法

搭配提供之相機校正軟體所需之步驟


✅ PAGE 6 — Purpose（目的）

本文件旨在說明以下內容：

校正流程

校正場景的建置方式

非魚眼相機在搭配提供之校正軟體庫時，如何進行放置與拍攝

✅ PAGE 7 — Usage Limitation（使用限制）

本工具目前的限制如下：

尚不支援魚眼鏡頭（fisheye lens）校正。

校正初始化需要使用鏡頭廠商提供的 Vendor Curve（廠商畸變曲線）。

✅ PAGE 8 — Usage Limitation（使用限制，續）

本校正工具 不支援魚眼影像的校正（僅支援一般大廣角但非魚眼）。

在執行校正之前，必須先由廠商提供 Lens Distortion Vendor Curve，並依工具轉換成可使用的格式。

✅ PAGE 9 — Overview（總覽）

本章節說明整體校正流程：

Calibration overview（校正總覽）

Calibration procedure（校正步驟）

✅ PAGE 10 — Calibration Overview（校正流程概述）

整體校正流程包含四大步驟：

1. Circle Detection（圓點偵測）

從校正板上偵測所有黑白點（Dot Chart）的位置。

2. Optical Center Detection（光學中心偵測）

根據「Sparse Image」中的點位置推算相機光軸的中心。

3. LDC Calibration（LDC 畸變校正）

利用 Dense Image 建出鏡頭畸變模型的 1D LDC Curve。

ROI 擷取示例：Dense Image 的 ROI 需要人工裁切

裁切 ROI（區域）的注意事項：

裁切後的影像必須覆蓋影像中心。

需包含足夠密集的點，便於光學中心判定。

裁切區域必須只包含點陣，不可包含其他邊框或雜訊。

文件附圖中示意：

Good：裁切 ROI 恰好框住中心區域且全為點陣。

Bad：裁切位置偏移或包含無關背景。

✅ PAGE 11 — Calibration Procedure（校正步驟）
Step 1. 設置校正環境
1. 建立校正設備

列印校正板（Dot Chart）

具體方式請參考：Environment Setup

工具用途：建立實體點陣校正板（Physical dot chart pattern creation）

2. 設置合適的均勻光源

建議使用 5500K–6500K 的高均勻度散射光源

光源需避免造成校正板上的明暗陰影

目的是讓點陣特徵在影像中具有良好對比

3. 設定相機參數

設定相機輸出解析度

記錄相機物理參數（原生解析度、像素尺寸、焦距）

校正影像不可經過縮放（scale）或裁切（crop）處理

將相機固定於架設設備上

4. 若影像雜訊過多

檢查自動曝光（AEC）增益是否小於 2×

若增益過高，建議提高環境光線（選擇性）

✅ PAGE 12 — Calibration Procedure（校正步驟）
Step 2. 拍攝校正所需影像
1. 拍攝兩張影像（Near 與 Far）

Sparse Image（稀疏影像）：放置相機於 Near（近距離） 位置

Dense Image（密集影像）：放置相機於 Far（遠距離） 位置

兩張影像分別用於：

光學中心偵測（Sparse）

LDC 曲線校正（Dense）

必要時可在 Near/Far 附近微調位置。

2. 檢查影像品質，確保可用於校正

需確認影像無以下問題：

Sparse Image 失敗案例

Dense Image 失敗案例

完整失敗例圖示於後續頁面。

✅ PAGE 13 — Calibration Procedure（校正步驟）
Step 3. 執行校正流程
1. Vendor Curve 轉換

使用工具將廠商提供的畸變表轉換為 1D 曲線格式。
→ 詳細參考 Tool usage: Vendor curve conversion

2. 執行 Dot Chart 校正（主校正程式）

輸入 Sparse 與 Dense 影像

校正結果輸出為二進位（.bin）格式
→ 詳細參考：

LDC calibration

Calibration result format

3. 若有需要，可進行參數微調（Tuning）

例如：

平滑化參數

Dot detection 參數

Corner rejection 參數等

✅ PAGE 14 — Calibration Procedure（校正步驟）
Step 4. 驗證校正結果
1. Log 分析

需檢查以下校正品質指標：

不合格參數（failed criteria parameters）

Dot 偵測數量是否合理

光學中心偏移比

Pinhole 最大值
→ 詳見後續章節：

Log analysis

Failed criteria parameters

2. 使用 PC 工具（LDC Tool）進行影像驗證

匯入校正結果

將影像去畸變（warping）

檢查去畸變後直線是否平直、平滑
→ 詳見 Related tool

✅ PAGE 15 — Environment Setup（校正環境）

本章節將說明三項校正環境的重要參數：

Hyper focal distance（超焦距）

Near and Far distance（近距與遠距位置）

Calibration pattern（校正板尺寸與製作方式）

後續頁面會逐步說明如何計算與建立校正環境。