# Copilot Instructions for IQTool

## 專案架構總覽
- 本專案為多模組 Python 工具集，聚焦於機器視覺、AI、條碼處理、數據轉換等領域。
- 主要目錄：
  - `ai/`：AI 相關腳本與 API Key 檢查、Gemini API 整合、自然語言處理流程。
  - `barcode/`：條碼產生與網頁展示。
  - `IQ Tool/`：影像調整、數據轉換、數學運算，含多個子目錄（如 `影像調整說明/`、`數據轉換/`、`Math/`）。
  - `qualcomm/`：機器視覺、感測器、VCM（馬達）控制腳本。
  - `SerDes/`：序列/解序列器相關 C 程式與設定。

## 關鍵開發流程
- **執行/測試**：
  - 主要 Python 腳本可直接以 `python <script>` 執行。
  - 若有 `.spec` 檔，代表可用 PyInstaller 打包：
    - Powershell 指令範例：`pyinstaller <spec file>`
  - 影像/AI 相關腳本多以 Jupyter Notebook (`.ipynb`) 或獨立 Python 檔案呈現。
- **依賴管理**：
  - 無明確 requirements.txt，請依各子目錄腳本 import 自行安裝（如 `opencv-python`, `numpy`, `requests`）。
  - AI 相關腳本可能需 Google Gemini API Key，請參考 `ai/GeminiApiKeyCheck.py`。

## 專案慣例與模式
- 影像處理、數據轉換、AI 皆以獨立模組/腳本分工，少有跨目錄 import。
- 主要流程/入口通常為 `Main.py` 或同名腳本（如 `IQ Tool/image test/Main.py`）。
- 影像調整、數據轉換、數學運算皆有對應子目錄，並以 `test.py`、`math_test.py` 等作為測試腳本。
- 重要流程圖、說明文件以 `.drawio`、`.md`、`.txt` 格式存放於各子目錄。

## 整合與溝通
- AI 與影像模組間以檔案（如圖片、CSV）交換資料，少有直接函式呼叫。
- Qualcomm 相關腳本與 SerDes C 程式為硬體溝通橋樑，請參考各自目錄。

## 典型範例
- 影像調整：`IQ Tool/image test/imageTuning.py`、`IQ Tool/image test/image_light.py`
- AI API Key 檢查：`ai/GeminiApiKeyCheck.py`、`ai/apikeycheck.py`
- 條碼產生：`barcode/barcodemake.py`
- 數據轉換：`IQ Tool/數據轉換/csv2bin.py`

## 其他注意事項
- 專案仍在持續補充，部分目錄/腳本可能尚未完成。
- 若需新增模組，建議依現有目錄結構獨立分工，並於 README 或目錄下補充說明。

---
如有不明確或遺漏之處，請回饋以便補充完善。
