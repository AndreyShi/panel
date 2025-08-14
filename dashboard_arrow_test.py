import pygame
import sys
import time

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
WIDTH, HEIGHT = 1607, 906
# Инициализация
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Приборная панель")

# Загрузка фона и стрелки
try:
    background = pygame.image.load("dashboard.png").convert()  # Фон
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
except:
    print("Ошибка: dashboard.jpg не найден. Использую чёрный фон.")
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill((0, 0, 0))

# Загрузка стрелки с прозрачностью
try:
    needle_img = pygame.image.load("needle.png").convert_alpha()  # Важно!
    # Уменьшаем в 0.5 раза (50% от оригинала)
    needle_img = scale_image(needle_img, 0.51)
    needle_rect = needle_img.get_rect(center=(463, 383))
except:
    print("Ошибка: needle.png не найден. Создаю красный прямоугольник.")
    needle_img = pygame.Surface((20, 150), pygame.SRCALPHA)
    pygame.draw.rect(needle_img, (255, 0, 0), (0, 0, 20, 150))
    needle_rect = needle_img.get_rect(center=(450, 240))

angle = 0  # Начальный угол

# Основной цикл
clock = pygame.time.Clock()
running = True
ccw = -1
toup = True

# Добавление текста (скорость, RPM)
font = pygame.font.SysFont('Arial', 133)
# Таймеры
last_update_time = time.time()
update_interval = 0.25  # Обновлять скорость каждые 0.5 секунды
speed_text = font.render(f"{int(angle*0.73)}", True, WHITE)
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Обновление угла (имитация данных)
    if angle < 109 and toup == True:
        angle = (angle + 1) % 110
    elif angle == 0:
        toup = True
    else:
        angle = (angle - 1) % 110
        toup = False

    # Отрисовка
    screen.blit(background, (0, 0))

    # Вращение стрелки
    rotated_needle = pygame.transform.rotate(needle_img, ccw * (angle + 228))  # Минус для правильного направления
    new_rect = rotated_needle.get_rect(center=needle_rect.center)
    screen.blit(rotated_needle, new_rect.topleft)

        # --- Обновление данных (реже, чем кадры) ---
    current_time = time.time()
    if current_time - last_update_time > update_interval:
        last_update_time = current_time
        # Обновление скорости
        speed_text = font.render(f"{int(angle*0.73)}", True, WHITE)
        #speed_text = font.render(f"{int(43)}", True, WHITE)
    screen.blit(speed_text, (730, 35))

    pygame.display.flip()
    clock.tick(60)  # 60 FPS

pygame.quit()
sys.exit()