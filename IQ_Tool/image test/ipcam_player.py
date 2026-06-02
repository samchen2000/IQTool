# -*- coding: utf-8 -*-
"""
IP CAM 串流播放器
- 左側: 即時影像視窗，顯示解析度與 FPS
- 右側: URL 輸入框與控制按鈕 (開啟/關閉)
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import threading
import time
from PIL import Image, ImageTk
import queue
import configparser
from pathlib import Path

# ===== 抑制 OpenCV RTSP 警告訊息 =====
# 設定環境變數來降低 OpenCV 日誌級別
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'
os.environ['OPENCV_LOG_LEVEL_VIDEOIO'] = 'OFF'

# 禁用 OpenCV 的詳細輸出 (適配不同版本)
try:
    if hasattr(cv2, 'setLogLevel'):
        # OpenCV 4.4.0+
        cv2.setLogLevel(0)  # 0 = SILENT
    elif hasattr(cv2, 'utils') and hasattr(cv2.utils, 'logging'):
        # 另一種方式
        cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)
except Exception:
    # 若都不支援，忽略此步驟
    pass


class IPCAMPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("IP CAM 串流播放器")
        self.root.geometry("1000x600")
        
        # 載入配置檔案
        self.config = self._load_config()
        
        # 串流控制變數
        self.stream_running = False
        self.cap = None
        self.frame_queue = queue.Queue(maxsize=2)
        self.stream_thread = None
        
        # FPS 計算變數
        self.fps = 0.0
        self.frame_count = 0
        self.last_time = time.time()
        self.resolution = (0, 0)
        
        # 建立 UI
        self.create_ui()
    
    def _load_config(self):
        """載入配置檔案"""
        config = configparser.ConfigParser()
        config_path = Path(__file__).parent / "ipcam_config.ini"
        
        # 預設配置
        defaults = {
            'RTSP_SETTINGS': {
                'BUFFER_SIZE': '1',
                'CONNECT_TIMEOUT_MS': '5000',
                'READ_TIMEOUT_MS': '5000',
                'NETWORK_CACHE_SIZE': '0',
                'TRANSPORT_PROTOCOL': '0',
                'FPS_LIMIT': '0'
            },
            'DISPLAY_SETTINGS': {
                'UI_UPDATE_INTERVAL': '30',
                'CANVAS_WIDTH': '640',
                'CANVAS_HEIGHT': '480'
            },
            'DEBUG_SETTINGS': {
                'SHOW_OPENCV_DEBUG': 'False',
                'VERBOSE_DEBUG': 'False'
            }
        }
        
        # 建立預設配置
        for section, options in defaults.items():
            if not config.has_section(section):
                config.add_section(section)
            for key, value in options.items():
                if not config.has_option(section, key):
                    config.set(section, key, value)
        
        # 嘗試讀取配置檔案
        if config_path.exists():
            try:
                config.read(config_path, encoding='utf-8')
            except Exception as e:
                print(f"警告: 讀取配置檔案失敗 {e}，使用預設值")
        else:
            # 若配置檔案不存在，建立一個
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    config.write(f)
            except Exception:
                pass
        
        return config
    
    def create_ui(self):
        """建立使用者介面"""
        # 主容器
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左側: 影像視窗
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 標題標籤
        ttk.Label(left_frame, text="即時影像", font=("Arial", 12, "bold")).pack(anchor="nw")
        
        # 影像顯示區域
        self.canvas = tk.Canvas(left_frame, bg="black", width=640, height=480)
        self.canvas.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 狀態訊息標籤 (在影像下方)
        self.status_frame = ttk.Frame(left_frame)
        self.status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.resolution_label = ttk.Label(self.status_frame, text="解析度: --", foreground="green")
        self.resolution_label.pack(side=tk.LEFT, padx=5)
        
        self.fps_label = ttk.Label(self.status_frame, text="FPS: --", foreground="blue")
        self.fps_label.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(self.status_frame, text="狀態: 未連線", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 右側: 控制面板
        right_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=15)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0), ipady=10)
        
        # URL 輸入區
        ttk.Label(right_frame, text="RTSP/HTTP URL:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.url_var = tk.StringVar(value="rtsp://192.168.1.2:1254")
        self.url_entry = ttk.Entry(right_frame, textvariable=self.url_var, width=35, font=("Consolas", 10))
        self.url_entry.pack(fill=tk.X, pady=(0, 15))
        self.url_entry.bind("<Return>", lambda e: self.open_stream())
        
        # 按鈕容器
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 開啟按鈕
        self.open_button = ttk.Button(
            button_frame,
            text="開啟串流",
            command=self.open_stream,
            width=20
        )
        self.open_button.pack(pady=5)
        
        # 關閉按鈕
        self.close_button = ttk.Button(
            button_frame,
            text="關閉串流",
            command=self.close_stream,
            width=20,
            state=tk.DISABLED
        )
        self.close_button.pack(pady=5)
        
        # 退出按鈕
        self.exit_button = ttk.Button(
            button_frame,
            text="退出程式",
            command=self.root.quit,
            width=20
        )
        self.exit_button.pack(pady=5)
        
        # 連線狀態資訊
        info_frame = ttk.LabelFrame(right_frame, text="連線資訊", padding=10)
        info_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Label(info_frame, text="狀態:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", pady=3)
        self.connection_status = ttk.Label(info_frame, text="未連線", foreground="red", font=("Arial", 9, "bold"))
        self.connection_status.grid(row=0, column=1, sticky="w", padx=10)
        
        ttk.Label(info_frame, text="解析度:", font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=3)
        self.info_resolution = ttk.Label(info_frame, text="-- x --", font=("Arial", 9, "bold"))
        self.info_resolution.grid(row=1, column=1, sticky="w", padx=10)
        
        ttk.Label(info_frame, text="FPS:", font=("Arial", 9)).grid(row=2, column=0, sticky="w", pady=3)
        self.info_fps = ttk.Label(info_frame, text="0.0", font=("Arial", 9, "bold"))
        self.info_fps.grid(row=2, column=1, sticky="w", padx=10)
    
    def open_stream(self):
        """開啟 IP CAM 串流"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("警告", "請輸入 RTSP/HTTP URL")
            return
        
        if self.stream_running:
            messagebox.showinfo("提示", "串流已在執行中")
            return
        
        # 重設統計
        self.frame_count = 0
        self.fps = 0.0
        self.last_time = time.time()
        
        # 啟動串流執行緒
        self.stream_running = True
        self.stream_thread = threading.Thread(target=self._stream_worker, args=(url,), daemon=True)
        self.stream_thread.start()
        
        # 更新按鈕狀態
        self.open_button.config(state=tk.DISABLED)
        self.close_button.config(state=tk.NORMAL)
        self.url_entry.config(state=tk.DISABLED)
        
        # 更新連線狀態標籤
        self.connection_status.config(text="連線中...", foreground="orange")
        self.status_label.config(text="狀態: 連線中...", foreground="orange")
        
        # 啟動 UI 更新迴圈
        self._update_ui()
    
    def close_stream(self):
        """關閉 IP CAM 串流"""
        self.stream_running = False
        
        # 等待執行緒結束
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2)
        
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        
        # 清空佇列
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        
        # 更新按鈕狀態
        self.open_button.config(state=tk.NORMAL)
        self.close_button.config(state=tk.DISABLED)
        self.url_entry.config(state=tk.NORMAL)
        
        # 清空畫布
        self.canvas.delete("all")
        self.canvas.create_text(320, 240, text="未連線", font=("Arial", 24), fill="white")
        
        # 更新狀態標籤
        self.connection_status.config(text="未連線", foreground="red")
        self.status_label.config(text="狀態: 未連線", foreground="red")
        self.resolution_label.config(text="解析度: --")
        self.fps_label.config(text="FPS: --")
        self.info_resolution.config(text="-- x --")
        self.info_fps.config(text="0.0")
        
        messagebox.showinfo("提示", "串流已關閉")
    
    def _stream_worker(self, url):
        """串流讀取執行緒"""
        try:
            self.cap = cv2.VideoCapture(url)
            
            # ===== RTSP 連線最佳化設定 =====
            # 設定緩衝區大小以減少延遲
            buffer_size = self.config.getint('RTSP_SETTINGS', 'BUFFER_SIZE', fallback=1)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)
            
            # 設定連線超時時間 (毫秒)
            connect_timeout = self.config.getint('RTSP_SETTINGS', 'CONNECT_TIMEOUT_MS', fallback=5000)
            self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, connect_timeout)
            
            # 設定讀取超時時間 (毫秒)
            read_timeout = self.config.getint('RTSP_SETTINGS', 'READ_TIMEOUT_MS', fallback=5000)
            self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, read_timeout)
            
            # 禁用網路快取 (降低延遲)
            cache_size = self.config.getint('RTSP_SETTINGS', 'NETWORK_CACHE_SIZE', fallback=0)
            self.cap.set(cv2.CAP_PROP_NETWORK_CACHE_SIZE, cache_size)
            
            # 設定 RTSP 傳輸協議為 TCP (更穩定，但可能延遲稍高)
            # 0 = UDP, 1 = TCP
            transport = self.config.getint('RTSP_SETTINGS', 'TRANSPORT_PROTOCOL', fallback=0)
            self.cap.set(cv2.CAP_PROP_TRANSPORT_SPEED, transport)
            
            if not self.cap.isOpened():
                raise Exception("無法開啟 URL")
            
            # 獲取解析度
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.resolution = (width, height)
            
            # 更新連線狀態
            self.connection_status.config(text="已連線", foreground="green")
            self.status_label.config(text="狀態: 已連線", foreground="green")
            self.info_resolution.config(text=f"{width} x {height}")
            
            # 持續讀取影像
            while self.stream_running:
                ret, frame = self.cap.read()
                
                if not ret:
                    break
                
                # 將影像放入佇列 (只保留最新的一幀)
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
                self.frame_queue.put(frame)
                
                self.frame_count += 1
                
                # 計算 FPS
                current_time = time.time()
                elapsed = current_time - self.last_time
                if elapsed >= 1.0:
                    self.fps = self.frame_count / elapsed
                    self.frame_count = 0
                    self.last_time = current_time
        
        except Exception as e:
            messagebox.showerror("串流錯誤", f"無法連線到 URL:\n{str(e)}\n\n請檢查：\n1. URL 是否正確\n2. 網路連線是否正常\n3. IP CAM 是否已啟動")
            self.stream_running = False
        
        finally:
            if self.cap:
                try:
                    self.cap.release()
                except Exception:
                    pass
            self.stream_running = False
    
    def _update_ui(self):
        """更新 UI 中的影像與狀態訊息"""
        if self.stream_running:
            try:
                frame = self.frame_queue.get(timeout=1)
                
                # 轉換顏色空間
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 調整尺寸以適應畫布
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                
                if canvas_width > 1 and canvas_height > 1:
                    # 計算縮放比例 (保持寬高比)
                    frame_h, frame_w = frame.shape[:2]
                    scale = min(canvas_width / frame_w, canvas_height / frame_h)
                    new_w = int(frame_w * scale)
                    new_h = int(frame_h * scale)
                    
                    frame_rgb = cv2.resize(frame_rgb, (new_w, new_h))
                    
                    # 轉換為 PIL 影像
                    pil_image = Image.fromarray(frame_rgb)
                    photo = ImageTk.PhotoImage(pil_image)
                    
                    # 在畫布中心顯示影像
                    self.canvas.delete("all")
                    self.canvas.create_image(
                        canvas_width // 2,
                        canvas_height // 2,
                        image=photo
                    )
                    self.canvas.image = photo  # 保持參考
                
                # 更新 FPS 和解析度標籤
                if self.resolution[0] > 0:
                    self.resolution_label.config(
                        text=f"解析度: {self.resolution[0]} x {self.resolution[1]}"
                    )
                
                self.fps_label.config(text=f"FPS: {self.fps:.1f}")
                self.info_fps.config(text=f"{self.fps:.1f}")
                
            except queue.Empty:
                pass
            except Exception as e:
                if self.config.getboolean('DEBUG_SETTINGS', 'VERBOSE_DEBUG', fallback=False):
                    print(f"UI 更新錯誤: {e}")
            
            # 讀取更新間隔設定
            update_interval = self.config.getint('DISPLAY_SETTINGS', 'UI_UPDATE_INTERVAL', fallback=30)
            
            # 繼續更新迴圈
            self.root.after(update_interval, self._update_ui)
        else:
            # 串流已停止，檢查是否需要重新啟動迴圈
            if self.stream_running:
                self.root.after(30, self._update_ui)


def main():
    """主程式"""
    root = tk.Tk()
    app = IPCAMPlayer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
