```mermaid
graph TD
    A[感測器 RAW Bayer 資料] --> B{DCMIPP <br/>ISP 管道處理}
    
    subgraph "DCMIPP (硬體加速處理)"
    B --> B1[基礎校正: 壞點/黑位/ISP增益]
    B1 --> B2[去馬賽克 Demosaicing: RAW 轉 RGB]
    B2 --> B3[影像優化: 色彩校正/伽瑪/對比度]
    B3 --> B4[色彩空間轉換: RGB 轉 YUV]
    end
    
    B4 --> C[系統記憶體 DDR / Buffer]
    B2 --> C
    
    subgraph "最終格式封裝與編碼"
    C --> D[VENC 硬體加速器]
    D --> D1[<b>JPG</b> / JPEG 編碼]
    
    C --> E[軟體封裝 Software]
    E --> E1[<b>BMP</b> 點陣圖]
    
    C --> F[IQTune 工具 / 軟體]
    F --> F1[<b>PNG</b> 影像檔]
    end

    style B fill:#f9f,stroke:#333,stroke-width:2px
    style D fill:#bbf,stroke:#333,stroke-width:2px
    style E fill:#fff,stroke:#333,stroke-dasharray: 5 5
    ```