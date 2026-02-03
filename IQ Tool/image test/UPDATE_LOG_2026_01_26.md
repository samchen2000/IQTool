# ccm_test_3.py 更新日誌

## 更新時間
2026年1月26日

## 新增功能概述

### 功能 1：Close Image File 菜單選項
**位置**：File 菜單  
**功能描述**：關閉用戶打開的圖片文件，回復到默認的24色色卡顯示狀態

**實現細節**：
- 新增 `on_close_image()` 回調函數
- 清除 `user_image` 和 `user_image_display`
- 移除所有編輯的方框
- 退出手動模式 (`is_manual_mode = False`)
- 恢復右側顯示為原始24色色卡
- 重繪 Matplotlib 介面

**使用方式**：
```
File 菜單 → Close Image File
```

---

### 功能 2：色塊編號輸入框（Color Block Selector）
**位置**：窗口底部，Reset 按鈕左側  
**功能描述**：輸入色塊編號（1-24）快速選擇和操作特定的色塊

**界面元素**：
| 元素 | 位置 | 說明 |
|------|------|------|
| 標籤 | x=0.15 | "Color Block (1-24):" |
| 輸入框 | x=0.30 | 黃色背景，默認值為 "1" |
| Select 按鍵 | x=0.39 | 確認選擇指定編號的色塊 |

**使用方式**：

**方式 A：使用 Select 按鍵**
1. 在輸入框中輸入 1-24
2. 點擊 "Select" 按鍵
3. 對應色塊邊框變為紅色並加粗

**方式 B：鍵盤操作**
1. 點擊輸入框（邊框變藍色表示激活）
2. 輸入色塊編號（0-9 數字）
3. 按 Enter 確認 或 Escape 取消

**實現細節**：
- 新增 `on_select_color_block()` - 選擇色塊回調
- 新增 `on_color_block_pick()` - pick 事件處理
- 新增 `on_color_block_key()` - 鍵盤事件處理
- 新增 `combined_on_key_event()` - 整合鍵盤事件處理
- 支援輸入驗證（1-24範圍檢查）
- 支援視覺反饋（邊框顏色變化）

**功能特色**：
✅ 快速導航到特定色塊  
✅ 支援鍵盤和鼠標雙輸入  
✅ 實時視覺反饋  
✅ 輸入驗證和錯誤提示  
✅ 與現有方框拖拽功能整合  

---

## 代碼修改概述

### 新增回調函數

```python
# 在菜單部分
def on_close_image():
    """關閉圖片菜單回調 - 回復24色色卡顯示"""
    # 清除用戶圖片及相關方框
    # 恢復右側顯示為原始24色色卡

# 在色塊輸入框部分
def on_select_color_block(event):
    """根據輸入的編號選擇色塊"""

def on_color_block_pick(event):
    """點擊色塊輸入框時觸發"""

def on_color_block_key(event):
    """色塊輸入框的鍵盤事件"""

def combined_on_key_event(event):
    """組合的鍵盤事件處理"""
```

### 全局變量擴展

在 `global_data` 字典中已有的字段對新功能的支持：
- `color_boxes` - 存儲方框對象
- `box_positions` - 存儲方框位置
- `selected_box_idx` - 當前選中的方框索引
- `is_manual_mode` - 手動模式狀態
- `color_block_input_text` - **新增** 色塊輸入框文本對象

### 事件連接管理

修改了舊的鍵盤事件連接方式，改為：
```python
# 保存舊的鍵盤事件處理
old_on_key_event = on_key_event

# 創建整合的處理函數
def combined_on_key_event(event):
    on_color_block_key(event)      # 先處理色塊輸入
    old_on_key_event(event)        # 再處理原有功能

# 連接新的組合事件
fig.canvas.mpl_connect('key_press_event', combined_on_key_event)
```

---

## 使用場景示例

### 場景 1：快速定位色塊進行手動調整
```
1. 點擊 File → Open Image 打開用戶圖片
2. 在輸入框中輸入想要調整的色塊編號（例如：5）
3. 點擊 Select 按鍵
4. 編號 5 的色塊邊框變為紅色
5. 使用鼠標拖拽調整方框位置和大小
6. Lab 值自動更新並顯示在分析窗口
```

### 場景 2：標準24色色卡瀏覽
```
1. 在默認模式（24色色卡顯示）
2. 使用色塊輸入框快速跳轉到特定編號的色塊
3. 查看該色塊的詳細 Lab 值信息
```

### 場景 3：圖片切換
```
1. 打開用戶圖片進行調整
2. 點擊 File → Close Image File 關閉
3. 回復到默認24色色卡顯示
4. 色塊輸入框仍可使用，但不影響圖片
5. 可再次打開新圖片進行調整
```

---

## 技術細節

### 事件流程

**Select 按鍵被點擊**：
1. `on_select_color_block()` 被觸發
2. 驗證輸入（1-24 範圍）
3. 清除之前的選擇（所有邊框變青色）
4. 在手動模式下高亮選中的色塊（邊框變紅色）
5. `fig.canvas.draw_idle()` 重繪

**輸入框被點擊**：
1. `on_color_block_pick()` 被觸發
2. 激活編輯模式 (`color_block_editing['active'] = True`)
3. 改變邊框顏色為藍色表示激活

**鍵盤輸入**：
1. `combined_on_key_event()` 被觸發
2. 檢查是否在編輯模式
3. 處理特殊鍵（Backspace, Escape, Enter）
4. 處理數字輸入（最多2位）
5. 實時更新輸入框顯示

---

## 相容性說明

- ✅ 與現有 CCM 調整功能完全相容
- ✅ 與現有方框拖拽、大小調整功能完全相容
- ✅ 不影響現有的 Reset 按鈕功能
- ✅ 不影響現有的菜單和滑桿功能

---

## 已知限制

1. 色塊輸入框在 24 色色卡模式下可見但功能有限
2. 最多只能同時選中 1 個色塊
3. 輸入框只接受 1-24 的有效數字

---

## 未來改進建議

- [ ] 支持多色塊同時選擇
- [ ] 添加快捷鍵（如 Ctrl+數字）快速選擇
- [ ] 添加色塊批量操作功能
- [ ] 支持色塊位置預設模板保存/加載
