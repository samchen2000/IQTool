# SFR (Spatial Frequency Response) 與 MTF (Modulation Transfer Function)
在影像處理領域，這兩者基本上是在討論同一件事：「系統對於影像細節的還原能力」。簡單來說，就是相機、鏡頭或演算法能把影像拍得多清楚。
---
## 1. 核心概念與公式
### MTF (調制度轉換函數)
MTF 描述的是不同空間頻率下，影像對比度的還原率。 對比度（Contrast）的公式定義為：
$$C = \frac{I_{max} - I_{min}}{I_{max} + I_{min}}$$
其中 $I_{max}$ 和 $I_{min}$ 分別是影像中亮部與暗部的強度。

MTF 的定義則是：

$$MTF(f) = \frac{C_{output}(f)}{C_{input}(f)}$$
通常我們假設輸入的對比度是 1，所以 MTF 就是輸出影像的對比度隨頻率變化的函數。

### SFR (空間頻率響應)
SFR 是計算 MTF 的一種具體方法，最常見的是 「斜邊法」(Slanted Edge Method, ISO 12233)。它的計算流程如下：

1. ESF (Edge Spread Function, 邊緣擴散函數)： 找到影像中的斜邊，對其垂直方向取樣，得到亮暗交界的曲線。

2. LSF (Line Spread Function, 線擴散函數)： 對 ESF 求一階導數，這代表了系統對「線」的反應。
$$LSF(x) = \frac{d}{dx} ESF(x)$$
