from machine import I2C, Pin
import time
import struct

# MPU6050 I2C 位址
MPU6050_ADDR = 0x68

# MPU6050 暫存器
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43

# 初始化 I2C（I2C0）
i2c = I2C(0, scl=Pin(0), sda=Pin(1), freq=400000)

# 喚醒 MPU6050（預設為睡眠模式）
i2c.writeto_mem(MPU6050_ADDR, PWR_MGMT_1, b'\x00')

def read_raw_data(addr):
    """讀取兩個 byte 並轉成有號整數"""
    high = i2c.readfrom_mem(MPU6050_ADDR, addr, 1)[0]
    low = i2c.readfrom_mem(MPU6050_ADDR, addr + 1, 1)[0]
    value = (high << 8) | low
    if value > 32768:
        value -= 65536
    return value

while True:
    # 讀取加速度原始值
    acc_x = read_raw_data(ACCEL_XOUT_H)
    acc_y = read_raw_data(ACCEL_XOUT_H + 2)
    acc_z = read_raw_data(ACCEL_XOUT_H + 4)

    # 讀取陀螺儀原始值
    gyro_x = read_raw_data(GYRO_XOUT_H)
    gyro_y = read_raw_data(GYRO_XOUT_H + 2)
    gyro_z = read_raw_data(GYRO_XOUT_H + 4)

    # 轉換成實際單位
    # 加速度 ±2g → 16384 LSB/g
    ax = acc_x / 16384.0
    ay = acc_y / 16384.0
    az = acc_z / 16384.0

    # 陀螺儀 ±250°/s → 131 LSB/(°/s)
    gx = gyro_x / 131.0
    gy = gyro_y / 131.0
    gz = gyro_z / 131.0

    print("加速度 (g)")
    print("X: {:.2f}  Y: {:.2f}  Z: {:.2f}".format(ax, ay, az))

    print("角速度 (°/s)")
    print("X: {:.2f}  Y: {:.2f}  Z: {:.2f}".format(gx, gy, gz))
    print("-" * 40)

    time.sleep(1)
