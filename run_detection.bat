@echo off
echo Desktop Insect Detection Tool
echo =============================
echo.
echo 1. Desktop Detection Tool (Recommended)
echo 2. Camera Detection (Command Line)
echo 3. Image Detection (Command Line)  
echo 4. Batch Detection (Command Line)
echo.
set /p choice="Select option (1-4): "

cd detection

if "%choice%"=="1" (
    echo Starting desktop detection tool...
    python desktop_detection_tool.py
) else if "%choice%"=="2" (
    echo Starting camera detection...
    python detect_camera.py --model ../training/models/insect_detector_best.pt
) else if "%choice%"=="3" (
    set /p imagepath="Enter image path: "
    python detect_image.py --model ../training/models/insect_detector_best.pt --input "%imagepath%"
) else if "%choice%"=="4" (
    set /p folderpath="Enter folder path: "
    python detect_image.py --model ../training/models/insect_detector_best.pt --input "%folderpath%" --batch
) else (
    echo Invalid choice!
)

pause
