@echo off
echo YOLO Model Comparison Tool
echo ==========================
echo.

cd /d "%~dp0training"

echo Comparing YOLO models performance:
echo    - YOLOv8n (baseline)
echo    - YOLO10n (newer)
echo    - YOLO11n (latest, recommended)
echo.
echo This will run a quick training test for comparison...
echo.

python compare_yolo_models.py --epochs 5

if %ERRORLEVEL% neq 0 (
    echo.
    echo Model comparison failed
    pause
) else (
    echo.
    echo Model comparison completed successfully
    echo Check comparison/ folder for detailed results
    pause
)
