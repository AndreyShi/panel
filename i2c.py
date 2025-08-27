from typing import Optional, Callable

# Условный импорт smbus2 с заглушкой
try:
    # Пытаемся импортировать настоящий smbus2
    import smbus2
    HAS_REAL_HARDWARE = True
    print("✓ Настоящий smbus2 загружен (Raspberry Pi)")
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
    
    # Создаем mock-модуль smbus2
    class MockSMBusModule:
        def SMBus(self, bus_number: int):
            return MockSMBus(bus_number)
    
    smbus2 = MockSMBusModule()