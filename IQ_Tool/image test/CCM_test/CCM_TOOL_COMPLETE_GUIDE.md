# ccm_test_3.py - 完整功能說明

## 概述

ccm_test_3.py 是一個互動式 CCM（色彩校正矩陣）調整工具，結合了標準 24 色標準色卡和自訂圖片模式。

## 核心功能

### 1. 標準模式（預設）
- 載入標準 24 色 Macbeth ColorChecker
- 支持 9 個 CCM 參數的滑塊調整
- 支援增加/減少按鍵（±0.05）
- 支援直接輸入框編輯

### 2. 手動圖片模式（新增）
- 打開自訂圖片（JPEG/PNG/BMP）
- 自動檢測 24 色塊位置
- 手動調整方框位置和大小
- 即時 Lab 值更新

### 3. 功能表列（新增）
```
File
├── Open Image (JPEG/PNG/BMP)  # 打開圖片
└── Exit                        # 退出程式
```

## 使用流程

### 標準模式使用
1. 運行程式
2. 默認載入 24 色標準色卡
3. 使用滑塊、按鍵或輸入框調整 CCM 參數
4. 在左側查看原始色卡，右側查看調整後的色卡
5. 在 Lab 分析視窗查看即時資料

### 手動圖片模式使用
1. 運行程式
2. 點擊菜單 **File → Open Image**
3. 選擇圖片檔（JPEG/PNG/BMP）
4. 系統自動：
   - 縮放圖片以適應顯示區域
   - 檢測 24 個色塊位置
   - 生成可調整的方框
5. 調整方框位置和大小：
   - **點擊方框**：選中（邊框變紅）
   - **拖拽**：移動方框
   - **Shift + 拖拽**：調整大小
6. 即時查看 Lab 值變化

## 技術實現

### 自動色塊檢測
```
演算法：K-means 聚類
步驟：
1. 將圖像轉換為圖元清單
2. 使用 cv2.kmeans 進行 24 類聚類
3. 為每個聚類計算邊界框
4. 按 (y, x) 座標排序
```

### 顏色提取
```
流程：
1. 獲取方框內所有圖元
2. 計算平均 RGB 值
3. 應用 CCM 矩陣變換
4. 轉換為 Lab 色彩空間
5. 更新 Lab 顯示視窗
```

### 滑鼠交互
```
事件處理：
- button_press_event      → 記錄起始點
- motion_notify_event     → 移動或調整大小
- button_release_event    → 結束操作
- pick_event              → 選擇方框或輸入框

操作模式：
- 默認拖拽 → 移動方框
- Shift + 拖拽 → 調整方框大小
```

## 全域資料結構

```python
global_data = {
    # 標準模式資料
    'lab_values': [],                    # Lab 值列表
    'color_names': [],                   # 顏色名稱
    'text_widget': None,                 # Lab 顯示視窗
    'colors_rgb_original': [],           # 原始 RGB 顏色
    'current_ccm': np.eye(3),            # 當前 CCM 矩陣
    
    # Matplotlib 對象
    'fig': None,
    'ax': None,
    'img_display': None,                 # 圖像顯示物件
    'ax_adjusted': None,                 # 右側 axis
    
    # 手動模式資料
    'user_image': None,                  # 使用者打開的圖片
    'user_image_display': None,          # 使用者圖片顯示物件
    'color_boxes': [],                   # 方框物件清單
    'is_manual_mode': False,             # 是否手動模式
    'box_positions': [],                 # 方框位置資訊
    'selected_box_idx': None,            # 當前選中方框
}
```

## 關鍵函數

### 圖片處理
| 函數 | 說明 |
|------|------|
| `open_image_file()` | 打開檔對話方塊並載入圖片 |
| `detect_color_blocks_kmeans()` | 自動檢測 24 色塊位置 |
| `load_user_image_to_plot()` | 將使用者圖片載入到 Matplotlib |
| `create_initial_boxes()` | 創建初始 24 個方框 |

### 資料更新
| 函數 | 說明 |
|------|------|
| `update()` | CCM 滑塊更新回檔 |
| `update_manual_mode_display()` | 手動模式 Lab 值更新 |
| `update_text_display()` | 更新 Lab 顯示視窗 |

### 事件處理
| 函數 | 事件類型 | 說明 |
|------|---------|------|
| `on_open_image()` | 功能表點擊 | 打開圖片 |
| `on_box_pick_event()` | pick_event | 選擇方框 |
| `on_mouse_press()` | button_press_event | 滑鼠按下 |
| `on_mouse_motion()` | motion_notify_event | 滑鼠移動/調整 |
| `on_mouse_release()` | button_release_event | 滑鼠釋放 |

## 檔結構

```
d:\IQ app\python\IQTool\IQ Tool\image test\
├── ccm_test_3.py                    # 主程序
├── MANUAL_IMAGE_MODE.md             # 手動模式使用指南
├── CHANGES.md                       # 版本更新說明
└── USAGE_GUIDE.md                   # 通用使用指南
```

## 特色功能

### ✅ 已實現
- [x] 功能表列（File 菜單）
- [x] 打開圖片對話方塊（支援 JPEG/PNG/BMP）
- [x] 自動色塊檢測（K-means）
- [x] 可拖拽方框
- [x] 方框大小調整（Shift + 拖拽）
- [x] 即時 Lab 值更新
- [x] 功能表列集成
- [x] 圖片尺寸自動調整
- [x] 方框顏色回饋（選中變紅）

### 🚀 可擴展方向
- 方框網格對齊功能
- 撤銷/重做功能
- 保存/載入方框配置
- 批量圖片處理
- 色塊驗證報告
- 高級色彩分析

## 注意事項

### 性能
- 自動檢測大圖片可能需要數秒
- 建議圖片解析度 ≤ 2000×2000
- 每次調整時會即時更新（可能較慢）

### 相容性
- 支持 Windows、macOS、Linux
- 需要 OpenCV、NumPy、Matplotlib、scikit-image
- Python 3.7+

### 邊界處理
- 方框會自動限制在圖片範圍內
- 超出範圍的圖元會被自動裁剪
- 顏色計算會跳過無效區域

## 快速參考

### 標準模式快速鍵
| 操作 | 說明 |
|------|------|
| 拖拽滑塊 | 調整 CCM 參數 |
| 點擊 ± 按鍵 | 增加/減少 0.05 |
| 點擊輸入框 | 直接編輯數值 |
| Enter | 確認輸入 |
| Escape | 取消編輯 |

### 手動模式快速鍵
| 操作 | 說明 |
|------|------|
| File → Open | 打開圖片 |
| 點擊方框 | 選中方框 |
| 拖拽 | 移動方框 |
| Shift + 拖拽 | 調整大小 |
| File → Exit | 退出 |

## 常見問題解答

### Q: 如何切換回標準色卡？
A: 重新運行程式或在代碼中注釋掉 `open_image_file()` 相關代碼。

### Q: 自動檢測精度不夠高？
A: 可手動調整方框位置和大小。對於複雜背景的圖片，檢測可能不準確。

### Q: 方框數量為什麼是 24 個？
A: 對應標準 Macbeth ColorChecker 的 24 色色塊規格。

### Q: 如何提高檢測速度？
A: 使用較小解析度的圖片（< 1000×1000 圖元）。

### Q: 能否保存調整結果？
A: 目前可通過截圖保存。未來版本將支援資料匯出。

## 聯繫與回饋

如有問題或建議，請在專案中提交 Issue 或 Pull Request。

---

**最後更新**: 2026-01-23
**版本**: 3.0 (手動圖片模式版)


