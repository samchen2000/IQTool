# ... existing code ...
        # 繪圖變數 (用於滑鼠框選)
        self.canvas_img = None     # 畫布上的圖片物件
        self.rect_id = None        # 框選矩形的ID
        self.start_x = None
        self.start_y = None
        
        # 【Sam 新增】：透視變換 4 點座標儲存區 (左上, 右上, 右下, 左下)
        self.pts_4point = []
        self.point_markers = []

        # 色卡參考值 (ColorChecker 24 - sRGB D65 參考值，這裡使用近似值)
# ... existing code ...
    def set_mode(self, new_mode):
        """設定當前的操作模式"""
        if self.original_img_cv is None:
            self.status_label.config(text="狀態：請先開啟圖片！", foreground="red")
            return
            
        self.mode = new_mode
        self.clear_canvas_drawings() # 重置繪圖與點位

        if new_mode == 'color_chart':
            self.status_label.config(text="狀態：請依序點擊 ColorChecker 24 四個角 (左上->右上->右下->左下)", foreground="green")
            self.display_message("已進入 ColorChecker 透視分析模式。請在畫布上依序點擊色卡 4 個角落。")
        elif new_mode == 'density_chart':
            self.status_label.config(text="狀態：請在 Q14 階梯圖上點擊/框選要分析的位置。", foreground="orange")
            self.display_message("已進入 Q14 密度分析模式。請框選一個或多個階梯區域。")
        elif new_mode == 'srf_chart':
            self.status_label.config(text="狀態：請框選 SFR 斜邊。", foreground="purple")
            self.display_message("已進入 SFR 銳利度分析模式。請框選斜邊。")
        else:
            self.status_label.config(text="狀態：空閒中", foreground="blue")

    def clear_canvas_drawings(self):
        """清除畫布上的輔助標記線條與點位"""
        self.pts_4point = []
        for marker in self.point_markers:
            self.canvas.delete(marker)
        self.point_markers = []
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

    # --- GUI 事件處理 ---

    def open_image(self):
# ... existing code ...
            self.display_message(f"成功開啟圖片: {os.path.basename(path)}")
            self.set_mode('none') # 重置模式
            self.report_data = [] # 清空報表數據
            
    def on_button_press(self, event):
        """滑鼠按下事件：依模式進行 4 點點擊或矩形框選"""
        if self.original_img_cv is None:
            return
        
        # 取得 Canvas 上的點擊座標
        click_x = self.canvas.canvasx(event.x)
        click_y = self.canvas.canvasy(event.y)

        # 【Sam 擴充功能】： ColorChecker 24 四點透視點擊邏輯
        if self.mode == 'color_chart':
            # 轉換座標至原始圖片解析度
            scale_x = self.original_img_cv.shape[1] / self.current_display_img.width
            scale_y = self.original_img_cv.shape[0] / self.current_display_img.height
            
            orig_x = click_x * scale_x
            orig_y = click_y * scale_y

            self.pts_4point.append((orig_x, orig_y))
            pt_num = len(self.pts_4point)
            
            # 在畫布上記錄點擊視覺標籤 (紅色圓點 + 數字)
            r = 4
            marker = self.canvas.create_oval(click_x-r, click_y-r, click_x+r, click_y+r, fill='red', outline='yellow', width=1.5)
            text_marker = self.canvas.create_text(click_x+10, click_y-5, text=str(pt_num), fill='yellow', font=('Arial', 10, 'bold'))
            self.point_markers.extend([marker, text_marker])

            corner_names = ["左上 (Top-Left)", "右上 (Top-Right)", "右下 (Bottom-Right)", "左下 (Bottom-Left)"]
            self.display_message(f"已選取第 {pt_num} 角落 [{corner_names[pt_num-1]}]: ({int(orig_x)}, {int(orig_y)})")

            # 集滿 4 點後自動啟動透視校正與 24 色塊分析
            if len(self.pts_4point) == 4:
                self.display_message("4 個角落點選完畢，開始進行四點透視校正與 ROI 採樣...")
                self.analyze_color_chart_perspective()
            return

        # 其他模式（如矩形框選）
        self.start_x = click_x
        self.start_y = click_y
        
        # 刪除舊的矩形
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        # 創建新的矩形
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=2
        )
        
    def on_mouse_drag(self, event):
        """滑鼠拖曳事件：更新矩形大小"""
        if self.rect_id and self.mode != 'color_chart':
            end_x = self.canvas.canvasx(event.x)
            end_y = self.canvas.canvasy(event.y)
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, end_x, end_y)

    def on_button_release(self, event):
        """滑鼠釋放事件：結束框選並進行分析"""
        if self.mode == 'color_chart':
            return # ColorChecker 使用 4 點點擊，跳過 Drag Release 邏輯

        if self.rect_id is None or self.original_img_cv is None:
            return

        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        
        # 轉換座標從顯示圖片到原始圖片尺寸
        scale_x = self.original_img_cv.shape[1] / self.current_display_img.width
        scale_y = self.original_img_cv.shape[0] / self.current_display_img.height

        x1 = int(min(self.start_x, end_x) * scale_x)
        y1 = int(min(self.start_y, end_y) * scale_y)
        x2 = int(max(self.start_x, end_x) * scale_x)
        y2 = int(max(self.start_y, end_y) * scale_y)

        # 確保 ROI 是有效的
        if x2 <= x1 or y2 <= y1:
             self.display_message("警告：無效的框選區域。")
             return

        # 擷取原始影像 ROI
        roi_img_cv = self.original_img_cv[y1:y2, x1:x2]

        if self.mode == 'density_chart':
            self.analyze_step_chart(roi_img_cv, x1, y1, x2, y2)
        elif self.mode == 'srf_chart':
            self.display_message("SFR 分析模式: 由於演算法複雜度，我們使用基礎銳利度估計。")
            self.analyze_sharpness(roi_img_cv)
        
        self.canvas.delete(self.rect_id)
        self.rect_id = None
        
    # --- 專門分析函數 ---
