import serial
import numpy as np
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ser = serial.Serial('COM15', 115200, timeout=1)

root = tk.Tk()
root.title("MPU6050 3D 姿態（Roll / Pitch / Yaw）")

left = tk.Frame(root, padx=10)
left.pack(side=tk.LEFT, fill=tk.Y)

right = tk.Frame(root)
right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

labels = {}
fields = ["AX","AY","AZ","GX","GY","GZ","ROLL","PITCH","YAW"]

for i, f in enumerate(fields):
    tk.Label(left, text=f, font=("Arial",11)).grid(row=i, column=0, sticky="w")
    l = tk.Label(left, text="0.00", font=("Arial",11), width=8)
    l.grid(row=i, column=1)
    labels[f] = l

fig = plt.figure(figsize=(5,5))
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim([-1,1])
ax.set_ylim([-1,1])
ax.set_zlim([-1,1])
ax.set_box_aspect([1,1,1])

canvas = FigureCanvasTkAgg(fig, master=right)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

cube = np.array([
    [-0.5,-0.5,-0.5],[0.5,-0.5,-0.5],[0.5,0.5,-0.5],[-0.5,0.5,-0.5],
    [-0.5,-0.5,0.5],[0.5,-0.5,0.5],[0.5,0.5,0.5],[-0.5,0.5,0.5]
])

faces_idx = [
    [0,1,2,3],[4,5,6,7],[0,1,5,4],
    [2,3,7,6],[1,2,6,5],[0,3,7,4]
]

poly = Poly3DCollection([], alpha=0.6, facecolor="cyan")
ax.add_collection3d(poly)

# 座標軸（紅 X、綠 Y、藍 Z）
axes_lines = [
    ax.plot([0,1],[0,0],[0,0],'r')[0],
    ax.plot([0,0],[0,1],[0,0],'g')[0],
    ax.plot([0,0],[0,0],[0,1],'b')[0]
]

def rotation_matrix(roll, pitch, yaw):
    r,p,y = np.deg2rad([roll,pitch,yaw])

    Rx = np.array([[1,0,0],[0,np.cos(r),-np.sin(r)],[0,np.sin(r),np.cos(r)]])
    Ry = np.array([[np.cos(p),0,np.sin(p)],[0,1,0],[-np.sin(p),0,np.cos(p)]])
    Rz = np.array([[np.cos(y),-np.sin(y),0],[np.sin(y),np.cos(y),0],[0,0,1]])

    return Rz @ Ry @ Rx

def update():
    try:
        line = ser.readline().decode().strip()
        if line:
            d = list(map(float, line.split(",")))
            if len(d) == 9:
                axv,ayv,azv,gx,gy,gz,roll,pitch,yaw = d

                for k,v in zip(fields,d):
                    labels[k].config(text=f"{v:.2f}")

                R = rotation_matrix(roll,pitch,yaw)
                rot = cube @ R.T
                faces = [[rot[i] for i in f] for f in faces_idx]
                poly.set_verts(faces)

                # 更新座標軸
                origin = np.zeros((3,))
                axes = np.eye(3) @ R.T
                for i,l in enumerate(axes_lines):
                    l.set_data([0,axes[i][0]],[0,axes[i][1]])
                    l.set_3d_properties([0,axes[i][2]])

                canvas.draw()
    except:
        pass

    root.after(50, update)

update()
root.mainloop()
