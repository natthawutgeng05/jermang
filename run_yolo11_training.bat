@echo off
echo 🏋️ เริ่ม Training ด้วย YOLO11
echo ==============================
echo.

cd /d "%~dp0training"

echo 🚀 YOLO11 Training:
echo    - ประสิทธิภาพสูงสุด
echo    - ความแม่นยำดีที่สุด
echo    - รองรับ GPU acceleration
echo.

python train_yolo.py --model_version yolo11 --epochs 100

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ การ Training ล้มเหลว
    pause
) else (
    echo.
    echo ✅ Training เสร็จสมบูรณ์
    echo 📁 โมเดลที่ train แล้วอยู่ใน training/models/
    pause
)
