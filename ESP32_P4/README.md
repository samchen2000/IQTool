## 1. 概述
ESP32 是集成 2.4 GHz Wi-Fi 和蓝牙双模的单芯片方案，采用台积电 (TSMC) 超低功耗的 40 纳米工艺，具有超
高的射频性能、稳定性、通用性和可靠性，以及超低的功耗，满足不同的功耗需求，适用于各种应用场景。
目前 ESP32 系列的产品型号包括 ESP32-D0WDQ6，ESP32-D0WD，ESP32-D2WD 和 ESP32-S0WD。产品型
号说明和订购信息请参照章节产品型号和订购信息 。
### 1.1 专用解决方案
#### 1.1.1 超低功耗
ESP32 专为移动设备、可穿戴电子产品和物联网 (IoT) 应用而设计。作为业内领先的低功耗芯片，ESP32 具有精
细的时钟门控、省电模式和动态电压调整等特性。
例如，在低功耗 IoT 传感器 Hub 应用场景中，ESP32 只有在特定条件下才会被周期性地唤醒。低占空比可以极大降低 ESP32 芯片的能耗。射频功率放大器的输出功率也可调节，以实现通信距离、数据率和功耗之间的最佳
平衡。
#### 1.1.2 高集成度
ESP32 是业内领先的高度集成的 Wi-Fi+ 蓝牙解决方案，外部元器件只需大约 20 个。ESP32 集成了天线开关、射频 Balun、功率放大器、低噪声放大器、滤波器以及电源管理模块，极大减少了印刷电路板 (PCB) 的面积。  
ESP32 采用 CMOS 工艺实现单芯片集成射频和基带，还集成了先进的自校准电路，实现了动态自动调整，可以消除外部电路的缺陷，更好地适应外部环境的变化。因此，ESP32 的批量生产可以不需要昂贵的专用 Wi-Fi 测试设备。  
### 1.2 Wi-Fi 主要特性
• 802.11 b/g/n  
• 802.11 n (2.4 GHz) 速度高达 150 Mbps  
• 无线多媒体 (WMM)  
• 帧聚合 (TX/RX A-MPDU, RX A-MSDU)  
• 立即块回复 (Immediate Block ACK)  
• 重组 (Defragmentation)  
• Beacon 自动监测（硬件 TSF）  
• 4 × 虚拟 Wi-Fi 接口  
• 同时支持基础结构型网络 (Infrastructure BSS) Station 模式/SoftAP 模式/混杂模式
请注意 ESP32 在 Station 模式下扫描时，SoftAP 信道会同时改变
• 天线分集  
### 1.3 蓝牙主要特性
• 蓝牙 v4.2 完整标准，包含传统蓝牙 (BR/EDR) 和低功耗蓝牙 (BLE)  
• 支持标准 Class-1、Class-2 和 Class-3，且无需外部功率放大器  
• 增强型功率控制 (Enhanced Power Control)  
• 输出功率高达 +12 dBm  
• NZIF 接收器具有–97 dBm 的 BLE 接收灵敏度  
• 自适应跳频 (AFH)  
• 基于 SDIO/SPI/UART 接口的标准 HCI  
• 高速 UART HCI，最高可达 4 Mbps  
• 支持蓝牙 4.2 BR/EDR 和 BLE 双模 controller  
• 同步面向连接/扩展同步面向连接 (SCO/eSCO)  
• CVSD 和 SBC 音频编解码算法  
• 蓝牙微微网 (Piconet) 和散射网 (Scatternet)  
• 支持传统蓝牙和低功耗蓝牙的多设备连接  
• 支持同时广播和扫描  
### 1.4 MCU 和高级特性
#### 1.4.1 CPU 和存储
• Xtensa® 32-bit LX6 单/双核处理器，运算能力高达 600 MIPS（除 ESP32-S0WD 为 200 MIPS，ESP32-D2WD
为 400 MIPS）  
• 448 KB ROM  
• 520 KB SRAM  
• 16 KB RTC SRAM  
• QSPI 支持多个 flash/SRAM  
#### 1.4.2 时钟和定时器
• 内置 8 MHz 振荡器，支持自校准  
• 内置 RC 振荡器，支持自校准  
• 支持外置 2 MHz 至 60 MHz 的主晶振（如果使用 Wi-Fi/蓝牙功能，则目前仅支持 40 MHz 晶振） 
• 支持外置 32 kHz 晶振，用于 RTC，支持自校准  
• 2 个定时器群组，每组包括 2 个 64-bit 通用定时器和 1 个主系统看门狗  
• 1 个 RTC 定时器  
• RTC 看门狗  
#### 1.4.3 高级外设接口
• 34 个 GPIO 口  
• 12-bit SAR ADC，多达 18 个通道  
• 2 个 8-bit D/A 转换器  
• 10 个触摸传感器  
• 4 个 SPI  
• 2 个 I²S  
• 2 个 I²C  
• 3 个 UART  
• 1 个 Host SD/eMMC/SDIO  
• 1 个 Slave SDIO/SPI  
• 带有专用 DMA 的以太网 MAC 接口，支持 IEEE 1588  
• CAN2.0  
• IR (TX/RX)  
• 电机 PWM  
• LED PWM，多达 16 个通道  
• 霍尔传感器  
##### 1.4.4 安全机制
• 安全启动  
• flash 加密  
• 1024-bit OTP，用户可用的高达 768 bit  
• 加密硬件加速器：  
- AES
- Hash (SHA-2)
- RSA
- ECC
- 随机数生成器 (RNG)
