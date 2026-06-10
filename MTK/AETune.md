根據提供的 MTK MT8390 文件，AE（自動曝光）的調整主要分為```前置準備```、```感測器線性測試```、```基礎參數校準```以及 ```P-line 與偏移校準```四個階段。以下是詳細的流程與說明：
## 1. 調整前置準備與要求
在開始正式調整 AE 之前，需確保 ISP 的基本功能正常：
- 亮度規格： AE 應能將影像亮度歸一化，使其與目標參考機（Target Phone）的亮度水平基本一致。
- 與 Gamma/Tone 配合： 必須先將 Gamma 和 Tone 調整至最佳狀態，因為這兩者會直接影響影像的亮度與對比度表現。
- P-line 對齊： 確保 AE P-line 表與目標參考機對齊。
## 2. 感測器線性測試 (Exposure & Gain Linearity)
這是為了確保感測器在不同曝光時間和增益下的輸出是線性的。
- 曝光線性測試 (Exposure Linearity)：
    - 將相機對準光源，選擇 Preview 模式。
    - 設定 Gain、曝光起始/結束時間及間隔。注意曝光時間需依照頻率設定以避免閃爍（如 50Hz 最小曝光單位為 10000us）。
    - 執行測試並匯出分析結果。
- 增益線性測試 (Gain Linearity)：
    - 流程同上，但選擇 Gain Linearity。
    - 最小增益間隔建議設定為感測器的增益步長（Gain step）。
## 3. 基礎參數校準與檢查
- 最小增益檢查 (Min Gain check)： 需確認感測器驅動程式中的 .min_gain 設定是否正確（例如某些專案基準為 64）。
- 最小 ISO 校準 (Minimum ISO Calibration)：
    - 將相機對準燈箱（LSB），將 LV 值設為 9 (範圍 LV8-LV10)。
    - 在工具中設定 Mode、LV 與 F 值後取得曝光時間。
    - 擷取 RAW 檔並執行測試，將結果填回感測器的 metadata 標頭檔（.h）或驅動程式（.c）中。
- 最小飽和增益校準 (Minimum Saturation Gain Calibration)：
    - 在 LV9 環境下設定模式、衰減率（Decline Rate）與增益緩衝（Gain Buffer）。
    - 此校準結果（1024 為基準）將用來決定 AE P-line 表第一列的 ISORatioMin。
## 4. AE P-line 與 EV 偏移校準
- AE P-line 校準：
    - 在 Offline 狀態下進行，定義 Min/Max Exp 與 ISORatioMin/Max。
    - 編輯規則： 根據場景需求決定最大曝光時間，且每一列參數中只能變動一個因素（曝光時間或增益比率其中之一）。
- AE 偏移校準 (AE Calibration)：
    - 將燈箱設為 LV10 並拍攝一張 JPG 檔案存至電腦。
    - 在工具中設定 Target EV 為 100 (代表 LV10)。
    - 載入 JPG 進行校準，工具會計算出 EV offset，最後儲存至資料庫（DB）中。
## 5. 手動 AE 設定 (用於測試)
若需手動固定曝光參數進行測試，可透過 ADB 指令設定：
- 啟用 AE 管理器：adb shell setprop vendor.debug.ae_mgr.enable 1。
- 鎖定 AE：adb shell setprop vendor.debug.ae_mgr.lock 1。
- 設定曝光時間（單位 us）：adb shell setprop vendor.debug.ae_mgr.shutter 30000。
- 設定感測器增益（1024 為 1x）：adb shell setprop vendor.debug.ae_mgr.sensorgain 1024。

