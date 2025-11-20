## 🔶 一、EIS（電子防手震）功能解析
### 1. 為何需要 EIS？

EIS 主要解決兩種手機錄影常見問題：

- 手震（shake & jitter）：使用者握持手機時的高頻抖動

- Rolling Shutter（果凍效應）：CMOS 行曝光造成，畫面在快速旋轉時產生彎曲

EIS 的目的：

- 產生更平滑的相機姿態軌跡（trajectory smoothing）

- 結合 Gyro 與 影像追蹤（optical flow）

- 修正 鏡頭畸變 LDC 與 Rolling Shutter

## 🔶 二、LDC（鏡頭畸變校正）功能解析
1. 為何需要 LDC？

文件明確指出：

** 所有使用 EIS 的 sensor 都必須先完成 LDC 調校 **

80-PN984-8_REV_A_Qualcomm_Spect…

原因：

- EIS 的計算需要「等效無畸變影像」

- 鏡頭邊緣區域的 barrel/pincushion 失真會導致 gyro/影像對應錯誤

- LDC 必須提供 Out2In / In2Out 網格（grid） 作為校正基礎

2. Qualcomm 使用的 LDC Grid

- Out2In（ctc_grid）：無畸變 → 畸變

- In2Out（ld_i2u_grid）：畸變 → 無畸變（EIS 內部使用）

- Qualcomm 會自動從 Out2In 推算 In2Out

3. LDC 可用網格尺寸

- 35×27（目前唯一支援）

## 🔶 三、EIS + LDC Calibration 整體工作流程

以下根據文件（Calibration Flow Diagram）重建完整圖示：

### 📌 完整 EIS / LDC 校正流程：

1. ISP & 3A 良好狀態（前置要求）

2. Device Configuration（設定 EIS calibration mode）

3. 拍攝 LDC checkerboard

4. LDC Calibration（生成 LDC grids）

5. 拍攝 EIS Calibration videos

6. Dump gyro + frame logs

7. EIS Log Analyzer（檢查 log 是否能用）

8. EIS Calibration 模型訓練（focal length + time offset）

9. Blur Masking 調整（室內走動影片）

10. 產出 XML（EIS Chromatix）存入裝置

11. On-device validation

## 🔶 四、EIS 調整步驟（依章節精準整理）

以下依照文件章節架構，每一章節整理成 工程可用操作清單。
### 📍 Step 1 – Device Configuration（裝置設定）

（將裝置設置成 EIS 校正模式）

### 必要條件 

- 80-PN984-8_REV_A_Qualcomm_Spect…

- 3A fully functional（特別是 AF 不能呼吸）

- FPS 需穩定（≤ 0.5% deviation）

- OIS 必須固定在中心 (OIS lock on center)

- Gyro 不能掉 sample

### 設定 EIS Operation Mode = 2（校正模式）
```
adb root
adb remount
adb shell "echo EISv3GyroDumpEnabled=1 >> /vendor/etc/camera/eisoverridesettings.txt"
adb shell "echo EISv2OperationMode=2 >> /vendor/etc/camera/eisoverridesettings.txt"
adb shell "echo EISv3OperationMode=2 >> /vendor/etc/camera/eisoverridesettings.txt"
adb shell "echo fovcEnable=0 >> /vendor/etc/camera/camxoverridesettings.txt"
```
### Margin 設定（重要）
（若 physical margin 不夠，EIS 會自動加 virtual margin）

| Sensor | 建議 Margin                               |
| ------ | --------------------------------------- |
| 16:9   | WidthMargin = 0.20, HeightMargin = 0.20 |
| 4:3    | HeightMargin 可到 0.40                    |

### 📍 Step 2 – LDC Calibration（鏡頭畸變校正）
#### 拍攝 Checkerboard 
80-PN984-8_REV_A_Qualcomm_Spect…

- 使用 YUV 或 JPEG（不能用 video）

- 20–30 張

- 不同距離、不同角度

- 棋盤格不能出框

- 需使用 Operation Mode 2（raw input FOV）

#### 設定 LDC Calibration 參數

| Parameter        | Value               |
| ---------------- | ------------------- |
| ldc_grid_source  | 0（使用 EIS Chromatix） |
| ldc_calib_domain | 2（基於 IFE output）    |
| ldc_grid_size    | 0（35×27）            |

輸出：

- Out2In (ctc_grid)

- In2Out 由工具自動生成

### 📍 Step 3 – Content Capturing（拍攝 EIS 校正影片）

EIS 校正需要三種影片：

### A. 影片 1：完全靜止 60 秒（用於 gyro bias）