# ... existing code ...
    def analyze_color_chart(self, roi_img_cv):
        """[舊版 矩形框選備用]"""
        pass

    def analyze_color_chart_perspective(self):
        """
        【Sam 影像處理小幫手 - 四點透視變換與 24 色塊 ROI 視覺化校驗】
        透過 OpenCV cv2.getPerspectiveTransform 將傾斜圖卡透視拉直，
        並在畫布上將 24 個動態 ROI 繪製出來供使用者檢查是否對齊。
        """
        if len(self.pts_4point) != 4:
            self.display_message("錯誤：透視變換需要精確的 4 個點！")
            return

        self.display_message("\n--- ColorChecker 24 (四點透視變換) 分析開始 ---")

        # 1. 取得用戶點選的 4 個頂點 (左上, 右上, 右下, 左下)
        src_pts = np.array(self.pts_4point, dtype=np.float32)

        # 2. 計算目標拉直影像的標準寬度與高度 (以長邊作為標準，預設 6:4 比例)
        width_top = np.linalg.norm(src_pts[1] - src_pts[0])
        width_bottom = np.linalg.norm(src_pts[2] - src_pts[3])
        max_w = int(max(width_top, width_bottom))

        height_left = np.linalg.norm(src_pts[3] - src_pts[0])
        height_right = np.linalg.norm(src_pts[2] - src_pts[1])
        max_h = int(max(height_left, height_right))

        # 強制 6:4 色卡標準比例尺寸
        dst_w = max_w
        dst_h = int(max_w * (4.0 / 6.0))

        # 定義透視目標四角座標
        dst_pts = np.array([
            [0, 0],
            [dst_w - 1, 0],
            [dst_w - 1, dst_h - 1],
            [0, dst_h - 1]
        ], dtype=np.float32)

        # 3. 計算 Perspective Matrix (正向與逆向 Transform 矩陣)
        M_prespective = cv2.getPerspectiveTransform(src_pts, dst_pts)
        M_inv = cv2.getPerspectiveTransform(dst_pts, src_pts)

        # 將原始影像進行透視扭正 Warp Perspective
        warped_card = cv2.warpPerspective(self.original_img_cv, M_prespective, (dst_w, dst_h))

        # 4. 在透視校正圖上劃分 4x6 網格，並計算 24 個色塊採樣區
        rows, cols = 4, 6
        block_w = dst_w / cols
        block_h = dst_h / rows

        # 計算縮放比（將透視後點轉回原始 Display Canvas 用）
        scale_x = self.current_display_img.width / self.original_img_cv.shape[1]
        scale_y = self.current_display_img.height / self.original_img_cv.shape[0]

        analysis_results = []

        for i in range(rows):
            for j in range(cols):
                patch_id = i * cols + j
                ref_rgb = self.REF_COLOR_24[patch_id]

                # 標準透視圖上該色塊的中心座標與採樣範圍 (取中心 40% 避免邊緣失真)
                cx_warped = (j + 0.5) * block_w
                cy_warped = (i + 0.5) * block_h
                sample_w = block_w * 0.4
                sample_h = block_h * 0.4

                x1_w = int(cx_warped - sample_w / 2)
                x2_w = int(cx_warped + sample_w / 2)
                y1_w = int(cy_warped - sample_h / 2)
                y2_w = int(cy_warped + sample_h / 2)

                # 擷取校正圖上的色塊畫素
                patch_img = warped_card[y1_w:y2_w, x1_w:x2_w]
                
                # 計算實際測量值的平均 BGR -> RGB
                if patch_img.size > 0:
                    avg_bgr = np.mean(patch_img, axis=(0, 1))
                    sample_rgb = (avg_bgr[2], avg_bgr[1], avg_bgr[0])
                else:
                    sample_rgb = (0, 0, 0)

                # 計算 Delta E 2000 與 Delta C
                delta_e, delta_c = calculate_delta_e_c(ref_rgb, sample_rgb)

                analysis_results.append({
                    'ID': patch_id + 1,
                    'Ref RGB': ref_rgb,
                    'Sample RGB': tuple(int(c) for c in sample_rgb),
                    'Delta E 2000': delta_e,
                    'Delta C 2000': delta_c
                })

                # --- 5. 【視覺化 ROI 驗證】將透視矩陣逆變換 (M_inv)，在原始 Canvas 上劃出 24 個藍色採樣點/框 ---
                # 原圖座標中的色塊中心
                pt_warped_center = np.array([[[cx_warped, cy_warped]]], dtype=np.float32)
                pt_orig_center = cv2.perspectiveTransform(pt_warped_center, M_inv)[0, 0]

                # 轉換為 GUI Canvas 畫面座標
                canvas_cx = pt_orig_center[0] * scale_x
                canvas_cy = pt_orig_center[1] * scale_y

                # 畫出 24 個 ROI 圓形標示與 Patch ID
                r = 3
                roi_marker = self.canvas.create_oval(
                    canvas_cx - r, canvas_cy - r, canvas_cx + r, canvas_cy + r,
                    outline='#38bdf8', fill='#0284c7', width=1.5
                )
                roi_text = self.canvas.create_text(
                    canvas_cx, canvas_cy - 8,
                    text=f"P{patch_id+1}", fill='#38bdf8', font=('Arial', 7, 'bold')
                )
                self.point_markers.extend([roi_marker, roi_text])

                # 輸出 Log
                self.display_message(
                    f"  色塊 {patch_id+1:02d}: ΔE={delta_e:.2f}, ΔC={delta_c:.2f} "
                    f"(Ref:{ref_rgb}, Sample:{tuple(int(c) for c in sample_rgb)})"
                )

                # 計算灰態 SNR
                if patch_id >= 18:
                    density, snr = analyze_density_snr(patch_img)
                    self.display_message(f"    (灰階 P{patch_id+1}): Y-SNR={snr:.2f}")
                    analysis_results[-1]['Y-SNR'] = snr

        # 將結果加入報表數據
        self.report_data.append({
            'Test Item': 'ColorChecker 24 (Perspective Transform)',
            'Result': analysis_results,
            'Unit': 'Delta E/C'
        })
        self.display_message("✅ ColorChecker 24 透視校正與 24 色塊 ROI 驗證繪製完成！")
        self.status_label.config(text="狀態：ColorChecker 分析完成，請查看畫面上的 24 個 ROI 藍點驗證位置。", foreground="blue")

    def generate_report(self):
# ... existing code ...