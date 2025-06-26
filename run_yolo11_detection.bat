@echo off
echo 🚀 เริ่มโปรแกรมตรวจจับแมลง YOLO11
echo ====================================
echo.

cd /d "%~dp0detection"

echo 💡 โหลด YOLO11 เป็น default model...
echo    - ขนาดเล็ก (~6MB)
echo    - ความแม่นยำสูง
echo    - ประมวลผลเร็ว
echo.

python desktop_detection_tool.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ เกิดข้อผิดพลาด
    pause
) else (
    echo.
    echo ✅ ปิดโปรแกรมเรียบร้อย
)
