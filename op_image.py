from email.policy import default
import tkinter as tk

root = tk.Tk()
root.title('oxxo.studio')
root.geometry('300x300')

a = tk.StringVar()   # 定義文字變數
a.set('0,0')

# 定義顯示函式，注意一定要有一個參數
def show(e):
    a.set(f'{scale_h.get()},{scale_v.get()}')

label = tk.Label(root, textvariable=a)
label.pack()

scale_h = tk.Scale(root, from_=0, to=100, orient='horizontal', command=show)  # 改變時執行 show
scale_h.pack()

scale_v = tk.Scale(root, from_=0, to=100, orient='vertical', command=show)  # 改變時執行 show
scale_v.pack()

root.mainloop()