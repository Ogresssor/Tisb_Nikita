@echo off
chcp 65001 >nul
title Informatsionnaya sistema Kinoteatr
python kinoteatr.py
if errorlevel 1 (
    echo.
    echo Ne udalos zapustit programmu.
    echo Proverte, chto ustanovlen Python 3 i otmechena galochka Add Python to PATH.
    pause
)
