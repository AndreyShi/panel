import time
from threading import Event, Lock
from queue import Queue, Full 
from typing import List
import subprocess
import time
import os
'''
Параметр	            Рекомендуемый интервал	Частота
RPM, SPEED	            100-500 ms	            2-10 Hz
COOLANT_TEMP, THROTTLE	500-2000 ms	            0.5-2 Hz
FUEL_LEVEL, VOLTAGE	    2000-5000 ms	        0.2-0.5 Hz
STATUS, DTC	            5000-10000 ms	        0.1-0.2 Hz
OIL_PRESSURE	        10000-30000 ms	        0.03-0.1 Hz
'''
try:
    #sudo apt-get update
    #sudo apt-get install bluetooth bluez python3-bluez
    #pip3 install pybluez obd
    # Создание виртуального окружения
    # python3 -m venv obd_env
    # Активация окружения
    # source obd_env/bin/activate
    # Установка библиотеки в виртуальное окружение
    #pip install obd
    # Деактивация (когда закончите работу)
    # deactivate
    import bluetooth
    import obd
    from obd import OBDCommand, Unit
    from obd.protocols import ISO_14230_4_5baud
    from obd.utils import bytes_to_int

    class ELM327Bluetooth:
        def __init__(self, threads_manager=False):
            self.connection = None
            self.obd_connection = None
            self.connection_ok = False
            self.lock = Lock()
            print("Linux ELM327Bluetooth")
            if threads_manager == True:
                #device_addr = self.discover_devices()
                device_addr = "00:1D:A5:06:04:CB"                    
                if device_addr:
                    self.connection_ok = self.connect_to_elm327(device_addr)
                else:
                    print("не найдено OBD2 устройство")            
        def safe_obd_query(self, command):
            with self.lock:
                response = self.obd_connection.query(command)
                return response
        def task_COOLANT_TEMP(self, stop_event:Event, queues_dict):          
            if self.connection_ok == False:
                toup_oj_temp = True
                oj_temp = 0
                while not stop_event.is_set():
                    if toup_oj_temp:  # Движение вверх
                        oj_temp += 1 #random.uniform(0.0, 13.0)
                        if oj_temp >= 99:
                            oj_temp = 99
                            toup_oj_temp = False  # достигли верха - идем вниз
                    else:        # Движение вниз
                        oj_temp -= 1  #random.uniform(0.0, 3.0)
                        if oj_temp <= 0:
                            oj_temp = 0
                            toup_oj_temp = True   # достигли низа - идем вверх
                    try:
                        queues_dict['oj_temp'].put(oj_temp, timeout=1.0)                    
                    except Full:
                        print(f"Очередь queues_dict['oj_temp'] переполнена, данные oj_temp: {oj_temp} потеряны") 
                    stop_event.wait(1)
            else:
                while not stop_event.is_set():
                    response = self.safe_obd_query(obd.commands.COOLANT_TEMP)
                    if not response.is_null():
                        try:
                            oj_temp = response.value.magnitude
                            queues_dict['oj_temp'].put(oj_temp, timeout = 1.0)
                        except Full:
                            print(f"Очередь oj_temp переполнена, данные: {oj_temp} потеряны") 
                    status_response = self.safe_obd_query(obd.commands.STATUS)
                    if not status_response.is_null():
                        status = status_response.value
                        print(f"MIL (Check Engine): {status.MIL}")          # True/False
                        print(f"DTC count: {status.DTC_count}")             # количество ошибок
                        print(f"Запусков после очистки: {status.ignition_cycles}")
                    oil_response = self.safe_obd_query(obd.commands.OIL_PRESSURE)
                    if not oil_response.is_null():
                        print(f"Давление масла: {oil_response.value}")           # с единицами
                        print(f"Числовое значение: {oil_response.value.magnitude}")  # только число
                    else:
                        print("Давление масла не поддерживается")
                    stop_event.wait(1)

        def task_RPM(self, stop_event:Event, queues_dict):
            if self.connection_ok == False:
                angle_rmp = 0
                toup_rmp = True
                rmp = 0
                while not stop_event.is_set():
                    if angle_rmp < 109 and toup_rmp == True:
                        angle_rmp = (angle_rmp + 1) % 110
                    elif angle_rmp == 0:
                        toup_rmp = True
                    else:
                        angle_rmp = (angle_rmp - 1) % 110
                        toup_rmp = False
                    rmp = angle_rmp * 6000/110 
                    try:
                        queues_dict['rpm'].put(rmp, timeout=1.0)                    
                    except Full:
                        print(f"Очередь queues_dict['rpm'] переполнена, данные rmp: {rmp:.1f} потеряны")
                    stop_event.wait(0.1)
            else:
                while not stop_event.is_set():
                    response = self.safe_obd_query(obd.commands.RPM)
                    if not response.is_null():
                        try:
                            rmp = response.value.magnitude
                            queues_dict['rpm'].put(rmp, timeout=1.0)
                        except Full:
                            print(f"Очередь rmp переполнена, данные: {rmp} потеряны") 
                    stop_event.wait(0.01)
            
        def discover_devices(self):
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
                #sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                #sock.connect((device_address, 1))
                #self.connection = sock
                #print("Подключение установлено!")
                
                # Настройка OBD соединения
                result = self.setup_obd_connection(device_address)
                return result
                
            except Exception as e:
                print(f"Ошибка подключения: {e}")
                return False
        
        def setup_obd_connection(self, device_address):
            """Настройка OBD соединения"""
            try:
                # Создаем пользовательские команды для ISO27145-4
                #self.setup_custom_commands()
                rfport_name = "rfcomm0"
                result = False
                print(f"Создаем RFCOMM порт: {rfport_name} {device_address}")
                subprocess.run(['sudo', 'rfcomm', 'release', 'all'], check=False)
                subprocess.run(['sudo', 'rfcomm', 'bind', f'/dev/{rfport_name}', device_address, '1'], check=True)
                time.sleep(2)     
                # 2. Проверяем что порт создан
                if not os.path.exists(f'/dev/{rfport_name}'):
                    print(f"Ошибка: порт /dev/{rfport_name} не создан")
                    return result
                else:
                    # 3. Даем права
                    subprocess.run(['sudo', 'chmod', '666', f'/dev/{rfport_name}'], check=True)
                    # Подключаемся через pyOBD
                    #ports = obd.scan_serial()
                    #if ports:
                    self.obd_connection = obd.OBD(portstr=f'/dev/{rfport_name}', baudrate=38400, protocol="6",timeout=30)
                    if not self.obd_connection.is_connected():
                        print("OBD соединение не установлено!")
                        result = False
                    else:
                        print("OBD соединение установлено!")
                        result = True
                    #else:
                    #    print("OBD порты не найдены")
                    return result
                    
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
        
        def read_data_continuously(self, stop_event:Event=None,queues_dict=None):
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
        
        def task_ELM327BL(self, stop_event:Event, queues_dict):        
            try:
                device_addr = self.discover_devices()                # Поиск устройства                
                if device_addr:
                    if self.connect_to_elm327(device_addr):                    # Подключение
                        self.read_data_continuously(stop_event,queues_dict)                        # Чтение данных
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
            device_addr = elm.discover_devices()            # Поиск устройства          
            if device_addr:
                if elm.connect_to_elm327(device_addr):                # Подключение
                    elm.read_data_continuously()                    # Чтение данных
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
    from obd import OBDCommand, Unit, OBDStatus
    import serial.tools.list_ports
    class ELM327Bluetooth:
        def __init__(self, threads_manager=False):
            self.connection = None
            self.obd_connection = False
            print("Windows ELM327Bluetooth")
            if threads_manager == True:
                self.lock = Lock()
                com_port = self.find_bluetooth_com_port()                    
                if com_port:
                    self.obd_connection = self.connect_via_bluetooth(com_port)
                else:
                    print("не найден COM порт")
        def safe_obd_query(self, command):
            with self.lock:
                response = self.connection.query(command)
                return response
        def task_COOLANT_TEMP(self, stop_event:Event, queues_dict):          
            if self.obd_connection == False:
                toup_oj_temp = True
                oj_temp = 0
                while not stop_event.is_set():
                    if toup_oj_temp:  # Движение вверх
                        oj_temp += 1 #random.uniform(0.0, 13.0)
                        if oj_temp >= 99:
                            oj_temp = 99
                            toup_oj_temp = False  # достигли верха - идем вниз
                    else:        # Движение вниз
                        oj_temp -= 1  #random.uniform(0.0, 3.0)
                        if oj_temp <= 0:
                            oj_temp = 0
                            toup_oj_temp = True   # достигли низа - идем вверх
                    try:
                        queues_dict['oj_temp'].put(oj_temp, timeout=1.0)                    
                    except Full:
                        print(f"Очередь queues_dict['oj_temp'] переполнена, данные oj_temp: {oj_temp} потеряны") 
                    stop_event.wait(1)
            else:
                while not stop_event.is_set():
                    response = self.safe_obd_query(obd.commands.COOLANT_TEMP)
                    if not response.is_null():
                        try:
                            oj_temp = response.value.magnitude
                            queues_dict['oj_temp'].put(oj_temp, timeout = 1.0)
                        except Full:
                            print(f"Очередь oj_temp переполнена, данные: {oj_temp} потеряны") 
                    stop_event.wait(1)

        def task_RPM(self, stop_event:Event, queues_dict):
            if self.obd_connection == False:
                angle_rmp = 0
                toup_rmp = True
                rmp = 0
                while not stop_event.is_set():
                    if toup_rmp:  
                        angle_rmp += 5 
                        if angle_rmp >= 110:
                            angle_rmp = 110
                            toup_rmp = False  
                    else:        
                        angle_rmp -= 1  
                        if angle_rmp <= 0:
                            angle_rmp = 0
                            toup_rmp = True   
                    rmp = angle_rmp * 6000/110 
                    try:
                        queues_dict['rpm'].put(rmp, timeout=1.0)                    
                    except Full:
                        print(f"Очередь queues_dict['rpm'] переполнена, данные rmp: {rmp:.1f} потеряны")
                    stop_event.wait(0.1)
            else:
                while not stop_event.is_set():
                    response = self.safe_obd_query(obd.commands.RPM)
                    if not response.is_null():
                        try:
                            rmp = response.value.magnitude
                            queues_dict['rpm'].put(rmp, timeout=1.0)
                        except Full:
                            print(f"Очередь rmp переполнена, данные: {rmp} потеряны") 
                    stop_event.wait(0.005)
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
                    return port.device
            return None
        
        def connect_via_bluetooth(self, com_port):
            try:
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
            if self.connection is None:
                return data
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
        
        def monitor_data(self, stop_event:Event=None, queues_dict=None):
            """Мониторинг данных в реальном времени"""
            print("Мониторинг данных OBD2...")
            print("Нажмите Ctrl+C для остановки")
            print("-" * 50)
            if stop_event is None:
                stop_event = Event() 
            try:
                while not stop_event.is_set():
                    data = self.get_obd_data()
                    
                    oj_temp = data.get('coolant_temp', 'N/A')
                    print(f"Температура ОЖ: {oj_temp}°C")
                    if queues_dict is not None:
                        try:
                            queues_dict['oj_temp'].put_nowait(oj_temp)                    
                        except Full:
                            print(f"Очередь queues_dict['oj_temp'] переполнена, данные oj_temp: {oj_temp} потеряны") 

                    rmp = data.get('rpm', 'N/A')
                    print(f"Обороты: {rmp} об/мин")
                    if queues_dict is not None:
                        try:
                            queues_dict['rpm'].put_nowait(rmp)                    
                        except Full:
                            print(f"Очередь queues_dict['rpm'] переполнена, данные rmp: {rmp} потеряны") 
                    
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
        
        def task_ELM327BL(self, stop_event:Event, queues_dict):
            try:
                com_port = self.find_bluetooth_com_port() # Поиск Bluetooth порта 
                if com_port:
                    if self.connect_via_bluetooth(com_port): # Подключение
                        self.monitor_data(stop_event, queues_dict) # Запуск мониторинга
                else:
                    print("не найден COM порт")
                    self.simulation(stop_event, queues_dict)
            except Exception as e:
                print(f"Ошибка: {e}")
            finally:
                self.close()

        def simulation(self, stop_event:Event, queues_dict):
            toup_rmp = True
            angle_rmp = 0.0
            toup_oj_temp = True
            oj_temp = 0.0
            intervals =   {'rpm': 0.01,'oj_temp': 1.0}
            last_update = {'rpm': 0  ,'oj_temp': 0}
            while not stop_event.is_set():
                stop_event.wait(0.01)
                current_time = time.time()
                if current_time - last_update['rpm'] > intervals['rpm']:
                    last_update['rpm'] = current_time
                    if angle_rmp < 109 and toup_rmp == True:
                        angle_rmp = (angle_rmp + 1) % 110
                    elif angle_rmp == 0:
                        toup_rmp = True
                    else:
                        angle_rmp = (angle_rmp - 1) % 110
                        toup_rmp = False
                    rmp = angle_rmp * 6000/110 
                    try:
                        queues_dict['rpm'].put(rmp,timeout=1.0)                    
                    except Full:
                        print(f"Очередь queues_dict['rpm'] переполнена, данные rmp: {rmp:.1f} потеряны")

                current_time = time.time()
                if current_time - last_update['oj_temp'] > intervals['oj_temp']:
                    last_update['oj_temp'] = current_time
                    if toup_oj_temp:  # Движение вверх
                        oj_temp += 1 #random.uniform(0.0, 13.0)
                        if oj_temp >= 99:
                            oj_temp = 99
                            toup_oj_temp = False  # достигли верха - идем вниз
                    else:        # Движение вниз
                        oj_temp -= 1  #random.uniform(0.0, 3.0)
                        if oj_temp <= 0:
                            oj_temp = 0
                            toup_oj_temp = True   # достигли низа - идем вверх
                    try:
                        queues_dict['oj_temp'].put(oj_temp,timeout=0.2)                    
                    except Full:
                        print(f"Очередь queues_dict['oj_temp'] переполнена, данные oj_temp: {oj_temp} потеряны") 
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

