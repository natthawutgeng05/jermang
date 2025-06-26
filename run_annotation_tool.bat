@echo off
echo Starting Desktop Insect Annotation Tool...
echo.

cd annotation_tool
python desktop_annotation_tool.py

if errorlevel 1 (
    echo.
    echo Failed to start annotation tool!
    echo Make sure you have installed the requirements first.
    echo.
    echo Alternative: You can also use the web version:
    echo python app.py
    pause
    exit /b 1
)

pause
