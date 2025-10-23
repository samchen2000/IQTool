## PDAF & CAP 工作原理
PDAF（相位檢測）、CAF（對比檢測） 的原理、常見策略、實務注意事項與市面上常見做法講清楚，然後給一個可讀、註解完整的 Python 示範程式（模擬 PDAF 的位移估計 + CAF 的對比量測與 hill-climb 搜索），程式可在本地修改並執行做實驗。

### PDAF（Phase Detection AF） — 原理重點

物理原理：把鏡頭光圈「分成兩個子孔徑」（或在感測器上用兩組微透鏡 / 兩個光電二極體位元），兩個子孔徑看同一場景但光線入射角度不同。若鏡頭未對焦，兩個子孔徑產生的影像在感應面會有水平/垂直位移（phase / disparity）。比較左右（或上下）影像之間的相位差或位移，就能直接得到「焦點在前方還是後方」及大致的偏移量（signed focus error）。

### 核心優點：

可直接得知方向（前移/後移）與量值 → 可以一次性（或少次）移動鏡組到正確位置（不像純 CAF 要反覆試探）。

速度快，非常適合連續追蹤（video / AF-C）。

### 需求/限制：

需要分辨左/右光路的差異（硬體支援：專用相位像素或雙像素），與足夠的紋理/對比度以計算位移。

在低光與低對比場景、或高度重複紋理（格柵）下，位移測量品質下降，可能造成誤鎖。

### 常見實作：

DSLR：獨立相位 AF 模組（反光鏡導光到專用 AF 感測器）。

Mirrorless / 手機：on-sensor PDAF（例如 Dual-Pixel 的概念：一個像素內有左右兩個感測單元），可做到每像素相位檢測與高覆蓋率。

### CAF（Contrast-detection AF） — 原理重點

物理原理：以影像「對比/銳利度」作為焦準依據（沒有直接方向資訊）。常用的對比指標：Laplacian variance、Tenengrad（梯度能量）、Brenner metric、normalized variance 等。演算法會改變焦距、測量對比並尋找最大值（optimize contrast）。

### 核心優點：

硬體需求少（直接在影像上計算），終點通常非常準（局部極大通常對應最佳解析）。

在某些情況下（沒有 PDAF 硬體的便宜系統）是唯一選擇。

#### 缺點：

不能直接知道要往哪一方向移動（無符號誤差），因此常採「試探式（hunt）」或搜尋演算法（coarse-to-fine / hill-climb / golden-section / bracketing）。

若場景低對比或動態場景（被攝物移動），CAF 會產生慢或震盪。

#### 加速技巧：

先做粗搜尋，再做細搜尋（multi-scale）。

用多個測點平均或 ROI 採樣以避免局部最大值誤鎖。

用預測（motion model）在 CAF 上疊加動態追蹤能力。

#### 對焦策略（工程上常見的設計）

Hybrid AF（混合式）：PDAF 作為 coarse / initial lock（快速找到方向與大致量），CAF 作為 fine-tune（精準化、去毛刺）。手機/相機常用。

Two-stage lock：先 PDAF 單步到估計位置 → 用小區間 CAF 差異最大化做收尾。

Continuous tracking (AF-C)：把測焦當成一個控制問題 — 使用運動預測（Kalman filter / constant-velocity model）、歷史位置、subject recognition（人臉/眼睛）來決定下一步鏡頭位移。

Zone / Face / Eye AF：把重心放在偵測出來的目標區域，減少被背景高對比干擾。

Calibration & mapping：PDAF 輸出（disparity）與鏡頭馬達步數或感測器焦平面需要事先校準 mapping（disparity → lens step），常以多點校準或線性近似。

Motor control：微調使用 PID 控制或更簡單的斜坡/限速控制避免過衝（不同驅動器：VCM、步進、STM 等）。

### 市面常見的對焦方式（快速列表）

```專用相位``` AF 模組（DSLR）：高速度、低延遲（需要反光鏡）。

```On-sensor PDAF```（Mirrorless / 手機）：Dual Pixel（Canon）、像 Sony/ Samsung 的相位像素、手機常見的 PDAF pixel array。

```Contrast``` AF（CDAF）：低成本系統 & 用於精修。

```Hybrid``` AF（PDAF + CDAF）：目前主流（手機、無反相機）。

```Laser``` AF / Time-of-Flight / Lidar depth：短距離快速測距並用於輔助對焦（手機）。

```Depth from stereo``` / multi-camera：雙鏡頭提供景深估計，輔助快速決策。

```機器學習的 subject``` / eye-AF：用 NN 偵測人臉/眼睛再把 AF 點聚焦於目標上。

### 實務注意（工程師要注意的事情）

PDAF 給的是位移量，但和鏡頭位置之間的關係必須校準（不同鏡頭、不同光圈下映射不同）。

CAF 很準但慢；在動態場景需結合運動預測或 PDAF 做初步導向。

混合策略常是最佳折衷：速度 + 精確度。

特殊場景：低對比、夜間、反光、薄景深下錯誤率升高；需要 fallback（多點檢查 / 增加曝光 / 使用輔助光）。