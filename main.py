import sys
import threading
import i2c
import uart 
import dashboard
import argparse
from queue import Queue


def main():
    parser = argparse.ArgumentParser(description='приложение с аргументами')  
    parser.add_argument('-w', '--window', action='store_true',help='Запуск в оконном режиме')  
    args = parser.parse_args()
    arguments = ''
    if args.window:
        arguments = '-w'

    running = [True]
    que = [Queue(1)] # que[0] - очередь для датчика уровня топлива

    i2c_devices = i2c.i2c()
    thread_i2c = threading.Thread(target=i2c_devices.task_ADS1115, name="task_ADS1115",args=(running, que, ))
    thread_i2c.start()
   
    uart_device = uart.uart()
    thread_uart = threading.Thread(target=uart_device.task_GPSReader, name="thread_uart",args=(running, ))
    thread_uart.start()

    thread_dashboard = threading.Thread(target=dashboard.task_Dashboard, name="thread_dasboard",args=(running, arguments, que ))
    thread_dashboard.start()

    thread_dashboard.join()
    thread_uart.join()
    thread_i2c.join()
    sys.exit()

if __name__ == "__main__":
    main()