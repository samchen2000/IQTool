import cv2
import numpy as np
import time

class AutoFocusSimulator:
    def __init__(self, steps=50):
        self.steps = steps  # 模擬 Actuator 步數
        self.best_focus = None
        self.best_score = -1

    def sharpness_metric(self, image):
        """
        使用 Laplacian Variance 作為清晰度評估指標
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def simulate_actuator_movement(self, image):
        """
        模擬致動器掃描流程
        """
        print("開始 AF 掃描...")
        for step in range(self.steps):
            # 模擬不同對焦程度：增加模糊
            blur_level = abs(step - self.steps // 2) / (self.steps // 2) * 5
            blurred = cv2.GaussianBlur(image, (5, 5), blur_level)

            score = self.sharpness_metric(blurred)

            print(f"Step {step}, Sharpness Score: {score:.2f}")

            if score > self.best_score:
                self.best_score = score
                self.best_focus = step

            time.sleep(0.05)  # 模擬驅動延遲

        print(f"最佳對焦位置: Step {self.best_focus}, Score: {self.best_score:.2f}")
        return self.best_focus

# 測試程式
if __name__ == "__main__":
    # 使用測試圖像 (可以換成實際相機抓取的圖片)
    image = np.full((480, 640, 3), 255, dtype=np.uint8)  # 白底影像
    cv2.putText(image, "AF Test Pattern", (50, 240), cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 0, 0), 2, cv2.LINE_AA)

    af = AutoFocusSimulator(steps=30)
    af.simulate_actuator_movement(image)
