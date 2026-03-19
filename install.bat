@echo off
chcp 65001 >nul 2>&1
title ติดตั้งระบบตรวจจับแมลง
color 0A

echo.
echo  ============================================================
echo   🐛  ระบบตรวจจับแมลง - Insect Detection System             🐛
echo  ============================================================
echo.
echo  กำลังติดตั้งระบบ... กรุณารอสักครู่
echo.

REM ตรวจสอบว่ามี Python ติดตั้งแล้วหรือยัง
python --version >nul 2>&1
if errorlevel 1 (
    echo  ❌  ไม่พบ Python หรือ Python ยังไม่ได้เพิ่มใน PATH
    echo.
    echo  กรุณาติดตั้ง Python 3.8 หรือสูงกว่าก่อน
    echo  ดาวน์โหลดได้ที่: https://www.python.org/downloads/
    echo.
    echo  ⚠️  อย่าลืมเลือก "Add Python to PATH" ระหว่างติดตั้ง
    echo.
    pause
    exit /b 1
)

echo  ✅  พบ Python:
python --version
echo.

REM รันสคริปต์ติดตั้งหลัก
echo  📦  กำลังติดตั้ง dependencies...
echo.
python setup.py

if errorlevel 1 (
    echo.
    echo  ❌  การติดตั้งล้มเหลว!
    echo.
    echo  คุณสามารถลองติดตั้งเองด้วยคำสั่ง:
    echo     pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   ✅  ติดตั้งเสร็จสมบูรณ์!
echo  ============================================================
echo.
echo  คุณสามารถใช้งานระบบได้ดังนี้:
echo.
echo    1. เปิดโปรแกรม Annotation  ->  run_annotation_tool.bat
echo    2. เริ่ม Train โมเดล       ->  run_training.bat
echo    3. เปิดโปรแกรมตรวจจับ     ->  run_detection.bat
echo    4. เมนูหลัก                ->  start.bat
echo.
echo  ============================================================
echo.
pause
