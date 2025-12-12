import tkinter as tk
from tkinter import filedialog, messagebox
from skimage.metrics import structural_similarity as ssim
import cv2
import numpy as np
from PIL import Image, ImageTk


def load_image(path):
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"無法讀取影像: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def compute_ssim():
    global img1_path, img2_path

    if not img1_path or not img2_path:
        messagebox.showerror("錯誤", "請先選擇兩張影像")
        return

    try:
        img1 = load_image(img1_path)
        img2 = load_image(img2_path)

        # 若影像大小不同 → 自動 resize
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        score, diff = ssim(img1, img2, full=True)
        diff = (diff * 255).astype("uint8")

        result_label.config(text=f"SSIM：{score:.4f}")

        # 顯示差異圖
        diff_img = Image.fromarray(diff)
        diff_img = diff_img.resize((300, 300))
        diff_tk = ImageTk.PhotoImage(diff_img)
        diff_label.config(image=diff_tk)
        diff_label.image = diff_tk

    except Exception as e:
        messagebox.showerror("錯誤", str(e))


def choose_img1():
    global img1_path
    img1_path = filedialog.askopenfilename(
        title="選擇參考影像 (Reference)",
        filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")]
    )
    img1_label.config(text=f"參考影像：{img1_path}")


def choose_img2():
    global img2_path
    img2_path = filedialog.askopenfilename(
        title="選擇比較影像 (Test)",
        filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")]
    )
    img2_label.config(text=f"比較影像：{img2_path}")


# ---------------------- GUI 設計 ----------------------
root = tk.Tk()
root.title("SSIM 計算工具")
root.geometry("600x500")

img1_path = None
img2_path = None

tk.Button(root, text="選擇參考影像 (Reference)", command=choose_img1).pack(pady=5)
img1_label = tk.Label(root, text="參考影像：未選擇")
img1_label.pack()

tk.Button(root, text="選擇比較影像 (Test)", command=choose_img2).pack(pady=5)
img2_label = tk.Label(root, text="比較影像：未選擇")
img2_label.pack()

tk.Button(root, text="計算 SSIM", command=compute_ssim, height=2, width=20).pack(pady=20)

result_label = tk.Label(root, text="SSIM：")
result_label.pack()

tk.Label(root, text="差異圖 (Diff Map)：").pack()
diff_label = tk.Label(root)
diff_label.pack()

root.mainloop()