### 根據文件 "MTK_MT8390_AE_Tuning_Introduction_Development_Guilde_v1.0"，MT8390 的 AE（自動曝光）調整旨在透過演算法自動修正曝光設定，使相機影像亮度能像人類視覺一樣適應環境。
以下是 AE 調整的核心方式、調整步驟與相關機制的詳細說明：
## 一、 AE 演算法核心架構 (Algorithm Overview)
AE 的運作是一個閉環系統（Loop），主要包含三個階段：
- 統計 (Statistics)： 觀察感測器目前的亮度設定並統計數據。
- 亮度決定 (Brightness Decide)： 分析目前亮度並決定適合的目標亮度。
- 曝光變更 (Exposure Change)： 設定感測器的曝光時間與增益（Gain），並不斷循環以維持亮度穩定。
## 二、 AE 調整的詳細步驟
根據文件的 Block Diagram，AE 調整可分為以下具體流程：
### 1. 獲取統計資料 (Get Statistics)
- 從硬體獲取亮度資訊，計算出中央加權平均亮度 (CWV)。
- MT8390 提供 128x96 個可調整的測光區域。
- 為了高準確度，統計資料提升至 12-bit (0~4095)，這比舊版的 8-bit 更精確。
- 包含 6 個 LE/SE 直方圖（Histogram）供演算法使用。
### 2. 決定目標亮度 (Decide Target Brightness / Metering)
這是 AE 調整中最複雜的部分，演算法會根據不同場景計算出最終的 AE 目標值 (CWR)：
- Main Target (MT)： 基本測光機制，處理大多數正常場景。
- Histogram Stretch (HS) v6.0： 優化直方圖分佈。例如處理雪地場景（避免太暗）或過曝場景（避免細節遺失）。
- Anti-Backlight (ABL)： 逆光補償機制，當偵測到主體過暗而背景過亮時，會增加亮度。
- Night Scene (NS)： 專門處理夜景，避免天空部分被拍得過亮。
- Face / Touch AE： 當偵測到人臉或使用者點擊螢幕時，會給予該區域更高的權重，確保主體亮度正確。
### 3. 計算亮度差異與平滑化 (Difference & Smooth)
- 計算差異： 比較目前亮度 (CWV) 與目標亮度 (CWR) 的差距。
- 查詢 Pline 表： 將目標亮度轉換為實際的曝光參數（快門、增益、光圈）。Pline 是一張預先寫好的曝光組合表。
- AE Smooth (平滑化)： 為了避免亮度變化過於劇烈，演算法會控制收斂速度。MT8390 支援 Finer EV，可達到 0.01 EV 的精細調整步長，使過渡更自然。
### 4. 曝光參數設定 (Set Exposure)
- 設定感測器的曝光時間、增益以及 ISP 增益。
- 確保設定在生效後再回到統計階段，開始下一次的循環。
## 三、 AE 調整的關鍵參數與工具
- AE Target： 正確曝光下期望的影像亮度。
- AE Index： 在 Pline 表中的索引值，數字越大代表環境越暗。
- EV Bias： 用於人為增加或減少影像亮度的偏置值。
- Debug Log 指令： 可透過 ADB 指令啟用 AE 流程 log (vendor.debug.aaa.pvlog.enable 1) 以追蹤演算法的收斂過程。
- 手動 AE 設定： 在調整期間，可手動固定快門與增益進行測試（如 adb shell setprop vendor.debug.ae_mgr.shutter 30000）。
## 四、 NVRAM 結構
AE 的調整參數會儲存在 NVRAM 中，主要分為 8 個部分，包括硬體設定 (hw)、統計設定 (stat)、測光參數 (metering)、人臉參數 (face) 與平滑化參數 (smooth) 等。

# P-line 編輯時有哪些限制條件？
根據 MTK MT8390 的 AE P-line 校準文件說明，在編輯 P-line 表格時有以下幾項主要的限制與規則：
- 離線狀態操作：進行 P-line 校準時，CCT (Camera Control Tool) 必須處於 Offline (離線) 狀態。
- 單一因素變動原則：在表格的每一列（row）參數中，只能變動一個因素。也就是說，在同一列中，要麼只改變曝光時間（Exposure Time），要麼只改變增益比率（ISORatio/Gain），不能兩者同時變動。
- 最大曝光時間限制：必須根據特定的場景需求（Scenario requirements）來決定並設定最大曝光時間（MaxExp）。
- 首列最小 ISO 限制：AE P-line 表格第一列的 ISORatioMin 是由**最小飽和增益（Minimum Saturation Gain）**的校準結果所決定的。
- 參數定義規範：
    - MinExp / MaxExp：單位為微秒 (microsecond)。
    - ISORatioMin / ISORatioMax：數值為「相對於最小 ISO 的比率 × 1000」。
