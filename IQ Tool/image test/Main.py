import tkinter as tk
from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfile
from PIL import Image, ImageTk
import time
import cv2
from queue import Queue
from threading import Thread
import sys
import getopt
import numpy as np

#vid_cam = cv2.VideoCapture(source)

#while True:
#    try:
#        num = float(input('請輸入用電度數 : '))
#        output = 200
#        if num<=200:
#            output = num*3.2
#        elif num>200 and num<=300:
#            output = 200*3.2 + (num - 200)*3.4
#        else:
#            output = 200*3.2 + 100*3.4 + (num - 300)*3.6
#        print(f'用電 {num} 度共 {output} 元')
#    except:
#        break

class GUI():
    def __init__(self, w=720, h=640):
        # ---------------主界面--------------------
        self.width = w
        self.height = h
        self.mygui = Tk(className="影像處理技術")
        self.mygui.geometry(str(w)+'x'+str(h))
        self.mygui.resizable(False, False)  # 固定視窗大小
        self.mygui.grid()
        self.createWiget()
    def createWiget(self):
        # ---------------菜單欄--------------------
        self.mymenu = Menu(self.mygui)

        # 建立下拉選單
        filemenu = Menu(self.mymenu, tearoff=0)
        filemenu.add_command(label='打開圖片', command=self.command_open)
        self.mymenu.add_cascade(label="文件", menu=filemenu)
        # 二值化菜單
        self.mymenu.add_command(label="二值化", command=self.command_threshold)
        self.mygui.config(menu=self.mymenu)
        # RGB 菜單
        self.mymenu.add_command(label="RGB", command=self.show_cam)
        self.mygui.config(menu=self.mymenu)
        # 幫助菜單
        self.mymenu.add_command(label="幫助", command=self.command_help)
        self.mygui.config(menu=self.mymenu)

        # ---------------圖片控件------------------- 變量3->label
        self.label = Label(self.mygui, width=self.width, height=self.height)
        self.label.place(relx=0.01, rely=0.01)

    #def createBtn(self):
        #btn = self.Button(root, )

    def command_open(self):
        global img
        filename = askopenfilename(initialdir='Sample.bmp')
        self.image = Image.open(filename)
        image1 = self.image.resize((self.width, self.height), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(image1)  #轉換格式
        self.label['image'] = img

    def Threshold(self):
        global img1
        img1 = np.array(self.image)
        self.low = self.v1.get()
        self.choice = self.v2.get()
        w, h = self.image.size
        if (self.choice == 1):
            for j in range(h):
                for i in range(w):
                    if img1[j, i] < self.low:
                       img1[j, i] = 255
                    else:
                       img1[j, i] = 0
        elif (self.choice == 2):
            for j in range(h):
                for i in range(w):
                    if img1[j, i] < self.low:
                       img1[j, i] = 0
                    else:
                       img1[j, i] = 255
        image1 = Image.fromarray(np.uint8(img1))
        image1 = image1.resize((self.width, self.height), Image.ANTIALIAS)
        img1 = ImageTk.PhotoImage(image1)  # 转格式
        self.label['image'] = img1

    def pic_cancel(self):
        self.top.destroy()


    def command_threshold(self):
        self.top = Toplevel(width=500, height=250)
        # 增加標題
        self.top.title('二值化處理')
        # 增加按鈕
        bottom1 = tk.Button(self.top, text='二值處理', font=('宋体', 16), command=self.Threshold)
        bottom1.place(relx=0.2, rely=0.8, relwidth=0.16, relheight=0.12)
        bottom2 = tk.Button(self.top, text='關閉', font=('宋体', 16), command=self.pic_cancel)
        bottom2.place(relx=0.6, rely=0.8, relwidth=0.16, relheight=0.12)
        # 增加標籤
        Label1 = tk.Label(self.top, text="閥值", font=('宋体', 16))
        Label1.place(relx=0.01, rely=0.3, relwidth=0.16, relheight=0.12)
        # 增加本文框
        self.v1 = IntVar()
        self.Entry1 = tk.Entry(self.top, textvariable=self.v1, font=('Times New Roman', 16))
        self.Entry1.place(relx=0.16, rely=0.3, relwidth=0.15, relheight=0.12)
        self.v1.set(100)
        # 增加單選按鈕
        LabelFrame1 = tk.LabelFrame(self.top, text="白像素", font=('宋体', 16))
        LabelFrame1.place(relx=0.35, rely=0.1, relwidth=0.5, relheight=0.5)
        self.v2 = IntVar()

        Radiobutton1 = tk.Radiobutton(LabelFrame1, text='以下', font=('宋体', 16), variable=self.v2, value=1)
        Radiobutton1.place(relx=0.1, rely=0.4, relwidth=0.25, relheight=0.2)
        Radiobutton2 = tk.Radiobutton(LabelFrame1, text='以上', font=('宋体', 16), variable=self.v2, value=2)
        Radiobutton2.place(relx=0.4, rely=0.4, relwidth=0.25, relheight=0.2)
        self.v2.set(1)
    def command_rgbData(self):
        exit()
    
    def command_help(self):
        user_name = input("關於學習過程需要不斷的練習,要有明確的目標,勇往向前.")
        
    def show_cam(self):
        source = "rtsp://192.168.1.10/video0"
        vid_cam = cv2.VideoCapture(0)
        if not vid_cam.isOpened():
            print('無法打開攝影機')
            exit()
        while(vid_cam.isOpened()):
           # vid_cam.get = cv2.COLOR_BGR2GRAY
            ret, image_frame = vid_cam.read() 
            #TODO : 使用可以測試的環境進行測試
            
            cv2.imshow('UVC CAM', image_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        vid_cam.release()
        cv2.destroyAllWindows()
    def window_draw(self):
        window = tk.Tk()
        window.title("設定影像參數")
        Label = tk.Label(window, text="使用參數調整影像")
        Label.pack()
        contrast_But = tk.Button(window, text="對比度")
        brightness_But = tk.Button(window,text="明亮度")
        sharpness_But = tk.Button(window, text="銳利度")
        hue_But = tk.Button(window,text="色相")
        color_But = tk.Button(window, text="色度", width= 100, height= 30,X= 100,Y=30 )
""""        
class Camera:
    device_id = 1
    def __init__(self, device_id, frame_queue):
        self.device_id = device_id
        self.cam = cv2.VideoCapture(self.device_id)
        self.frame_queue = frame_queue
        self.is_running = False
        self.fps = 0.0
        self._t_last = time.time() * 1000
        self._data = {}
    def capture_queue(self):
        self._t_last = time.time() * 1000
        while self.is_running and self.cam.isOpened():
            ret, frame = self.cam.read()
            if not ret:
                break
            if self.frame_queue.qsize() < 1:
                t = time.time() * 1000
                t_span = t - self._t_last
                self.fps = int(1000.0 / t_span)
                self._data["image"] = frame.copy()
                self._data["fps"] = self.fps
                self.frame_queue.put(self._data)
                self._t_last = t
    def run(self):
        self.is_running = True
        self.thread_capture = Thread(target=self.capture_queue)
        self.thread_capture.start()
        
    def stop(self):
        self.is_running = False
        self.cam.release()
def show_frame(frame):
        while True:
            data = frame.get()
            image = data["image"]
            cv2.putText(image, "fps:{fps}".format(fps=data["fps"]), (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0))
            cv2.namedWindow("camera", cv2.WINDOW_AUTOSIZE)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            frame_queue.task_done()
"""
if __name__ == "__main__":

    root = GUI(720, 640)
#    frame_queue = Queue()
#    cam = Camera(0, frame_queue)
#    cam.run()
    
#    thread_show = Thread(target=show_frame, args=(frame_queue,))
#    thread_show.start()
#    time.sleep(60)
#    cam.stop()
    mainloop()