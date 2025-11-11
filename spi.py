from queue import Full 
from threading import Lock
import time
from dataclasses import dataclass

# Важные регистры MCP2515
MCP2515_REG_CANCTRL       =0x0F
MCP2515_REG_CANSTAT       =0x0E
MCP2515_REG_CNF1          =0x2A
MCP2515_REG_CNF2          =0x29
MCP2515_REG_CNF3          =0x28
MCP2515_REG_CANINTE       =0x2B
MCP2515_REG_CANINTF       =0x2C
MCP2515_REG_TXB0CTRL      =0x30
MCP2515_REG_TXB0SIDH      =0x31
MCP2515_REG_TXB0SIDL      =0x32
MCP2515_REG_TXB0DLC       =0x35
MCP2515_REG_TXB0D0        =0x36
MCP2515_REG_RXB0CTRL      =0x60
MCP2515_REG_RXB0SIDH      =0x61
MCP2515_REG_RXB0DLC       =0x65
MCP2515_REG_RXB0D0        =0x66

# PID коды
PID_ENGINE_RPM            =0x0C
PID_COOLANT_TEMP          =0x05    # Температура охлаждающей жидкости
PID_DTC_STATUS            =0x01    # Статус DTC (Diagnostic Trouble Codes)
PID_FREEZE_DTC            =0x02    # Замороженные кадры DTC

# Команды RTS (Request To Send) для конкретных буферов
MCP2515_CMD_RTS_TX0   =0x81  #// Запрос отправки для TXB0
MCP2515_CMD_RTS_TX1   =0x82  #// Запрос отправки для TXB1  
MCP2515_CMD_RTS_TX2   =0x84  #// Запрос отправки для TXB2
MCP2515_CMD_RTS_ALL   =0x87  #// Запрос отправки для всех буферов

# CAN ID для OBD (ISO 15765-4)
CAN_OBD_REQUEST_ID        =0x7DF   # Широковещательный запрос
CAN_OBD_RESPONSE_ID       =0x7E8   # Ответ от двигателя

@dataclass
class DTCStatus:
    mil_status: int = 0        # 0 - MIL выключен, 1 - MIL включен (Check Engine)
    dtc_count: int = 0         # Количество активных DTC
    supported_tests: int = 0   # Поддерживаемые тесты
    test_completion: int = 0   # Завершение тестов

