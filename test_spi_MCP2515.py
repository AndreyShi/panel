import spidev
import time
import RPi.GPIO as GPIO

# Настройки GPIO для CS (Chip Select)
CS_PIN = 8  # GPIO8 (физический пин 24)
GPIO.setmode(GPIO.BCM)
GPIO.setup(CS_PIN, GPIO.OUT)
GPIO.output(CS_PIN, GPIO.HIGH)  # CS активен низким уровнем

# Команды MCP2515 согласно datasheet
MCP2515_CMD_READ = 0x03
MCP2515_CMD_WRITE = 0x02
MCP2515_CMD_RTS = 0x80
MCP2515_CMD_READ_RX = 0x90

# Адреса регистров MCP2515
MCP2515_REG_CANCTRL = 0x0F
MCP2515_REG_CANSTAT = 0x0E

# Инициализация SPI
spi = spidev.SpiDev()
spi.open(0, 0)  # bus 0, device 0 (CS0)
spi.max_speed_hz = 100000  # 100 kHz
spi.mode = 0b00  # Режим 0 (CPOL=0, CPHA=0)
spi.no_cs = True  # Важно! Отключаем автоматическое управление CS

def mcp2515_read_register(reg_addr):
    """
    Чтение одного регистра MCP2515.
    
    Args:
        reg_addr: Адрес регистра для чтения
        
    Returns:
        Прочитанное значение регистра (байт)
    """
    tx_data = [MCP2515_CMD_READ, reg_addr, 0x00]
    
    GPIO.output(CS_PIN, GPIO.LOW)  # Активируем CS
    rx_data = spi.xfer2(tx_data)   # Полный дуплексный обмен
    GPIO.output(CS_PIN, GPIO.HIGH) # Деактивируем CS
    
    # rx_data[0] - мусор (принимался во время передачи команды)
    # rx_data[1] - значение регистра (во время передачи адреса)
    # rx_data[2] - значение (во время передачи dummy байта)
    return rx_data[2]

def mcp2515_write_register(reg_addr, reg_data):
    """
    Запись одного регистра MCP2515.
    
    Args:
        reg_addr: Адрес регистра для записи
        reg_data: Данные для записи
    """
    tx_data = [MCP2515_CMD_WRITE, reg_addr, reg_data]
    
    GPIO.output(CS_PIN, GPIO.LOW)  # Активируем CS
    spi.xfer2(tx_data)             # Передаем данные
    GPIO.output(CS_PIN, GPIO.HIGH) # Деактивируем CS

def test_while_mcp2515():
    """
    Цикл тестирования MCP2515 - аналог вашей функции на STM32
    """
    print("Цикл тестирования MCP2515")
    i = 0
    
    try:
        while True:
            if i == 0:
                # Режим конфигурации
                mcp2515_write_register(MCP2515_REG_CANCTRL, 0x80)
                i = 1
            else:
                # Нормальный режим
                mcp2515_write_register(MCP2515_REG_CANCTRL, 0x00)
                i = 0
            
            time.sleep(1)  # Задержка 1 секунда
            
            # Чтение и вывод значения регистра
            reg_value = mcp2515_read_register(MCP2515_REG_CANCTRL)
            print(f"CANCTRL: 0x{reg_value:02X} ({reg_value})")
            
    except KeyboardInterrupt:
        print("\nТестирование прервано пользователем")
    finally:
        spi.close()
        GPIO.cleanup()