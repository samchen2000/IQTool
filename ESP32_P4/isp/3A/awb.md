整體功能說明
這是一個自動白平衡(AWB)控制器的實現，用於影像處理中的白平衡調整。主要功能包括：

1. AWB 控制器的創建與刪除
2. 配置 AWB 參數
3. 支援單次和連續統計模式  
4. 中斷處理機制

### 關鍵結構體  
```
typedef struct isp_awb_controller_t {
    _Atomic isp_fsm_t fsm;         // 狀態機,控制 AWB 的運行狀態
    portMUX_TYPE spinlock;         // 自旋鎖,用於臨界區保護
    intr_handle_t intr_handle;     // 中斷處理句柄
    isp_proc_handle_t isp_proc;    // ISP 處理器句柄
    QueueHandle_t evt_que;         // 事件佇列
    esp_isp_awb_cbs_t cbs;        // 回調函數集合
    void *user_data;              // 用戶數據指針
} isp_awb_controller_t;
```
### 主要功能函數說明
### 1. 創建控制器
```
esp_err_t esp_isp_new_awb_controller(...)
```
- 分配記憶體空間
- 初始化事件佇列
- 設置中斷處理
- 配置硬體參數

### 2.統計功能
```
esp_err_t esp_isp_awb_controller_get_oneshot_statistics(...)
```
- 執行單次白平衡統計
- 等待統計結果
- 返回統計數據
### 3. 連續統計模式
```
esp_err_t esp_isp_awb_controller_start_continuous_statistics(...)
esp_err_t esp_isp_awb_controller_stop_continuous_statistics(...)
```
- 啟動/停止連續統計模式
- 通過回調函數返回統計結果

## 4.中斷處理
```
bool IRAM_ATTR esp_isp_awb_isr(...)
```
- 處理 AWB 完成中斷
- 收集統計數據
- 觸發回調函數
- 維護連續統計模式

### 安全性考慮
1. 使用自旋鎖保護共享資源
2. 狀態機確保操作順序
3. 參數驗證
4. 支援 IRAM 安全配置

### 統計數據包括
- 白點數量
- R/G/B 累積值
- 子窗口統計資訊

這個模組是典型的嵌入式影像處理系統中的重要組件,用於確保影像的色彩準確性。它通過硬體加速來完成白平衡計算,並提供靈活的配置選項和運行模式。