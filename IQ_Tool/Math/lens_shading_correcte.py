import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QSlider, QLabel, QFileDialog,
                             QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap


class LSCWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lens Shading Correction Tool")
        self.resize(1000, 700)
        self.image = None
        self.corrected_image = None
        self.initUI()

    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        control_panel = QVBoxLayout()
        self.btn_open = QPushButton("開啟影像")
        self.btn_open.clicked.connect(self.load_image)
        
        self.slider_gain = QSlider(Qt.Orientation.Horizontal)
        self.slider_gain.setRange(100, 200)
        self.slider_gain.setValue(100)
        self.slider_gain.valueChanged.connect(self.apply_lsc)

        control_panel.addWidget(self.btn_open)
        control_panel.addWidget(QLabel("邊緣增益 (Edge Gain):"))
        control_panel.addWidget(self.slider_gain)
        
        self.img_display = QLabel("請載入影像")
        self.img_display.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(control_panel, 1)
        layout.addWidget(self.img_display, 4)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "開啟影像",
            "",
            "影像檔案 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        )
        if not file_path:
            return

        image = cv2.imread(file_path, cv2.IMREAD_COLOR)
        if image is None:
            QMessageBox.warning(self, "載入失敗", "無法讀取所選影像。")
            return

        self.image = image
        self.apply_lsc()

    def generate_gain_map(self, h, w, gain_factor):
        if h <= 0 or w <= 0:
            raise ValueError("影像高度與寬度必須大於 0")
        if not np.isfinite(gain_factor) or gain_factor < 1.0:
            raise ValueError("邊緣增益必須是大於或等於 1.0 的有限數值")

        center_x = (w - 1) / 2.0
        center_y = (h - 1) / 2.0
        yy, xx = np.ogrid[:h, :w]
        distance_squared = (xx - center_x) ** 2 + (yy - center_y) ** 2
        max_distance = np.hypot(
            max(center_x, w - 1 - center_x),
            max(center_y, h - 1 - center_y),
        )
        if max_distance == 0:
            return np.ones((h, w), dtype=np.float32)

        normalized_radius_squared = distance_squared / (max_distance ** 2)
        return (1.0 + (gain_factor - 1.0) * normalized_radius_squared).astype(
            np.float32
        )

    def apply_lsc(self):
        if self.image is None:
            return

        gain_factor = self.slider_gain.value() / 100.0
        height, width = self.image.shape[:2]
        gain_map = self.generate_gain_map(height, width, gain_factor)
        corrected = np.multiply(
            self.image.astype(np.float32),
            gain_map[:, :, np.newaxis],
        )
        self.corrected_image = np.clip(corrected, 0, 255).astype(np.uint8)
        self._update_preview()

    def _update_preview(self):
        if self.corrected_image is None:
            return

        rgb_image = cv2.cvtColor(self.corrected_image, cv2.COLOR_BGR2RGB)
        height, width = rgb_image.shape[:2]
        qimage = QImage(
            rgb_image.data,
            width,
            height,
            rgb_image.strides[0],
            QImage.Format.Format_RGB888,
        ).copy()
        pixmap = QPixmap.fromImage(qimage)
        self.img_display.setPixmap(
            pixmap.scaled(
                self.img_display.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_preview()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LSCWindow()
    win.show()
    sys.exit(app.exec())
