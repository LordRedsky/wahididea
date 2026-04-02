@echo off
REM Balitbang Muna Extractor - Quick Build Script
REM This script builds the Windows executable

echo ============================================================
echo  Balitbang Muna Extractor - Build Script
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python found!
echo.

REM Install build dependencies
echo Installing build dependencies...
pip install pyinstaller>=5.0.0
echo.

REM Run the build script
echo Running build script...
python build\build_exe.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Build completed successfully!
echo ============================================================
echo.
echo Next steps:
echo 1. Check the 'build\installer' folder for the built files
echo 2. Use Inno Setup to create the installer
echo    - Open 'build\installer.iss' with Inno Setup Compiler
echo    - Click Build ^> Compile
echo.
echo The installer will be created in 'installer_output\' folder
echo.
pause
