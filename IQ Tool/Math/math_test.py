import math
import tkinter as tk
from tkinter import *
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk
import cv2


angle = 90 #設定角度
angle_1 = 60
radians = math.radians(angle)   #將角度轉換為弧度  radians = angle * Pi / 180
sin_value = math.sin(radians)   #計算正弦值
angle_value = math.cos(angle_1)
param_13 = 1.0/3.0
param_16116 = 16.0/116.0
Xn = 0.950456
Yn = 1.0
Zn = 1.088754

print(f'radians={radians}')
print(f'sin value={sin_value}')
print(f'angle_value={angle_value}')

class MAIN_GUI():
    def __init__(mathgui, w=920, h=640):
        left = 10
        top = 10
        mathgui.width = w
        mathgui.height = h
        mathgui.mygui = Tk(className = "數學計算介面")
        mathgui.mygui.geometry(f'{mathgui.width}x{mathgui.height}+{left}+{top}')
        mathgui.mygui.resizable(False, False)
        
        mathgui.mygui.grid()
        mathgui.createWiget()
       # mathgui.showbmp()
        #mathgui.image_frame()
    def image_frame(imageframe, imgw=920, imgh=640):
        left = 10
        top = 10
        imageframe.width = imgw
        imageframe.height = imgh
        imageframe.mygui = Tk(className = "參數介面")
        imageframe.mygui.geometry(f'{imageframe.width}x{imageframe.height}+{left}+{top}')
        imageframe.mygui.resizable(False, False)
        imageframe.mygui.grid()    
    def createWiget(mathgui):
        # --------------參數說明-------------------
        #|-----方法-------|-----------------參數----------------|------------------------------------說明-------------------------|
        #|  add_command() |	label, command, image, compound	   |  選單項目，label 顯示文字，command 執行函式，image 圖示，compound 圖示與文字排列。
        #|  add_cascade() |	label, menu	                       |  父選單，label 顯示文字，menu 內容子選單。
        #| add_separator()|	                                   |  分隔線。
        #|-----------------------------------------------------------------------------------------------------------------------|
        
        # ---------------菜單欄--------------------
        mathgui.mymenu = Menu(mathgui.mygui)  #建立主菜單
        # 建立下拉選單

        filemenu = Menu(mathgui.mymenu, )
        filemenu.add_command(label='開啟檔案', command=mathgui.image_open)
        filemenu.add_command(label="開啟USB Cam", command=mathgui.image_frame)
        filemenu.add_command(label="開啟 IP Cam")
        mathgui.mymenu.add_cascade(label="檔案", menu=filemenu)
        
        IQ_filemenu = Menu(mathgui.mymenu, )
        IQ_filemenu.add_command(label="SFR 計算", command=IQ_MATH.Lab(10,20,30))
        IQ_filemenu.add_command(label="RGB 計算", command=IQ_MATH.RGB2YUV(1, 10, 20, 30))
        Exp_A_filemenu = Menu(mathgui.mymenu, )
        IQ_filemenu.add_cascade(label="Exposure 計算", menu=Exp_A_filemenu)
        Exp_A_filemenu.add_command(label="全域計算")
        Exp_A_filemenu.add_command(label="區域計算")
        mathgui.mymenu.add_cascade(label="影像計算", menu=IQ_filemenu)
        
        Data_filemenu = Menu(mathgui.mymenu, )
        Data_filemenu.add_command(label="Gamma 數值")
        Data_filemenu.add_command(label="SNR 計算", command=IQ_MATH.math_snr)
        Data_filemenu.add_command(label="Noise 計算")
        Data_filemenu.add_command(label="FOV 計算", command=IQ_MATH.math_fov)
        Data_filemenu.add_command(label="Sharpening 計算", command=mathgui.test)
        Data_filemenu.add_command(label="Edge 計算")
        Data_filemenu.add_command(label="Texture 計算")
        Data_filemenu.add_command(label="Lab 計算", command=IQ_MATH.RGB2Lab(255, 0, 0))
        mathgui.mymenu.add_cascade(label="參數計算", menu=Data_filemenu)
        
        Lsc_filemenu = Menu(mathgui.mymenu, )
        Lsc_filemenu.add_command(label="lllumination")
        Lsc_filemenu.add_command(label="color uniformity")
        Lsc_filemenu.add_command(label="Veiling Glare")
        mathgui.mymenu.add_cascade(label="全畫面", menu=Lsc_filemenu)
        
        Focus_filemenu = Menu(mathgui.mymenu, )
        Focus_filemenu.add_command(label="Distance")
        Focus_filemenu.add_command(label="Closest")
        mathgui.mymenu.add_cascade(label="焦距", menu=Focus_filemenu)
        
        mathgui.mymenu.add_command(label="離開", command=exit)        
        
        #顯示菜單對象
        mathgui.mygui.config(menu=mathgui.mymenu)
        mathgui.lable = Label(mathgui.mygui, text='image1', width=mathgui.width, height=mathgui.height)
        mathgui.lable.place(relx=0.01, rely=0.01)
        
    def FOV(mathgui):
        pass
    def color(mathgui):
        pass
    def exposure(mathgui):
        pass
    def gamma(mathgui):
        pass
    def image_open(mathgui):
        global img
        image_width = mathgui.width/2
        image_height = mathgui.height/2
        filename = askopenfilename(initialdir='Sample.bmp')
        mathgui.image = Image.open(filename)
        image1 = mathgui.image.resize((int(image_width), int(image_height)), Image.LANCZOS)
        img = ImageTk.PhotoImage(image1)  #轉換格式
        mathgui.lable['image'] = img 
        mathgui.lable.place(x=200, y=140)
    def image_frame_open(imageframe):
        global img
        image_width = imageframe.width/2
        image_height = imageframe.height/2
        filename = askopenfilename(initialdir='Sample.bmp')
        imageframe.image = Image.open(filename)
        image1 = imageframe.image.resize((int(image_width), int(image_height)), Image.LANCZOS)
        img = ImageTk.PhotoImage(image1)  #轉換格式
        imageframe.lable['image'] = img     
    def test(mategui):
            num = float(input('請輸入用電度數 : '))
            output = 200
            if num<=200:
                output = num*3.2
            elif num>200 and num<=300:
                output = 200*3.2 + (num - 200)*3.4
            else:
                output = 200*3.2 + 100*3.4 + (num - 300)*3.6
            print(f'用電 {num} 度共 {output} 元')
    def showbmp(mathgui):
        yuvimage = Image.open('YUV_UV_plane.jpg')
        yuvbmp = ImageTk.PhotoImage(yuvimage)
        Canvas = tk.Canvas(mathgui.mygui, width=100, height=100)
        Canvas.create_image(20, 20, image=yuvbmp)
        Canvas.pack()    
        
