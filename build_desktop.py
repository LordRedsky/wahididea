"""
Build script to create offline Windows desktop application
"""
import os
import subprocess
import sys
import shutil

def check_requirements():
    """Check if all required tools are installed"""
    print("🔍 Checking requirements...")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller installed")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed")
    
    # Check Tesseract
    tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    
    tesseract_found = any(os.path.exists(path) for path in tesseract_paths)
    if tesseract_found:
        print("✅ Tesseract OCR found")
    else:
        print("⚠️  Tesseract OCR not found!")
        print("📥 Please install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   Default installation path: C:\\Program Files\\Tesseract-OCR")
        return False
    
    return True

def build_executable():
    """Build the desktop application"""
    print("\n🔨 Building desktop application...")
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "RadiationDoseRecorder",
        "--onedir",
        "--windowed",
        "--icon", "NONE",
        "--add-data", "app.py;.",
        "--add-data", "ocr_extractor.py;.",
        "--add-data", "excel_handler.py;.",
        "--hidden-import", "streamlit",
        "--hidden-import", "plotly",
        "--hidden-import", "plotly.express",
        "--hidden-import", "plotly.graph_objects",
        "--hidden-import", "pandas",
        "--hidden-import", "openpyxl",
        "--hidden-import", "pytesseract",
        "--hidden-import", "PIL",
        "--hidden-import", "cv2",
        "--hidden-import", "numpy",
        "--collect-all", "streamlit",
        "--collect-all", "plotly",
        "--collect-all", "pandas",
        "launcher.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("\n✅ Build successful!")
        print("📁 Output directory: dist/RadiationDoseRecorder/")
        print("🚀 Run: dist/RadiationDoseRecorder/RadiationDoseRecorder.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        return False

def create_installer():
    """Create a simple installer script"""
    installer_content = """@echo off
echo ========================================
echo Radiation Dose Recorder - Setup
echo ========================================
echo.

:: Check if Tesseract is installed
if exist "C:\\Program Files\\Tesseract-OCR\\tesseract.exe" (
    echo [OK] Tesseract OCR is installed
) else (
    echo [WARNING] Tesseract OCR not found!
    echo.
    echo Please install Tesseract OCR first:
    echo 1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. Install to default location
    echo 3. Run this installer again
    echo.
    pause
    exit /b 1
)

:: Create desktop shortcut
echo Creating desktop shortcut...
set SCRIPT="%TEMP%\\CreateShortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\\Radiation Dose Recorder.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%~dp0RadiationDoseRecorder.exe" >> %SCRIPT%
echo oLink.WorkingDirectory = "%~dp0" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo You can now run Radiation Dose Recorder from:
echo - Desktop shortcut
echo - Start Menu
echo - Or directly: RadiationDoseRecorder.exe
echo.
pause
"""
    
    with open("setup.bat", "w") as f:
        f.write(installer_content)
    
    print("✅ Created setup.bat installer")

def main():
    print("=" * 60)
    print("🏥 Radiation Dose Recorder - Desktop Builder")
    print("=" * 60)
    print()
    
    if not check_requirements():
        print("\n❌ Requirements check failed. Please install missing dependencies.")
        sys.exit(1)
    
    build_executable()
    create_installer()
    
    print("\n" + "=" * 60)
    print("📦 Build Summary")
    print("=" * 60)
    print("✅ Executable: dist/RadiationDoseRecorder/RadiationDoseRecorder.exe")
    print("✅ Installer: setup.bat")
    print("✅ Ready for offline use!")
    print()
    print("To distribute:")
    print("1. Copy the entire dist/RadiationDoseRecorder folder")
    print("2. Run setup.bat on target machine")
    print("3. Application will work offline!")

if __name__ == "__main__":
    main()
