@echo off
xcopy res          C:\temp\res\     /E /I /Y >nul
xcopy .vscode      C:\temp\.vscode\ /E /I /Y >nul
xcopy bt.py        C:\temp\         /Y       >nul
xcopy check_env.py C:\temp\         /Y       >nul
xcopy dashboard.py C:\temp\         /Y       >nul
xcopy gpio.py      C:\temp\         /Y       >nul
xcopy i2c.py       C:\temp\         /Y       >nul
xcopy main.py      C:\temp\         /Y       >nul
xcopy uart.py      C:\temp\         /Y       >nul
xcopy usb.py       C:\temp\         /Y       >nul
echo copying completed!