"""
Complete Build Script - Creates Professional Windows Installer
This script:
1. Builds the application with PyInstaller
2. Creates a professional .exe installer using Inno Setup
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_prerequisites():
    """Check if all required tools are installed"""
    print("=" * 70)
    print("🔍 Checking Prerequisites")
    print("=" * 70)
    
    issues = []
    
    # Check PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller: Installed")
    except ImportError:
        print("❌ PyInstaller: NOT FOUND")
        issues.append("PyInstaller")
    
    # Check Tesseract
    tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    tesseract_found = any(os.path.exists(p) for p in tesseract_paths)
    if tesseract_found:
        print("✅ Tesseract OCR: Found")
    else:
        print("⚠️  Tesseract OCR: NOT FOUND (user will be prompted to install)")
    
    # Check Inno Setup
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]
    inno_found = any(os.path.exists(p) for p in inno_paths)
    if inno_found:
        print("✅ Inno Setup: Found")
    else:
        print("❌ Inno Setup: NOT FOUND")
        issues.append("Inno Setup")
    
    if issues:
        print("\n" + "=" * 70)
        print("⚠️  Missing Prerequisites:")
        print("=" * 70)
        if "PyInstaller" in issues:
            print("\n1. Install PyInstaller:")
            print("   pip install pyinstaller")
        if "Inno Setup" in issues:
            print("\n2. Download & Install Inno Setup:")
            print("   https://jrsoftware.org/isdl.php")
            print("   Install to default location")
        print()
        return False
    
    print("\n✅ All prerequisites met!\n")
    return True

def build_with_pyinstaller():
    """Build the application using PyInstaller"""
    print("=" * 70)
    print("🔨 Step 1: Building with PyInstaller")
    print("=" * 70)
    
    # Clean previous builds
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"🗑️  Cleaned: {folder}")
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "RadiationDoseRecorder",
        "--onedir",
        "--windowed",
        "--icon", "NONE",
        "--add-data", f"app.py{os.pathsep}.",
        "--add-data", f"ocr_extractor.py{os.pathsep}.",
        "--add-data", f"excel_handler.py{os.pathsep}.",
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
    
    print("\n🚀 Running PyInstaller...")
    try:
        subprocess.check_call(cmd)
        print("✅ PyInstaller build successful!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ PyInstaller build failed: {e}\n")
        return False

def compile_inno_setup():
    """Compile Inno Setup script to create installer"""
    print("=" * 70)
    print("📦 Step 2: Creating Windows Installer (.exe)")
    print("=" * 70)
    
    # Find Inno Setup compiler
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]
    
    iscc_path = None
    for path in inno_paths:
        if os.path.exists(path):
            iscc_path = path
            break
    
    if not iscc_path:
        print("❌ Inno Setup compiler not found!")
        print("Please install Inno Setup from: https://jrsoftware.org/isdl.php")
        return False
    
    print(f"✅ Found Inno Setup: {iscc_path}")
    
    # Compile the .iss script
    iss_file = "radiation_dose_recorder.iss"
    if not os.path.exists(iss_file):
        print(f"❌ Inno Setup script not found: {iss_file}")
        return False
    
    print(f"\n🚀 Compiling installer from: {iss_file}")
    try:
        subprocess.check_call([iscc_path, iss_file])
        print("✅ Installer compiled successfully!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Installer compilation failed: {e}\n")
        return False

def main():
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  🏥 Radiation Dose Recorder - Windows Installer Builder".ljust(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        print("❌ Please install missing prerequisites and try again.")
        sys.exit(1)
    
    # Build with PyInstaller
    if not build_with_pyinstaller():
        print("❌ PyInstaller build failed!")
        sys.exit(1)
    
    # Compile Inno Setup
    if not compile_inno_setup():
        print("⚠️  Inno Setup compilation failed!")
        print("You can still distribute the PyInstaller build manually.")
        print("Location: dist/RadiationDoseRecorder/")
    else:
        print("=" * 70)
        print("🎉 BUILD COMPLETE!")
        print("=" * 70)
        print()
        print("📁 Installer Location:")
        print("   installer_output/RadiationDoseRecorder_Setup.exe")
        print()
        print("📋 Distribution Instructions:")
        print("   1. Share the .exe installer file")
        print("   2. User double-clicks to install")
        print("   3. Application installs and runs automatically")
        print()
        print("✨ Your professional Windows installer is ready!")
        print()

if __name__ == "__main__":
    main()
