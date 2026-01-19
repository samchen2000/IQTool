import serial
import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# ========= Serial =========
ser = serial.Serial('COM15', 115200, timeout=1)

# ========= Tkinter =========
root = tk.Tk()
root.title("MPU6050 3D 姿態 + 數值顯示")

left_frame = tk.Frame(root, padx=10)
left_frame.pack(side=tk.LEFT, fill=tk.Y)

right_frame = tk.Frame(root)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# ========= 數值顯示 =========
labels = {}
fields = ["AX", "AY", "AZ", "GX", "GY", "ROLL", "PITCH"]

for i, name in enumerate(fields):
    tk.Label(left_frame, text=name, font=("Arial", 12)).grid(row=i, column=0, sticky="w")
    lbl = tk.Label(left_frame, text="0.00", font=("Arial", 12), width=8)
    lbl.grid(row=i, column=1)
    labels[name] = lbl

# ========= Matplotlib 3D =========
fig = plt.figure(figsize=(5, 5))
ax = fig.add_subplot(111, projection='3d')

ax.set_xlim([-1, 1])
ax.set_ylim([-1, 1])
ax.set_zlim([-1, 1])
ax.set_box_aspect([1, 1, 1])
ax.set_title("3D Attitude")

canvas = FigureCanvasTkAgg(fig, master=right_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# ========= Cube =========
cube = np.array([
    [-0.5, -0.5, -0.5],
    [ 0.5, -0.5, -0.5],
    [ 0.5,  0.5, -0.5],
    [-0.5,  0.5, -0.5],
    [-0.5, -0.5,  0.5],
    [ 0.5, -0.5,  0.5],
    [ 0.5,  0.5,  0.5],
    [-0.5,  0.5,  0.5]
])

faces_idx = [
    [0,1,2,3],
    [4,5,6,7],
    [0,1,5,4],
    [2,3,7,6],
    [1,2,6,5],
    [0,3,7,4]
]

poly = Poly3DCollection([], alpha=0.6, facecolor="cyan", edgecolor="k")
ax.add_collection3d(poly)

# ========= Rotation =========
def rotation_matrix(roll, pitch):
    r = np.deg2rad(roll)
    p = np.deg2rad(pitch)

    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(r), -np.sin(r)],
        [0, np.sin(r),  np.cos(r)]
    ])

    Ry = np.array([
        [ np.cos(p), 0, np.sin(p)],
        [ 0,         1, 0        ],
        [-np.sin(p), 0, np.cos(p)]
    ])

    return Ry @ Rx

# ========= Update =========
def update():
    try:
        line = ser.readline().decode().strip()
        if line:
            data = line.split(",")
            if len(data) == 8:
                ax_v, ay_v, az_v, gx_v, gy_v, gz_v, roll, pitch = map(float, data)

                # 更新數值
                labels["AX"].config(text=f"{ax_v:.2f}")
                labels["AY"].config(text=f"{ay_v:.2f}")
                labels["AZ"].config(text=f"{az_v:.2f}")
                labels["GX"].config(text=f"{gx_v:.2f}")
                labels["GY"].config(text=f"{gy_v:.2f}")
                labels["GY"].config(text=f"{gz_v:.2f}")
                labels["ROLL"].config(text=f"{roll:.2f}°")
                labels["PITCH"].config(text=f"{pitch:.2f}°")

                # 更新 3D 姿態
                R = rotation_matrix(roll, pitch)
                rotated = cube @ R.T
                faces = [[rotated[i] for i in face] for face in faces_idx]
                poly.set_verts(faces)

                canvas.draw()
    except:
        pass

    root.after(50, update)

update()
root.mainloop()
