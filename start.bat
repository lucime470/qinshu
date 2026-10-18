@echo off
chcp 65001 >nul
cd /d %~dp0
if not exist .venv (
  py -3 -m venv .venv
  if errorlevel 1 (
    echo 无法创建虚拟环境，请先安装 Python 3.10 或更高版本。
    pause
    exit /b 1
  )
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo 依赖安装失败，请检查网络或 requirements.txt。
  pause
  exit /b 1
)
python app.py
if errorlevel 1 pause
