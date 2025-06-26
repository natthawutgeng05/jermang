@echo off
echo Starting YOLO Training...
echo.

cd training
python train_yolo.py

if errorlevel 1 (
    echo.
    echo Training failed!
    echo Make sure you have annotated images in the dataset folder.
    pause
    exit /b 1
)

echo.
echo Training completed!
pause
