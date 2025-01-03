import math
import tkinter as tk
from tkinter import *
import cv2

angle = 90 #設定角度
angle_1 = 60
radians = math.radians(angle)   #將角度轉換為弧度  radians = angle * Pi / 180
sin_value = math.sin(radians)   #計算正弦值
angle_value = math.cos(angle_1)
print(f'radians={radians}')
print(f'sin value={sin_value}')
print(f'angle_value={angle_value}')

class MAIN_GUI():
    def __init__(mathgui, w=920, h=640):
        left = 30
        top = 30
        mathgui.width = w
        mathgui.height = h
        mathgui.mygui = Tk(className = "數學計算介面")
        mathgui.mygui.geometry(f'{mathgui.width}x{mathgui.height}+{left}+{top}')
        mathgui.mygui.resizable(False, False)
        mathgui.mygui.grid()
        mathgui.createWiget()
        
    def createWiget(mathGUI):
        # ---------------菜單欄--------------------
        mathGUI.mymenu = Menu(mathGUI.mygui)
        # 建立下拉選單

        mathGUI.mymenu.add_command(label="AAA", menu=A_filemenu)
        A_filemenu = Menu(mathGUI.mymenu, )
        A_filemenu.add_command(label='A____A')
        A_filemenu.add_command(label="A____B")
        A_filemenu.add_command(label="A____C")
        
        B_filemenu = Menu(mathGUI.mymenu, )
        mathGUI.mymenu.add_command(label="BBBB", menu=B_filemenu)
        B_filemenu.add_command(label="B______A")
        B_filemenu.add_command(label="B______B")
        B_filemenu.add_command(label="B______C")
        
        D_filemenu = Menu(mathGUI.mymenu, )
        mathGUI.mymenu.add_command(label="DDD", menu=D_filemenu)
        D_filemenu.add_command(label="D______A")
        D_filemenu.add_command(label="D______B")
        D_filemenu.add_command(label="D______C")
        
        mathGUI.mymenu.add_command(label="EEE", menu=E_filemenu)
        E_filemenu = Menu(mathGUI.mymenu, )
        E_filemenu.add_command(label="E______A")
        E_filemenu.add_command(label="E______B")
        E_filemenu.add_command(label="E______C")
        
        mathGUI.mymenu.add_command(label="FFF", menu=F_filemenu)
        F_filemenu = Menu(mathGUI.mymenu, )
        F_filemenu.add_command(label="F______A")
        F_filemenu.add_command(label="F______B")
        F_filemenu.add_command(label="F______C")
        
        mathGUI.mymenu.add_command(label="GGG")
        #顯示菜單對象
        mathGUI.mygui.config(menu=mathGUI.mymenu)
        mathGUI.lable = Label(mathGUI.mygui, width=mathGUI.width, height=mathGUI.height)
        mathGUI.lable.place(relx=0.01, rely=0.01)
        
    def FOV(mathGUI):
        pass
    def color(mathGUI):
        pass
    def exposure(mathGUI):
        pass
    def gamma(mathGUI):
        pass
class IQ_MATH():
    def math_fov(mathIQ):
        pass
    def math_color(mathIQ):
        pass
    def mathexposur(mathIQ):
        pass
    def gamme(mathGUI):
        pass    
if __name__ == "__main__":
    root = MAIN_GUI()
    mainloop()