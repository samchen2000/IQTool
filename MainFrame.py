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

class Main_GUI():
    def __init__(self, w = 1080, h = 640):
        #self = tk.Tk()
        left = 30
        top = 30
        self.width = w
        self.height = h
        self.mygui = Tk(className="影像處理主介面")
        #self.mygui.geometry(str(self.width)+'x'+str(self.height))
        self.mygui.geometry(f'{self.width}x{self.height}+{left}+{top}')  # 定義視窗的尺寸和位置
        self.mygui.resizable(False, False)  # 固定視窗大小
        self.mygui.grid()
        self.createWiget()
        self.LableFrame()
        self.Button()
        self.Table()
        self.radiobutton()
        self.entry()
        self.scale()
       # self.ImageFrame()
       # self.cam_frame()
        '''
        self.mygui = Tk(className="影像處理技術")
        self.mygui.geometry(f'{width}x{height}+{left}+{top}')  # 定義視窗的尺寸和位置
        self.mygui.title('主畫面')
        self.mygui.resizable(False, False)  # 固定視窗大小
        self.mygui.grid()
        self.Button()
        #self.cam_frame()
        '''        
    def Button(self):
        #增加按鍵
        contrast_But = tk.Button(self.mygui,padx=1,pady=1,text="對比度", font=('宋体', 12, 'bold'), bg='pink')
        contrast_But.place(relx=0.88, rely=0.05, relwidth=0.1, relheight=0.06)
        brightness_But = tk.Button(self.mygui,padx=1, pady=1, text="明亮度", font=('宋体', 12, 'bold'), bg= 'yellow')
        brightness_But.place(relx=0.88, rely=0.12, relwidth=0.1, relheight=0.06)
        sharpness_But = tk.Button(self.mygui,padx=1, pady=1, text="銳利度", font=('宋体', 12 , 'bold'), bg='green')
        sharpness_But.place(relx=0.88, rely=0.19, relwidth=0.1, relheight=0.06)
        saturation_But = tk.Button(self.mygui, padx=1, pady=1, text="飽和度", font=('宋体', 12, 'bold'), bg='red')
        saturation_But.place(relx=0.88, rely=0.26, relwidth=0.1, relheight=0.06)
        hue_But = tk.Button(self.mygui, padx=1, pady=1, text="色相", font=('宋体', 12, 'bold'), bg='blue')
        hue_But.place(relx=0.88, rely=0.33, relwidth=0.1, relheight=0.06)
        color_But = tk.Button(self.mygui, padx=1, pady=1, text="色度", font=('宋体', 12, 'bold'), bg='red')
        color_But.place(relx=0.88, rely=0.4, relwidth=0.1, relheight=0.06)
            
    def Table(self):
        #增加文字
        contrast_Lab = tk.Label(self.mygui, text='對比=', anchor='w', bg='green', )
        contrast_Lab.place(relx=0.67, rely=0.06, relwidth=0.06, relheight=0.03)
        brightness_Lab = tk.Label(self.mygui, text='明亮=', anchor='w', )
        brightness_Lab.place(relx=0.67, rely=0.12, relwidth=0.06, relheight=0.03)
        sharpness_Lab = tk.Label(self.mygui, text='銳利=', anchor='w', )
        sharpness_Lab.place(relx=0.67, rely=0.18, relwidth=0.06, relheight=0.03)
        saturation_Lab = tk.Label(self.mygui, text='飽和=', anchor='w', )
        saturation_Lab.place(relx=0.67, rely=0.24, relwidth=0.06, relheight=0.03)
        hue_Lab = tk.Label(self.mygui, text='色相=', anchor='w', )
        hue_Lab.place(relx=0.67, rely=0.30, relwidth=0.06, relheight=0.03)
        color_Lab = tk.Label(self.mygui, text='白平衡=', anchor='w', )
        color_Lab.place(relx=0.67, rely=0.36, relwidth=0.06, relheight=0.03)
        BLC_Lab = tk.Label(self.mygui, text='背光補償=', anchor='w', )
        BLC_Lab.place(relx=0.67, rely=0.42, relwidth=0.06, relheight=0.03)
        exposure_Lab = tk.Label(self.mygui, text='曝光=', anchor='w', )
        exposure_Lab.place(relx=0.67, rely=0.48, relwidth=0.06, relheight=0.03)
        gain_Lab = tk.Label(self.mygui, text='增益=', anchor='w', )
        gain_Lab.place(relx=0.67, rely=0.54, relwidth=0.06, relheight=0.03)
        width_Lab = tk.Label(self.mygui, text='寬度=', anchor='w', )
        width_Lab.place(relx=0.88, rely=0.50, relwidth=0.04, relheight=0.03)
        height_Lab = tk.Label(self.mygui, text='高度=', anchor='w', )
        height_Lab.place(relx=0.88, rely=0.55, relwidth=0.04, relheight=0.03)
        FPS_Lab = tk.Label(self.mygui, text='幀率=', anchor='w', )
        FPS_Lab.place(relx=0.88, rely=0.60, relwidth=0.04, relheight=0.03)
        
    
    def LableFrame(self):
        #增加文字功能框
        camera_Lab_frame = tk.LabelFrame(self.mygui, font=(12), text='main cam')
        camera_Lab_frame.place(relx=0.005, rely=0.01, relwidth=0.65, relheight=0.55)
        cam_contrel_Lab_frame = tk.LabelFrame(self.mygui, font=(12), text='相機控制')
        cam_contrel_Lab_frame.place(relx=0.66, rely=0.01, relwidth=0.33, relheight=0.63)
        face_detect_Lab_frame = tk.LabelFrame(self.mygui, font=(12), text='人臉偵測控制')
        face_detect_Lab_frame.place(relx=0.005, rely=0.64, relwidth=0.3, relheight=0.35)
        article_detect_Lab_frame = tk.LabelFrame(self.mygui, font=(12), text='物品偵測控制')
        article_detect_Lab_frame.place(relx=0.31, rely=0.64, relwidth=0.33, relheight=0.35)
        number_Lab_frame = tk.LabelFrame(self.mygui, font=(12), text='車牌偵測控制')
        number_Lab_frame.place(relx=0.65, rely=0.64, relwidth=0.34, relheight=0.35)
    
    def ImageFrame(self):
        frame = tk.Frame(self.mygui, width= 300, height=300, bg= 'blue', bd='3')
        frame.place(relx=0.01, rely=0.05, relwidth=0.48, relheight=0.5)
        filename = askopenfilename(initialdir='Sample.bmp')
        self.image = Image.open(filename)
        image1 = self.image.resize((self.width, self.height), Image.LANCZOS)
        la_image = ImageTk.PhotoImage(image1)  #轉換格式
        canvas = tk.Canvas(frame, width=500, height=300, bg='gray')  # Canvas
        canvas.create_image(5, 5, ancgro='nw', image=la_image)
        
        scrollX = tk.Scrollbar(frame, orient='horizontal')    # 水平捲軸
        scrollX.pack(side='bottom', fill='x')
        scrollX.config(command=Canvas.xview)

        scrollY = tk.Scrollbar(frame, orient='vertical')      # 垂直捲軸
        scrollY.pack(side='right', fill='y')
        scrollY.config(command=canvas.yview)

        canvas.config(xscrollcommand=scrollX.set, yscrollcommand=scrollY.set)   # Canvas 綁定捲軸
        canvas.pack(side='left')
    
    def cam_frame(self):
        cam_frome1 = tk.Frame(self.mygui, width=640, height=480, relief='raised', bg='gray', bd='5')
        #cam_frome1.pack()
        cam_frome1.place(relx=0.01, rely=0.05, relwidth=0.64, relheight=0.48)
        label1 = tk.Label(cam_frome1, text='camera NO.1', width=10, bg='blue')
        label1.pack()
        
        source = "rtsp://192.168.1.10/video0"
        cam_frome1 = cv2.VideoCapture(0)
        
        if not cam_frome1.isOpened():
            print('無法打開攝影機')
            exit()
        while(cam_frome1.isOpened()):
           # vid_cam.get = cv2.COLOR_BGR2GRAY
           # ret, image_frame = vid_cam.read()
            ret, self.cam_frame = cam_frome1.read() 
            #TODO : 在這裡進行畫圖,動態計算的參數值顯示
            self.draw_camOSD()  # 在畫面上劃中心線與場域框
            cv2.imshow('UVC CAM', self.cam_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cam_frome1.release()
        cv2.destroyAllWindows()
        
    def radiobutton(self):
        #增加測試選項
        val = tk.StringVar()
        video_btn_face = tk.Radiobutton(self.mygui, text='face detect', font=('宋体', 12, 'bold'), variable=val, value=1)
        video_btn_face.place(relx=0.02, rely=0.57, relwidth=0.15, relheight=0.05)
        #video_btn_FixAE.pack(fill='x', side='bottom')
        #video_btn_FixAE.select()  # 搭配 select() 方法選取 radio_btn_FixAE

        video_btn_article = tk.Radiobutton(self.mygui, text='article detect', font=('宋体', 12, 'bold'), variable=val, value=2)
        video_btn_article.place(relx=0.22, rely=0.57, relwidth=0.15, relheight=0.05)
        
        video_btn_number = tk.Radiobutton(self.mygui, text='number detect', font=('宋体', 12, 'bold'), variable=val, value=3)
        video_btn_number.place(relx=0.42, rely=0.57, relwidth=0.15, relheight=0.05)
        #video_btn_FixColor.pack(fill='y', side='bottom')
       # self.v2.set(1)
        print(f'val={val}')
    
    def entry(self):
        source = "rtsp://192.168.1.10/video0"
        #vid_cam = cv2.VideoCapture(0)
        #vid_cam.set(3,1280)
        #vid_cam.set(propId=4,value=720)
        #str=tk.StringVar()
        #x = 10
        #y = 20
        #width_data = format(vid_cam.get(2))
        #height_data = format(vid_cam.get(3))
        #FPS_data = str(vid_cam.get(4))
        #brightness_data = vid_cam.get(10)
        #contrast_data = vid_cam.get(11)
        #saturation_data = vid_cam.get(12)
        #hue_data = vid_cam.get(13)
        #gain_data = vid_cam.get(14)
        #exposure_data = vid_cam.get(15)
        #whitebalance_data = vid_cam.get(17)
        Entry_x = 0.73
        Enyry_width = 0.04
        contrast_entry = tk.Entry(self.mygui, font=(10), )
        contrast_entry.place(relx=Entry_x, rely=0.06, relwidth=Enyry_width, relheight=0.03)
        
        brightness_entry = tk.Entry(self.mygui, font=(10), )
        brightness_entry.place(relx=Entry_x, rely=0.12, relwidth=Enyry_width, relheight=0.03)
        
        sharpness_entry = tk.Entry(self.mygui, font=(10), text='No Data', )
        sharpness_entry.place(relx=Entry_x, rely=0.18, relwidth=Enyry_width, relheight=0.03)
        
        saturation_entry = tk.Entry(self.mygui, font=(10), )
        saturation_entry.place(relx=Entry_x, rely=0.24, relwidth=Enyry_width, relheight=0.03)
        
        hue_entry = tk.Entry(self.mygui, font=(10), )
        hue_entry.place(relx=Entry_x, rely=0.30, relwidth=Enyry_width, relheight=0.03)
        
        color_entry = tk.Entry(self.mygui, font=(10), )
        color_entry.place(relx=Entry_x, rely=0.36, relwidth=Enyry_width, relheight=0.03)
        
        BLC_entry = tk.Entry(self.mygui, font=(10), text='No Data', )
        BLC_entry.place(relx=Entry_x, rely=0.42, relwidth=Enyry_width, relheight=0.03)
        
        exposure_entry = tk.Entry(self.mygui, font=(10), )
        exposure_entry.place(relx=Entry_x, rely=0.48, relwidth=Enyry_width, relheight=0.03)
        
        gain_entry = tk.Entry(self.mygui, font=(10), )
        gain_entry.place(relx=Entry_x, rely=0.54, relwidth=Enyry_width, relheight=0.03)
        
        width_entry = tk.Entry(self.mygui, font=(10), )
        width_entry.place(relx=0.92, rely=0.50, relwidth=0.06, relheight=0.03)
        
        height_entry = tk.Entry(self.mygui, font=(10), )
        height_entry.place(relx=0.92, rely=0.55, relwidth=0.06, relheight=0.03)
        
        FPS_entry = tk.Entry(self.mygui, font=(10), )
        FPS_entry.place(relx=0.92, rely=0.60, relwidth=0.06, relheight=0.03)        
        
    def scale(self):
        contrast_scale = tk.Scale(self.mygui, from_= -50, to= 50, orient='horizontal')
        contrast_scale.place(relx=0.78, rely=0.03, )
        brightness_scale = tk.Scale(self.mygui, from_=0, to=100, orient='horizontal')
        brightness_scale.place(relx=0.78, rely=0.09, )
        sharpness_scale = tk.Scale(self.mygui, from_=0, to=100, orient='horizontal')
        sharpness_scale.place(relx=0.78, rely=0.15, )
        saturation_scale = tk.Scale(self.mygui, from_=0, to=100, orient='horizontal')
        saturation_scale.place(relx=0.78, rely=0.21, )    
        hue_scale = tk.Scale(self.mygui, from_=0, to=100, orient='horizontal')
        hue_scale.place(relx=0.78, rely=0.27, )
        color_scale = tk.Scale(self.mygui, from_=0, to=100, orient='horizontal')
        color_scale.place(relx=0.78, rely=0.33, )
        BLC_scale = tk.Scale(self.mygui, from_=0, to=100, orient='horizontal')
        BLC_scale.place(relx=0.78, rely=0.39, )
        exposure_scale = tk.Scale(self.mygui, from_=0, to=100, orient='horizontal')
        exposure_scale.place(relx=0.78, rely=0.45, )
        gain_scale = tk.Scale(self.mygui, from_=0, to=100, orient='horizontal')
        gain_scale.place(relx=0.78, rely=0.51, )
        
        def_But = tk.Button(self.mygui,padx=1,pady=1,text="預設值", font=('宋体', 10, 'bold'), bg='#F0F0F0')
        def_But.place(relx=0.75, rely=0.58, relwidth=0.07, relheight=0.05)
        
        #print(f'control = {control_iq}')

    def def_but(self):
        def_But = tk.Button(self.mygui,padx=1,pady=1,text="預設值", font=('宋体', 12, 'bold'), bg='#F0F0F0')
        def_But.place(relx=0.78, rely=0.57, relwidth=0.08, relheight=0.06)
        
    def createWiget(self):
        # ---------------菜單欄--------------------
        self.mymenu = Menu(self.mygui)

        # 建立下拉選單
        
        # 文件菜單
        filemenu = Menu(self.mymenu, tearoff=0)
        filemenu.add_command(label='打開圖片', command=self.command_open)
        filemenu.add_command(label='開啟UVC cam', command=self.show_cam)
        filemenu.add_separator()
        filemenu.add_command(label='關閉', command=self.command_exit)
        
        self.mymenu.add_cascade(label="文件", menu=filemenu)
        
        # 二值化菜單
        self.mymenu.add_command(label="二值化", command=self.command_threshold)
        self.mygui.config(menu=self.mymenu)
        # RGB 菜單
        self.mymenu.add_command(label="RGB", command=self.face_detect_cam)
        self.mygui.config(menu=self.mymenu)
        # 幫助菜單
        self.mymenu.add_command(label="幫助", command=self.command_help)
        self.mygui.config(menu=self.mymenu)

        # ---------------圖片控件------------------- 變量3->label
        self.label = Label(self.mygui, width=self.width, height=self.height)
        self.label.place(relx=0.01, rely=0.01)    

    def command_open(self):
        global img
        filename = askopenfilename(initialdir='Sample.bmp')
        self.image = Image.open(filename)
        image1 = self.image.resize((self.width, self.height), Image.LANCZOS)
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
        image1 = image1.resize((self.width, self.height), Image.LANCZOS)
        img1 = ImageTk.PhotoImage(image1)  # 轉格式
        self.label['image'] = img1

    def pic_cancel(self):
        self.top.destroy()

    def show_cam(self):  #基本UVC CAM 影像輸出
        cam_width = 1280
        cam_hieght = 720

        source = "rtsp://192.168.1.10/video0"
        vid_cam = cv2.VideoCapture(0)
        vid_cam.set(3,cam_width)
        vid_cam.set(4, cam_hieght)
        
        if not vid_cam.isOpened():
            print('無法打開攝影機')
            exit()
        while(vid_cam.isOpened()):
           # vid_cam.get = cv2.COLOR_BGR2GRAY
           # ret, image_frame = vid_cam.read()
            ret, self.cam_frame = vid_cam.read() 
            #TODO : 在這裡進行畫圖,動態計算的參數值顯示
            self.draw_camOSD()  # 在畫面上劃中心線與場域框
            #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # 彩色轉灰階
            cv2.imshow('UVC CAM', self.cam_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        vid_cam.release()
        cv2.destroyAllWindows()
    
    def detect_cam(self):  #影像移動偵測    
        # 開啟網路攝影機
        cap = cv2.VideoCapture(0)

        # 設定影像尺寸
        width = 1280
        height = 720

        # 設定擷取影像的尺寸大小
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # 計算畫面面積
        area = width * height

        # 初始化平均影像
        ret, frame = cap.read()
        avg = cv2.blur(frame, (4, 4))
        avg_float = np.float32(avg)

        while(cap.isOpened()):
            # 讀取一幅影格
            ret, frame = cap.read()

            # 若讀取至影片結尾，則跳出
            if ret == False:
                break

            # 模糊處理
            blur = cv2.blur(frame, (4, 4))

            # 計算目前影格與平均影像的差異值
            diff = cv2.absdiff(avg, blur)

            # 將圖片轉為灰階
            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

            # 篩選出變動程度大於門檻值的區域
            ret, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)

            # 使用型態轉換函數去除雜訊
            kernel = np.ones((5, 5), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

            # 產生等高線
            cntImg, cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for c in cnts:
            # 忽略太小的區域
                if cv2.contourArea(c) < 2500:
                    continue

            # 偵測到物體，可以自己加上處理的程式碼在這裡...

                # 計算等高線的外框範圍
                (x, y, w, h) = cv2.boundingRect(c)

                # 畫出外框
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # 畫出等高線（除錯用）
            cv2.drawContours(frame, cnts, -1, (0, 255, 255), 2)

            # 顯示偵測結果影像
            cv2.imshow('frame', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # 更新平均影像
            cv2.accumulateWeighted(blur, avg_float, 0.01)
            avg = cv2.convertScaleAbs(avg_float)

        cap.release()
        cv2.destroyAllWindows()
    def face_detect_cam(self):  #測試人臉跟眼睛的功能
        source = "rtsp://192.168.1.10/video0"
        face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
        eyes_cascade = cv2.CascadeClassifier("haarcascade_eye.xml")
        vid_cam = cv2.VideoCapture(index=1)

        #先设置参数，然后读取参数
        vid_cam.set(3,1280)
        vid_cam.set(propId=4,value=720)
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
        if not vid_cam.isOpened():
            print('無法打開攝影機')
            exit()

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
                #print('X='+str(x), 'Y='+str(y))
            eyes = eyes_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=3, minSize=(40, 40), )    #偵測眼睛
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(frame,(ex,ey),(ex+ew,ey+eh),(255,0,0),2)    #標記眼睛
            cv2.imshow('UVC Cam face detect', frame)
            if cv2.waitKey(1) == ord('q'):
                break
        vid_cam.release()
        cv2.destroyAllWindows()            
    def cam_data(self):
        pass
    
    def draw_camOSD(self):
        cam_width = 1280
        cam_hieght = 720
        crosshairline = 50  # 設定中心線的長度
        crosshairX = int(cam_width/2)
        crosshairY = int(cam_hieght/2)
        crosshairStarX = int(cam_width/2-crosshairline)
        crosshairEndX = int(cam_width/2+crosshairline)
        crosshairStarY = int(cam_hieght/2-crosshairline)
        crosshairEndY = int(cam_hieght/2+crosshairline)
        
        FOV = 0.8
        FOV_StartX = int((cam_width-(cam_width*cam_hieght*FOV/cam_hieght))/2)
        FOV_EndX = int(FOV_StartX+(cam_width*cam_hieght*FOV/cam_hieght))
        FOV_StartY = int((cam_hieght-(cam_width*cam_hieght*FOV/cam_width))/2)
        FOV_EndY = int(FOV_StartY+(cam_width*cam_hieght*FOV/cam_width))
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        cv2.line(self.cam_frame, (crosshairStarX, crosshairY), (crosshairEndX, crosshairY), (0, 0, 255), 2)
        cv2.line(self.cam_frame, (crosshairX, crosshairStarY), (crosshairX, crosshairEndY), (0, 0, 255), 2)
        cv2.rectangle(self.cam_frame, (FOV_StartX, FOV_StartY), (FOV_EndX, FOV_EndY), (0, 255, 0 ), 3)
        cv2.putText(self.cam_frame, 'FOV='+str(FOV), (10,50), font, 2, (255, 0, 0), 2, cv2.LINE_AA)
    
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
        pass
    
    def command_exit(self):
        exit()
    
    def command_help(self):
        user_name = input("關於學習過程需要不斷的練習,要有明確的目標,勇往向前.")

if __name__ == "__main__":
    root = Main_GUI()
    mainloop()