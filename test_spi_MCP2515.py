import time
from spi import spi
from spi import MCP2515_REG_CANCTRL
from spi import MCP2515_REG_CANSTAT

def main():
    spi_ = spi()
    """
    Цикл тестирования MCP2515 - аналог вашей функции на STM32
    """
    print("Цикл тестирования MCP2515")
    i = 0
    
    try:
        while True:
            if i == 0:
                # Режим конфигурации
                spi_.mcp2515_write_register(MCP2515_REG_CANCTRL, 0x80)
                i = 1
            else:
                # Нормальный режим
                spi_.mcp2515_write_register(MCP2515_REG_CANCTRL, 0x00)
                i = 0
            
            time.sleep(1)  # Задержка 1 секунда
            
            # Чтение и вывод значения регистра
            reg_value = spi_.mcp2515_read_register(MCP2515_REG_CANCTRL)
            print(f"CANCTRL: 0x{reg_value:02X} ({reg_value})")
            
    except KeyboardInterrupt:
        print("\nТестирование прервано пользователем")

if __name__ == "__main__":
    main()