from typing import Optional, Callable

# Условный импорт smbus2 с заглушкой
try:
    # Пытаемся импортировать настоящий smbus2
    import smbus2
    from smbus2 import SMBus
    import time
    HAS_REAL_HARDWARE = True
    print("✓ Настоящий smbus2 загружен (Raspberry Pi)")
    class ADS1115:
        def __init__(self, bus_number=1, address=0x48):
            self.bus = SMBus(bus_number)
            self.address = address
            self.REG_CONVERSION = 0x00
            self.REG_CONFIG = 0x01
            
        def read_differential_a0_a1(self):
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
            MUX = 0b100   # AIN0 vs AIN1 (дифференциальный)
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
            self.bus.write_i2c_block_data(self.address, self.REG_CONFIG, config_bytes)
            
            # Ожидание преобразования
            time.sleep(0.01)
            
            # Чтение результата
            result = self.bus.read_i2c_block_data(self.address, self.REG_CONVERSION, 2)
            value = (result[0] << 8) | result[1]
            
            # Конвертация в напряжение
            voltage = (value * 2.048) / 32767.0
            
            return value, voltage
    # Создаем модуль ADS1115
    class ADS1115module:
        def SMBus(self, bus_number: int):
            return ADS1115(bus_number)
    smbus2 = ADS1115module()
except ImportError:
    # Заглушка для Windows и других систем
    HAS_REAL_HARDWARE = False
    print("⚠ smbus2 недоступен, используется эмуляция")
    
    # Создаем mock-версию smbus2
    class MockSMBus:
        def __init__(self, bus_number: int):
            self.bus_number = bus_number
            self.devices = {}  # Виртуальные устройства I2C
            print(f"🖥 MockSMBus: виртуальная шина {bus_number}")
        
        def write_byte_data(self, address: int, register: int, value: int):
            """Имитация записи данных в устройство"""
            device_key = f"dev_0x{address:02X}"
            if device_key not in self.devices:
                self.devices[device_key] = {}
            
            self.devices[device_key][register] = value
            print(f"📝 Mock запись: адрес 0x{address:02X}, регистр 0x{register:02X}, значение 0x{value:02X}")
        
        def read_byte_data(self, address: int, register: int) -> int:
            """Имитация чтения данных из устройства"""
            device_key = f"dev_0x{address:02X}"
            value = self.devices.get(device_key, {}).get(register, 0x00)
            print(f"📖 Mock чтение: адрес 0x{address:02X}, регистр 0x{register:02X} → 0x{value:02X}")
            return value
        
        def close(self):
            """Имитация закрытия соединения"""
            print("🔒 MockSMBus: соединение закрыто")

        def read_differential_a0_a1(self):
            return 7, 7
    
    # Создаем mock-модуль smbus2
    class MockSMBusModule:
        def SMBus(self, bus_number: int):
            return MockSMBus(bus_number)
    
    smbus2 = MockSMBusModule()