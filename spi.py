from queue import Full 
from threading import Lock
import time

# Адреса регистров MCP2515
MCP2515_REG_CANCTRL = 0x0F
MCP2515_REG_CANSTAT = 0x0E

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
            self.bus.no_cs = True  # Важно! Отключаем автоматическое управление CS
        def mcp2515_read_register(self, reg_addr):
            MCP2515_CMD_READ = 0x03
            tx_data = [MCP2515_CMD_READ, reg_addr, 0x00]
            
            GPIO.output(self.CS_PIN_mcp2515, GPIO.LOW)  # Активируем CS
            rx_data = self.bus.xfer2(tx_data)   # Полный дуплексный обмен
            GPIO.output(self.CS_PIN_mcp2515, GPIO.HIGH) # Деактивируем CS
            
            # rx_data[0] - мусор (принимался во время передачи команды)
            # rx_data[1] - значение регистра (во время передачи адреса)
            # rx_data[2] - значение (во время передачи dummy байта)
            return rx_data[2]

        def mcp2515_write_register(self, reg_addr, reg_data):
            MCP2515_CMD_WRITE = 0x02
            tx_data = [MCP2515_CMD_WRITE, reg_addr, reg_data]
            
            GPIO.output(self.CS_PIN_mcp2515, GPIO.LOW)  # Активируем CS
            self.bus.xfer2(tx_data)             # Передаем данные
            GPIO.output(self.CS_PIN_mcp2515, GPIO.HIGH) # Деактивируем CS
except ImportError:
    class spi:
        def __init__(self):
            print("spi симуляция")
        def mcp2515_read_register(self, reg_addr):
            print(f"mcp2515_read_register reg_addr: {reg_addr}")
            return 0x0
        def mcp2515_write_register(self, reg_addr, reg_data):
            print(f"mcp2515_write_register reg_addr: {reg_addr} reg_data: {reg_data}")
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
                    print(f"Очередь queues_dict['rpm'] переполнена, данные rmp: {rpm:.1f} потеряны")
                stop_event.wait(0.01)

        def task_COOLANTTEMP_and_other(self, stop_event, queues_dict):
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