import pigpio
import time
from threading import Event

'''
делитель напряжения для выхода с датчика 8V
R1 (кОм)	R2 (кОм)	Vout при 8V (В)	Запас до 1.8V	Запас до 3.3V	Примечание
7.5     	3.3	          ~2.44	           0.64V	       0.86V	    Отличный баланс, highly recommended!
10	        4.7	          ~2.56	           0.76V	       0.74V	    Также отличный вариант
4.7	        2.2	          ~2.55	           0.75V	       0.75V	    Хорошо, но номинал 2.2 кОм чуть менее распространен
5.1	        2.2	          ~2.41	           0.61V	       0.89V	    Хорошо
'''
'''
PULSE_GPIO = 17 соотвествует GPIO17 --> физ пин (11)
   3V3  (1) ◉---◉  (2) 5V
 GPIO2  (3) ◉---◉  (4) 5V
 GPIO3  (5) ◉---◉  (6) GND
 GPIO4  (7) ◉---◉  (8) GPIO14
   GND  (9) ◉---◉ (10) GPIO15
GPIO17 (11) ◉---◉ (12) GPIO18
GPIO27 (13) ◉---◉ (14) GND
GPIO22 (15) ◉---◉ (16) GPIO23
   3V3 (17) ◉---◉ (18) GPIO24
GPIO10 (19) ◉---◉ (20) GND
 GPIO9 (21) ◉---◉ (22) GPIO25
GPIO11 (23) ◉---◉ (24) GPIO8
   GND (25) ◉---◉ (26) GPIO7
 GPIO0 (27) ◉---◉ (28) GPIO1
 GPIO5 (29) ◉---◉ (30) GND
 GPIO6 (31) ◉---◉ (32) GPIO12
GPIO13 (33) ◉---◉ (34) GND
GPIO19 (35) ◉---◉ (36) GPIO16
GPIO26 (37) ◉---◉ (38) GPIO20
   GND (39) ◉---◉ (40) GPIO21
'''
# Константы
PULSE_GPIO = 17
IMPULSES_PER_METER = 6

# Глобальные переменные
pulse_count = 0
current_speed_kmh = 0.0
running = True  # Флаг для управления потоком

# Включить автозагрузку демона pigpiod при загрузке системы
#sudo systemctl enable pigpiod

# (Опционально) Запустить его прямо сейчас, не дожидаясь перезагрузки
#sudo systemctl start pigpiod

# (Опционально) Проверить, что демон запустился и работает без ошибок
#sudo systemctl status pigpiod

# Функция-обработчик импульсов будет вызываться фоном демоном но в потоке процесса
def pulse_callback(gpio, level, tick):
    global pulse_count
    pulse_count += 1

# Функция, которая будет работать в отдельном потоке
def task_gpio_gps(stop_event:Event):
    global pulse_count, current_speed_kmh
    # Основной код
    pi = pigpio.pi()
    # 1. НАСТРАИВАЕМ РЕЖИМ ПИНА И ПОДТЯЖКУ
    pi.set_mode(PULSE_GPIO, pigpio.INPUT)           # Устанавливаем пин в режим входа
    pi.set_pull_up_down(PULSE_GPIO, pigpio.PUD_DOWN) # ВКЛЮЧАЕМ ПОДТЯЖКУ К ЗЕМЛЕ
    cb = pi.callback(PULSE_GPIO, pigpio.RISING_EDGE, pulse_callback)
    
    while not stop_event.is_set():
        count_start = pulse_count
        stopped = stop_event.wait(1.0) # период одна секунда, для удобного перевода в км/ч
        if stopped:
            break
        count_end = pulse_count
        impulses_in_second = count_end - count_start
        current_speed_kmh = (impulses_in_second / IMPULSES_PER_METER) * 3.6 # м/c в км/ч
        print(f"Скорость: {current_speed_kmh:.2f} км/ч")

    cb.cancel()
    pi.stop()


    