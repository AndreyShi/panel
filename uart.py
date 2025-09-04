import time
import serial
import platform
from threading import Event

class uart:
    def __init__(self):
        system = platform.system()
        port = ''
        if system == "Windows":
            port = 'COM5'
        elif system == "Linux":
            port = '/dev/ttyS0'

        try:
            self.ser = serial.Serial(port, 9600, timeout=0.1)  #0.1 для каждого символа
            self.buffer = ""
            print(f"GPSReader инициализирована на порту {port}")
        except serial.SerialException as e:
            print(f"Ошибка открытия порта {port}: {e}")
            self.ser = None
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            self.ser = None
        
    def task_GPSReader(self, stop_event:Event):
        while not stop_event.is_set() and self.ser is not None:
            data = self.ser.read(self.ser.in_waiting or 1).decode('ascii', errors='ignore')
            self.buffer += data

            lines = self.buffer.splitlines(keepends=True) # Делим, сохраняя символы \n
            for line in lines:
                if line.endswith('\n'):
                    # Нашли целую строку
                    full_line = line.strip()
                    if full_line.startswith('$GPRMC') and self.validate_checksum(full_line):
                        print(full_line)
                        #break
                else:
                    # Последняя строка без \n - это начало новой, неполной строки.
                    buffer = line
                    break
            else:
                # Если for не нашел ни одной полной строки, очищаем буфер
                # (или оставляем его, если ожидаются очень длинные строки)
                buffer = ""
            stop_event.wait(0.5)
        return None
        
    def close(self):
        print("порт закрыт")
    def debug_read_all(self, duration=10):
        return False
    def validate_checksum(self,nmea_sentence: str) -> bool:
        # Проверяем базовую структуру строки
        if not nmea_sentence.startswith('$') or '*' not in nmea_sentence:
            return False

        try:
            # Разделяем строку на данные и контрольную сумму
            data_part, checksum_received = nmea_sentence.split('*', 1)
            # Убираем начальный '$' и вычисляем XOR для оставшейся части
            data_to_check = data_part[1:]
            
            # Инициализируем нулем
            calculated_checksum = 0
            # Последовательно применяем XOR к каждому символу
            for char in data_to_check:
                calculated_checksum ^= ord(char)
            
            # Преобразуем вычисленную сумму в hex, обрезаем '0x' и делаем верхний регистр
            # Добавляем ведущий ноль, если результат однозначный
            calculated_checksum_hex = f"{calculated_checksum:02X}"
            
            # Сравниваем с полученной контрольной суммой (первые 2 символа после '*')
            # Обрезаем до 2 символов на случай, если в строке есть мусор
            return calculated_checksum_hex == checksum_received[0:2]
            
        except (ValueError, IndexError):
            # Если что-то пошло не так при разборе (например, нет данных после '*')
            return False
        