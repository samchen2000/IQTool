import serial
import tkinter as tk
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 修改成你的 COM Port
ser = serial.Serial('COM15', 115200, timeout=1)

root = tk.Tk()
root.title("MPU6050 即時姿態顯示")

labels = {}
names = ["AX", "AY", "AZ", "GX", "GY", "ROLL", "PITCH"]

for i, name in enumerate(names):
    tk.Label(root, text=name, font=("Arial", 11)).grid(row=i, column=0)
    lbl = tk.Label(root, text="0.00", font=("Arial", 11))
    lbl.grid(row=i, column=1)
    labels[name] = lbl

# ===== Matplotlib =====
fig, ax = plt.subplots(figsize=(6, 3))
ax.set_title("Roll / Pitch")
ax.set_ylim(-90, 90)
ax.set_xlabel("Samples")
ax.set_ylabel("Degrees")

roll_data = deque(maxlen=100)
pitch_data = deque(maxlen=100)

line_roll, = ax.plot([], [], label="Roll")
line_pitch, = ax.plot([], [], label="Pitch")
ax.legend()

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=0, column=2, rowspan=8)

def update():
    try:
        line = ser.readline().decode().strip()
        if line:
            data = line.split(",")
            if len(data) == 7:
                for i, name in enumerate(names):
                    labels[name].config(text=data[i])

                roll = float(data[5])
                pitch = float(data[6])

                roll_data.append(roll)
                pitch_data.append(pitch)

                line_roll.set_data(range(len(roll_data)), roll_data)
                line_pitch.set_data(range(len(pitch_data)), pitch_data)
                ax.set_xlim(0, len(roll_data))
                canvas.draw()
    except:
        pass

    root.after(50, update)

update()
root.mainloop()
