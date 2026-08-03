import os
import numpy as np


def verify_and_read_pure_raw(file_path):
    # 1. 定義您的感測器原始參數
    WIDTH = 3264
    HEIGHT = 2448
    BYTES_PER_PIXEL = 2  # 16-bit 封裝佔用 2 個位元組

    # 計算理論上應有的檔案大小
    EXPECTED_SIZE = WIDTH * HEIGHT * BYTES_PER_PIXEL  # 15980544 Bytes

    # 檢查檔案是否存在
    if not os.path.exists(file_path):
        print(f"❌ 錯誤：找不到檔案 {file_path}")
        return False

    # 獲取實際檔案大小
    actual_size = os.path.getsize(file_path)

    print("================== 階段一：檔案大小精確比對 ==================")
    print(f"理論預期大小: {EXPECTED_SIZE} Bytes (約 {EXPECTED_SIZE / (1024*1024):.2f} MB)")
    print(f"實際檔案大小: {actual_size} Bytes (約 {actual_size / (1024*1024):.2f} MB)")

    # 進行精確判定
    if actual_size != EXPECTED_SIZE:
        print("❌ 比對失敗！檔案大小不相符。")
        print("💡 可能原因：檔案可能損壞，或者該 16-bit RAW 檔案內含其他 Metadata 檔頭。")
        return False

    print("✅ 比對成功！該檔案大小完全符合 3264x2448 16bit 的純數據規格。")

    print("\n================== 階段二：解構 BGGR 排列數據 ==================")
    try:
        # 使用 numpy 直接讀取二進位資料 (16bit 使用 uint16)
        raw_data = np.fromfile(file_path, dtype=np.uint16)

        # 將一維陣列重塑 (Reshape) 為二維影像矩陣
        bayer_matrix = raw_data.reshape((HEIGHT, WIDTH))
        print(f"成功將數據還原為 2D 矩陣，形狀為: {bayer_matrix.shape}")

        # 📌 根據您的 BGGR 格式進行 2x2 矩陣精確切片：
        # 排列方式為：
        # [ B   GR ]
        # [ GB   R ]
        ch_B = bayer_matrix[0::2, 0::2]  # 偶數行，偶數列
        ch_GR = bayer_matrix[0::2, 1::2]  # 偶數行，奇數列
        ch_GB = bayer_matrix[1::2, 0::2]  # 奇數行，偶數列
        ch_R = bayer_matrix[1::2, 1::2]  # 奇數行，奇數列

        print("\n--- 成功提取物理通道像素數值 (左上角第一個點) ---")
        print(f"藍色通道 (B)   數值: {ch_B[0, 0]}")
        print(f"綠色通道 (GR)  數值: {ch_GR[0, 0]}")
        print(f"綠色通道 (GB)  數值: {ch_GB[0, 0]}")
        print(f"紅色通道 (R)   數值: {ch_R[0, 0]}")

        # 輸出矩陣最大最小值以驗證資料有效性 (16bit 最大理論值為 65535)
        print(f"\n矩陣數值區間: 最小值 = {bayer_matrix.min()}, 最大值 = {bayer_matrix.max()}")
        return True

    except Exception as e:
        print(f"❌ 讀取時發生未預期錯誤: {str(e)}")
        return False


# ====== 測試執行 ======
if __name__ == "__main__":
    # 📌 請在此替換成您實際的 RAW 檔案路徑
    target_raw_file = "./image/MC635X_raw_3264_2448_BGGR_16bit_20260722172259_dcOut_A_10bit.raw"

    verify_and_read_pure_raw(target_raw_file)
