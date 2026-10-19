import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication

from lens_shading_correcte import LSCWindow


class LensShadingCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = LSCWindow()

    def tearDown(self):
        self.window.close()

    def test_gain_map_has_unity_center_and_requested_corner_gain(self):
        gain_map = self.window.generate_gain_map(5, 5, 2.0)

        self.assertAlmostEqual(float(gain_map[2, 2]), 1.0)
        self.assertAlmostEqual(float(gain_map[0, 0]), 2.0)
        self.assertTrue(np.all(gain_map >= 1.0))
        self.assertTrue(np.all(gain_map <= 2.0))

    def test_unity_gain_leaves_map_unchanged_and_single_pixel_is_valid(self):
        np.testing.assert_array_equal(
            self.window.generate_gain_map(3, 4, 1.0),
            np.ones((3, 4), dtype=np.float32),
        )
        np.testing.assert_array_equal(
            self.window.generate_gain_map(1, 1, 2.0),
            np.ones((1, 1), dtype=np.float32),
        )

    def test_invalid_dimensions_and_gain_are_rejected(self):
        with self.assertRaises(ValueError):
            self.window.generate_gain_map(0, 4, 1.5)
        with self.assertRaises(ValueError):
            self.window.generate_gain_map(4, 4, 0.5)

    def test_load_image_reads_selected_file_and_updates_preview(self):
        image = np.full((4, 6, 3), 80, dtype=np.uint8)
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = os.path.join(temp_dir, "input.png")
            self.assertTrue(cv2.imwrite(image_path, image))
            with patch(
                "lens_shading_correcte.QFileDialog.getOpenFileName",
                return_value=(image_path, ""),
            ):
                self.window.load_image()

        np.testing.assert_array_equal(self.window.image, image)
        np.testing.assert_array_equal(self.window.corrected_image, image)
        self.assertIsNotNone(self.window.img_display.pixmap())

    def test_slider_applies_gain_and_refreshes_preview(self):
        self.window.image = np.full((5, 5, 3), 100, dtype=np.uint8)

        self.window.slider_gain.setValue(200)

        self.assertTrue(np.all(self.window.corrected_image[0, 0] == 200))
        self.assertTrue(np.all(self.window.corrected_image[2, 2] == 100))
        self.assertIsNotNone(self.window.img_display.pixmap())


if __name__ == "__main__":
    unittest.main()
