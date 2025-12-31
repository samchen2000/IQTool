#!/bin/bash

# 多選項表單 - Linux 系統互動式選單
# 使用方式：./menu_form.sh

# 顏色定義（可選）
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color


# 主選單函式
main_menu() {
    clear
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}         FocalTrans 文件系統選單${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo ""
    echo -e "${GREEN}請選擇一個選項：${NC}"
    echo ""
    echo "1) 讀取proc 獲取當前ISP工作訊息"
    echo "2) 讀取MIPI proc 工作訊息"
    echo "3) 打印ISP當前使用的模組開關與參數"
    echo "4) 打印MIPI proc文件"
    echo "5) 測試(TBD)"
    echo "6) 測試(TBD)"
    echo "0) 退出程式"
    echo ""
    echo -e "${YELLOW}請輸入選項 (0-6):${NC}"
}

# ISP 子選單
isp_menu() {
    clear
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}         ISP proc 訊息${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo ""
    echo "1) help : 印出所有支持的命令"
    echo "2) nr3d_[on/off]_[0/1/2] : 開關指定設備的NR3D"
    echo "3) nr3dcir_[on/off]_[0/1/2] : 開關指定設備的NR3D的循環緩衝,默認開啟"
    echo "4) nr3decdc_[on/off]_[0/1/2] : 開關指定設備的NR3D壓縮解壓,默認開啟"
    echo "5) nr3dnoddr_[on/off]_[0/1/2] : 開關指定設備的NR3D是否為直通模式,開啟後不經過DDR,默認關閉"
    echo "6) nr3ddep_[on/off]_[0/1/2] : 開關指定設備的NR3D循環緩衝深度"
    echo "7) trace_[on/off]_[0/1/2] : 開關指定設備API的調用追蹤訊息"
    echo "8) wdr_[on/off]_[0/1/2] : 開關指定設備WDR初始化的內存分配"
    echo "9) wdrcir_[on/off]_[0/1/2] : 開關指定設備WDR模式ECDC的循環緩存功能"
    echo "10) wdrciron_[buf num][buf_depth][0/1/2] : 配置WDR模式的緩存區個數與深度"
    echo "11) wdrecdc_[on/off]_[0/1/2] : 開關指定設備WDR模式的壓縮解壓"
    echo "12) addr : 列印當前ISP實際使用的資料位址的情況"
    echo "13) info : 打印當前ISP工作的調整訊息,實際創建了多少個ISP設備"
    echo "14) mod : 打印ISP當前使用的模組的開關,參數等情況"
    echo "15) idle_[0/1/2] : 打印指定設備的模組工作狀態"
    echo "16) colorbar_[1~30] : 配置彩條,後跟參數為FPS"
    echo "17) rst : reset ISP 流水線"
    echo "18) autoreset_[on/off] : 開啟或關閉 ISP 自動復位控制邏輯,硬體默認開啟自動復位"
    echo "19) aelog_[value]_[0/1/2] : 開啟或關閉指定設備的AE日誌訊息打印"
    echo "20) awblog_[0/1]_[0/1/2] : 開啟或關閉指定設備的AWB日誌訊息打印"
    echo "21) ispoutnum_[buf_num]_[0/1/2] : 配置指定設備ISP輸出的緩衝區個數,配置為0代表使用VB"
    echo "22) forcekick_[on/off] : 開啟或關閉VPU的強踢模式"
    echo "23) vgs_[on/off]_[0/1/2] : 開啟或關閉指定設備的VGS"
    echo "24) procmode_[0/1] : 調整訊息格式切換,默認調整訊息按照和項排列"
    echo "25) linearwdr_[on/off] : 離線兩路模式下,當一路是WDR一路是線性,並且NR3D為非直通時,需要將該開關配置為on"
    echo "26) 返回主選單"
    echo ""
    echo -e "${YELLOW}請輸入選項 (1-26):${NC}"
}

# MIPI 工具子選單
mipi_menu() {
    clear
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}          MIPI proc 訊息${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo ""
    echo "1) help : 打印MIPI相關的proc信息"
    echo "2) lane_[2/4] : MIPIPHY0固定為1X4LANE模式不可修改"
    echo "3) 讀取MIPIproc文件"
    echo "4) procmode_[0/1] : 調整訊息格式切換,默認調整訊息按照橫向排列"
    echo "5) 返回主選單"
    echo ""
    echo -e "${YELLOW}請輸入選項 (1-5):${NC}"
}

