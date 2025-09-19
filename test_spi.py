import spidev

# Создаем объект SPI
spi = spidev.SpiDev()

# Открываем SPI устройство (bus 0, device 0)
spi.open(0, 0)

# Настраиваем параметры SPI
spi.max_speed_hz = 1000000  # 1 MHz
spi.mode = 0                # Режим 0 (CPOL=0, CPHA=0)
spi.no_cs = False
# Отправляем один байт (например, 0x55)
data_to_send = [0x10,0x10]       # Должен быть список
response = spi.xfer(data_to_send)

print(f"Отправлено: {hex(data_to_send[0])}")
print(f"Получено в ответ: {hex(response[0])}")

# Закрываем соединение
spi.close()