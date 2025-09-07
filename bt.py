import time
from threading import Event

try:
    #sudo apt-get update
    #sudo apt-get install bluetooth bluez python3-bluez
    #pip3 install pybluez obd
    import bluetooth
    import obd
    from obd import OBDCommand, Unit
    from obd.protocols import ISO_14230_4_5baud
    from obd.utils import bytes_to_int

    class ELM327Bluetooth:
        def __init__(self):
            self.connection = None
            self.obd_connection = None
            
        def discover_devices(self):
            """Поиск Bluetooth устройств"""
            print("Поиск Bluetooth устройств...")
            devices = bluetooth.discover_devices(lookup_names=True)
            
            for addr, name in devices:
                print(f"Найдено устройство: {name} - {addr}")
                if "ELM327" in name.upper() or "OBD" in name.upper():
                    print(f"Найден ELM327: {name}")
                    return addr
            return None
        
        def connect_to_elm327(self, device_address):
            """Подключение к ELM327"""
            try:
                # Подключение через RFCOMM (канал обычно 1)
                sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                sock.connect((device_address, 1))
                self.connection = sock
                print("Подключение установлено!")
                
                # Настройка OBD соединения
                self.setup_obd_connection()
                return True
                
            except Exception as e:
                print(f"Ошибка подключения: {e}")
                return False
        
        def setup_obd_connection(self):
            """Настройка OBD соединения"""
            try:
                # Создаем пользовательские команды для ISO27145-4
                self.setup_custom_commands()
                
                # Подключаемся через pyOBD
                ports = obd.scan_serial()
                if ports:
                    self.obd_connection = obd.OBD(ports[0], protocol="ISO_14230_4_5baud")
                    print("OBD соединение установлено!")
                else:
                    print("OBD порты не найдены")
                    
            except Exception as e:
                print(f"Ошибка настройки OBD: {e}")
        
        def setup_custom_commands(self):
            """Настройка пользовательских команд для ISO27145-4"""
            # Температура охлаждающей жидкости
            obd.commands.COOLANT_TEMP = OBDCommand(
                "COOLANT_TEMP", 
                "Temperature of the engine coolant", 
                b"0105", 
                1, 
                lambda data: data[0] - 40, 
                Unit.CELSIUS
            )
            
            # Обороты двигателя
            obd.commands.RPM = OBDCommand(
                "RPM",
                "Engine RPM",
                b"010C",
                2,
                lambda data: (data[0] * 256 + data[1]) / 4.0,
                Unit.RPM
            )
            
            # Check Engine (MIL)
            obd.commands.STATUS = OBDCommand(
                "STATUS",
                "Status since DTCs cleared",
                b"0101",
                4,
                lambda data: data[0],
                Unit.NONE
            )
            
            # Давление масла (может потребоваться адаптация под конкретный автомобиль)
            obd.commands.OIL_PRESSURE = OBDCommand(
                "OIL_PRESSURE",
                "Engine oil pressure",
                b"010C",  # Может отличаться для разных авто
                1,
                lambda data: data[0],
                Unit.KPA
            )
        
        def get_coolant_temp(self):
            """Получение температуры охлаждающей жидкости"""
            try:
                response = self.obd_connection.query(obd.commands.COOLANT_TEMP)
                if response.is_null():
                    return None
                return response.value.magnitude
            except:
                return None
        
        def get_rpm(self):
            """Получение оборотов двигателя"""
            try:
                response = self.obd_connection.query(obd.commands.RPM)
                if response.is_null():
                    return None
                return response.value.magnitude
            except:
                return None
        
        def get_check_engine(self):
            """Проверка Check Engine"""
            try:
                response = self.obd_connection.query(obd.commands.STATUS)
                if response.is_null():
                    return None
                
                # Бит 7 указывает на статус MIL (Check Engine)
                status_byte = response.value.magnitude
                mil_status = (status_byte & 0x80) != 0
                return mil_status
            except:
                return None
        
        def get_oil_pressure(self):
            """Получение давления масла"""
            try:
                # Для давления масла может потребоваться специфичная команда
                response = self.obd_connection.query(obd.commands.OIL_PRESSURE)
                if response.is_null():
                    # Альтернативная попытка
                    response = self.obd_connection.query(obd.commands.INTAKE_MAP)
                    if response.is_null():
                        return None
                return response.value.magnitude
            except:
                return None
        
        def read_data_continuously(self, stop_event:Event=None):
            """Непрерывное чтение данных"""
            print("Начинаем чтение данных...")
            if stop_event is None:
                stop_event = Event()
            
            while not stop_event.is_set():
                try:
                    # Температура охлаждающей жидкости
                    coolant_temp = self.get_coolant_temp()
                    if coolant_temp is not None:
                        print(f"Температура ОЖ: {coolant_temp}°C")
                    
                    # Обороты
                    rpm = self.get_rpm()
                    if rpm is not None:
                        print(f"Обороты: {rpm} об/мин")
                    
                    # Check Engine
                    check_engine = self.get_check_engine()
                    if check_engine is not None:
                        status = "ВКЛ" if check_engine else "ВЫКЛ"
                        print(f"Check Engine: {status}")
                    
                    # Давление масла
                    oil_pressure = self.get_oil_pressure()
                    if oil_pressure is not None:
                        print(f"Давление масла: {oil_pressure} kPa")
                    
                    print("-" * 40)
                    stop_event.wait(2)
                    
                except KeyboardInterrupt:
                    print("\nОстановка...")
                    stop_event.set()
                except Exception as e:
                    print(f"Ошибка чтения: {e}")
                    stop_event.wait(1)
        
        def close_connection(self):
            """Закрытие соединения"""
            if self.connection:
                self.connection.close()
            if self.obd_connection:
                self.obd_connection.close()
            print("Соединения закрыты")
        
        def task_ELM327BL(self, stop_event:Event):        
            try:
                # Поиск устройства
                device_addr = self.discover_devices()
                
                if device_addr:
                    # Подключение
                    if self.connect_to_elm327(device_addr):
                        # Чтение данных
                        self.read_data_continuously(stop_event)
                    else:
                        print("Не удалось подключиться к ELM327")
                else:
                    print("ELM327 не найден")
                    
            except KeyboardInterrupt:
                print("\nПрограмма остановлена")
            finally:
                self.close_connection()
    # Основная программа
    if __name__ == "__main__":
        elm = ELM327Bluetooth()
        
        try:
            # Поиск устройства
            device_addr = elm.discover_devices()
            
            if device_addr:
                # Подключение
                if elm.connect_to_elm327(device_addr):
                    # Чтение данных
                    elm.read_data_continuously()
                else:
                    print("Не удалось подключиться к ELM327")
            else:
                print("ELM327 не найден")
                
        except KeyboardInterrupt:
            print("\nПрограмма остановлена")
        finally:
            elm.close_connection()