此外，雖然不是直接的編輯規則，但文件中也提到應根據環境頻率（如 50Hz 或 60Hz）設定曝光時間以避免閃爍（Flicker）。

# P-line 表格中 ISORatio 參數的計算方式為何？
根據 MTK MT8390 的 AE P-line 校準文件說明，P-line 表格中 ISORatio（包含 ISORatioMin 與 ISORatioMax）的計算方式與規範如下：
## 1. 基本定義與計算公式
ISORatio 代表的是影像感測器增益相對於**最小 ISO 值（Minimum ISO）**的比率，並為了表格填寫方便而進行了數值放大,。
### 計算公式： 
```
ISORatio=(相對於最小 ISO 的比率)×1000
```
### 參數說明：
- ISORatioMin(x1000)：該列參數定義的最小 ISO 比率值,。
- ISORatioMax(x1000)：該列參數定義的最大 ISO 比率值,。
- 最小 ISO (Minimum ISO)：是指感測器增益在最小值（通常設定為 1024）時所對應的 ISO 數值。
## 2. 第一列參數的決定方式
P-line 表格第一列的 ISORatioMin 並非隨意設定，而是由校準流程中的 「最小飽和增益（Minimum Saturation Gain）」 結果所決定。
- 基準轉換： 最小飽和增益的校準結果通常是以 1024 為基準（Base），但填入 P-line 表格時必須轉換為 1000 為基準的比率值。
    - 例如：若校準出的增益值為 1024，則對應的比率值即為 1000。
## 3. 編輯規則限制
在 P-line 表格中手動調整 ISORatio 時，須遵守以下規則：
- 單一變動原則：在表格的每一列參數中，只能變動一個因素。意即在同一列中，若變動了曝光時間（Exposure Time），則 ISORatio 應保持不變；反之亦然。
- 離線操作：所有的 P-line 編輯與計算設定都必須在 CCT 工具處於 Offline (離線) 狀態下進行。
# 如何設定 50Hz 或 60Hz 的曝光時間以避免閃爍？
根據提供的 MTK MT8390 AE 校準文件，為了避免在影像中出現閃爍（Flicker），必須根據環境光源的頻率（50Hz 或 60Hz）來設定曝光時間。以下是具體的設定原則與說明：
## 1. 基本設定原則
曝光時間的設定必須是該頻率週期時間的整數倍（N 倍），以確保感測器捕捉到的光量在各個週期內保持一致。
- 50Hz 環境：
    - 最小曝光單位： 10000 μs (即 1/100 秒)。
    - 設定要求： 曝光起始時間（Exp Start）與曝光間隔（Exp Interval）都必須是 10000 μs 的整數倍。
    - 校準範例： 在進行最小飽和增益校準時，若為 50Hz，應取得曝光時間為 {10000, 20000, ..., 250000} μs 的 25 個原始檔案。
- 60Hz 環境：
    - 雖然文件中未詳細列出 60Hz 的數值，但依照物理原則（1/120 秒），其基準單位約為 8333 μs。
    - 設定要求同樣需遵循 8333 μs 的整數倍。
## 2. 在工具（CCT）中的操作
在進行感測器校準（如 Minimum ISO Calibration）時，CCT 工具提供了頻率切換選項：
- 在 Calibration Mode 中選擇 Minimum ISO 後，可以在介面上直接勾選 50 Hz 或 60 Hz 模式。
- 選定頻率後，點擊「Refresh」即可獲得符合該頻率要求的曝光時間建議值。
## 3. 測試時的注意事項
- 在執行**曝光線性測試（Exposure Linearity）**時，務必遵守上述頻率規則來設定曝光起始、結束與間隔時間，否則測試結果會受到閃爍干擾而導致分析失敗。
- 手動設定 AE 時（透過 ADB 指令），例如設定 vendor.debug.ae_mgr.shutter 30000，此 30000 μs 即為 10000 μs 的 3 倍，適用於 50Hz 環境。