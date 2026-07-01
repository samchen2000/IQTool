#!/usr/bin/env bash

# 預設 device 前綴
DEV_PREFIX="/dev/v4l-subdev"

# 讀取 device 編號
read -p "請輸入 subdev 編號 (例如 2 代表 ${DEV_PREFIX}2): " dev_id
DEV="${DEV_PREFIX}${dev_id}"

echo "使用裝置: ${DEV}"
echo

# 檢查裝置是否存在
if [ ! -e "$DEV" ]; then
    echo "裝置 ${DEV} 不存在，請確認後再試。"
    exit 1
fi

# 主選單
PS3="請選擇要設定的 control (輸入數字): "
options=(
    "exposure"
    "gain_automatic"
    "auto_exposure"
    "analogue_gain"
    "digital_gain"
    "IR_LED_ON"
    "自動設定"
    "離開"
)

select opt in "${options[@]}"; do
    case "$opt" in
        "exposure")
            read -p "請輸入 exposure 整數值: " val
            v4l2-ctl -d "$DEV" --set-ctrl "exposure=${val}"
            ;;

        "gain_automatic")
            echo "0 = 關閉自動增益, 1 = 開啟自動增益"
            read -p "請輸入 gain_automatic (0 或 1): " val
            v4l2-ctl -d "$DEV" --set-ctrl "gain_automatic=${val}"
            ;;

        "auto_exposure")
            echo "請依據你的 sensor 驅動定義輸入模式值 (例如 0/1)。"
            read -p "請輸入 auto_exposure 整數值: " val
            v4l2-ctl -d "$DEV" --set-ctrl "auto_exposure=${val}"
            ;;

        "analogue_gain")
            read -p "請輸入 analogue_gain 整數值: " val
            v4l2-ctl -d "$DEV" --set-ctrl "analogue_gain=${val}"
            ;;

        "digital_gain")
            read -p "請輸入 digital_gain 整數值: " val
            v4l2-ctl -d "$DEV" --set-ctrl "digital_gain=${val}"
            ;;

        "IR_LED_ON")
            cd /sys/class/leds/white:infrared
	    echo 21 | sudo tee brightness
	    cd /sys/class/leds/white:infrared_1
	    echo 21 | sudo tee brightness
            ;;
            
        "自動設定")
            v4l2-ctl -d /dev/v4l-subdev2 --set-ctrl "gain_automatic=0,auto_exposure=1,analogue_gain=128,exposure=500,digital_gain=1024"	
            sleep 2
            v4l2-ctl -d /dev/v4l-subdev7 --set-ctrl "gain_automatic=0,auto_exposure=1,analogue_gain=128,exposure=500,digital_gain=1024"
            sleep 2
            v4l2-ctl -d /dev/v4l-subdev2 --get-ctrl 'exposure,analogue_gain,auto_exposure,digital_gain,gain_automatic'
            v4l2-ctl -d /dev/v4l-subdev7 --get-ctrl 'exposure,analogue_gain,auto_exposure,digital_gain,gain_automatic'
            ;;       

    	"離開")
            echo "結束。"
            break
            ;;

        *)
            echo "無效選項：$REPLY"
            ;;
    esac

    echo
    echo "目前控制項狀態："
    v4l2-ctl -d "$DEV" --list-ctrls
    echo
done

