import cv2

# 替換成你的 IPCam 串流 URL (RTSP 或 HTTP)
# 範例：rtsp://admin:12345@192.168.1.100:554/stream1
# 範例：192.168.1.95
ipcam_url = "rtsp://192.168.1.2:1254/test.sdp"

# 建立 VideoCapture 物件
cap = cv2.VideoCapture(ipcam_url)

# 檢查是否成功開啟
if not cap.isOpened():
    print("無法開啟串流！請檢查 URL 或網路連線。")
    exit()

while True:
    # 逐幀讀取
    ret, frame = cap.read()

    if not ret:
        print("讀取幀失敗，串流結束或中斷。")
        break

    # 顯示影像
    cv2.imshow('IPCam Feed', frame)

    # 按 'q' 鍵退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 釋放資源
cap.release()
cv2.destroyAllWindows()
