# OpenISP GUI Application - 使用指南

## 功能概覽
這是一個功能完整的Windows GUI圖像調整應用程式，整合了OpenISP的所有核心處理模塊。

## 系統要求
- Python 3.7+
- Windows/Linux/macOS

## 安裝步驟

### 1. 安裝依賴
```bash
pip install -r REQUIREMENTS.txt
```

### 2. 驗證環境
確保以下模塊能夠被導入：
- PyQt5 (GUI框架)
- opencv-python (圖像處理)
- matplotlib (圖像顯示)
- numpy (數值計算)

## 使用說明

### 啟動應用
```bash
python isp_gui_app.py
```

### 主界面說明

#### 左側面板 (控制區)

**1. File Operations (文件操作)**
- **Load RAW Image**: 加載RAW或標準圖像文件
  - 支持格式: .RAW, .jpg, .png, .bmp
  - RAW文件默認解析為 1280×720 的16位無符號整數
- **Save Processed Image**: 保存處理後的圖像
  - 支持格式: .png, .jpg

**2. Select Processing Modules (模塊選擇)**
- 包含15個ISP處理模塊
- 勾選想要應用的模塊
- 模塊按順序執行，遵循完整的ISP流程

可選模塊列表：
```
RAW域處理:
  ✓ dpc   - 死像素矯正 (Dead Pixel Correction)
  ✓ blc   - 黑電平補償 (Black Level Compensation)
  ✓ aaf   - 防黑混淆濾波 (Anti-Aliasing Filter)
  ✓ awb   - 白平衡增益 (Auto White Balance Gain)
  ✓ cnf   - 色度噪聲濾波 (Chroma Noise Filter)

RGB域處理:
  ✓ cfa   - 去馬賽克 (Color Filter Array Interpolation)
  ✓ ccm   - 色彩校正 (Color Correction Matrix)
  ✓ gc    - 伽馬校正 (Gamma Correction)

YUV域處理:
  ✓ csc   - 色彩空間轉換 (Color Space Conversion)
  ✓ nlm   - 非局部均值去噪 (Non-Local Means)
  ✓ bnf   - 雙邊濾波 (Bilateral Noise Filter)
  ✓ ee    - 邊緣增強 (Edge Enhancement)
  ✓ fcs   - 假色抑制 (False Color Suppression)
  ✓ hsc   - 色調/飽和度控制 (Hue/Saturation Control)
  ✓ bcc   - 亮度/對比度 (Brightness/Contrast Control)
```

**3. Parameters (參數調整)**
- 滾動面板包含所有可配置參數
- 根據參數類型顯示不同的控制器：
  - 整數: QSpinBox (範圍調整)
  - 浮點數: QDoubleSpinBox (精度調整)
  - 選項: QComboBox (下拉菜單)
  
主要參數類別：
- **RAW圖像**: 寬度、高度
- **DPC參數**: 閾值、模式、剪切值
- **BLC參數**: 各通道黑電平、融合參數
- **AWB參數**: R/G/B增益係數
- **CFA參數**: 去馬賽克模式
- **BNF參數**: 距離權重、色差閾值
- **EE參數**: 增益、閾值
- **色彩參數**: 色調、飽和度、亮度、對比度

**4. Process Button (處理按鈕)**
- 點擊開始圖像處理
- 必須先加載圖像才能處理
- 處理在後台線程執行，不阻塞UI

**5. Progress Bar (進度條)**
- 顯示處理進度 (0-100%)
- 實時更新當前執行步驟

#### 右側面板 (顯示區)

**Original Image**
- 顯示加載的原始圖像
- Bayer陣列以灰度顯示

**Processed Image**
- 顯示處理後的結果
- YUV格式自動轉換為RGB顯示
- 灰度圖像以灰度顯示

### 工作流程示例

#### 基本流程
1. 點擊 "Load RAW Image" 加載 `./raw/test.RAW`
2. 原始圖像在左上角顯示
3. 在 "Select Processing Modules" 中確認要使用的模塊
4. 在 "Parameters" 中調整處理參數
5. 點擊 "Process Image" 開始處理
6. 監控進度條，等待完成
7. 處理結果顯示在右下角
8. 點擊 "Save Processed Image" 保存結果

