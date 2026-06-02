import cv2

# 計算亮度的函數
def calculate_brightness(r, g, b):
    return (0.299*r + 0.587*g + 0.114*b)

# 初始化攝影機
cap = cv2.VideoCapture(0)

# 定義全域變數
drawing = False  # 是否正在畫矩形
ix, iy = -1, -1  # 矩形的起始點
x, y, w, h = 0, 0, 0, 0  # 矩形的位置和大小

# 滑鼠回調函數
def draw_rectangle(event, ex, ey, flags, param):
    global ix, iy, x, y, w, h, drawing

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = ex, ey

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            x, y, w, h = ix, iy, ex-ix, ey-iy

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        x, y, w, h = ix, iy, ex-ix, ey-iy

# 設定滑鼠回調函數
cv2.namedWindow('Frame')
cv2.setMouseCallback('Frame', draw_rectangle)

while True:
    # 捕捉逐幀影像
    ret, frame = cap.read()
    
    if w > 0 and h > 0:
        # 畫矩形
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        
        # 獲取矩形右上角的 RGB 值
        b, g, r = frame[y, x+w-1]
        
        # 計算亮度
        brightness = calculate_brightness(r, g, b)
        
        # 顯示 RGB 和亮度值
        text = f"R: {r} G: {g} B: {b} Brightness: {brightness:.2f}"
        cv2.putText(frame, text, (x+w+10, y+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # 顯示結果影像
    cv2.imshow('Frame', frame)
    
    # 按 'q' 鍵退出迴圈
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 釋放攝影機並關閉視窗
cap.release()
cv2.destroyAllWindows()