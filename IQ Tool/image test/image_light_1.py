import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw

class ImageViewer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("brightness Checker")

        # Create a label to display the image
        self.image_label = tk.Label(self.root)
        self.image_label.pack()

        # Button to open an image file
        self.open_button = tk.Button(
            self.root, text="Open Image", command=self.load_image)
        self.open_button.pack(pady=10)

        # 範圍設定（寬高，預設為1x1即單點）
        range_frame = tk.Frame(self.root)
        tk.Label(range_frame, text="設定框選寬:").pack(side=tk.LEFT)
        self.range_w_entry = tk.Entry(range_frame, width=4)
        self.range_w_entry.insert(0, "100")
        self.range_w_entry.pack(side=tk.LEFT)
        tk.Label(range_frame, text="設定框選高:").pack(side=tk.LEFT)
        self.range_h_entry = tk.Entry(range_frame, width=4)
        self.range_h_entry.insert(0, "100")
        self.range_h_entry.pack(side=tk.LEFT)
        range_frame.pack(pady=5)

        # 亮度顯示區
        self.brightness_label = tk.Label(self.root, text="", font=("Arial", 12), justify=tk.LEFT)
        self.brightness_label.pack(pady=10)

        # 重新計算按鈕
        self.recalc_button = tk.Button(
            self.root, text="重新計算", command=self.recalculate_brightness)
        self.recalc_button.pack(pady=5)

        # 用於顯示有方框的圖片
        self.display_image = None

    def load_image(self):
        filepath = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not filepath:
            return

        # Load the selected image
        self.image = Image.open(filepath)
        
        # Resize the image to a fixed size (1280x720)
        self.image = self.image.resize((1280, 720))

        # Convert and display the image in Tkinter Label
        img_tk = ImageTk.PhotoImage(self.image)
        self.image_label.config(image=img_tk)
        self.image_label.image = img_tk  # Keep a reference to avoid garbage collection

        self.recalculate_brightness()

    def recalculate_brightness(self):
        if not hasattr(self, 'image') or self.image is None:
            return
        try:
            rw = max(1, int(self.range_w_entry.get()))
            rh = max(1, int(self.range_h_entry.get()))
        except ValueError:
            rw, rh = 1, 1

        width, height = self.image.size

        # 計算五個方框的位置
        positions = {
            "Center": (width // 2 - rw // 2, height // 2 - rh // 2),
            "Top Left": (0, 0),
            "Bottom Left": (0, height - rh),
            "Top Right": (width - rw, 0),
            "Bottom Right": (width - rw, height - rh),
            "top": (width // 2 - rw // 2, 0),
            "Bottom": (width // 2 - rw // 2, height - rh),
            "Left": (0, height // 2 - rh // 2),
            "Right": (width - rw, height // 2 - rh // 2)
        }

        # 複製原圖並繪製方框
        img_with_boxes = self.image.copy()
        draw = ImageDraw.Draw(img_with_boxes)
        for pos in positions.values():
            x, y = pos
            draw.rectangle([x, y, x + rw - 1, y + rh - 1], outline="red", width=2)
        img_tk = ImageTk.PhotoImage(img_with_boxes)
        self.image_label.config(image=img_tk)
        self.image_label.image = img_tk

        # 計算亮度
        brightness_values = {
            k: self.get_brightness(x, y, rw, rh)
            for k, (x, y) in positions.items()
        }
        text = "\n".join([f"{k}: {v}" for k, v in brightness_values.items()])
        self.brightness_label.config(text=text)

    def get_brightness(self, x, y, rw=1, rh=1):
        if not hasattr(self, 'image') or self.image is None:
            return None
        pixels = []
        for dx in range(rw):
            for dy in range(rh):
                px = min(max(x + dx, 0), self.image.size[0] - 1)
                py = min(max(y + dy, 0), self.image.size[1] - 1)
                pixel = self.image.getpixel((px, py))
                if isinstance(pixel, int) or len(pixel) == 1:
                    pixels.append(pixel if isinstance(pixel, int) else pixel[0])
                else:
                    r, g, b = pixel[:3]
                    brightness = 0.299 * r + 0.587 * g + 0.114 * b
                    pixels.append(brightness)
        if pixels:
            return round(sum(pixels) / len(pixels))
        return None

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    viewer = ImageViewer()
    viewer.run()