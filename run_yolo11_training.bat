@echo off
echo Starting YOLO11 Training
echo ==============================
echo.

cd /d "%~dp0training"

echo YOLO11 Training Features:
echo    - Best performance
echo    - Highest accuracy  
echo    - GPU acceleration support
echo.

python train_yolo.py --model_version yolo11 --epochs 100

if %ERRORLEVEL% neq 0 (
    echo.
    echo Training failed
    pause
) else (
    echo.
    echo Training completed successfully
    echo Trained models are saved in training/models/
    pause
)
