import time
import math
from queue import Queue, Full 
from collections import deque
import threading
import random
from datetime import datetime
from threading import Event
from typing import List

try:
    # Пытаемся импортировать настоящий smbus2
    import smbus2
    print("✓ Настоящий smbus2 загружен (Raspberry Pi)")
    class i2c:
        def __init__(self, bus_number=1):
            self.bus = smbus2.SMBus(bus_number)
            self.lock = threading.Lock()

        def read_adc(self, config, address):
            with self.lock:    # блокируем доступ к шине
                REG_CONVERSION = 0x00
                REG_CONFIG = 0x01                               
                config_bytes = [config >> 8, config & 0xFF]
                self.bus.write_i2c_block_data(address, REG_CONFIG, config_bytes)
                time.sleep(0.01)# ждем преобразования АЦП
                result = self.bus.read_i2c_block_data(address, REG_CONVERSION, 2)
                value = (result[0] << 8) | result[1]
                return value    # разблокируем доступ к шине, в этот момент другой поток приступит к работе с шиной
        def task_ADS1115(self, stop_event:Event, que:List[Queue]):
            # Настройка конфигурации
            OS = 1        # Однократное преобразование
            # Дифференциальные режимы:
            #MUX = 0b000  # AIN0 vs AIN1 (дифф)
            #MUX = 0b001  # AIN0 vs AIN3 (дифф)
            #MUX = 0b010  # AIN1 vs AIN3 (дифф)
            #MUX = 0b011  # AIN2 vs AIN3 (дифф)
            # Single-Ended режимы:
            #MUX = 0b100  # AIN0 vs GND
            #MUX = 0b101  # AIN1 vs GND  
            #MUX = 0b110  # AIN2 vs GND
            #MUX = 0b111  # AIN3 vs GND
            MUX = 0b100   # AIN0 vs AIN1 
            # Константы усиления
            #PGA_6_144V = 0b000   # ±6.144V
            #PGA_4_096V = 0b001   # ±4.096V  
            #PGA_2_048V = 0b010   # ±2.048V (по умолчанию)
            #PGA_1_024V = 0b011   # ±1.024V
            #PGA_0_512V = 0b100   # ±0.512V
            #PGA_0_256V = 0b101   # ±0.256V
            PGA = 0b010   # ±2.048V
            MODE = 1      # Однократный режим
            DR = 0b100    # 128 SPS
            COMP_MODE = 0 # Традиционный компаратор
            COMP_POL = 0  # Активный низкий
            COMP_LAT = 0  # Не фиксировать
            COMP_QUE = 0b11 # Отключить компаратор                
            config = (OS << 15) | (MUX << 12) | (PGA << 9) | (MODE << 8) | (DR << 5) | (COMP_MODE << 4) | (COMP_POL << 3) | (COMP_LAT << 2) | COMP_QUE    
            # очередь для усреднения
            deq = deque(maxlen=5)

            while not stop_event.is_set():
                value = self.read_adc(config, 0x48)
                voltage = (value * 2.048) / 32767.0     # Конвертация в напряжение
                R2 = 430 * (voltage / (3.3 - voltage))  # Рассчет подсоединенного  сопротивления в схеме делителя напряжения
                deq.append(R2)
                R2_avg = sum(deq) / len(deq)
                #print(f"I2c value: {value}, voltage: {voltage:.3f}, R2: {R2:.3f}, R2_avg: {R2_avg:.3f}")
                if R2_avg >= 300:
                    R2_avg = 300
                elif R2_avg <= 0:
                     R2_avg = 0.2
                try:
                    que[0].put(R2_avg, timeout=1.0)                      #если что ждем бесконечно потомучто в отдельном потоке
                except Full:
                    print(f"Очередь que[0] переполнена, данные R2_avg: {R2_avg} потеряны") 
except ImportError:
    # Создаем mock-версию smbus2
    class i2c:
        def __init__(self, bus_number=1):
            self.bus_number = bus_number
            self.devices = {}  # Виртуальные устройства I2C
            print(f"🖥 i2c: виртуальная шина {bus_number}")
        def task_ADS1115(self, stop_event:Event, que:List[Queue]):
            toup_R2 = True
            R2 = 1  
            while not stop_event.is_set():
                if toup_R2:  # Движение вверх
                    R2 += 1 #random.uniform(0.0, 13.0)
                    if R2 >= 300:
                        R2 = 300
                        toup_R2 = False  # достигли верха - идем вниз
                else:        # Движение вниз
                    R2 -= 1  #random.uniform(0.0, 3.0)
                    if R2 <= 0:
                        R2 = 0.2
                        toup_R2 = True   # достигли низа - идем вверх
                #print(f"R2:  {R2:.2f}")
                try:             
                    que[0].put(R2, timeout=1.0)
                except Full:
                    print(f"Очередь que[0] переполнена, данные R2: {R2} потеряны") 
                #print(f"put {R2:.3f} {datetime.now().strftime("%S.%f")[:-3]}")
                