class IQ_MATH():
    def math_sfr(mathIQ):
        pass
    def math_mtf(mathIQ):
        pass
    def math_fov(mathIQ):
        print('FOV 測試開始')
    def math_snr(mathIQ):
        try:
            num = float(input('請輸入用電度數 : '))
            output = 200
            if num<=200:
                output = num*3.2
            elif num>200 and num<=300:
                output = 200*3.2 + (num - 200)*3.4
            else:
                output = 200*3.2 + 100*3.4 + (num - 300)*3.6
            print(f'用電 {num} 度共 {output} 元')
        except:
            print('發生錯誤')
    def math_color(mathIQ):
        pass
    def mathexposur(mathIQ):
        pass
    def gamme(mathIQ):
        pass
    def RGB2Lab(color_R, color_G, color_B):
        # 因為 RGB 無法直接轉換為 YUV,需要先將 GRB 轉換為XYZ
        X = 0.412453*color_R + 0.357580*color_G + 0.180423*color_B
        Y = 0.212671*color_R + 0.715160*color_G + 0.072169*color_B
        Z = 0.019334*color_R + 0.119193*color_G + 0.950227*color_B
        
        #再將XYZ 轉換為 Lab
        X /= 255*Xn
        Y /= 255*Yn
        Z /= 255*Zn
        
        if Y > 0.008856:
            fy = pow(Y, param_13) #傳回 Y 的 'param_13' 次方
            L = 116.0 * fy - 16.0
        else:
            fy = 7.787 * Y + param_16116
            L = 903.3 * fy
        
        if L < 0:
            L = 0.0
            
        if X > 0.008856:
            fx = pow(X, param_13)
        else:
            fx = 7.787 * X + param_16116
            
        if Z > 0.008856:
            fz = pow(Z, param_13)
        else:
            fz = 7.787037 * Z + param_16116
            
        a = 500.0 * (fx-fy)
        b = 200.0 * (fy-fz)
        
        print(f'L= {round(L,2)} + {X}')
        print(f'a= {round(a,2)} + {Y}')
        print(f'b= {round(b,2)} + {Z}')

    def RGB2Lab_new(color_R, color_G, color_B):
        # 因為 RGB 無法直接轉換為 YUV,需要先將 GRB 轉換為XYZ
        X = 0.412453*color_R + 0.357580*color_G + 0.180423*color_B
        Y = 0.212671*color_R + 0.715160*color_G + 0.072169*color_B
        Z = 0.019334*color_R + 0.119193*color_G + 0.950227*color_B
        
        #再將XYZ 轉換為 Lab
        X /= 255*Xn
        Y /= 255*Yn
        Z /= 255*Zn
        
        if Y > 0.008856:
            fy = pow(Y, param_13) #傳回 Y 的 'param_13' 次方
            l = 116.0 * fy - 16.0
        else:
            fy = 7.787 * Y + param_16116
            l = 903.3 * fy
        
        if l < 0:
            l = 0.0
            
        if X > 0.008856:
            fx = pow(X, param_13)
        else:
            fx = 7.787 * X + param_16116
            
        if Z > 0.008856:
            fz = pow(Z, param_13)
        else:
            fz = 7.787 * Z + param_16116
            
        a = 500.0 * (fx-fy)
        b = 200.0 * (fy-fz)
        
        print(f'L= {round(l,2)} + {X}')
        print(f'a= {round(a,2)} + {Y}')
        print(f'b= {round(b,2)} + {Z}')
        
    def Lab(L_1, a_1, b_1):
        L = 100
        a = 30
        b = 20
        DeltaE = math.sqrt((L_1-L)**2+(a_1-a)**2+(b_1-b)**2)
        print(f"DeltaE= {DeltaE}")
        
    def RGB2YUV(YUVmode, color_R, color_G, color_B):
        #color_R = 100
        #color_G = 110
        #color_B = 120
        if YUVmode == 1:  # 標準 YUV 轉換
            Y= 0.299*color_R + 0.587*color_G + 0.114*color_B
            U= -0.169*color_R - 0.331*color_G + 0.5*color_B + 128
            V= 0.5*color_R - 0.419*color_G - 0.081*color_B + 128
        elif YUVmode == 2:  # 4:4:4 完全取樣轉換
            Y= 0.299*color_R + 0.587*color_G + 0.114*color_B
            U= -0.147*color_R - 0.289*color_G + 0.436*color_B
            V= 0.5*color_R - 0.419*color_G - 0.081*color_B + 128
        elif YUVmode == 3:  # ITU-R版本的公式差異
            Y= 0.299*color_R + 0.587*color_G + 0.114*color_B
            U= -0.169*color_R - 0.331*color_G + 0.499*color_B + 128
            V= 0.499*color_R - 0.418*color_G - 0.0813*color_B + 128
        elif YUVmode == 4:
            Y= 0.299*color_R + 0.587*color_G + 0.114*color_B
            U= -0.169*color_R - 0.331*color_G + 0.5*color_B + 128
            V= 0.5*color_R - 0.419*color_G - 0.081*color_B + 128
        else:
             print('請重新選擇')     
             
        print(f'YUV = {YUVmode} {Y} {U} {V}')                

class IMAGE_TOOL():
    def command_open(mathimage):
        pass
       
if __name__ == "__main__":
    root = MAIN_GUI()
    mainloop()