import cv2
import ffmpeg
import numpy as np

source = "rtsp://192.168.1.10/video0"
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
eyes_cascade = cv2.CascadeClassifier("haarcascade_eye.xml")
vid_cam = cv2.VideoCapture(index=1)
#faces = face_cascade.detectMultiScale(gray)  # 需要定義 gray ps: gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)   # 將鏡頭影像轉換成灰階
#vid_cam = cv2.VideoCapture(source)
img = np.zeros((1920,1080,3),dtype = 'uint8')
#先设置参数，然后读取参数
vid_cam.set(3,1280)
vid_cam.set(propId=4,value=720)
#vid_cam.set(15, 0.1)
arr = np.array([1, 2, 3, 4, 5])
print(arr)    # [1 2 3 4 5]
print("width={}".format(vid_cam.get(3)))
print("height={}".format(vid_cam.get(4)))
print("FPS={}".format(vid_cam.get(5)))
print("Brightness={}".format(vid_cam.get(10)))
print("Contrast={}".format(vid_cam.get(11)))
print("Saturation={}".format(vid_cam.get(12)))
print("HUE={}".format(vid_cam.get(13)))
print("GAIN={}".format(vid_cam.get(14)))
print("exposure={}".format(vid_cam.get(15)))
print("White Balance={}".format(vid_cam.get(17)))
#print("test = {}",format (test)  )
#while True:
if not vid_cam.isOpened():
    print('無法打開攝影機')
    exit()
'''
while(vid_cam.isOpened()):
    ret, image_frame = vid_cam.read() 
    #TODO : 使用可以測試的環境進行測試
    cv2.line,(image_frame,(50,50),(250,250),(0,0,255),10)
    cv2.imshow('UVC Cam', image_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
'''
if not vid_cam.isOpened():
    print("Cannot open camera")
    exit()
while True:
    ret, frame = vid_cam.read()
    if not ret:
        print("Cannot receive frame")
        break
    frame = cv2.resize(frame,(640,480))              # 縮小尺寸，避免尺寸過大導致效能不好
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)   # 將鏡頭影像轉換成灰階
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=3, minSize=(40,40), )      # 偵測人臉
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)   # 標記人臉
        print('X='+str(x), 'Y='+str(y))
    eyes = eyes_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=3, minSize=(40, 40), )    #偵測眼睛
    for (ex, ey, ew, eh) in eyes:
        cv2.rectangle(frame,(ex,ey),(ex+ew,ey+eh),(255,0,0),2)    #標記眼睛
    cv2.imshow('UVC Cam face detect', frame)
    if cv2.waitKey(1) == ord('q'):
        break
vid_cam.release()
cv2.destroyAllWindows()