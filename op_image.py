import cv2  # 匯入 OpenCV 函式庫


img = cv2.imread('meme.jpg')  # 讀取圖片
cv2.imshow('oxxostudio',img)        # 賦予開啟的視窗名稱，開啟圖片
cv2.waitKey(0)                 # 按下任意鍵停止
cv2.destroyAllWindows()        # 結束所有圖片視窗