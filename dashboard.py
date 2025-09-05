import pygame
import time
import datetime
from datetime import datetime
from threading import Event
from typing import Literal
from typing import List
from queue import Queue,Empty

def is_raspberry_pi():
    """Проверяет, работает ли на Raspberry Pi"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Model'):
                    if 'Raspberry Pi' in line:
                        return True
    except:
        pass
    return False

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000.0
        return temp
    except:
        return 0.0

def task_Dashboard(stop_event:Event, 
                   arguments: Literal['-w',''], 
                   que:       List[Queue]):
    # Цвета
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    WHITE = (255, 255, 255)
    # Настройки окна
    WIDTH, HEIGHT = 1024, 576  # разрешение экрана в linux
    # Инициализация
    pygame.init()

    # Настройка режима
    if is_raspberry_pi():
        info = pygame.display.Info()
        if arguments == '-w':
            screen = pygame.display.set_mode((WIDTH, HEIGHT))
        else:
            screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.mouse.set_visible(True)

    pygame.display.set_caption("Приборная панель")

    # Загрузка фона
    try:
        background = pygame.image.load("res/dashboard_1024_576.png").convert()  # Фон
        background = pygame.transform.scale(background, (WIDTH, HEIGHT))
    except:
        print("Ошибка: dashboard_1024_576.png не найден.")

    # Загрузка стрелки скорости
    try:
        needle_img = pygame.image.load("res/arrowkmh_1024_576.png").convert_alpha()  # Важно!
        needle_rect = needle_img.get_rect(center=(294, 242))
    except:
        print("Ошибка: arrowkmh_1024_576.png не найден.")

    # Загрузка стрелки RMP
    try:
        rmp_img = pygame.image.load("res/arrowRMP_1024_576.png").convert_alpha()  # Важно!
        rmp_rect = rmp_img.get_rect(center=(294, 242))
    except:
        print("Ошибка: arrowRMP_1024_576.png не найден.")

    # Загрузка стрелки уровня
    try:
        level_img = pygame.image.load("res/level_arrow_1024_576.png").convert_alpha()  # Важно!
    except:
        print("Ошибка: level_arrow_1024_576.png не найден.")

    # Загрузка канистры
    try:
        full_canister_img = pygame.image.load("res/empty_canister_1024_576.png").convert_alpha()
        empty_canister_img = pygame.image.load("res/full_canister_1024_576.png").convert_alpha()
    except:
        print("Ошибка: canister_1024_576.png не найден.")

    # Загрузка вентилятора
    try:
        sprite_sheet = pygame.image.load("res/cooler_1024_576.png").convert_alpha()
    except:
        print("Ошибка: cooler_1024_576.png не найден.")
    on_rect = pygame.Rect(0, 0, 37, 37)
    off_rect = pygame.Rect(0, 37, 37, 37)
    on_image = sprite_sheet.subsurface(on_rect)
    off_image = sprite_sheet.subsurface(off_rect)
    switch_state_cooler = False
    last_update_time_cooler = time.time()
    update_interval_cooler = 0.7

    # Загрузка масленки
    try:
        sprite_sheet_maslenka = pygame.image.load("res/maslenka_1024_576.png").convert_alpha()
    except:
        print("Ошибка: maslenka_1024_576.png не найден.")
    on_rect_maslenka = pygame.Rect(0, 0, 59, 23)
    off_rect_maslenka = pygame.Rect(0, 23, 59, 23)
    on_image_maslenka = sprite_sheet_maslenka.subsurface(on_rect_maslenka)
    off_image_maslenka = sprite_sheet_maslenka.subsurface(off_rect_maslenka)
    switch_state_maslenka = False
    last_update_time_maslenka = time.time()
    update_interval_maslenka = 0.9

    # Загрузка температуры масла
    try:
        sprite_sheet_temp_oil = pygame.image.load("res/temp_oil_1024_576.png").convert_alpha()
    except:
        print("Ошибка: temp_oil_1024_576.png не найден.")
    on_rect_temp_oil = pygame.Rect(0, 0, 43, 43)
    off_rect_temp_oil = pygame.Rect(0, 43, 43, 43)
    on_image_temp_oil = sprite_sheet_temp_oil.subsurface(on_rect_temp_oil)
    off_image_temp_oil = sprite_sheet_temp_oil.subsurface(off_rect_temp_oil)
    switch_state_temp_oil = False
    last_update_time_temp_oil = time.time()
    update_interval_temp_oil = 1.9

    # Загрузка напряжения бортовой сети
    try:
        sprite_sheet_Bort_Voltage = pygame.image.load("res/Bort_Voltage_1024_576.png").convert_alpha()
    except:
        print("Ошибка: Bort_Voltage_1024_576.png не найден.")
    v14_5_rect = pygame.Rect(0,   0, 116, 121)
    v13_6_rect = pygame.Rect(0, 121, 116, 121)
    v12_8_rect = pygame.Rect(0, 242, 116, 121)
    v14_5_image = sprite_sheet_Bort_Voltage.subsurface(v14_5_rect)
    v13_6_image = sprite_sheet_Bort_Voltage.subsurface(v13_6_rect)
    v12_8_image = sprite_sheet_Bort_Voltage.subsurface(v12_8_rect)
    switch_state_Bort_Voltage = 145
    last_update_time_Bort_Voltage = time.time()
    update_interval_Bort_Voltage = 1.3

    # Загрузка шрифта времени
    main_shrift = 'Arial'
    time_font = pygame.font.SysFont(main_shrift, 46,bold=True)

    # Загрузка шрифта скорости
    font = pygame.font.SysFont(main_shrift, 70,bold=False)




    angle_rmp = 125  # Начальный угол
    angle = 0      # Начальный угол

    # Основной цикл
    clock = pygame.time.Clock()

    ccw = -1
    toup = True

    toup_rmp = True

    fuel_y = 0
    R2 = 0

    # Таймеры
    last_update_time = time.time()
    update_interval = 0.25  # Обновлять скорость каждые 0.5 секунды
    speed_text = font.render(f"{int(angle*0.73)}", True, WHITE)



    while not stop_event.is_set():
        start_time = time.time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_event.set()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Выход по ESC
                    stop_event.set()

        # Обновление угла стрелки Скорости(имитация данных)
        if angle < 119 and toup == True:
            angle = (angle + 1) % 120
        elif angle == 0 or angle < 0.1:
            toup = True
        else:
            angle = (angle - 1) % 120
            toup = False

        # Обновление угла стрелки RMP(имитация данных)
        #angle_rmp = (angle_rmp + 1) % 115
        if angle_rmp < 114 and toup_rmp == True:
            angle_rmp = (angle_rmp + 1) % 115
        elif angle_rmp == 0:
            toup_rmp = True
        else:
            angle_rmp = (angle_rmp - 1) % 115
            toup_rmp = False

        # Отрисовка
        screen.blit(background, (0, 0))

        # Вращение стрелки Скорости
        rotated_needle = pygame.transform.rotozoom(needle_img, ccw * (angle + 228),1)  # Минус для правильного направления
        new_rect = rotated_needle.get_rect(center=needle_rect.center)
        screen.blit(rotated_needle, new_rect.topleft)

        # Вращение стрелки RMP
        rotated_rmp = pygame.transform.rotozoom(rmp_img, -1 * (angle_rmp + 15),1)  # 15...130
        new_rect = rotated_rmp.get_rect(center=rmp_rect.center)
        screen.blit(rotated_rmp, new_rect.topleft)

        # Изменение уровня
        try:
            R2 = que[0].get_nowait()
            que[0].task_done()
        except Empty:
            print(f"Очередь que[0] пуста, используются предыдущие данные R2: {R2}")

        fuel_y = int((300 - R2) * (94 / 300)) % 94   

        # Вычисляем высоту бензина
        fuel_level = 0.98 - (fuel_y / 94)

        # В игровом цикле:
        current_fuel_height = int(empty_canister_img.get_height() * fuel_level)
        # Рисуем пустую канистру
        screen.blit(empty_canister_img, (954, 109))
        # Рисуем часть полной канистры
        if fuel_level > 0:
            # Создаем subsurface (более эффективно)
            fuel_rect = pygame.Rect(0, empty_canister_img.get_height() - current_fuel_height,
                                    empty_canister_img.get_width(), current_fuel_height)
            fuel_part = full_canister_img.subsurface(fuel_rect)
    
            # Рисуем на правильной позиции
            screen.blit(fuel_part, (954, 109 + (empty_canister_img.get_height() - current_fuel_height)))
        
        screen.blit(level_img, (1024 - 66 - 19 , 109+ fuel_y))  # Просто рисуем в нужной позиции

        #Отображение времени
        current_time = datetime.now()
        time_text = time_font.render(current_time.strftime("%H:%M"), True, (160, 160, 160))
        screen.blit(time_text, (668, 75))  # Правый верхний угол

        #Отображение скорости километры в час
        current_time = time.time()
        if current_time - last_update_time > update_interval:
            last_update_time = current_time
            speed_text = font.render(f"{int(angle*0.73)}", True, WHITE)
        screen.blit(speed_text, (480, 25))

        # Отображаем вентилятор
        current_time = time.time()
        if current_time - last_update_time_cooler > update_interval_cooler:
            last_update_time_cooler = current_time
            if switch_state_cooler:
                switch_state_cooler = False
            else:
                switch_state_cooler = True
        if switch_state_cooler:
            screen.blit(on_image, (641, 503))  # Рисуем состояние "вкл"
        else:
            screen.blit(off_image, (641, 503))  # Рисуем состояние "выкл"

        # Отображаем масленку
        current_time = time.time()
        if current_time - last_update_time_maslenka > update_interval_maslenka:
            last_update_time_maslenka = current_time
            if switch_state_maslenka:
                switch_state_maslenka = False
            else:
                switch_state_maslenka = True
        if switch_state_maslenka:
            screen.blit(on_image_maslenka, (700, 514))  # Рисуем состояние "вкл"
        else:
            screen.blit(off_image_maslenka, (700, 514))  # Рисуем состояние "выкл"

        # Отображаем температуру масла
        current_time = time.time()
        if current_time - last_update_time_temp_oil > update_interval_temp_oil:
            last_update_time_temp_oil = current_time
            if switch_state_temp_oil:
                switch_state_temp_oil = False
            else:
                switch_state_temp_oil = True
        if switch_state_temp_oil:
            screen.blit(on_image_temp_oil, (780, 497))  # Рисуем состояние "вкл"
        else:
            screen.blit(off_image_temp_oil, (780, 497))  # Рисуем состояние "выкл"

        # Отображаем напряжение бортовой сети
        current_time = time.time()
        if current_time - last_update_time_Bort_Voltage > update_interval_Bort_Voltage:
            last_update_time_Bort_Voltage = current_time
            if switch_state_Bort_Voltage == 145:
                switch_state_Bort_Voltage = 136
            elif switch_state_Bort_Voltage == 136:
                switch_state_Bort_Voltage = 128
            else:
                switch_state_Bort_Voltage = 145
        if switch_state_Bort_Voltage == 145:
            screen.blit(v14_5_image, (852, 418))  
        elif switch_state_Bort_Voltage == 136:
            screen.blit(v13_6_image, (852, 418))  
        else:
            screen.blit(v12_8_image, (852, 418))

        pygame.display.flip()
        # Адаптивное ожидание FPS = frame_time + wait_time
        frame_time = time.time() - start_time
        target_time = 1.0 / 40 #60FPS
        wait_time = max(0.005, target_time - frame_time)
        #print(f"frame_time: {frame_time:.3f} temp CPU: {get_cpu_temp():.1f}°C")
        stop_event.wait(wait_time)
    pygame.quit()
