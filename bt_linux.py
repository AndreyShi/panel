import obd
import bluetooth
import subprocess
import time
import os

def discover_devices():
    print("Поиск Bluetooth устройств...")
    devices = bluetooth.discover_devices(lookup_names=True)
            
    for addr, name in devices:
        print(f"Найдено устройство: {name} - {addr}")
        if "ELM327" in name.upper() or "OBD" in name.upper():
            print(f"Найден ELM327: {name}")
            return addr
    return None

def main():
    # 1. Подключаем Bluetooth socket
    #sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM) 
    device_address = "00:1D:A5:06:04:CB"  # Ваш MAC адрес
    #device_address = discover_devices()
    #sock.connect((device_address, 1))
    #print("Bluetooth socket подключен")
    rfport_name = "rfcomm0"
    print(f"# 1. Создаем RFCOMM порт: {rfport_name} {device_address}")
    subprocess.run(['sudo', 'rfcomm', 'release', 'all'], check=False)
    #эквивалентно sudo rfcomm bind /dev/rfcomm0 XX:XX:XX:XX:XX:XX 1
    subprocess.run(['sudo', 'rfcomm', 'bind', f'/dev/{rfport_name}', device_address, '1'], check=True)
    time.sleep(2)
        
    # 3. Проверяем что порт создан
    print("# 2. Проверяем что порт создан")
    if not os.path.exists(f'/dev/{rfport_name}'):
        print(f"Ошибка: порт /dev/{rfport_name} не создан")
        return None
    
    # 2. Даем права
    print("# 3. Даем права")
    subprocess.run(['sudo', 'chmod', '666', f'/dev/{rfport_name}'], check=True)

    # 2. Используем прямое socket подключение (обход scan_serial)
    try:
        # Формат для socket подключения
        connection = obd.OBD(
            portstr=f'/dev/{rfport_name}',
            baudrate=38400,
            timeout=30,
            fast=False
        )
        
        if connection.is_connected():
            print("OBD подключено!")
            # Проверим поддерживаемые PID
            supported_commands = connection.supported_commands
            print("Поддерживаемые команды:")
            for cmd in supported_commands:
                print(cmd.name)

            # Читаем данные
            cnt  = 3
            while cnt:
                speed = connection.query(obd.commands.SPEED)
                rpm = connection.query(obd.commands.RPM)
                print(f"Скорость: {speed.value}")
                print(f"Обороты: {rpm.value}")
                cnt = cnt - 1
                time.sleep(1)
        else:
            print("OBD не подключено")
            
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()