#### 自定義調整流程
1. 在 "Parameters" 中修改特定模塊的參數
2. 只勾選需要的模塊（例如只測試BNF）
3. 點擊 "Process Image" 
4. 比較結果與原始圖像

### 配置文件

應用自動加載 `./config/config.csv` 中的默認參數。配置文件包含：

```csv
變數名,數值,描述
raw_w,1920,Raw圖像寬度
raw_h,1080,Raw圖像高度
dpc_thres,30,DPC閾值
...
```

您可以編輯此文件更改默認參數值，重啟應用後生效。

### 參數調整建議

#### DPC (死像素矯正)
- **dpc_thres**: 越低越敏感 (推薦: 20-50)
- **dpc_mode**: 通常使用 'gradient' 模式

#### BLC (黑電平補償)
- **bl_r, bl_gr, bl_gb, bl_b**: 根據傳感器校準值設置 (通常為0)

#### AWB (白平衡)
- **r_gain**: 紅色增益 (推薦: 1.0-2.0)
- **b_gain**: 藍色增益 (推薦: 1.0-2.0)
- **gr/gb_gain**: 綠色增益 (通常保持1.0)

#### BNF (雙邊濾波)
- **bnf_dw**: 距離權重 (中心值越大，中心像素權重越高)
- **bnf_rw**: 色差權重 (控制降噪強度)
- **bnf_rthres**: 色差閾值 (決定像素相似性判斷)

#### EE (邊緣增強)
- **ee_gain**: 邊緣增強強度 (範圍: min-max)
- **ee_thres**: 邊緣檢測閾值

#### 色調調整
- **hue**: 色調偏移 (0-255)
- **saturation**: 飽和度 (推薦: 200-300)
- **brightness**: 亮度 (-255~255)
- **contrast**: 對比度 (-32~128)

### 技術細節

#### 後台處理線程
- `ImageProcessingThread` 在單獨的QThread中執行
- 不會凍結UI
- 實時發送進度信號

#### 圖像顯示
- 使用 Matplotlib 嵌入式Canvas
- 支持自動縮放和導出
- Bayer/灰度圖像以灰度模式顯示
- YUV圖像轉換為RGB後顯示

#### 參數管理
- 從 config.csv 自動加載參數
- 支持動態參數類型識別
- 參數值實時同步到處理線程

### 常見問題

**Q: 如何加載自己的RAW圖像？**
A: 使用 "Load RAW Image" 按鈕。應用會自動檢測文件格式：
   - .RAW 文件: 解析為 1280×720 的16位整數
   - 其他格式: 使用 OpenCV 加載並轉為灰度

**Q: 處理速度很慢？**
A: 
  - 減少選中的模塊
  - 使用更小的圖像
  - 檢查 BNF 模塊（計算量較大）

**Q: 如何只應用某個模塊？**
A: 在 "Select Processing Modules" 中只勾選該模塊，取消勾選其他模塊

**Q: 參數修改後如何應用？**
A: 直接修改參數後點擊 "Process Image" 即可應用新參數

**Q: 如何保存當前配置？**
A: 編輯 `./config/config.csv` 文件並保存，重啟應用生效

### 問題排查

#### 應用無法啟動
- 檢查 Python 版本 (3.7+)
- 運行 `pip install -r REQUIREMENTS.txt`
- 檢查是否在項目根目錄運行

#### 無法加載圖像
- 確認文件路徑正確
- RAW 文件應為 16 位無符號整數格式
- 檢查文件權限

#### 處理失敗
- 查看詳細錯誤消息
- 檢查參數值是否在合理範圍內
- 嘗試禁用某些模塊逐一排查

### 版本信息
- OpenISP GUI v1.0
- 基於 OpenISP 開源項目
- 支持所有核心ISP算法

---

**更多信息**: 參考 README.md 和各模塊的源代碼註釋
