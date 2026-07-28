@echo off
rem AI CAD Studio 一键启动脚本（自动创建虚拟环境并安装依赖）
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+ 并勾选 "Add to PATH"。
    pause
    exit /b 1
)

if not exist ".venv" (
    echo 正在创建虚拟环境...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

python -c "import PySide6" 2>nul
if errorlevel 1 (
    echo 正在安装依赖（首次运行需要几分钟）...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo 启动 AI CAD Studio...
python main.py
if errorlevel 1 pause
