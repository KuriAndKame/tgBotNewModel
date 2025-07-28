@echo off
setlocal enabledelayedexpansion

REM Название лог-файла
set LOG_FILE=parser_log.txt

REM Указание пути до скрипта (если нужно)
set SCRIPT=tg_scraper.py

REM Цикл автоматического перезапуска
:LOOP
echo.
echo [%date% %time%] ==== PARSER TG-CHANNEL SCRIPT START ==== 
echo [%date% %time%] ==== PARSER ON AIR ==== >> %LOG_FILE%

python %SCRIPT% >> %LOG_FILE% 2>&1

echo [%date% %time%] ---- PARSER IS STOPPED OR FINISHED ----
echo [%date% %time%] ---- ПPARSER IS STOPPED OR FINISHED ---- >> %LOG_FILE%

echo RELOADIND 5 SECOND...
timeout /t 5 /nobreak >nul
goto LOOP
