try:
    import serial
    class GPSReader:
        def __init__(self, port='/dev/ttyS0'):
            self.ser = serial.Serial(port, 9600, timeout=2)  # Увеличили timeout
            self.ser.flushInput()
            print(f"GPSReader инициализирован на порту {port}")
        
        def get_speed(self):
            """Чтение скорости с диагностикой"""
            try:
                # Читаем сырые данные
                raw_data = self.ser.readline()
                if not raw_data:
                    print("Нет данных от порта (пустой readline)")
                    return None
                
                # Декодируем
                try:
                    line = raw_data.decode('utf-8', errors='ignore').strip()
                except UnicodeDecodeError:
                    print("Ошибка декодирования UTF-8")
                    return None
                
                if not line:
                    print("Получена пустая строка")
                    return None
                    
                print(f"Получено: {line}")  # Диагностика
                
                # Парсим только GPRMC
                if line.startswith('$GPRMC'):
                    parts = line.split(',')
                    print(f"Части: {parts}")  # Диагностика
                    
                    # Проверяем длину и статус
                    if len(parts) < 8:
                        print("Слишком мало полей в GPRMC")
                        return None
                    
                    if parts[2] != 'A':
                        print(f"Невалидные данные, статус: {parts[2]}")
                        return None
                    
                    # Проверяем поле скорости
                    if not parts[7]:
                        print("Поле скорости пустое")
                        return None
                    
                    # Пытаемся конвертировать
                    try:
                        speed_knots = float(parts[7])
                        speed_kmh = speed_knots * 1.852
                        print(f"Успешно: {speed_kmh:.1f} км/ч")
                        return speed_kmh
                    except ValueError:
                        print(f"Ошибка конвертации скорости: {parts[7]}")
                        return None
                
                else:
                    print(f"Не GPRMC: {line[:10]}...")
                    return None
                    
            except Exception as e:
                print(f"Исключение в get_speed: {e}")
                return None
        
        def debug_read_all(self, duration=10):
            """Чтение всех данных для диагностики"""
            print(f"\nЧтение всех данных в течение {duration} секунд:")
            start_time = time.time()
            
            while time.time() - start_time < duration:
                try:
                    raw_data = self.ser.readline()
                    if raw_data:
                        line = raw_data.decode('utf-8', errors='ignore').strip()
                        print(f"RAW: {line}")
                except:
                    pass
            
            print("Диагностика завершена\n")
        
        def close(self):
            if self.ser.is_open:
                self.ser.close()
                print("Порт закрыт")
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
        def debug_read_all(self, duration=10):
            return False
        