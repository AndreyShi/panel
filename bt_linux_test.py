from bt import ELM327Bluetooth
from threading import Event
from threading import Thread
from queue import Queue, Empty

def testing(stop_event, queues_dict):
    print("Нажмите и держите Cntrl + C для остановки")
    try:
        while not stop_event.is_set():
            rmp = 0
            oj_temp = 0
            try:
                rmp = queues_dict['rpm'].get_nowait()
                queues_dict['rpm'].task_done()
            except Empty:
                print(f"Очередь queues_dict['rpm'] пуста, используются предыдущие данные rmp: {rmp}")

            try:
                oj_temp = queues_dict['oj_temp'].get_nowait()
                queues_dict['oj_temp'].task_done()
            except Empty:
                print(f"Очередь queues_dict['oj_temp'] пуста, используются предыдущие данные oj_temp: {oj_temp}")
           

            print(f"rmp {rmp}, oj_temp {oj_temp}")
            stop_event.wait(1)
    except KeyboardInterrupt:
                print("\nОстановка мониторинга...")
                stop_event.set()
      

def main():
    print("bt_linux_test.py")
    stop_event = Event()
    queues_dict = {
        'R2_canister_1' :Queue(maxsize=1),
        'rpm'           :Queue(maxsize=1),
        'oj_temp'       :Queue(maxsize=1)
    }

    OBD2 = ELM327Bluetooth(threads_manager=True)
    thread_OBD2_COOLANT_TEMP = Thread(target=OBD2.task_COOLANT_TEMP, name="task_COOLANT_TEMP",args=(stop_event, queues_dict, ))
    thread_OBD2_COOLANT_TEMP.start()
    thread_OBD2_RMP = Thread(target=OBD2.task_RPM, name="task_RMP",args=(stop_event, queues_dict, ))
    thread_OBD2_RMP.start()

    thread = Thread(target=testing, name="testing",args=(stop_event, queues_dict, ))
    thread.start()

    thread.join()
    thread_OBD2_RMP.join()
    thread_OBD2_COOLANT_TEMP.join()



if __name__ == "__main__":
    main()