# 選項執行函式
execute_option() {
    local choice=$1
    
    case $choice in
        1)
            echo -e "${GREEN}正在執行ISP proc 訊息...${NC}"
            sleep 2
            ;;
        2)
            echo -e "${GREEN}正在執行 ISP proc 訊息...${NC}"
            sleep 2
            ;;
        3)
            echo -e "${GREEN}正在執行打印ISP當前使用的模組開關與參數...${NC}"
            sleep 2
            ;;
        4)
            echo -e "${GREEN}正在執行打印MIPI proc文件...${NC}"
            sleep 2
            ;;
        5)
            echo -e "${GREEN}先預留...${NC}"
            sleep 2
            ;;
        6)
            echo -e "${GREEN}先預留...${NC}"
            sleep 2
            ;;
        0)
            echo -e "${RED}退出程式${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}無效的選項，請重新選擇${NC}"
            sleep 2
            ;;
    esac
}

# 執行ISP proc 訊息選項
execute_isp_option() {
    local choice=$1
    
    case $choice in
        1)
            echo -e "${GREEN}help...${NC}"
            # python ../IQ\ Tool/image\ test/imageTuning.py
            echo help > /proc/driver/isp
            cat /proc/driver/isp
            sleep 2
            ;;
        2)
            echo -e "${GREEN}執行 nr3d...${NC}"
            # python ../IQ\ Tool/Math/gammaCheck.py
            sleep 2
            ;;
        3)
            echo -e "${GREEN}執行 nr3dcir...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;
        4)
            echo -e "${GREEN}執行 nr3decdc...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;        
        5)
            echo -e "${GREEN}執行 nr3dnoddr...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;    
        6)
            echo -e "${GREEN}執行 nr3ddep...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;        
        7)
            echo -e "${GREEN}執行 trace...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;   
        8)
            echo -e "${GREEN}執行 wdr...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;
        9)
            echo -e "${GREEN}執行 wdrcir...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;
        10)
            echo -e "${GREEN}執行 wdrciron...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;
        11)
            echo -e "${GREEN}執行 wdrecdc...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;
        12)
            echo -e "${GREEN}執行 addr...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;
        13)
            echo -e "${GREEN}執行 info...${NC}"
            echo info > /proc/driver/isp
            cat /proc/driver/isp
            sleep 2
            ;;
        14)
            echo -e "${GREEN}執行 mod...${NC}"
            echo mod > /proc/driver/isp
            cat /proc/driver/isp
            sleep 2
            ;;
        15)
            echo -e "${GREEN}執行 idle...${NC}"
            echo idle > /proc/driver/isp
            cat /proc/driver/isp
            sleep 2
            ;;
        16)
            echo -e "${GREEN}執行 colorbar...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;
        17)
            echo -e "${GREEN}執行 rst...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;
        18)
            echo -e "${GREEN}執行 autoreset...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;
        19)
            echo -e "${GREEN}執行 aelog...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;   
        20)
            echo -e "${GREEN}執行 awblog...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;; 
        21)
            echo -e "${GREEN}執行 ispoutnum...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;; 
        22)
            echo -e "${GREEN}執行 forcekick...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;; 
        23)
            echo -e "${GREEN}執行 vgs...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;   
        24)
            echo -e "${GREEN}執行 procmode...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;
        25)
            echo -e "${GREEN}執行 linearwdr...${NC}"
            # python ../IQ\ Tool/SSIM/ssim_check.py
            sleep 2
            ;;                                                                     
        26)
            return
            ;;
        *)
            echo -e "${RED}無效的選項${NC}"
            sleep 2
            ;;
    esac
}

# 執行 AI 選項
execute_mipi_option() {
    local choice=$1
    
    case $choice in
        1)
            echo -e "${GREEN}MIPI help...${NC}"
            # python ../ai/AI_Ap/gemini_1.py
            sleep 2
            ;;
        2)
            echo -e "${GREEN}lane...${NC}"
            sleep 2
            ;;
        3)
            echo -e "${GREEN}讀取 MIPI proc 文件...${NC}"
            sleep 2
            ;;
        4)
            echo -e "${GREEN}procmode...${NC}"
            sleep 2
            ;;
        5)
            return
            ;;
        *)
            echo -e "${RED}無效的選項${NC}"
            sleep 2
            ;;
    esac
}

# 主程式迴圈
main_loop() {
    while true; do
        main_menu
        read -r choice
        
        if [ "$choice" = "1" ]; then
            while true; do
                isp_menu
                read -r isp_choice
                
                if [ "$isp_choice" = "4" ]; then
                    break
                fi
                
                execute_isp_option "$isp_choice"
            done
        elif [ "$choice" = "2" ]; then
            while true; do
                mipi_menu
                read -r mipi_choice
                
                if [ "$mipi_choice" = "4" ]; then
                    break
                fi
                
                execute_mipi_option "$mipi_choice"
            done
        else
            execute_option "$choice"
        fi
        
        if [ "$choice" = "0" ]; then
            break
        fi
        
        echo ""
        echo -e "${YELLOW}按 Enter 繼續...${NC}"
        read -r
    done
}

# 執行主程式
main_loop
