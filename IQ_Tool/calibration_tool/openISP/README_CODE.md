## 📊 openISP 項目分析報告  
### 一、項目概覽
openISP (Open Image Signal Processor) 是一個開源的圖像信號處理系統，用於將相機傳感器採集的原始RAW圖像轉換為RGB/YUV格式供進一步處理或顯示。

### 二、文件夾結構分類
文件夾	|功能	|内容|
----|----|----|
model/	|ISP算法實現	|14個Python模塊，每個對應一個處理步驟
config/	|參數配置	|config.csv(主配置)、config_test.csv(測試配置)
raw/	|圖像數據	|test.RAW(10/12位原始圖像)、test_12_bit_img.jpeg
docs/	|文檔資料	|Image Signal Processor.pdf、.xmind(思維導圖)
images/	|流程圖	|isp_pipeline.png、isp_pipeline2.png
------------------------------------------------------

### 三、核心程式模塊 (model/ 目錄)
處理流程順序與功能：
#### 第一階段：RAW域處理 (保持Bayer陣列)

1. DPC - 死像素矯正 (Dead Pixel Correction)
2. BLC - 黑電平補償 (Black Level Compensation)
3. AAF - 防黑混淆濾波 (Anti-Aliasing Filter)
4. WBGC (AWB) - 白平衡增益控制 (Auto White Balance)
5. CNF - 色度噪聲濾波 (Chroma Noise Filter)
#### 第二階段：RGB域處理
6. CFA - 色彩濾波陣列插值/去馬賽克 (Demosaicing)
7. CCM - 色彩校正矩陣 (Color Correction Matrix)
8. GC - 伽馬校正 (Gamma Correction)

#### 第三階段：YUV域處理
9. CSC - 色彩空間轉換 (Color Space Conversion: RGB→YUV)
10. NLM - 非局部均值去噪 (Non-Local Means Denoising)
11. BNF - 雙邊濾波降噪 (Bilateral Noise Filtering)
12. EE - 邊緣增強 (Edge Enhancement)
13. FCS - 假色抑制 (False Color Suppression)
14. HSC - 色調/飽和度控制 (Hue/Saturation Control)
15. BCC - 亮度/對比度控制 (Brightness/Contrast Control)

### 四、程式運作流程

┌─────────────────────────────────────────────────────────────┐  
│ 1. 加載配置 (isp_pipeline.py)                                │  
│    └→ 讀取 config.csv 獲取所有處理參數                       │
├─────────────────────────────────────────────────────────────┤  
│ 2. 加載RAW圖像                                               │  
│    └→ 讀取 test.RAW (1280×720, 16位無符號整數)              │
├─────────────────────────────────────────────────────────────┤  
│ 3. RAW域處理 (Bayer陣列)                                    │  
│    DPC → BLC → AAF → WBGC → CNF                             │
├─────────────────────────────────────────────────────────────┤  
│ 4. RGB域處理                                                │  
│    CFA(去馬賽克) → CCM(色彩校正) → GC(伽馬校正)              │  
├─────────────────────────────────────────────────────────────┤  
│ 5. 色彩空間轉換                                              │  
│    CSC: RGB → YUV                                           │  
├─────────────────────────────────────────────────────────────┤  
│ 6. YUV域處理 (降噪+增強)                                    │  
│    NLM → BNF → EE → FCS → HSC → BCC                         │
├─────────────────────────────────────────────────────────────┤  
│ 7. 輸出最終圖像                                              │  
│    └→ 亮度(Y) + 色度(Cb,Cr) 組合                            │
└─────────────────────────────────────────────────────────────┘

### 五、配置文件分析 (config.csv)
配置參數分類：  
----|----|----|----|  
類別 |	參數	| 示例值	| 說明 | 
----|----|----|----|
RAW圖像	|raw_w, raw_h	|1920×1080	|輸入圖像尺寸
DPC	|dpc_thres, dpc_mode	|30, gradient	|死像素閾值和檢測模式
BLC	|bl_r, bl_gr, bl_gb, bl_b	|0	|各色通道黑電平偏移
AWB	|r_gain, gr_gain, gb_gain, b_gain	|1.5, 1.0, 1.0, 1.1	|白平衡增益
BNF	|bnf_dw (5×5矩陣)	|見config.csv	|距離權重(用於雙邊濾波)
EE	|ee_gain, ee_thres	|[32,128], [32,64]	|邊緣增強增益和閾值
色彩	|hue, saturation	|128, 256	|色調和飽和度調整

### 六、核心算法示例
1. DPC (死像素矯正) - dpc.py
- 使用梯度檢測方法
- 檢查周圍8個像素(3×3窗口)的梯度
- 若中心像素與周圍差異超過閾值，替換為鄰近值
- 采用反射填充避免邊界問題
2. CFA (去馬賽克) - cfa.py
- 支持 Malvar 插值算法
- 處理RGGB Bayer陣列中4種像素類型：
    - Red (R)：紅色像素
    - Green-Red (Gr)：紅色行綠色像素
    - Green-Blue (Gb)：藍色行綠色像素
    - Blue (B)：藍色像素
- 每種類型使用不同的插值公式
3. BNF (雙邊濾波) - bnf.py
核心邏輯：
- 計算5×5窗口內每個像素與中心像素的色差 (radiometric difference)
- 根據色差分檔選擇権重 (rw[0-3])
- 將色差權重與距離權重相乘 (距離權重: dw矩陣)
- 加權平均計算輸出像素值

### 七、測試文件 (test_bnf.py)
用於單獨測試BNF模塊：

- 使用縮小的圖像 (128×72) 加快測試
- 使用 config_test.csv 配置
- 大多數模塊被註釋，只測試BNF功能
- 用於開發時調試和驗證

### 八、數據流向圖
test.RAW (原始圖像)  
    ↓  
config.csv (參數)  
    ↓  
[DPC] → [BLC] → [AAF] → [WBGC] → [CNF]  
    ↓  
[CFA去馬賽克]  
    ↓  
[CCM色彩校正] → [GC伽馬校正]  
    ↓  
[CSC色彩空間轉換]  
    ↓  
[NLM] → [BNF] → [EE] → [FCS]  
    ↓  
[HSC] + [BCC]  
    ↓  
最終YUV圖像輸出  

### 九、技術亮點
1. **模塊化設計**：每個算法獨立為一個類，易於集成和調試
2. **參數可配置**：所有參數通過CSV文件管理，無需修改代碼
3. **多域處理**：結合RAW、RGB、YUV三個域的優勢
4. **降噪策略**：使用非局部均值 + 雙邊濾波的兩層降噪
5. **硬體友好**：設計參考硬體實現，包含邊界和溢出處理

### 十、主要文件速覽
文件	|大小	|用途
----|----|----|
isp_pipeline.py	|~326行	|完整ISP流水線主程序
test_bnf.py	|~337行	|BNF算法單元測試
model/*.py	|各式規模	|14個ISP模塊實現
config.csv	|112行	|完整參數配置表  

