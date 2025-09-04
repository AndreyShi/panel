import sys
from threading import Event
from threading import Thread
from i2c  import i2c
from uart import uart
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

    stop_event = Event()
    que = [
        Queue(1), #очередь с size 1 для датчика уровня топлива
        Queue()   #пока еще не используется
    ] 

    i2c_manager = i2c()
    thread_i2c_ADS1115 = Thread(target=i2c_manager.task_ADS1115, name="task_ADS1115",args=(stop_event, que, ))
    thread_i2c_ADS1115.start()
   
    uart_device = uart()
    thread_uart = Thread(target=uart_device.task_GPSReader, name="thread_uart",args=(stop_event, ))
    thread_uart.start()

    thread_dashboard = Thread(target=dashboard.task_Dashboard, name="thread_dasboard",args=(stop_event, arguments, que ))
    thread_dashboard.start()

    thread_dashboard.join()
    thread_uart.join()
    thread_i2c_ADS1115.join()
    sys.exit()

if __name__ == "__main__":
    main()