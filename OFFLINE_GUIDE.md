# 🏥 Radiation Dose Recorder - Offline Windows Installation Guide

## 📋 Prerequisites

### 1. Install Tesseract OCR
Tesseract is required for OCR functionality.

**Download:** https://github.com/UB-Mannheim/tesseract/wiki

**Installation Steps:**
1. Download the Windows installer
2. Run the installer
3. Install to default location: `C:\Program Files\Tesseract-OCR`
4. Make sure to check "Additional language data" if needed
5. Complete the installation

## 🚀 Quick Start (Development Mode)

If you have Python installed and want to run the app directly:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python launcher.py
```

The application will automatically:
- Start a local server
- Open your default browser
- Work completely offline!

## 📦 Build Desktop Application (Standalone EXE)

Create a standalone Windows application that doesn't require Python:

```bash
# Run the build script
python build_desktop.py
```

This will:
1. Check all requirements
2. Build executable with PyInstaller
3. Create `setup.bat` installer

### After Building:

1. Navigate to `dist/RadiationDoseRecorder/`
2. Run `setup.bat` to create desktop shortcut
3. Launch from desktop or start menu

## 📁 Distribution Package

To distribute to other computers:

1. **Copy the entire folder:**
   ```
   RadiationDoseRecorder/
   ├── RadiationDoseRecorder.exe
   ├── _internal/
   └── (all other files)
   ```

2. **On target computer:**
   - Install Tesseract OCR first
   - Copy the folder
   - Run `RadiationDoseRecorder.exe`

## 🔧 Troubleshooting

### Tesseract Not Found
**Error:** `Tesseract is not installed or not in PATH`

**Solution:**
1. Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: `C:\Program Files\Tesseract-OCR`
3. Restart the application

### Port Already in Use
**Error:** `Address already in use`

**Solution:**
- The app automatically finds a free port
- Close any other Streamlit apps running
- Or restart your computer

### Application Won't Start
**Solution:**
1. Check if Python is installed: `python --version`
2. Install dependencies: `pip install -r requirements.txt`
3. Run launcher directly: `python launcher.py`

### Browser Doesn't Open
**Solution:**
- Manually open browser and go to: `http://localhost:8501`
- Or check the console output for the correct port number

## 💡 Features

✅ **100% Offline** - No internet required
✅ **Local Server** - Runs on your PC only
✅ **Auto Browser** - Opens automatically
✅ **Easy Distribution** - Share with colleagues
✅ **Data Privacy** - All data stays on your PC

## 📊 System Requirements

- **OS:** Windows 10/11
- **RAM:** 4GB minimum (8GB recommended)
- **Storage:** 500MB free space
- **Tesseract OCR:** Required
- **Python:** 3.8+ (for development mode only)

## 🎯 Usage Tips

1. **First Run:** May take a few seconds to start
2. **Multiple Instances:** Each instance uses a different port
3. **Closing:** Close the console window to stop the app
4. **Data Location:** Excel files saved in the same folder

## 📞 Support

For issues or questions:
- Check the console output for error messages
- Ensure Tesseract is properly installed
- Verify all dependencies are installed

---

**Built with:** Streamlit, Python, Tesseract OCR
**Version:** 1.0
**Author:** Abdurrahman Wahid, ST
**Project:** AKTUALISASI LATSAR CPNS 2026
