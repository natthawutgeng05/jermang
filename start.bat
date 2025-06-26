@echo off
title Insect Detection System
color 0A

:MAIN_MENU
cls
echo.
echo     ===============================================
echo     🐛 ระบบตรวจจับแมลง - Insect Detection System 🐛
echo     ===============================================
echo.
echo     เลือกเครื่องมือที่ต้องการใช้งาน:
echo.
echo     1. 🏷️  เครื่องมือ Annotation (สำหรับติดป้ายกำกับ)
echo     2. 🤖  การ Train โมเดล
echo     3. 🔍  เครื่องมือตรวจจับแมลง
echo     4. ⚙️  ติดตั้งและตั้งค่าระบบ
echo     5. 📖  คู่มือการใช้งาน
echo     6. ❌  ออกจากโปรแกรม
echo.
echo     ===============================================
echo.

set /p choice="กรุณาเลือก (1-6): "

if "%choice%"=="1" goto ANNOTATION
if "%choice%"=="2" goto TRAINING  
if "%choice%"=="3" goto DETECTION
if "%choice%"=="4" goto SETUP
if "%choice%"=="5" goto HELP
if "%choice%"=="6" goto EXIT
goto INVALID

:ANNOTATION
cls
echo.
echo 🏷️ กำลังเปิดเครื่องมือ Annotation...
echo.
call run_annotation_tool.bat
goto MAIN_MENU

:TRAINING
cls
echo.
echo 🤖 กำลังเริ่มการ Train โมเดล...
echo.
call run_training.bat
goto MAIN_MENU

:DETECTION  
cls
echo.
echo 🔍 กำลังเปิดเครื่องมือตรวจจับแมลง...
echo.
call run_detection.bat
goto MAIN_MENU

:SETUP
cls
echo.
echo ⚙️ กำลังติดตั้งและตั้งค่าระบบ...
echo.
call install.bat
echo.
echo การติดตั้งเสร็จสิ้น!
pause
goto MAIN_MENU

:HELP
cls
echo.
echo 📖 คู่มือการใช้งานระบบตรวจจับแมลง
echo ========================================
echo.
echo 🔄 ขั้นตอนการใช้งาน:
echo.
echo 1. ติดตั้งระบบ (เมนู 4) - ทำครั้งเดียวตอนเริ่มใช้งาน
echo 2. เพิ่มรูปภาพแมลงลงในโฟลเดอร์ dataset/images/
echo 3. ใช้เครื่องมือ Annotation (เมนู 1) เพื่อติดป้ายกำกับ
echo 4. Train โมเดล (เมนู 2) เมื่อมีข้อมูล annotation พอแล้ว
echo 5. ใช้เครื่องมือตรวจจับ (เมนู 3) เพื่อทดสอบโมเดล
echo.
echo 💡 เทคนิคการใช้งาน:
echo.
echo • ควรมี annotation อย่างน้อย 100+ รูปต่อคลาส
echo • ใช้รูปภาพที่หลากหลาย (มุมมอง แสง พื้นหลัง)
echo • ปรับ confidence threshold ในเครื่องมือตรวจจับ
echo • บันทึกผลลัพธ์และสถิติเป็นประจำ
echo.
echo 📁 โครงสร้างไฟล์:
echo.
echo dataset/images/      - ใส่รูปภาพต้นฉบับ
echo dataset/annotations/ - ไฟล์ annotation (สร้างอัตโนมัติ)
echo training/models/     - โมเดลที่ train แล้ว
echo detection/output/    - ผลการตรวจจับที่บันทึก
echo.
echo ⚠️  หากพบปัญหา:
echo.
echo • ตรวจสอบว่าติดตั้ง Python 3.8+ แล้ว
echo • ลองติดตั้งระบบใหม่ (เมนู 4)
echo • ตรวจสอบ requirements.txt
echo.
pause
goto MAIN_MENU

:INVALID
cls
echo.
echo ❌ ตัวเลือกไม่ถูกต้อง กรุณาเลือกใหม่ (1-6)
echo.
pause
goto MAIN_MENU

:EXIT
cls
echo.
echo 👋 ขอบคุณที่ใช้ระบบตรวจจับแมลง!
echo.
echo 🐛 Happy Bug Detecting! 🐛
echo.
pause
exit
