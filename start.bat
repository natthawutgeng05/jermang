@echo off
title Insect Detection System - YOLO11
color 0A

:MAIN_MENU
cls
echo.
echo     ===============================================
echo       Insect Detection System (YOLO11)
echo     ===============================================
echo.
echo     Select the tool you want to use:
echo.
echo     1. Annotation Tool (for labeling images)
echo     2. Model Training (YOLO11 Default)
echo     3. Detection Tool (YOLO11 Auto-Load)
echo     4. Model Comparison (YOLOv8 vs v10 vs v11)
echo     5. Install/Setup System
echo     6. User Manual
echo     7. Exit Program
echo.
echo     ===============================================
echo.

set /p choice="Please select (1-7): "

if "%choice%"=="1" goto ANNOTATION
if "%choice%"=="2" goto TRAINING  
if "%choice%"=="3" goto DETECTION
if "%choice%"=="4" goto COMPARISON
if "%choice%"=="5" goto SETUP
if "%choice%"=="6" goto HELP
if "%choice%"=="7" goto EXIT
goto INVALID

:ANNOTATION
cls
echo.
echo Starting Annotation Tool...
echo.
call run_annotation_tool.bat
goto MAIN_MENU

:TRAINING
cls
echo.
echo Starting YOLO11 Model Training...
echo.
call run_yolo11_training.bat
goto MAIN_MENU

:DETECTION  
cls
echo.
echo Starting YOLO11 Detection Tool...
echo.
call run_yolo11_detection.bat
goto MAIN_MENU

:COMPARISON
cls
echo.
echo Starting Model Comparison...
echo.
call run_model_comparison.bat
goto MAIN_MENU

:SETUP
cls
echo.
echo Installing and Setting up System...
echo.
call install.bat
echo.
echo Installation completed!
pause
goto MAIN_MENU

:HELP
cls
echo.
echo User Manual - Insect Detection System
echo ========================================
echo.
echo Usage Steps:
echo.
echo 1. Install System (Menu 5) - Do this once when starting
echo 2. Add insect images to dataset/images/ folder
echo 3. Use Annotation Tool (Menu 1) to label images
echo 4. Train Model (Menu 2) when you have enough annotations
echo 5. Use Detection Tool (Menu 3) to test the model
echo.
echo Usage Tips:
echo.
echo • Need at least 100+ annotations per class
echo • Use diverse images (angles, lighting, backgrounds)
echo • Adjust confidence threshold in detection tool
echo • Save results and statistics regularly
echo.
echo File Structure:
echo.
echo dataset/images/      - Place original images here
echo dataset/annotations/ - Annotation files (auto-created)
echo training/models/     - Trained models
echo detection/output/    - Saved detection results
echo.
echo If you encounter problems:
echo.
echo • Check if Python 3.8+ is installed
echo • Try reinstalling system (Menu 5)
echo • Check requirements.txt
echo.
pause
goto MAIN_MENU

:INVALID
cls
echo.
echo Invalid option. Please select again (1-7)
echo.
pause
goto MAIN_MENU

:EXIT
cls
echo.
echo Thank you for using Insect Detection System!
echo.
echo Happy Bug Detecting!
echo.
pause
exit
