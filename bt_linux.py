
import time
from threading import Event, Lock
from queue import Queue, Full 
from typing import List
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
                device_addr = self.discover_devices()                    
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
                        queues_dict['rmp'].put(rmp, timeout=1.0)                    
                    except Full:
                        print(f"Очередь queues_dict['rmp'] переполнена, данные rmp: {rmp:.1f} потеряны")
                    stop_event.wait(0.1)
            else:
                while not stop_event.is_set():
                    response = self.safe_obd_query(obd.commands.RMP)
                    if not response.is_null():
                        try:
                            rmp = response.value.magnitude
                            queues_dict['rmp'].put(rmp, timeout=1.0)
                        except Full:
                            print(f"Очередь rmp переполнена, данные: {rmp} потеряны") 
                    stop_event.wait(0.1)
            
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
                sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                sock.connect((device_address, 1))
                self.connection = sock
                print("Подключение установлено!")
                
                # Настройка OBD соединения
                result = self.setup_obd_connection()
                return result
                
            except Exception as e:
                print(f"Ошибка подключения: {e}")
                return False
        
        def setup_obd_connection(self):
            """Настройка OBD соединения"""
            try:
                # Создаем пользовательские команды для ISO27145-4
                self.setup_custom_commands()
                result = False
                # Подключаемся через pyOBD
                ports = obd.scan_serial()
                if ports:
                    self.obd_connection = obd.OBD(ports[0], baudrate=500000, protocol="6",timeout=15)
                    print("OBD соединение установлено!")
                    result = True
                else:
                    print("OBD порты не найдены")
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
                # Поиск устройства
                device_addr = self.discover_devices()
                
                if device_addr:
                    # Подключение
                    if self.connect_to_elm327(device_addr):
                        # Чтение данных
                        self.read_data_continuously(stop_event,queues_dict)
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