條件：

- 裝置完全固定（腳架）

- 室內也可

### B. 影片 2：EIS Calibration Video（最重要）
| 條件  | 要求                         |
| --- | -------------------------- |
| 開頭  | 1–2 秒完全靜止                  |
| 動作  | 僅旋轉，不可走路、不應包含前後移動          |
| 時間  | ≥ 25 秒                     |
| 景物  | 至少 5 公尺以外（避免 local motion） |
| 光線  | 戶外、充足光線（降低 motion blur）    |
| 影片數 | 每個 mode 建議 2–3 部           |

### C. 影片 3：Blur Masking Tuning（室內走動）

- 包含靜止 + 室內行走

- 用於調 blur masking thresholds

### 📍 Step 4 – EIS Log Analyzer（Gyro 與 Frame Log 檢查）

Log Analyzer 分成：

- Error（阻擋 calibration）

- Warning（品質下降，但可使用）

- Info

必須先達成：
```
"EIS/Gyro data is adequate for calibration"
若 inadequate → 影片不能用。
```
需確認：

- Gyro 無 missing samples

- No abnormal FPS drop

- RS skew 合法

- margin 設置正確

- 時間戳（timestamp）同步
### 📍 Step 5 – EIS Calibration（主校正程序）

__Calibration 包含三大階段：__ 

80-PN984-8_REV_A_Qualcomm_Spect…

1. Log Analyzer

2. Video pre-processing（可能耗時數分鐘）

3. Motion tracker / trajectory estimation

### Calibration 會自動產生：

| 參數                                      | 說明                      |
| --------------------------------------- | ----------------------- |
| **Focal Length（pixel normalized 1920）** | EIS stabilization 的核心   |
| **Timing Offset [us]**                  | Gyro timestamp 與 SOF 對齊 |

標準：

- timing offset ≈ 0 ±1000 µs

- avg calibration error ≈ 1 px（越低越好）

### 📍 Step 6 – Blur Masking Tuning（校正模糊遮蔽）

參考表格（文件內容）：
| Parameter              | 說明                             | 建議值     |
| ---------------------- | ------------------------------ | ------- |
| enable                 | 開啟模糊遮蔽                         | 1       |
| exposure_time_th       | 曝光超過此值才啟動 blur masking         | 0.009 s |
| start_decrease_at_blur | 掃到 blur pixel 數量 > 12 開始減少 EIS | 12      |
| end_decrease_at_blur   | 超過 20 停止 EIS                   | 20      |
| min_strength           | 最低 EIS 力度                      | 0.8     |

使用方式：

1. 載入 gyro log

2. 點選 Estimate Blur

3. 視 blur peak 位置調整 threshold

## 🔶 五、EIS & LDC 全套調整步驟流程表（工程可用）
| 步驟 | 類型                    | 內容                                       | 目的                    |
| -- | --------------------- | ---------------------------------------- | --------------------- |
| 1  | 前置                    | ISP/3A 準備、AF 穩定、FPS 穩定                   | 確保校正可用                |
| 2  | Device Config         | 設為 Operation Mode 2，開啟 gyro dump，關閉 FOVC | 進入校正模式                |
| 3  | 設定 Margin             | 設置 EISWidthMargin / HeightMargin         | 提供防手震裁切空間             |
| 4  | 拍攝 LDC Checkerboard   | 20–30 張、不同角度                             | LDC grid 產生           |
| 5  | LDC Calibration       | 產出 Out2In + In2Out grids                 | EIS RS correction 使用  |
| 6  | 拍攝靜止影片                | 60 秒固定                                   | 校正 gyro bias/noise    |
| 7  | 拍攝 Calibration Videos | 旋轉 25s、遠距場景、光線良好                         | 獲得 motion model input |
| 8  | 拍攝 Blur Masking Video | 室內走動 + 靜止                                | Blur masking 調校       |
| 9  | 匯出 Logs               | gyro/frame/init dumps                    | 校正必需資料                |
| 10 | EIS Log Analyzer      | 檢查影片與 log 是否可用                           | 阻擋錯誤輸入                |
| 11 | EIS Calibration       | 計算 focal length、timing offset            | 生成核心參數                |
| 12 | Blur Masking Tuning   | 設置三個 threshold                           | 讓 EIS 在模糊時不過度補償       |
| 13 | 匯出 Chromatix XML      | 寫入 EIS/LDC 最終值                           | 用於 device deploy      |
| 14 | On-device Validation  | 拍攝實際影片檢查                                 | 確認穩定與畫質一致             |
