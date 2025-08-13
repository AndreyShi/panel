import pygame
import sys

def scale_image(image, factor):
    """Масштабирует изображение с сохранением пропорций"""
    new_size = (int(image.get_width() * factor), 
                int(image.get_height() * factor))
    return pygame.transform.scale(image, new_size)

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
    needle_img = scale_image(needle_img, 0.5)
    needle_rect = needle_img.get_rect(center=(460, 380))
except:
    print("Ошибка: needle.png не найден. Создаю красный прямоугольник.")
    needle_img = pygame.Surface((20, 150), pygame.SRCALPHA)
    pygame.draw.rect(needle_img, (255, 0, 0), (0, 0, 20, 150))
    needle_rect = needle_img.get_rect(center=(450, 240))

angle = 295  # Начальный угол

# Основной цикл
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Обновление угла (имитация данных)
    #angle = (angle + 1) % 360

    # Отрисовка
    screen.blit(background, (0, 0))

    # Вращение стрелки
    rotated_needle = pygame.transform.rotate(needle_img, -angle)  # Минус для правильного направления
    new_rect = rotated_needle.get_rect(center=needle_rect.center)
    screen.blit(rotated_needle, new_rect.topleft)

    pygame.display.flip()
    clock.tick(60)  # 60 FPS

pygame.quit()
sys.exit()