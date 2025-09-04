import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageEnhance
from tkinter import messagebox

root = tk.Tk()
root.title('Camera Image Tuning')
root.geometry('640x480')

# 開啟圖片並在 Canvas 中顯示圖片
def show(path):
    global img                              # 定義全域變數 img
    img = Image.open(path)                  # 取得圖片路徑
    w, h = img.size                         # 取得圖片長寬
    tk_img = ImageTk.PhotoImage(img)        # 轉換成 tk 圖片物件
    canvas.delete('all')                    # 清空 Canvas 原本內容
    canvas.config(scrollregion=(0,0,w,h))   # 改變捲動區域
    canvas.create_image(0, 0, anchor='nw', image=tk_img)   # 建立圖片
    canvas.tk_img = tk_img                  # 修改屬性更新畫面
    scale_1.set(0)                          # 開啟圖片時，捲軸數值歸零
    scale_2.set(0)                          # 開啟圖片時，捲軸數值歸零
    scale_3.set(0)                          # 開啟圖片時，捲軸數值歸零
    scale_4.set(0)                          # 開啟圖片時，捲軸數值歸零

# 使用 Scale 調整圖片
def enhance(e):
    global output                                          # 定義全域變數 output
    output = img.copy()                                    # 複製 img 圖片
    brightness = ImageEnhance.Brightness(output)           # 調整亮度
    output = brightness.enhance(1+int(scale_1.get())/100)  # 讀取 Scale 數值並轉換成調整的數值
    contrast = ImageEnhance.Contrast(output)               # 調整對比
    output = contrast.enhance(1+int(scale_2.get())/100)    # 讀取 Scale 數值並轉換成調整的數值
    color = ImageEnhance.Color(output)                     # 調整飽和度
    output = color.enhance(1+int(scale_3.get())/100)       # 讀取 Scale 數值並轉換成調整的數值
    sharpness = ImageEnhance.Sharpness(output)             # 調整銳利度
    output = sharpness.enhance(1+int(scale_4.get())/10)    # 讀取 Scale 數值並轉換成調整的數值

    tk_img = ImageTk.PhotoImage(output)                    # 轉換成 tk 圖片物件
    canvas.delete('all')                                   # 清空 Canvas 原本內容
    canvas.create_image(0, 0, anchor='nw', image=tk_img)   # 建立圖片
    canvas.tk_img = tk_img                                 # 修改屬性更新畫面

# 開啟檔案
def open():
    try:
        img_path = filedialog.askopenfilename(filetypes=[('png', '*.png'),('jpg', '*.jpg'),('gif', '*.gif')])  # 指定開啟檔案格式
        show(img_path)
    except:
        pass

# 儲存檔案
def save():
    global output
    try:
        img_path = filedialog.asksaveasfile(filetypes = [('png', '*.png'),('jpg', '*.jpg'),('gif', '*.gif')]).name   # 指定儲存檔案格式
        img_type = img_path.split('.')[1]    # 取得檔案類型
        output.save(img_path, img_type)
        messagebox.showinfo('showinfo', '儲存完成')
    except:
        pass

# 關閉程式
def exit():
    print('exit')
    root.destroy()

menu = tk.Menu(root)                            # 加入選單
menubar = tk.Menu(menu)
menubar.add_command(label="開啟", command=open)  # 開啟檔案按鈕
menubar.add_command(label="儲存", command=save)  # 儲存檔案按鈕
menubar.add_command(label="結束", command=exit)  # 關閉程式按鈕
menu.add_cascade(label='檔案', menu=menubar)     # 選單分類
root.config(menu=menu)

frame = tk.Frame(root, width=300, height=300)   # 加入 Frame，放置 Canvas
frame.place(x=10,y=10)

canvas = tk.Canvas(frame, width=300, height=300, bg='#fff')  # 加入 Canvas

scrollX = tk.Scrollbar(frame, orient='horizontal')    # 水平捲軸
scrollX.pack(side='bottom', fill='x')
scrollX.config(command=canvas.xview)

scrollY = tk.Scrollbar(frame, orient='vertical')      # 垂直捲軸
scrollY.pack(side='right', fill='y')
scrollY.config(command=canvas.yview)

canvas.config(xscrollcommand=scrollX.set, yscrollcommand=scrollY.set)   # Canvas 綁定捲軸
canvas.pack(side='left')

# 亮度調整 Scale
scale_1 = tk.Scale(root, from_=-100, to=100, orient='horizontal', length=150, label='亮度', command=enhance)
scale_1.place(x=10,y=335)
scale_1.set(0)

# 對比調整 Scale
scale_2 = tk.Scale(root, from_=-100, to=100, orient='horizontal', length=150, label='對比', command=enhance)
scale_2.place(x=180,y=335)
scale_2.set(0)

# 飽和度調整 Scale
scale_3 = tk.Scale(root, from_=-100, to=100, orient='horizontal', length=150, label='飽和度', command=enhance)
scale_3.place(x=10,y=410)
scale_3.set(0)

# 銳利度調整 Scale
scale_4 = tk.Scale(root, from_=0, to=100, orient='horizontal', length=150, label='銳利度', command=enhance)
scale_4.place(x=180,y=410)
scale_4.set(0)

root.mainloop()