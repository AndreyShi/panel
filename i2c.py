import time
import math

try:
    # Пытаемся импортировать настоящий smbus2
    import smbus2
    print("✓ Настоящий smbus2 загружен (Raspberry Pi)")
    class i2c:
        def __init__(self, bus_number=1):
            self.bus = smbus2.SMBus(bus_number)
        def task_I2cbus(self, running):
            while running[0]:
                self.task_ADS1115()
                time.sleep(0.5)
        def task_ADS1115(self, address=0x48):            
            REG_CONVERSION = 0x00
            REG_CONFIG = 0x01
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
                
            config = (OS << 15) | (MUX << 12) | (PGA << 9) | (MODE << 8) | \
                        (DR << 5) | (COMP_MODE << 4) | (COMP_POL << 3) | \
                        (COMP_LAT << 2) | COMP_QUE
                
            # Записываем конфигурацию
            config_bytes = [config >> 8, config & 0xFF]
            self.bus.write_i2c_block_data(address, REG_CONFIG, config_bytes)
                
            # Ожидание преобразования
            time.sleep(0.01)
                
            # Чтение результата
            result = self.bus.read_i2c_block_data(address, REG_CONVERSION, 2)
            value = (result[0] << 8) | result[1]
                
            # Конвертация в напряжение
            voltage = (value * 2.048) / 32767.0
            
            # Рассчет подсоединенного  сопротивления в схеме делителя напряжения
            R2 = 430 * (voltage/(3.3 - voltage))
            print(f"I2c value: {value}, voltage: {voltage:.2f}, R2: {R2:.2f}")
except ImportError:
    # Создаем mock-версию smbus2
    class i2c:
        def __init__(self, bus_number=1):
            self.bus_number = bus_number
            self.devices = {}  # Виртуальные устройства I2C
            print(f"🖥 i2c: виртуальная шина {bus_number}")
        def task_I2cbus(self, running):
            while running[0]:
                self.task_ADS1115()
                time.sleep(1)
        def task_ADS1115(self, address=0x48):
                print(f"I2c value: {math.pi:.2f}, voltage: {math.pi:.2f}, R2: {math.pi:.2f}")