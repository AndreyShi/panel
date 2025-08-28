import time
import threading
import queue
from i2c import *


def polling(func):
    # Теперь smbus2 доступен в любой системе
    I2cBus = smbus2.SMBus(1)  # Работает и на Pi, и на Windows
    while func():
        value, voltage = I2cBus.read_differential_a0_a1()
        print("value: ",value,"voltage: ",voltage)
        time.sleep(1)