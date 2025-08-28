import time
import threading
import queue
from i2c  import *
from uart import *


def polling(func):
    # Теперь smbus2 доступен в любой системе
    I2cBus = smbus2.SMBus(1)  # Работает и на Pi, и на Windows
    UartBus = GPSReader()
    while func():
        value, voltage = I2cBus.read_differential_a0_a1()
        print("I2c value: ",value,"voltage: ",voltage)
        speed = UartBus.get_speed()
        print(f"Uart Скорость: {speed:.1f} км/ч" if speed else "Uart Ошибка чтения")
        time.sleep(1)