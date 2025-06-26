@echo off
echo Starting YOLO11 Insect Detection Tool
echo ====================================
echo.

cd /d "%~dp0detection"

echo Loading YOLO11 as default model...
echo    - Small size (~6MB)
echo    - High accuracy
echo    - Fast processing
echo.

python desktop_detection_tool.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo Error occurred during execution
    pause
) else (
    echo.
    echo Program closed successfully
)
