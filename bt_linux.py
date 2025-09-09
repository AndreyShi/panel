import obd
import bluetooth
import subprocess
import time
import os

def main():
    # 1. Подключаем Bluetooth socket
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    device_address = "00:1D:A5:06:04:CB"  # Ваш MAC адрес
    sock.connect((device_address, 1))
    print("Bluetooth socket подключен")

    print("Создаем RFCOMM порт...")
    subprocess.run(['sudo', 'rfcomm', 'release', 'all'], check=False)
    subprocess.run(['sudo', 'rfcomm', 'bind', '/dev/rfcomm0', device_address, '1'], check=True)
    time.sleep(2)
        
    # 2. Даем права
    subprocess.run(['sudo', 'chmod', '666', '/dev/rfcomm0'], check=True)
        
    # 3. Проверяем что порт создан
    if not os.path.exists('/dev/rfcomm0'):
        print("Ошибка: порт /dev/rfcomm0 не создан")
        return None


    # 2. Используем прямое socket подключение (обход scan_serial)
    try:
        # Формат для socket подключения
        connection = obd.OBD(
            portstr='/dev/rfcomm0',
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