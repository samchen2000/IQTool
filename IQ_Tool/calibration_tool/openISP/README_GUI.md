# OpenISP GUI 應用 - 快速入門指南

## 📋 概覽

本項目提供了兩個GUI應用版本用於圖像信號處理 (ISP)：
- **Tkinter版本** (推薦) - 輕量級，依賴最少
- **PyQt5版本** - 功能豐富，UI更專業

## 🚀 快速開始 (Tkinter 版本 - 推薦)

### 1. 安裝依賴
```bash
pip install -r REQUIREMENTS.txt
```

### 2. 啟動應用
```bash
python isp_gui_tkinter.py
```

## 🎨 應用功能

### 主功能
✅ **圖像加載**
   - 支持 RAW 格式 (16位無符號整數)
   - 支持標準格式 (JPG, PNG, BMP)

✅ **實時處理**
   - 15個ISP模塊可選
   - 後台線程處理，不阻塞UI
   - 實時進度條顯示

✅ **參數調整**
   - 直觀的參數控制界面
   - 實時應用參數更改
   - 支持所有ISP配置參數

✅ **結果保存**
   - 保存為PNG或JPG格式
   - 支持即時導出

### 處理流程

```
加載圖像
   ↓
選擇ISP模塊 (15個可選)
   ├→ RAW域: DPC, BLC, AAF, WBGC, CNF
   ├→ RGB域: CFA, CCM, GC  
   └→ YUV域: CSC, NLM, BNF, EE, FCS, HSC, BCC
   ↓
調整參數
   ↓
點擊 "Process Image" 處理
   ↓
查看結果
   ↓
保存圖像
```

## 📊 模塊說明

### RAW 域處理
- **DPC** - 死像素矯正 (Dead Pixel Correction)
  - 檢測並修復傳感器的壞像素
  - 參數: dpc_thres (閾值), dpc_mode (檢測模式)

- **BLC** - 黑電平補償 (Black Level Compensation)
  - 消除傳感器的黑電平偏移
  - 參數: bl_r, bl_gr, bl_gb, bl_b (各通道偏移)

- **AAF** - 防黑混淆濾波 (Anti-Aliasing Filter)
  - 高頻低通濾波

- **AWB** - 白平衡增益 (Auto White Balance)
  - 調整RGB通道增益平衡
  - 參數: r_gain, g_gain, b_gain

- **CNF** - 色度噪聲濾波 (Chroma Noise Filter)
  - 在色度通道進行降噪

### RGB 域處理
- **CFA** - 去馬賽克 (Demosaicing)
  - 將Bayer陣列插值為完整RGB圖像
  - 算法: Malvar 或 Bilinear

- **CCM** - 色彩校正矩陣 (Color Correction Matrix)
  - 校正光源相關的色偏

- **GC** - 伽馬校正 (Gamma Correction)
  - 進行非線性亮度調整

### YUV 域處理
- **CSC** - 色彩空間轉換 (RGB → YUV)
  - 轉換為YUV格式便於進一步處理

- **NLM** - 非局部均值去噪 (Non-Local Means)
  - 先進的降噪算法，保留細節

- **BNF** - 雙邊濾波 (Bilateral Noise Filter)
  - 邊緣保留的平滑濾波

- **EE** - 邊緣增強 (Edge Enhancement)
  - 增強邊緣細節和清晰度

- **FCS** - 假色抑制 (False Color Suppression)
  - 抑制色度分量的偽色

- **HSC** - 色調/飽和度控制 (Hue/Saturation Control)
  - 調整色調和飽和度

- **BCC** - 亮度/對比度 (Brightness/Contrast Control)
  - 最終的亮度和對比度調整

## 🎮 使用示例

### 基本流程
```
1. 點擊 "Load RAW Image" 加載圖像
2. 原始圖像在左上角顯示
3. 在 "Processing Modules" 中選擇要使用的模塊
4. 點擊 "Process Image" 開始處理
5. 等待進度條完成 (100%)
6. 結果顯示在右下角
7. 點擊 "Save Processed Image" 保存
```

