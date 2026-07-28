@echo off
rem 用 PyInstaller 打包为独立 exe（输出在 dist\AI-CAD-Studio\）
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv" (
    echo 请先运行 run.bat 完成环境初始化。
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
pip show pyinstaller >nul 2>nul || pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple

pyinstaller --noconfirm --clean --windowed --name "AI-CAD-Studio" ^
    --collect-submodules app ^
    --hidden-import win32com --hidden-import win32com.client --hidden-import pythoncom ^
    --hidden-import serial ^
    main.py

echo.
echo 打包完成：dist\AI-CAD-Studio\AI-CAD-Studio.exe
pause