try:
    #sudo apt update
    #sudo apt install python3-spidev python3-dev
    # Или через pip
    #pip install spidev
    import spidev
    import RPi.GPIO as GPIO
    class spi:
        def __init__(self):
            print("spi работа с железом")
            # Настройки GPIO для CS (Chip Select)
            self.CS_PIN_mcp2515 = 8  # GPIO8 (физический пин 24)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.CS_PIN_mcp2515, GPIO.OUT)
            GPIO.output(self.CS_PIN_mcp2515, GPIO.HIGH)  # CS активен низким уровнем
            # Инициализация SPI
            self.bus = spidev.SpiDev() # композиция
            self.bus.open(0, 0)  # bus 0, device 0 (CS0)
            self.bus.max_speed_hz = 100000  # 100 kHz
            self.bus.mode = 0b00  # Режим 0 (CPOL=0, CPHA=0)
            self.bus.no_cs = True  # Важно! включаем автоматическое управление CS
        def MCP2515_Read_Register(self, reg_addr):
            MCP2515_CMD_READ = 0x03
            tx_data = [MCP2515_CMD_READ, reg_addr, 0x00]
            
            GPIO.output(self.CS_PIN_mcp2515, GPIO.LOW)  # Активируем CS
            rx_data = self.bus.xfer2(tx_data)   # Полный дуплексный обмен
            GPIO.output(self.CS_PIN_mcp2515, GPIO.HIGH) # Деактивируем CS
            
            # rx_data[0] - мусор (принимался во время передачи команды)
            # rx_data[1] - значение регистра (во время передачи адреса)
            # rx_data[2] - значение (во время передачи dummy байта)
            return rx_data[2]

        def MCP2515_Write_Register(self, reg_addr, reg_data):
            MCP2515_CMD_WRITE = 0x02
            tx_data = [MCP2515_CMD_WRITE, reg_addr, reg_data]
            
            GPIO.output(self.CS_PIN_mcp2515, GPIO.LOW)  # Активируем CS
            self.bus.xfer2(tx_data)             # Передаем данные
            GPIO.output(self.CS_PIN_mcp2515, GPIO.HIGH) # Деактивируем CS
        def MCP2515_Send_OBD_Request(self, can_id:int, pid:int):
            # Буфер для отправки (8 байт)
            tx_buffer = bytearray(8)

            #// Формируем OBD2 запрос
            tx_buffer[0] = 0x02       #// Кол-во байт данных
            tx_buffer[1] = 0x01       #// Режим: Show current data
            tx_buffer[2] = pid        #// PID запроса (0x0C - RPM)
            tx_buffer[3] = 0x00       #// Заполнители
            tx_buffer[4] = 0x00
            tx_buffer[5] = 0x00
            tx_buffer[6] = 0x00
            tx_buffer[7] = 0x00

            # 1. Записываем ID сообщения (11-bit)
            self.MCP2515_Write_Register(MCP2515_REG_TXB0SIDH, (can_id >> 3)) # Старшие 8 бит ID
            self.MCP2515_Write_Register(MCP2515_REG_TXB0SIDL, (can_id << 5)) # Младшие 3 бита ID

            # 2. Записываем DLC (длину данных) = 8
            self.MCP2515_Write_Register(MCP2515_REG_TXB0DLC, 0x08)

            # 3. Записываем данные
            for i in range(8):
                self.MCP2515_Write_Register(MCP2515_REG_TXB0D0 + i, tx_buffer[i])
            
            # 4. Запрашиваем отправку (RTS) для буфера TXB0
            rts_cmd = [MCP2515_CMD_RTS_TX0]
            GPIO.output(self.CS_PIN_mcp2515, GPIO.LOW)  # Активируем CS
            self.bus.xfer2(rts_cmd) 
            GPIO.output(self.CS_PIN_mcp2515, GPIO.HIGH) # Деактивируем CS
        def MCP2515_Read_Message_Polling_FreeRTOS(self, data: bytearray, pid: int, timeout: float) -> int: 
            wait_start = time.time()
            while((time.time() - wait_start) < timeout):
                # ОПРОС флага принятия сообщения в регистре CANINTF (бит 0 - RX0IF)
                if self.MCP2515_Read_Register(MCP2515_REG_CANINTF) & 0x01:               
                    # Читаем DLC чтобы узнать длину данных
                    dlc = self.MCP2515_Read_Register(MCP2515_REG_RXB0DLC) & 0x0F                    
                    # Читаем данные из буфера RXB0
                    for i in range(dlc):
                        data[i] = self.MCP2515_Read_Register(MCP2515_REG_RXB0D0 + i)                    
                    # !!! ВАЖНО: Сбрасываем флаг вручную, записывая 0 в бит RX0IF !!!
                    self.MCP2515_Write_Register(MCP2515_REG_CANINTF, 0x00)
                    if data[2] == pid:
                        return dlc # Возвращаем количество принятых байт                
                time.sleep(0.001)#osDelay(1)        
            return 0 # Сообщения нет
        def Handle_Negative_Response(self, data: bytearray, length: int) -> int:
            if data[1] != 0x71:
                return 0
            if length >= 4:
                requested_service = data[2]
                error_code = data[3]              
                print(f"NRC: Service 0x{requested_service:02X}, Error: 0x{error_code:02X} - ", end="")             
                if error_code == 0x11:
                    print("Service not supported")
                elif error_code == 0x12:
                    print("Sub-function not supported")
                elif error_code == 0x13:
                    print("Invalid format")
                elif error_code == 0x22:
                    print("Conditions not correct")
                elif error_code == 0x31:
                    print("Request out of range")
                else:
                    print("Unknown error")           
            return 1
        def Parse_Engine_RPM(self, data: bytearray, length: int) -> float:
            # Проверяем что это ответ на PID 0x0C
            # Формат ответа: [04] [41] [0C] [A] [B] [00] [00] [00]
            if length >= 5 and data[1] == 0x41 and data[2] == PID_ENGINE_RPM:
                # Объединяем два байта
                rpm_value = (data[3] << 8) | data[4]
                return rpm_value / 4.0  # Применяем формулу 
            return 0.0
        def Parse_Coolant_Temperature(self, data: bytearray, length: int) -> float:
            # Формат ответа: [03] [41] [05] [T] [00] [00] [00] [00]
            if length >= 4 and data[1] == 0x41 and data[2] == PID_COOLANT_TEMP:
                temp_value = data[3]
                return temp_value - 40.0  # Формула: значение - 40 = температура в °C
            return -40.0  # Значение по умолчанию/ошибка
        def Parse_DTC_Status(self, data: bytearray, length: int) -> DTCStatus:
            status = DTCStatus()          
            # Формат ответа: [04] [41] [01] [A] [B] [C] [D] [00]
            if length >= 8 and data[1] == 0x41 and data[2] == PID_DTC_STATUS:
                # Бит 7 байта A: статус MIL (0 - выкл, 1 - вкл)
                status.mil_status = (data[3] >> 7) & 0x01                
                # Биты 6-0 байта A: количество DTC
                status.dtc_count = data[3] & 0x7F               
                # Байты B, C, D содержат информацию о тестах
                status.supported_tests = data[4]
                status.test_completion = data[5]           
            return status
        def task_COOLANT_TEMP(self, stop_event, queues_dict):
            # 1. Переход в режим конфигурации
            self.MCP2515_Write_Register(MCP2515_REG_CANCTRL, 0x80); # Режим конфигурации
            stop_event.wait(0.01)#HAL_Delay(10);

            # 2. Настройка битрейта 500 kbps для кварца 8 МГц
            self.MCP2515_Write_Register(MCP2515_REG_CNF1, 0x00) # SJW=1, BRP=0
            self.MCP2515_Write_Register(MCP2515_REG_CNF2, 0xD0) # BTLMODE=1, SAM=0, PS1=6 Tq
            self.MCP2515_Write_Register(MCP2515_REG_CNF3, 0x02) # PS2=3 Tq

            # 3. !!! НАСТРОЙКА ПРЕРЫВАНИЙ ПРОПУСКАЕТСЯ !!!
            # MCP2515_Write_Register(MCP2515_REG_CANINTE, 0x01); // ЭТУ СТРОКУ УБИРАЕМ

            # 4. Настройка буфера приема RXB0
            self.MCP2515_Write_Register(MCP2515_REG_RXB0CTRL, 0x00) # Принимать все сообщения

            # 5. Возврат в нормальный режим
            self.MCP2515_Write_Register(MCP2515_REG_CANCTRL, 0x00) # Нормальный режим
            stop_event.wait(0.01)#HAL_Delay(10);
            while not stop_event.is_set():
                rx_data = bytearray(8)

                self.MCP2515_Send_OBD_Request(CAN_OBD_REQUEST_ID, PID_ENGINE_RPM) 
                data_length = self.MCP2515_Read_Message_Polling_FreeRTOS(rx_data, PID_ENGINE_RPM, 0.05);
                if data_length > 0:
                    if self.Handle_Negative_Response(rx_data, 8):
                        print("rpm: er    ")#xQueueOverwrite(rpm_error_Queue, &(const char*){"rpm: er    "});
                    else:
                        engine_rpm = self.Parse_Engine_RPM(rx_data, 8)
                        queues_dict['rpm'].put(engine_rpm, timeout=1.0) #xQueueOverwrite(rpm_Queue, &engine_rpm);                
                else: 
                    print("rpm: -    ")#xQueueOverwrite(rpm_error_Queue, &(const char*){"rpm: -    "}); }  
                
                stop_event.wait(0.01)#osDelay(10); задержка для восстановления MCP2515
                self.MCP2515_Send_OBD_Request(CAN_OBD_REQUEST_ID, PID_COOLANT_TEMP)  
                if self.MCP2515_Read_Message_Polling_FreeRTOS(rx_data, PID_COOLANT_TEMP, 0.05) > 0:
                    if self.Handle_Negative_Response(rx_data, 8):
                        print("coolant: er    ")#xQueueOverwrite(coolant_error_Queue, &(const char*){"coolant: er    "});
                    else:
                        t = self.Parse_Coolant_Temperature(rx_data,8)
                        queues_dict['oj_temp'].put(engine_rpm, timeout=1.0)#xQueueOverwrite(coolant_Queue, &t);
                else:
                    print("coolant: -    ")#xQueueOverwrite(coolant_error_Queue, &(const char*){"coolant: -    "}); 
                
                stop_event.wait(0.01)#osDelay(10); //задержка для восстановления MCP2515
                self.MCP2515_Send_OBD_Request(CAN_OBD_REQUEST_ID, PID_DTC_STATUS)
                if self.MCP2515_Read_Message_Polling_FreeRTOS(rx_data, PID_DTC_STATUS, 0.05) > 0:
                    if self.Handle_Negative_Response(rx_data, 8):
                        print("check: er    ")#xQueueOverwrite(checkengine_error_Queue, &(const char*){"check: er    "});
                    else:
                        dt = self.Parse_DTC_Status(rx_data,8)
                        queues_dict['check'].put(engine_rpm, timeout=1.0)#xQueueOverwrite(checkengine_Queue, &dt.mil_status);
                else:
                    print("check: -    ")#xQueueOverwrite(checkengine_error_Queue, &(const char*){"check: -    "});}

                stop_event.wait(0.1)
except ImportError:
    class spi:
        def __init__(self):
            print("spi симуляция")
        def MCP2515_Read_Register(self, reg_addr):
            print(f"MCP2515_Read_Register reg_addr: {reg_addr}")
            return 0x0
        def MCP2515_Write_Register(self, reg_addr, reg_data):
            print(f"MCP2515_Write_Register reg_addr: {reg_addr} reg_data: {reg_data}")
        def task_RPM(self, stop_event, queues_dict):
            angle_rpm = 0
            toup_rpm = True
            rpm = 0
            while not stop_event.is_set():
                if toup_rpm:  
                    angle_rpm += 5 
                    if angle_rpm >= 110:
                        angle_rpm = 110
                        toup_rpm = False  
                else:        
                    angle_rpm -= 1  
                    if angle_rpm <= 0:
                        angle_rpm = 0
                        toup_rpm = True   
                rpm = angle_rpm * 6000/110 
                try:
                    queues_dict['rpm'].put(rpm, timeout=1.0)                    
                except Full:
                    print(f"Очередь queues_dict['rpm'] переполнена, данные rpm: {rpm:.1f} потеряны")
                stop_event.wait(0.01)

        def task_COOLANT_TEMP(self, stop_event, queues_dict):
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