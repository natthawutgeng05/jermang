@echo off
echo Desktop Insect Detection Tool (YOLO11)
echo =========================================
echo.
echo Detection Options (YOLO11 Recommended):
echo 1. Desktop Detection Tool (YOLO11 Auto-Load)
echo 2. Camera Detection (Command Line)
echo 3. Image Detection (Command Line)  
echo 4. Batch Detection (Command Line)
echo.
set /p choice="Select option (1-4): "

cd detection

if "%choice%"=="1" (
    echo Starting YOLO11 desktop detection tool...
    echo    Auto-loading YOLO11 model automatically
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
