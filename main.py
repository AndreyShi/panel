import sys
from threading import Event
from threading import Thread
from i2c  import i2c
from uart import uart
import dashboard
import argparse
from queue import Queue
from bt import ELM327Bluetooth
from typing import Dict
from spi import spi


def main():
    parser = argparse.ArgumentParser(description='приложение с аргументами')  
    parser.add_argument('-w', '--window', action='store_true',help='Запуск в оконном режиме')  
    args = parser.parse_args()
    arguments = ''
    if args.window:
        arguments = '-w'

    stop_event = Event()
    queues_dict = {
        'R2_canister_1' :Queue(maxsize=1),
        'rpm'           :Queue(maxsize=1),
        'oj_temp'       :Queue(maxsize=1)
    }


    i2c_manager = i2c()
    thread_i2c_ADS1115 = Thread(target=i2c_manager.task_ADS1115, name="task_ADS1115",args=(stop_event, queues_dict, ))
    thread_i2c_ADS1115.start()
   
    #uart_device = uart()
    #thread_uart = Thread(target=uart_device.task_GPSReader, name="thread_uart",args=(stop_event, ))
    #thread_uart.start()

    OBD2 = ELM327Bluetooth(threads_manager=True)
    thread_OBD2_COOLANT_TEMP = Thread(target=OBD2.task_COOLANT_TEMP, name="task_COOLANT_TEMP",args=(stop_event, queues_dict, ))
    thread_OBD2_COOLANT_TEMP.start()
    thread_OBD2_RMP = Thread(target=OBD2.task_RPM, name="task_RPM",args=(stop_event, queues_dict, ))
    thread_OBD2_RMP.start()

    #spi_manager = spi()
    #thread_spi_RPM = Thread(target=spi_manager.task_RPM, name="task_RPM", args=(stop_event, queues_dict, ))
    #thread_spi_RPM.start()
    #thread_spi_COOLANTTEMP_and_other = Thread(target=spi_manager.task_COOLANTTEMP_and_other, name="task_COOLANTTEMP_and_other", args=(stop_event, queues_dict, ))
    #thread_spi_COOLANTTEMP_and_other.start()

    thread_dashboard = Thread(target=dashboard.task_Dashboard, name="task_dasboard",args=(stop_event, arguments, queues_dict ))
    thread_dashboard.start()

    thread_dashboard.join()
    #thread_uart.join()
    thread_i2c_ADS1115.join()
    thread_OBD2_RMP.join()
    thread_OBD2_COOLANT_TEMP.join()
    #thread_spi_RPM.join()
    #thread_spi_COOLANTTEMP_and_other.join()
    sys.exit()

if __name__ == "__main__":
    main()