# 查看機器基本資訊
import machine
import gc
import os

# 查看 CPU 運行速率（Hz）
cpu_freq = machine.freq() / 1000 / 1000  # 轉換為 MHz

# 查看記憶體使用狀況
gc.collect()  # 手動垃圾回收，獲取準確的記憶體使用狀況
free_memory = gc.mem_free() / 1024  # 可用記憶體，轉換為 KB
allocated_memory = gc.mem_alloc() / 1024  # 已分配記憶體，轉換為 KB

# 查看 Flash 空間大小
fs_stat = os.statvfs('/')
total_flash = fs_stat[0] * fs_stat[2] / 1024 / 1024  # 總共的 Flash 空間，轉換為 MB
free_flash = fs_stat[0] * fs_stat[3] / 1024  / 1024  # 可用的 Flash 空間，轉換為 MB

# 獲取機器的 UID
uid = machine.unique_id()
# 將 UID 轉換為十六進位表示並格式化為字符串
uid_str = ':'.join(f'{b:02x}' for b in uid)

print(f"CPU 運算頻率: {cpu_freq:.2f} MHz")
print(f"可用記憶體: {free_memory:.2f} KB")
print(f"已分配的記憶體: {allocated_memory:.2f} KB")
print(f"全部 Flash 空間: {total_flash:.2f} MB")
print(f"可用 Flash 空間: {free_flash:.2f} MB")
print(f"機器的 UID: {uid_str}")
