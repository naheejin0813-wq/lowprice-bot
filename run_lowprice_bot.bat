@echo off
chcp 65001 > nul
setlocal

set "PYTHON_EXE="
if exist "C:\Users\나희진\AppData\Local\Programs\Thonny\python.exe" (
    set "PYTHON_EXE=C:\Users\나희진\AppData\Local\Programs\Thonny\python.exe"
) else (
    for %%P in (python.exe py.exe) do (
        where %%P >nul 2>nul && set "PYTHON_EXE=%%P"
    )
)

if "%PYTHON_EXE%"=="" (
    echo [오류] Python 실행 경로를 찾을 수 없습니다.
    pause
    exit /b 1
)

cd /d "%~dp0"
"%PYTHON_EXE%" lowprice_bot.py %*

echo.
pause
