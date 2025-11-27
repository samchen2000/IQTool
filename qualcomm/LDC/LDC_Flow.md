# 安裝
## 安裝LDC工具：

開啟高通軟體套件管理器 3 (QPM3) 或造訪https://qpm.qualcomm.com。
如果您無法訪問，請聯絡您的高通技術客戶經理。

# 點選“工具”。
# 搜尋“LDC”。
點選展開「相機工具」，然後點選「Qualcomm® 相機鏡頭畸變校準工具 (LDC)」。
選擇版本並點選安裝。
LDC軟體包包含兩個工具：

dot_chart_calib用於運行校準過程。 有關範例配置和照片，請參閱Qualcomm_LDC\Camera_Distortion_Calibration\tool\materials 。
LdcTool用於驗證校準並執行仿真
dot_chart_calib
要求

dot_chart_calib需要 OpenCV v4.2.0 和 OpenCV 庫。請從https://opencv.org/下載 OpenCV 函式庫。

限制

目前不支援魚眼鏡頭
初始化需要供應商曲線
命令

以下命令在以下環境中可用：dot_chart_calib:

1. 產生實體點陣圖圖案：
```
dot_chart_calib.exe Chart <chart_config_file> <output_pattern_svg>
```
例如：
```
dot_chart_calib.exe Chart chart_config.txt output_pattern.svg
```
將供應商表格轉換為一維曲線格式以進行校準：
```
dot_chart_calib.exe Vendor <vendor_config_file> <output_curve_bin>
dot_chart_calib.exe Parse <output_curve_bin><output_curve_txt>
```
例如：
```
dot_chart_calib.exe Vendor vendor_config.txt vendor_garbled.bin
pause
dot_chart_calib.exe Parse vendor_garbled.bin vendor.txt
pause
```
執行LDC校準：
```
dot_chart_calib.exe Calib <config_file> <output_bin>
```
例如：
```
dot_chart_calib.exe Calib calib_config.txt output_bin.bin
pause
```
將 LDM 二進位檔案轉換為文字檔：
```
dot_chart_calib.exe Parse <parse_input_bin> <parse_output_txt>
```
例如：
```
dot_chart_calib.exe Parse output_bin.bin parsed_output.txt
pause
```
將失敗的條件參數二進位轉換為文字檔：
```
dot_chart_calib.exe Parse_criteria <parse_input_bin> <parse_output_txt>
```
例如：
```
dot_chart_calib.exe Parse_criteria output_bin.bin parsed_output.txt
pause
```
### LdcTool
工具模式

LdcTool它有兩種不同的模式：

轉換模式 – 用於將 1D LUT 轉換為 2D 變形貼圖：
LdcTool Convert <config file> <1D LUT> <2D warp map>
可以使用此dot_chart_calib工具產生一維查找表 (1D LUT)。請參閱 一維查找表 (1D LUT)。

變形模式－用於根據給定的變形圖對輸入影像進行去畸變/校正：
LdcTool Warp <config file> <warp map> <map type> <input YUV image> <output YUV image>
<warp map>此功能<2D warp map>來自轉換模式。此處僅支援標準 iWarp 映射（類型 2）。輸入影像和輸出影像均為 YUV NV12 格式，無填充。例如：
LdcTool.exe Warp config.txt 2d_mesh_result.txt 2 input.yuv output.yuv
pause
設定檔

兩種模式都需要設定檔。此檔案包含以下基本配置和調優參數。

範圍	描述
Image width out
Image height out
<輸出影像>的寬度和高度。
Image width in
Image height in
輸入影像的寬度和高度。

兩者的長寬比必須與校準影像的長寬比相同。

Number of vertices per row
Number of vertices per column
每行和每列的頂點數決定了網格的所需大小。這些數值通常不需要改變。

預設值分別為 65 和 97。

Projection type	對於LDC，投影類型可以留空為0，即透視/針孔投影。該工具還支援將影像還原為非透視平面，例如圓柱面（投影類型=1）和等距柱狀投影（投影類型=2）。
RxRyRz	
RxRyRz 是三個參數，分別定義了圍繞這三個軸旋轉的角度。在進行影像去畸變處理時，這些參數可用於旋轉和裁​​切輸入影像。

預設值均為 0，表示不旋轉。

這些在IPC ePTZ應用中非常有用。

Output FOV horizontal
Output FOV vertical
對於水平/垂直輸出視場角，假設輸出投影平面正好位於焦點處（校準檔案中提供的焦點長度將被縮放並通過 1D LUT）。

此參數定義了輸出影像水平/垂直方向的視野範圍（以度為單位）。

如果您不想故意改變寬高比，建議將垂直 FOV 設定為 0。

Cp initial phase	CP初始相位（0-360）是圓柱投影的起始相位。調整此參數可使輸出影像水平旋轉。
Cp cutoff	CP截止角（0-45）是圓柱投影中的截止角。它定義了從相機中心開始的“盲圓”。
以下是一個設定檔範例：
Image width out: 3840
Image height out: 2160
Image width in: 3840
Image height in: 2160
Number of vertices per row: 65
Number of vertices per column: 97
Projection type: 0
RxRyRz: 0 0 0
Output FOV horizontal: 90
Output FOV vertical: 0
Cp initial phase: 0
Cp cutoff: 20
限制

目前，影像扭曲模擬僅支援 NV12 YUV 影像。輸出影像與使用相同扭曲貼圖的目標扭曲引擎的輸出影像品質相當，但並非位元精確匹配。

由於透視投影的特性，理論上的最大支持視場角不超過180度。實際上，對於全視野大尺寸液晶顯示器，建議視場角不超過160度。


