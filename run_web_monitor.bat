@echo off
echo Starting Web-based Insect Detection Monitor
echo ==========================================
echo.

cd /d "%~dp0detection"

echo Web Monitor Features:
echo    - Real-time video streaming
echo    - Mobile-responsive interface
echo    - Remote monitoring capability
echo    - YOLO11 auto-detection
echo.

echo Starting web server...
echo Access from computer: http://localhost:5000
echo Access from mobile: http://[your-ip-address]:5000/mobile
echo.

python web_monitor.py --host 0.0.0.0 --port 5000

if %ERRORLEVEL% neq 0 (
    echo.
    echo Web monitor failed to start
    echo Make sure Flask dependencies are installed
    pause
) else (
    echo.
    echo Web monitor stopped
)
