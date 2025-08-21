import pygame
import sys
import time
import datetime

def scale_image(image, factor):
    """Масштабирует изображение с сохранением пропорций"""
    new_size = (int(image.get_width() * factor), 
                int(image.get_height() * factor))
    return pygame.transform.scale(image, new_size)
# Цвета
BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
# Настройки окна
WIDTH, HEIGHT = 1024, 576  # разрешение экрана в linux
# Инициализация
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Приборная панель")

# Загрузка фона
try:
    background = pygame.image.load("res/dashboard_1024_576.png").convert()  # Фон
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
except:
    print("Ошибка: dashboard.jpg не найден. Использую чёрный фон.")
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill((0, 0, 0))

# Загрузка стрелки скорости
try:
    needle_img = pygame.image.load("res/arrowkmh_1024_576.png").convert_alpha()  # Важно!
    # Уменьшаем в 0.8 раза (50% от оригинала)
    # needle_img = scale_image(needle_img, 0.4)
    needle_rect = needle_img.get_rect(center=(294, 242))
except:
    print("Ошибка: arrowkmh_1024_576.png не найден. Создаю красный прямоугольник.")

# Загрузка стрелки RMP
try:
    rmp_img = pygame.image.load("res/arrowRMP_1024_576.png").convert_alpha()  # Важно!
    rmp_rect = rmp_img.get_rect(center=(294, 242))
except:
    print("Ошибка: arrowRMP_1024_576.png не найден. Создаю красный прямоугольник.")

# Загрузка стрелки уровня
try:
    level_img = pygame.image.load("res/level_arrow_1024_576.png").convert_alpha()  # Важно!
    #level_rect = level_img.get_rect(center=(969, 111))
except:
    print("Ошибка: level_arrow_1024_576.png не найден. Создаю красный прямоугольник.")

# Загрузка канистры
try:
    canister_img = pygame.image.load("res/canister_1024_576.png").convert_alpha()
    canister_rect = canister_img.get_rect()
except:
    print("Ошибка: canister_1024_576.png не найден. Создаю красный прямоугольник.")

# Загрузка шрифта времени
main_shrift = 'Arial'
time_font = pygame.font.SysFont(main_shrift, 48,bold=True)
# Загрузка шрифта скорости
font = pygame.font.SysFont(main_shrift, 70,bold=False)


angle_rmp = 125  # Начальный угол
angle = 0      # Начальный угол

# Основной цикл
clock = pygame.time.Clock()
running = True
ccw = -1
toup = True

toup_rmp = True

fuel_y = 0
todown_fuel = True

# Таймеры
last_update_time = time.time()
update_interval = 0.25  # Обновлять скорость каждые 0.5 секунды
speed_text = font.render(f"{int(angle*0.73)}", True, WHITE)
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Обновление угла стрелки Скорости(имитация данных)
    if angle < 119 and toup == True:
        angle = (angle + 1) % 120
    elif angle == 0:
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
    rotated_needle = pygame.transform.rotate(needle_img, ccw * (angle + 228))  # Минус для правильного направления
    new_rect = rotated_needle.get_rect(center=needle_rect.center)
    screen.blit(rotated_needle, new_rect.topleft)

    # Вращение стрелки RMP
    rotated_rmp = pygame.transform.rotate(rmp_img, -1 * (angle_rmp + 15))  # 15...130
    new_rect = rotated_rmp.get_rect(center=rmp_rect.center)
    screen.blit(rotated_rmp, new_rect.topleft)

    # Рисуем канистру
    screen.blit(canister_img, (954, 109))

    # Рисуем бензин в канистре
    # Вычисляем высоту бензина
    fuel_level = 1 - (fuel_y / 94)
    GASOLINE_COLOR = (43, 0, 181)  # Синий для бензина
    current_fuel_height = int(canister_img.get_height() * fuel_level) 
    # 1. Создаём поверхность для бензина  
    gasoline_surface = pygame.Surface(canister_img.get_size(), pygame.SRCALPHA)
    # 2. Закрашиваем область бензина
    fuel_area = pygame.Rect(0, canister_img.get_height() - current_fuel_height, 
                          canister_img.get_width(), current_fuel_height)
    pygame.draw.rect(gasoline_surface, GASOLINE_COLOR, fuel_area)
    # 3. Используем канистру как маску - бензин появится только там, где канистра непрозрачна
    gasoline_surface.blit(canister_img, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    # 4. Рисуем бензин на экране
    screen.blit(gasoline_surface, (954, 109))
    
    # Изменение уровня
    #fuel_y =  (fuel_y + 1 ) % 94 #MIN_Y + (MAX_Y - MIN_Y) * (1 - fuel_level)
    if fuel_y < 93 and todown_fuel == True:
        fuel_y = (fuel_y + 1) % 94
    elif fuel_y == 0:
        todown_fuel = True
    else:
        fuel_y = (fuel_y - 1) % 94
        todown_fuel = False
    screen.blit(level_img, (1024 - 66 - 19 , 110+ fuel_y))  # Просто рисуем в нужной позиции

    #Отображение времени
    current_time = datetime.datetime.now()
    time_text = time_font.render(current_time.strftime("%H:%M"), True, (160, 160, 160))
    screen.blit(time_text, (668, 75))  # Правый верхний угол

    #Отображение скорости километры в час
    current_time = time.time()
    if current_time - last_update_time > update_interval:
        last_update_time = current_time
        # Обновление скорости
        speed_text = font.render(f"{int(angle*0.73)}", True, WHITE)
        #speed_text = font.render(f"{int(43)}", True, WHITE)
    screen.blit(speed_text, (480, 25))

    pygame.display.flip()
    clock.tick(60)  # 60 FPS

pygame.quit()
sys.exit()