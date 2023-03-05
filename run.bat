@echo off

set "dir=%~dp0"

if exist "%dir%\venv" (
    echo "Virtual environment already exists"
) else (
    python -m venv "%dir%\venv"
)

call "%dir%\venv\Scripts\activate"

echo "Installing requirements"
pip install -r requirements.txt

echo "Running"
python bot.py