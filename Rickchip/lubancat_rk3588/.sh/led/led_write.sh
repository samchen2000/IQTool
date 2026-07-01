#!/bin/bash

# 檢查是否有輸入參數
if [ -z "$1" ]; then
	    echo "使用方式：$0 <亮度 0~21>"
	        exit 1
fi

TARGET="$1"

# 檢查是否為 0~21 的數字
# 先檢查是否為純數字
if ! echo "$TARGET" | grep -Eq '^[0-9]+$'; then
	    echo "錯誤：亮度必須是 0~21 的整數"
	        exit 1
fi

# 再檢查範圍
if [ "$TARGET" -lt 0 ] || [ "$TARGET" -gt 21 ]; then
	    echo "錯誤：亮度超出範圍，必須介於 0~21 之間"
	        exit 1
fi

set_and_check() {
	    LED_PATH="$1"

	        cd "$LED_PATH" || {
			        echo "無法進入目錄：$LED_PATH"
		        return 1
			    }

			        echo "$TARGET" | sudo tee brightness >/dev/null

				    VALUE=$(cat brightness | tr -d '\n')

				        if [ "$VALUE" != "$TARGET" ]; then
						        echo "$LED_PATH: 讀取數值與設定不同 (設定=$TARGET, 讀到=$VALUE)"
							        return 1
								    else
									            echo "$LED_PATH: 設定成功 (亮度=$VALUE)"
										            return 0
											        fi
											}

											# 對兩個 LED 操作，並記錄是否有錯
											ERROR=0

											set_and_check "/sys/class/leds/white:infrared" || ERROR=1
											set_and_check "/sys/class/leds/white:infrared_1" || ERROR=1

											exit $ERROR
