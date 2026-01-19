import serial
import tkinter as tk

# 修改成你的 COM Port
ser = serial.Serial('COM15', 115200, timeout=1)

root = tk.Tk()
root.title("MPU6050 即時數據")

labels = []

names = ["AX", "AY", "AZ", "GX", "GY", "GZ"]

for i, name in enumerate(names):
    tk.Label(root, text=name, font=("Arial", 12)).grid(row=i, column=0)
    lbl = tk.Label(root, text="0.00", font=("Arial", 12))
    lbl.grid(row=i, column=1)
    labels.append(lbl)

def update():
    try:
        line = ser.readline().decode().strip()
        if line:
            data = line.split(",")
            if len(data) >= 6:
                for i in range(6):
                    labels[i].config(text=data[i])
    except:
        pass
    root.after(50, update)

update()
root.mainloop()
