@echo off
title Radiation Dose Recorder
echo ========================================
echo Radiation Dose Recorder
echo ========================================
echo.
echo Starting application...
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: Check if Tesseract is installed
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo [OK] Tesseract OCR found
) else (
    echo [WARNING] Tesseract OCR not found!
    echo Please install from: https://github.com/UB-Mannheim/tesseract/wiki
    echo.
)

:: Install dependencies if needed
if not exist "venv" (
    echo Setting up virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

echo.
echo Starting application...
echo The browser will open automatically.
echo.
echo Press Ctrl+C to stop the application.
echo.

:: Run launcher
python launcher.py

pause
