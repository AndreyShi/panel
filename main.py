import sys
from threading import Event
from threading import Thread
from i2c  import i2c
from uart import uart
import dashboard
import argparse
from queue import Queue
from bt import ELM327Bluetooth


def main():
    parser = argparse.ArgumentParser(description='приложение с аргументами')  
    parser.add_argument('-w', '--window', action='store_true',help='Запуск в оконном режиме')  
    args = parser.parse_args()
    arguments = ''
    if args.window:
        arguments = '-w'

    stop_event = Event()
    Que = [
        Queue(1),  #очередь [0] с size 1 для датчика уровня топлива
        Queue(1),  #очередь [1] с size 1 для обротов/мин
        Queue(1)   #очередь [2] с size 1 для температуры ОЖ
    ] 
    queues_dict = {
        'R2_canister_1' :Queue(maxsize=1),
        'rmp'           :Queue(maxsize=1),
        'coolant_temp'  :Queue(maxsize=1)
    }


    i2c_manager = i2c()
    thread_i2c_ADS1115 = Thread(target=i2c_manager.task_ADS1115, name="task_ADS1115",args=(stop_event, Que, ))
    thread_i2c_ADS1115.start()
   
    #uart_device = uart()
    #thread_uart = Thread(target=uart_device.task_GPSReader, name="thread_uart",args=(stop_event, ))
    #thread_uart.start()

    OBD2 = ELM327Bluetooth()
    thread_OBD2 = Thread(target=OBD2.task_ELM327BL, name="task_ELM327BL",args=(stop_event, Que, ))
    thread_OBD2.start()

    thread_dashboard = Thread(target=dashboard.task_Dashboard, name="thread_dasboard",args=(stop_event, arguments, Que ))
    thread_dashboard.start()

    thread_dashboard.join()
    #thread_uart.join()
    thread_i2c_ADS1115.join()
    sys.exit()

if __name__ == "__main__":
    main()