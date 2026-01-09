# IP CAM 串流播放器 (IP CAM Streaming Player)

## 功能特色

- **即時影像顯示**: 左側大型畫布實時顯示 RTSP/HTTP 串流影像
- **解析度與 FPS 顯示**: 
  - 左下角實時顯示當前影像解析度與 FPS
  - 右側控制面板也顯示詳細的連線資訊
- **URL 輸入與控制**: 右側輸入框可輸入任意 RTSP/HTTP URL
- **多執行緒架構**: 使用獨立執行緒讀取串流，避免 UI 卡頓
- **低延遲設計**: 配置 OpenCV 緩衝區大小以最小化延遲

## 系統需求

- Python 3.8+
- tkinter (通常包含在 Python 安裝中)
- OpenCV (cv2)
- Pillow (PIL)

## 安裝依賴

```powershell
pip install -r requirements_ipcam.txt
```

或手動安裝：

```powershell
pip install opencv-python pillow
```

## 使用方式

### 啟動程式

```powershell
cd "d:\IQ app\python\IQTool\IQ Tool\image test"
python ipcam_player.py
```

### 操作步驟

1. **輸入 URL**
   - 在右側「RTSP/HTTP URL」輸入框中輸入串流位址
   - 範例: `rtsp://192.168.1.2:1254`
   - 預設值已填入上述範例

2. **開啟串流**
   - 按「開啟串流」按鈕，或在輸入框中按 Enter
   - 會自動連線並在左側影像區顯示

3. **監控狀態**
   - 左下角顯示即時解析度與 FPS
   - 右側連線資訊面板顯示詳細狀態

4. **關閉串流**
   - 按「關閉串流」按鈕停止連線

5. **退出程式**
   - 按「退出程式」或關閉視窗

## URL 格式

### RTSP (推薦)
```
rtsp://[使用者:密碼@]IP:連接埠/路徑
rtsp://192.168.1.2:1254
rtsp://admin:12345@192.168.1.2:554/stream
```

### HTTP
```
http://[使用者:密碼@]IP:連接埠/路徑
http://192.168.1.100:8080/video.mjpeg
```

## 常見問題

### 問題 1: 無法連線到 IP CAM
**解決方案**:
- 檢查 IP 位址與連接埠是否正確
- 確認網路連線正常
- 驗證 IP CAM 已啟動且正在運行
- 嘗試用其他工具(如 VLC) 驗證 URL 是否有效

### 問題 2: FPS 很低
**原因與解決**:
- 網路延遲: 檢查網路品質
- IP CAM 負載: 降低 IP CAM 解析度或幀率
- 本機性能: 關閉其他應用程式，增加可用資源

### 問題 3: 影像卡頓或延遲高
**解決方案**:
- 減少其他網路流量
- 降低 IP CAM 解析度
- 嘗試關閉並重新開啟串流

## 進階調整

若需調整程式行為，可編輯 `ipcam_player.py` 中的以下參數：

```python
# 串流緩衝區大小 (數值越小延遲越低，但可能出現掉幀)
self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# UI 更新間隔 (毫秒)
self.root.after(30, self._update_ui)  # 改為更大的值可降低 CPU 使用率
```

## 輸出訊息

### 視窗狀態指示
- **紅色 (未連線)**: 未建立連線或已斷開
- **橙色 (連線中)**: 正在嘗試連線
- **綠色 (已連線)**: 成功連線且正在接收影像

## 技術細節

- **執行緒架構**: 獨立執行緒處理網路 I/O，主執行緒負責 UI 更新
- **影像佇列**: 使用 `queue.Queue` 在執行緒間傳遞影像，大小限制為 2 幀
- **FPS 計算**: 基於接收到的幀數與經過時間計算
- **寬高比保持**: 顯示影像時保持原始寬高比

## 相容性

- 支援 RTSP、HTTP、RTMP 等 OpenCV VideoCapture 支援的格式
- 可用於監控攝影機、IP CAM、MJPEG 伺服器等

## 授權

用於教學與內部測試用途。

---

**版本**: 1.0  
**最後更新**: 2026-01-09
