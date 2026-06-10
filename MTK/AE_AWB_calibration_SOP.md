***「MTK_MT8390_AE_AWB_Calibration_SOP_Development_Guilde_v2.2」***文件，MT8390 的 ISP 調整與測試項目主要分為感測器測試、感測器校準、AE/AWB/CCM 校準以及陰影校準等。以下為詳細的測試項目分析、調整流程與工具使用說明：
## 1. 感測器測試 (Sensor Test)
此階段旨在驗證感測器的硬體特性是否符合線性要求及 OB（光學黑電平）的穩定性。
- 測試項目：
    - 曝光線性度 (Exposure Linearity)： 檢查感測器在不同曝光時間下的輸出是否呈線性增長。
    - 增益線性度 (Gain Linearity)： 檢查感測器在不同增益（Gain）設定下的輸出線性。
    - OB 穩定度 (OB Stability)： 檢查在變動增益或快門時，以及不同模式（預覽/擷取/錄影）間，OB 數值是否保持穩定。
- 工具： Camera Control Tool (CCT) 需處於 Online 狀態。
- 調整流程：
    - 將相機對準均勻光源（如 DNP 或背光板）。
    - 在 CCT 的「CDVT Sensor Test」頁面選擇對應的測試模式（如 Exposure Linearity）。
    - 設定 Gain、起始/結束曝光時間及間隔（注意需符合頻率以避免閃爍，如 50Hz 單位為 10000us）。
    - 點擊「Run」執行測試，並透過「Analysis」分頁查看 R-square 是否大於 0.98。
## 2. 感測器校準 (Sensor Calibration)
此步驟為 ISP 調整的基礎，需取得正確的感測器元數據（Metadata）。
- 調整項目：
    - OB 校準： 取得不同感光度設定下的 OB 平均值。
    - 最小 ISO 校準 (Minimum ISO)： 取得感測器在最小增益（1x, 即 1024）時的 ISO 數值。
    - 最小飽和增益校準 (Minimum Saturation Gain)： 尋找感測器達到飽和時（綠色通道）的最小增益值。
- 工具： CCT（需處於 Offline 狀態）、Dump Raw 腳本（如 03_Dump_raw_ob.bat）。
- 調整流程：
    - OB 校準： 在全黑環境下執行 OB 腳本擷取 RAW 檔，導入 CCT 計算 OB offset 並寫回資料庫（DB）。
    - 最小 ISO 校準： 對準 LV9 的燈箱，在 CCT 中設定模式/LV值/光圈值取得建議曝光時間，執行腳本擷取 RAW 後計算結果，並填入感測器的標頭檔（.h）或驅動（.c）中。
    - 最小飽和增益校準： 對準 LV9 燈箱，設定衰減率與增益緩衝，擷取多張不同曝光的 RAW 檔計算結果。此結果將決定 AE P-line 表格第一列的 ISORatioMin。
## 3. AE P-line 校準 (AE P-line Calibration)
- 調整項目： 定義曝光時間與 ISO 比例（ISORatio）的對應關係表。
- 工具： CCT (Offline)、DBKey 工具。
- 調整流程：
    - 使用 DBKey 選擇感測器並點擊「Apply」。
    - 在「AE P-line Calibration」分頁編輯 P-line 表格。
    - 編輯規則： 根據場景需求設定最大曝光時間，且表格每一列只能變動一個因素（時間或增益），首列 ISORatioMin 需參考前述校準結果。
    - 點擊「Save DB」儲存。
## 4. 陰影校準 (Shading Calibration / TSF)
- 調整項目： 修正鏡頭周邊亮度與色偏問題。包含基礎 Shading 與進階 TSF（三重陰影擬合）。
- 工具： 擴散片 (Diffuser)、DNP 燈箱、CCT、MediaTek Online (MOL) 模擬平台。
- 調整流程：
    - Shading 校準： 鏡頭加裝擴散片拍攝 DNP 燈箱取得 Pure RAW，導入 CCT 選擇色溫（High/Middle/Low）進行計算並儲存至 DB。
    - TSF 校準： 需準備至少 4 個模組與 5 種光源（D65, DNP, CWF, TL84, A）。擷取所有光源的 RAW 檔後，上傳至 MOL 平台進行模擬校準，下載參數後使用工具轉為 DB 格式。
## 5. AE、AWB 與 CCM 校準
- AE 偏移校準 (AE Calibration)：
    - 流程： 將燈箱設為 LV10 拍攝 JPG，在 CCT 中設定 Target EV 為 100，載入圖片計算 EV offset 並儲存。
- AWB 校準 (AWB Calibration)：
    - 流程： 在燈箱中拍攝 D65, TL84, CWF, A 等不同光源下的灰卡 Process RAW，在 CCT 中設定 ROI（感興趣區域）並點擊「Calibration」執行校準。
- CCM 校準 (Color Correction Matrix)：
    - 流程： 在 18% 灰背景下拍攝 24 色色卡 (Color Checker) 的 Process RAW，導入 CCT 後設定 Gamma 文件，手動或自動框選色塊 ROI，執行「Optimize」優化色彩矩陣並儲存。
附錄：手動 AE 設定方式
若在校準過程中需要手動固定曝光參數，可透過 ADB 指令操作：
- 啟用 AE 管理：adb shell setprop vendor.debug.ae_mgr.enable 1
- 鎖定 AE：adb shell setprop vendor.debug.ae_mgr.lock 1
- 設定曝光（如 30ms）：adb shell setprop vendor.debug.ae_mgr.shutter 30000
- 設定增益（如 1x）：adb shell setprop vendor.debug.ae_mgr.sensorgain 1024