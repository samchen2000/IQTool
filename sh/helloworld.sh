#!/bin/sh

# 定義選單項目
options=("Option 1: Show Date" "Option 2: List Files" "Option 3: Exit")

# 使用 select 建立選單
echo "請選擇一個選項:"
select opt in "${options[@]}"
do
    case $opt in
        "Option 1: Show Date")
            echo "現在日期和時間是:"
            date
            ;;
        "Option 2: List Files")
            echo "當前目錄檔案列表:"
            ls -l
            ;;
        "Option 3: Exit")
            echo "退出選單。"
            break # 結束 select 循環
            ;;
        *) # 處理無效輸入
            echo "無效選項 $REPLY。請重新選擇。"
            ;;
    esac
done