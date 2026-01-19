# CCM (Color Correction Matrix, 色彩校正矩陣)
在相機 ISP (Image Signal Processor) 流程中是非常關鍵的一步，它決定了影像最終呈現出來的色彩風格是否準確、討喜。

簡單來說，感光元件（Sensor）“看到”的顏色，和人眼“看到”的顏色是不一樣的。CCM 的作用就是充當一個「翻譯官」，把 Sensor 抓到的原始 RGB 數值，轉換成符合人類視覺標準（例如 sRGB 色域）的 RGB 數值。
1. CCM 的核心概念與公式
CCM 本質上是一個 3x3 的線性代數矩陣。它透過矩陣乘法，將輸入影像的每一個像素的 R、G、B 三個通道的值重新混合，計算出新的 R、G、B 值。
數學公式
假設輸入像素的顏色向量是 $\begin{bmatrix} R_{in} \\ G_{in} \\ B_{in} \end{bmatrix}$，輸出像素的顏色向量是 $\begin{bmatrix} R_{out} \\ G_{out} \\ B_{out} \end{bmatrix}$，而 CCM 矩陣為 $M$：

$$M = \begin{bmatrix} C_{rr} & C_{rg} & C_{rb} \\ C_{gr} & C_{gg} & C_{gb} \\ C_{br} & C_{bg} & C_{bb} \end{bmatrix}$$

那麼校正過程就是：
$$\begin{bmatrix} R_{out} \\ G_{out} \\ B_{out} \end{bmatrix} = \begin{bmatrix} C_{rr} & C_{rg} & C_{rb} \\ C_{gr} & C_{gg} & C_{gb} \\ C_{br} & C_{bg} & C_{bb} \end{bmatrix} \times \begin{bmatrix} R_{in} \\ G_{in} \\ B_{in} \end{bmatrix}$$

展開來看，新的紅色通道 $R_{out}$ 是由原本的 R, G, B 按比例混合而成的：

$$R_{out} = C_{rr} \cdot R_{in} + C_{rg} \cdot G_{in} + C_{rb} \cdot B_{in}$$
$$G_{out} = C_{gr} \cdot R_{in} + C_{gg} \cdot G_{in} + C_{gb} \cdot B_{in}$$
$$B_{out} = C_{br} \cdot R_{in} + C_{bg} \cdot G_{in} + C_{bb} \cdot B_{in}$$

## 關鍵特性 (Sam 的小筆記)
1. 對角線元素 (Diagonal Elements): $C_{rr}, C_{gg}, C_{bb}$ 通常接近 1.0，代表保留原始通道的主要成分。
2. 非對角線元素 (Off-diagonal Elements): 用來引入其他通道的顏色進行修正。例如 $C_{rg}$ 是負值時，表示為了讓紅色更純淨，需要減去一些綠色的成分。
3. 白平衡保持 (White Balance Preservation): 理想情況下，CCM 每一列（Row）的總和應該等於 1 (例如 $C_{rr} + C_{rg} + C_{rb} = 1$)。這樣能確保純白色經過轉換後依然是純白色，不會偏色。
4. 線性域操作: 標準的 CCM 運算應該在「線性 RGB 空間」進行。也就是說，輸入影像如果已經經過 Gamma 校正 (如常見的 JPG)，理論上要先「反 Gamma (De-Gamma)」，做完 CCM 後再乘回 Gamma。但為了範例的直觀性與互動速度，下面的程式我們直接在現有影像上操作，這在快速調整風格時也很常見。