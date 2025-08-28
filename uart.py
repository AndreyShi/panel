try:
    import serial
    class GPSReader:
        def __init__(self, port='/dev/ttyS0'):
            self.ser = serial.Serial(port, 9600, timeout=1)
            self.ser.flushInput()
            print(f"Реальный GPSReader инициализирован на порту {port}")
        
        def get_speed(self):
            """Чтение скорости без переоткрытия порта"""
            try:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith('$GPRMC'):
                    parts = line.split(',')
                    if len(parts) > 7 and parts[2] == 'A' and parts[7]:
                        return float(parts[7]) * 1.852
            except:
                pass
            return None
        
        def close(self):
            """Закрытие порта"""
            if self.ser.is_open:
                self.ser.close()
                print("Реальный порт закрыт")

except ImportError:
    # Заглушка для случая, когда serial не установлен
    import time
    import random
    
    class GPSReader:
        def __init__(self, port='/dev/ttyS0'):
            self.port = port
            self.is_open = True
            print(f"Заглушка GPSReader инициализирована на порту {port}")
        
        def get_speed(self):
            """Имитация чтения скорости"""
            if not self.is_open:
                return None
            
            # Имитация задержки GPS модуля
            time.sleep(0.5)
            
            # С вероятностью 70% возвращаем случайную скорость
            # С вероятностью 30% возвращаем None (имитация потери сигнала)
            if random.random() < 0.7:
                # Случайная скорость от 0 до 120 км/ч
                speed_kmh = random.uniform(0, 120)
                #print(f"Заглушка: возвращаем скорость {speed_kmh:.1f} км/ч")
                return speed_kmh
            else:
                #print("Заглушка: сигнал GPS потерян")
                return None
        
        def close(self):
            """Закрытие заглушки"""
            self.is_open = False
            print("Заглушка порта закрыта")