import time
import threading
import queue
from i2c import *


def polling(func):
    # Теперь smbus2 доступен в любой системе
    bus = smbus2.SMBus(1)  # Работает и на Pi, и на Windows
    while func():
        bus.read_byte_data(1,2)
        time.sleep(1)