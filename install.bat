@echo off
echo Installing Insect Detection System...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo Python found!
python --version

echo.
echo Installing dependencies...
python setup.py

if errorlevel 1 (
    echo.
    echo Installation failed!
    pause
    exit /b 1
)

echo.
echo Installation completed successfully!
echo.
echo You can now:
echo 1. Run annotation tool: run_annotation_tool.bat
echo 2. Train model: run_training.bat  
echo 3. Run detection: run_detection.bat
echo.
pause
