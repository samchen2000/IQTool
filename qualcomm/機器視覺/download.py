import os

# Sandbox 的檔案目錄
directory = "/mnt/data"

# 列出所有檔案
files = os.listdir(directory)

# 只保留檔案（排除資料夾）
files = [f for f in files if os.path.isfile(os.path.join(directory, f))]

if not files:
    print("目前 /mnt/data 沒有檔案")
else:
    print("以下是 /mnt/data 的檔案及下載鏈接：\n")
    for f in files:
        path = f"sandbox:/mnt/data/{f}"  # ChatGPT Sandbox 下載鏈接格式
        print(f"- [{f}]({path})")
