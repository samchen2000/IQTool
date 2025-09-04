import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

class ImageViewer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Image Viewer")

        # Create a label to display the image
        self.image_label = tk.Label(self.root)
        self.image_label.pack()

        # Button to open an image file
        self.open_button = tk.Button(
            self.root, text="Open Image", command=self.load_image)
        self.open_button.pack(pady=10)

    def load_image(self):
        filepath = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not filepath:
            return

        # Load the selected image
        self.image = Image.open(filepath)
        width, height = self.image.size

        # Convert and display the image in Tkinter Label
        img_tk = ImageTk.PhotoImage(self.image)
        self.image_label.config(image=img_tk)
        self.image_label.image = img_tk  # Keep a reference to avoid garbage collection

        # Calculate brightness at specific points
        brightness_values = {
            "Center": self.get_brightness(width / 2, height / 2),
            "Top Left": self.get_brightness(0, 0),
            "Bottom Left": self.get_brightness(0, height - 1),
            "Top Right": self.get_brightness(width - 1, 0),
            "Bottom Right": self.get_brightness(width - 1, height - 1)
        }

        # Display brightness values in a message box
        messagebox.showinfo(
            title="Brightness Values",
            message="\n".join([f"{k}: {v}" for k, v in brightness_values.items()])
        )

    def get_brightness(self, x, y):
        if self.image:
            pixel = self.image.getpixel((x, y))
            # For grayscale images, the brightness value is simply the intensity
            if len(pixel) == 1: 
                return int(pixel[0])
            # If it's an RGB image, we can use a formula to compute brightness
            r, g, b = pixel
            return round(0.299 * r + 0.587 * g + 0.114 * b)
        else:
            return None

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    viewer = ImageViewer()
    viewer.run()