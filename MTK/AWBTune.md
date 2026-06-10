根據提供的 MTK MT8390 文件，AWB（自動白平衡）的調整主要分為**校準（Calibration）與演算法參數調整（Tuning）**兩個階段。校準是建立基準，而調整則是優化不同場景下的色彩表現。
以下是詳細的設定流程與說明：
## 1. AWB 前置校準流程 (Calibration)
在進行任何演算法調整前，必須先完成感測器的白平衡基準校準，這是在 CCT 工具的 Offline 模式下進行的。
- 準備工作： 使用 CCT 工具載入對應的感測器資料庫文件（ParameterDB.db）。
- 獲取 Process RAW： 在小燈箱內，分別在 D65, TL84, CWF, A, Horizon, DNP 六種標準光源下拍攝灰卡，並匯出儲存為 Process RAW 檔案。
- 執行校準：
    - 進入 CCT 的 AWB Calibration 頁面。
    - 設定 ROI（感測區域），通常選擇中央的灰卡區塊。
    - 載入對應光源的 RAW 檔，點擊「Update ROI」獲取數據。
    - 針對所有光源重複此動作，最後點擊「Calibration」生成基準增益（Pregain）並儲存至資料庫。
## 2. AWB 核心調整項目
MT8390 的 AWB 架構包含統計增益（Statistic）、空間預測（Spatial）與時域預測（Temporal）。
- 統計增益 (Statistic Gain)： 演算法的基礎，當場景中有足夠的白色點時，以此獲得正確結果。
- 空間預測器 (Spatial Predictor)： 當環境亮度很高或場景中缺乏白色點時，參考環境亮度來提供預設增益，增強準確性。
- 時域預測器 (Temporal Predictor)： 參考過去四幀的結果。在無白色點參考時替代統計增益，確保色彩穩定。
- 可靠模式 (Reliable Mode)： 根據場景中有效中性區塊（Neutral Block）的數量（NPB），決定最終增益是由統計、空間還是時域預測器混合而成。
## 3. 特殊場景與功能調整 (Special Conditions)
針對複雜場景，MTK 提供進階功能以優化色彩表現：
- Extra Color v3.0 (特殊色調整)： 用於處理大面積混淆色（如紅牆、黃牆或綠色植物）導致的偏色。它使用「中性窗口」偵測光源，並結合「混淆色窗口」偵測特定顏色。
- Sky Color Compensation (天空色彩補償)： 自動偵測天空區域，並根據場景亮度（LV）區分晴天或陰天，對原始目標增益進行補償，避免天空顏色影響全圖平衡。
- Face AWB (人臉白平衡)： 優先考慮人臉區域的統計數據，確保人臉膚色在不同光源下依然準確。
- Speed Control (收斂速度控制)： 調整 AWB 從目前增益過渡到目標增益的速度，數值越高收斂越快。
## 4. 偵錯與驗證工具 (Debug)
調整過程中，可透過 EXIF Tag 來分析演算法的判斷過程：
- AWB_TAG_RELIABLE_MODE： 觀察目前使用的是哪種可靠性模式。
- AWB_TAG_CCT： 查看演算法偵測到的環境色溫。
- AWB_TAG_EXTRA_0_CONF： 確認 Extra Color 功能的信心度與權重。  
調整參數主要儲存在 NVRAM 中，包含 AWB.cpp、AIAWB_MA.cpp 等文件，可透過 MediaToolKit 工具進行參數佈署。