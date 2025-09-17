from queue import Full 
from threading import Lock

try:
    #sudo apt update
    #sudo apt install python3-spidev python3-dev
    # Или через pip
    #pip install spidev
    import spidev
    class spi:
        def __init__(self):
            print("spi работа с железом")
except ImportError:
    class spi:
        def __init__(self):
            print("spi симуляция")
        def task_RPM(self, stop_event, queues_dict):
            angle_rpm = 0
            toup_rpm = True
            rpm = 0
            while not stop_event.is_set():
                if toup_rpm:  
                    angle_rpm += 5 
                    if angle_rpm >= 110:
                        angle_rpm = 110
                        toup_rpm = False  
                else:        
                    angle_rpm -= 1  
                    if angle_rpm <= 0:
                        angle_rpm = 0
                        toup_rpm = True   
                rpm = angle_rpm * 6000/110 
                try:
                    queues_dict['rpm'].put(rpm, timeout=1.0)                    
                except Full:
                    print(f"Очередь queues_dict['rpm'] переполнена, данные rmp: {rpm:.1f} потеряны")
                stop_event.wait(0.01)

        def task_COOLANTTEMP_and_other(self, stop_event, queues_dict):
            toup_oj_temp = True
            oj_temp = 0
            while not stop_event.is_set():
                if toup_oj_temp:  # Движение вверх
                    oj_temp += 1 #random.uniform(0.0, 13.0)
                    if oj_temp >= 99:
                        oj_temp = 99
                        toup_oj_temp = False  # достигли верха - идем вниз
                else:        # Движение вниз
                    oj_temp -= 1  #random.uniform(0.0, 3.0)
                    if oj_temp <= 0:
                        oj_temp = 0
                        toup_oj_temp = True   # достигли низа - идем вверх
                try:
                    queues_dict['oj_temp'].put(oj_temp, timeout=1.0)                    
                except Full:
                    print(f"Очередь queues_dict['oj_temp'] переполнена, данные oj_temp: {oj_temp} потеряны") 
                stop_event.wait(1)