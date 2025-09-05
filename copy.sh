#!/bin/bash

# Скрипт для копирования файлов на удаленный сервер
echo "Начало копирования файлов..."

# Копируем папки и файлы
scp -r res/ vasilii@192.168.0.107:/home/vasilii/panel_work/
scp -r .vscode/ vasilii@192.168.0.107:/home/vasilii/panel_work/
scp bt.py vasilii@192.168.0.107:/home/vasilii/panel_work/
scp check_env.py vasilii@192.168.0.107:/home/vasilii/panel_work/
scp dashboard.py vasilii@192.168.0.107:/home/vasilii/panel_work/
scp gpio.py vasilii@192.168.0.107:/home/vasilii/panel_work/
scp i2c.py vasilii@192.168.0.107:/home/vasilii/panel_work/
scp main.py vasilii@192.168.0.107:/home/vasilii/panel_work/
scp uart.py vasilii@192.168.0.107:/home/vasilii/panel_work/
scp usb.py vasilii@192.168.0.107:/home/vasilii/panel_work/

echo "Копирование завершено!"