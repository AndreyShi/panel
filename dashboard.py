import pygame
import sys
import math

# Инициализация Pygame
pygame.init()

# Настройки окна
WIDTH, HEIGHT = 1607, 906
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Приборная панель")

# Цвета
BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

# Загрузка изображений
try:
    background = pygame.image.load("dashboard.png").convert()  # Фоновая панель
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
except:
    print("Ошибка: не найден файл dashboard.png. Создаю чёрный фон.")
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill(BLACK)
    # Рисуем заглушку спидометра
    pygame.draw.circle(background, WHITE, (WIDTH//2, HEIGHT//2), 150, 5)

# Параметры стрелки
needle_img = pygame.Surface((20, 150), pygame.SRCALPHA)  # Прозрачная поверхность
pygame.draw.rect(needle_img, RED, (0, 0, 20, 150))  # Красная стрелка
needle_rect = needle_img.get_rect(center=(WIDTH//2, HEIGHT//2))
angle = 0  # Начальный угол

# Основной цикл
clock = pygame.time.Clock()
running = True

# Добавление текста (скорость, RPM)
font = pygame.font.SysFont('Arial', 130)



while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Обновление угла (имитация данных)
    angle = (angle + 1) % 360

    # Отрисовка
    screen.blit(background, (0, 0))

    # Вращение стрелки
    rotated_needle = pygame.transform.rotate(needle_img, -angle)  # Отрицательный угол для правильного направления
    new_rect = rotated_needle.get_rect(center=needle_rect.center)
    screen.blit(rotated_needle, new_rect.topleft)

    # Обновление скорости
    speed_text = font.render(f"{int(angle/3.6)}", True, WHITE)
    #speed_text = font.render(f"{int(43)}", True, WHITE)
    screen.blit(speed_text, (590, 10))

    pygame.display.flip()
    clock.tick(60)  # 60 FPS

pygame.quit()
sys.exit()