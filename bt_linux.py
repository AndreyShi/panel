import obd
import bluetooth

def main():
    # 1. Подключаем Bluetooth socket
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    device_address = "00:1D:A5:06:04:CB"  # Ваш MAC адрес
    sock.connect((device_address, 1))
    print("Bluetooth socket подключен")

    # 2. Используем прямое socket подключение (обход scan_serial)
    try:
        # Формат для socket подключения
        connection = obd.OBD(
            portstr=f"socket://{device_address}:1",
            baudrate=38400,
            timeout=30,
            fast=False
        )
        
        if connection.is_connected():
            print("OBD подключено!")
            # Читаем данные
            speed = connection.query(obd.commands.SPEED)
            rpm = connection.query(obd.commands.RPM)
            print(f"Скорость: {speed.value}")
            print(f"Обороты: {rpm.value}")
        else:
            print("OBD не подключено")
            
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    main()