except ImportError:
    #pip install obd pyserial
    import obd
    import time
    from obd import OBDCommand, Unit
    import serial.tools.list_ports
    class ELM327Bluetooth:
        def __init__(self):
            self.connection = None
        
        def find_bluetooth_com_port(self):
            """Поиск COM порта Bluetooth ELM327"""
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                print(f"Порт: {port.device} - {port.description}")
                # Ищем Bluetooth COM порты
                if ("Bluetooth" in port.description or 
                    "COM" in port.device and 
                    ("ELM327" in port.description.upper() or 
                    "OBD" in port.description.upper() or
                    "SPP" in port.description)):
                    print(f"Найден Bluetooth ELM327 на порту: {port.device}")
                    return "COM3"
            return None
        
        def connect_via_bluetooth(self, com_port):
            """Подключение через Bluetooth COM порт"""
            try:
                print(f"Подключение через виртуальный COM порт Bluetooth {com_port} ")
                self.connection = obd.OBD(com_port, baudrate=500000, protocol="6",timeout=15)
                
                if self.connection.is_connected():
                    print("Bluetooth подключение установлено!")
                    print(f"Адаптер: {self.connection.port_name()}")
                    print(f"Протокол: {self.connection.protocol_name()}")
                    return True
                else:
                    print("Не удалось подключиться по Bluetooth")
                    return False
                    
            except Exception as e:
                print(f"Ошибка Bluetooth подключения: {e}")
                return False
        
        def get_obd_data(self):
            """Получение всех данных"""
            data = {}
            
            try:
                # Температура охлаждающей жидкости
                response = self.connection.query(obd.commands.COOLANT_TEMP)
                if not response.is_null():
                    data['coolant_temp'] = response.value.magnitude
                
                # Обороты двигателя
                response = self.connection.query(obd.commands.RPM)
                if not response.is_null():
                    data['rpm'] = response.value.magnitude
                
                # Статус Check Engine
                response = self.connection.query(obd.commands.STATUS)
                if not response.is_null():
                    status_byte = response.value.magnitude
                    data['check_engine'] = (status_byte & 0x80) != 0
                
                # Попытка получить давление масла (разные PID)
                oil_pids = [obd.commands.OIL_PRESSURE, obd.commands.INTAKE_MAP]
                for pid in oil_pids:
                    try:
                        response = self.connection.query(pid)
                        if not response.is_null():
                            data['oil_pressure'] = response.value.magnitude
                            break
                    except:
                        continue
                        
            except Exception as e:
                print(f"Ошибка чтения данных: {e}")
                
            return data
        
        def monitor_data(self, stop_event:Event=None):
            """Мониторинг данных в реальном времени"""
            print("Мониторинг данных OBD2...")
            print("Нажмите Ctrl+C для остановки")
            print("-" * 50)
            if stop_event is None:
                stop_event = Event()
            
            try:
                while not stop_event.is_set():
                    data = self.get_obd_data()
                    
                    print(f"Температура ОЖ: {data.get('coolant_temp', 'N/A')}°C")
                    print(f"Обороты: {data.get('rpm', 'N/A')} об/мин")
                    
                    check_engine = data.get('check_engine')
                    if check_engine is not None:
                        print(f"Check Engine: {'ВКЛ' if check_engine else 'ВЫКЛ'}")
                    else:
                        print("Check Engine: N/A")
                    
                    oil_pressure = data.get('oil_pressure')
                    if oil_pressure is not None:
                        print(f"Давление: {oil_pressure} kPa")
                    else:
                        print("Давление масла: N/A")
                    
                    print("-" * 30)
                    stop_event.wait(2)
                    
            except KeyboardInterrupt:
                print("\nОстановка мониторинга...")
        
        def close(self):
            """Закрытие соединения"""
            if self.connection:
                self.connection.close()
                print("Соединение закрыто")
        
        def task_ELM327BL(self, stop_event:Event):
            try:
                # Поиск Bluetooth порта
                com_port = self.find_bluetooth_com_port()
                
                if com_port:
                    # Подключение
                    if self.connect_via_bluetooth(com_port):
                        # Запуск мониторинга
                        self.monitor_data(stop_event)
                    else:
                        print("Не удалось подключиться. Проверьте:")
                        print("1. Bluetooth включен на ПК и адаптере")
                        print("2. Адаптер сопряжен с Windows")
                        print("3. Зажигание включено")
                else:
                    print("Bluetooth ELM327 не найден!")
                    print("Выполните сопряжение вручную:")
                    print("1. Откройте настройки Bluetooth")
                    print("2. Найдите устройство 'ELM327' или 'OBD'")
                    print("3. Сопрягите (пароль обычно 1234)")
                    print("4. Запустите программу снова")
                    
            except Exception as e:
                print(f"Ошибка: {e}")
            finally:
                self.close()

    # Основная программа
    if __name__ == "__main__":
        obd_reader = ELM327Bluetooth()
        
        try:
            # Поиск Bluetooth порта
            com_port = obd_reader.find_bluetooth_com_port()
            
            if com_port:
                # Подключение
                if obd_reader.connect_via_bluetooth(com_port):
                    # Запуск мониторинга
                    obd_reader.monitor_data()
                else:
                    print("Не удалось подключиться. Проверьте:")
                    print("1. Bluetooth включен на ПК и адаптере")
                    print("2. Адаптер сопряжен с Windows")
                    print("3. Зажигание включено")
            else:
                print("Bluetooth ELM327 не найден!")
                print("Выполните сопряжение вручную:")
                print("1. Откройте настройки Bluetooth")
                print("2. Найдите устройство 'ELM327' или 'OBD'")
                print("3. Сопрягите (пароль обычно 1234)")
                print("4. Запустите программу снова")
                
        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            obd_reader.close()

