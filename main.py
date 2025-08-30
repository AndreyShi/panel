import sys
import threading
import i2c
import uart 
import dashboard
import argparse


running = True

def check_flag()->bool:
    return running
def set_flag():
    global running
    running = False


def main():

    parser = argparse.ArgumentParser(description='приложение с аргументами')  
    parser.add_argument('-w', '--window', action='store_true',help='Запуск в оконном режиме')  
    args = parser.parse_args()
    arguments = ''
    if args.window:
        arguments = '-w'

    i2c_devices = i2c.i2c()
    thread_i2c = threading.Thread(target=i2c_devices.bus_task, name="thread_i2c",args=(check_flag, ))
    thread_i2c.start()
   
    uart_device = uart.uart()
    thread_uart = threading.Thread(target=uart_device.task_GPSReader, name="thread_uart",args=(check_flag, ))
    thread_uart.start()

    thread_dashboard = threading.Thread(target=dashboard.task_Dashboard, name="thread_dasboard",args=(check_flag, set_flag, arguments, ))
    thread_dashboard.start()

    thread_dashboard.join()
    thread_uart.join()
    thread_i2c.join()
    sys.exit()

if __name__ == "__main__":
    main()