### 參數調整示例
```
示例1: 增強銳度和清晰度
- 勾選: EE (邊緣增強)
- 設置: 
  - ee_gain_min: 64 (增加邊緣增強)
  - ee_thres_min: 16 (降低邊緣檢測閾值)

示例2: 降低噪聲
- 勾選: NLM, BNF
- 設置:
  - nlm_h: 15 (增加去噪強度)
  - bnf_dw_22: 2048 (增加雙邊濾波中心權重)

示例3: 色彩調整
- 勾選: HSC, BCC
- 設置:
  - saturation: 300 (增加飽和度)
  - brightness: 20 (增加亮度)
  - contrast: 5 (增加對比度)
```

## 📁 文件結構

```
openISP/
├── isp_gui_tkinter.py          # ⭐ Tkinter GUI (推薦)
├── isp_gui_app.py              # PyQt5 GUI (可選)
├── REQUIREMENTS.txt            # 依賴清單
├── GUI_USAGE.md               # 詳細使用說明
├── README_GUI.md              # 本文件
├── isp_pipeline.py            # 完整ISP流水線
├── test_bnf.py                # BNF模塊測試
├── config/
│   ├── config.csv             # 完整參數配置
│   └── config_test.csv        # 測試參數配置
├── model/                      # ISP算法模塊
│   ├── dpc.py, blc.py, ...    # 15個ISP模塊
│   └── ...
├── raw/                        # 測試圖像
│   └── test.RAW              # 1280×720 16位圖像
└── docs/                       # 文檔和參考資料
```

## ⚙️ 配置文件

應用自動加載 `./config/config.csv` 中的默認參數。

主要參數示例：
```csv
變數名,數值,描述
raw_w,1920,RAW圖像寬度
raw_h,1080,RAW圖像高度
dpc_thres,30,DPC檢測閾值
r_gain,1.5,紅色增益
b_gain,1.1,藍色增益
hue,128,色調
saturation,256,飽和度
brightness,10,亮度
contrast,10,對比度
...
```

編輯此文件並保存，重啟應用後新參數自動載入。

## 🔧 系統要求

- **Python**: 3.7 或更新版本
- **操作系統**: Windows / Linux / macOS
- **內存**: 最少 512MB (推薦 2GB+)
- **依賴庫**:
  - numpy (必需)
  - Pillow (必需)

## 🚨 故障排除

### 應用無法啟動
```bash
# 檢查Python版本
python --version

# 重新安裝依賴
pip install --upgrade -r REQUIREMENTS.txt

# 在項目根目錄運行
cd openISP
python isp_gui_tkinter.py
```

### 無法加載圖像
- 確認文件路徑和格式正確
- RAW文件必須為 16 位無符號整數
- 其他格式使用標準工具轉換

### 處理速度慢
- 使用較小的圖像進行測試
- 禁用不必要的模塊
- BNF 和 NLM 計算量較大，適當調整參數

## 📖 詳細文檔

- **GUI_USAGE.md** - 完整的圖形界面使用說明
- **README.md** - OpenISP 項目文檔
- **model/*.py** - 各ISP模塊的源碼和註釋

## 💡 提示

1. **測試用途**: 使用 `config_test.csv` 和較小圖像快速測試
2. **參數保存**: 編輯 `config.csv` 保存常用配置
3. **模塊順序**: GUI自動按正確順序執行模塊，無需手動調整
4. **性能優化**: 根據圖像內容選擇必要的模塊，減少處理時間

## 📞 技術支持

遇到問題？檢查：
1. 依賴庫版本是否正確
2. Python 版本是否 3.7+
3. 模型文件位置是否正確
4. 參數值是否在合理範圍

---

**當前版本**: 1.0  
**最後更新**: 2026年6月  
**維護者**: OpenISP 社區  
