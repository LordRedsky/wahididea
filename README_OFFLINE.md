# 🏥 Radiation Dose Recorder - Offline Windows Application

## 🎯 Cara Menggunakan (Offline Mode)

### Metode 1: Quick Start (Paling Mudah)
**Untuk pengguna yang sudah memiliki Python terinstall:**

1. **Double-click** file: `run_offline.bat`
2. Aplikasi akan otomatis:
   - Setup virtual environment (pertama kali saja)
   - Install semua dependencies
   - Start server lokal
   - Buka browser otomatis
3. **Selesai!** Aplikasi siap digunakan offline

### Metode 2: Manual (Untuk Developer)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Jalankan aplikasi
python launcher.py
```

### Metode 3: Build Executable (Standalone App)
**Untuk membuat aplikasi .exe yang bisa didistribusikan:**

```bash
# Build executable
python build_desktop.py

# Hasil build ada di folder:
# dist/RadiationDoseRecorder/

# Untuk install di komputer lain:
# 1. Copy folder dist/RadiationDoseRecorder/ ke komputer target
# 2. Install Tesseract OCR di komputer target
# 3. Jalankan setup.bat untuk buat shortcut
# 4. Aplikasi siap digunakan!
```

## 📋 Requirements untuk Offline Use

### Wajib Install:
1. **Tesseract OCR**
   - Download: https://github.com/UB-Mannheim/tesseract/wiki
   - Install ke: `C:\Program Files\Tesseract-OCR`
   - Ini WAJIB untuk fitur OCR

### Otomatis Terinstall (via requirements.txt):
- ✅ Streamlit
- ✅ Plotly (untuk dashboard charts)
- ✅ Pandas (untuk data processing)
- ✅ OpenCV (untuk image processing)
- ✅ PyTesseract (OCR library)
- ✅ OpenPyXL (Excel handling)
- ✅ PyDICOM (DICOM file support)
- ✅ Pillow (image processing)

## 📁 Struktur File untuk Distribusi

```
RadiationDoseRecorder/
│
├── run_offline.bat          ← Double-click untuk jalankan
├── launcher.py              ← Launcher script
├── app.py                   ← Main application
├── ocr_extractor.py         ← OCR engine
├── excel_handler.py         ← Excel handler
├── requirements.txt         ← Dependencies
├── OFFLINE_GUIDE.md         ← Panduan lengkap
│
└── dist/                    ← Setelah build
    └── RadiationDoseRecorder/
        ├── RadiationDoseRecorder.exe  ← Standalone app
        ├── setup.bat                   ← Installer
        └── _internal/                  ← Dependencies
```

## 🚀 Cara Distribusi ke Komputer Lain

### Opsi A: Share Source Code + Installer
1. Zip seluruh folder project
2. Di komputer target:
   - Install Python 3.8+
   - Install Tesseract OCR
   - Extract folder
   - Double-click `run_offline.bat`

### Opsi B: Share Executable (Recommended)
1. Build executable: `python build_desktop.py`
2. Zip folder `dist/RadiationDoseRecorder/`
3. Di komputer target:
   - Install Tesseract OCR saja
   - Extract folder
   - Jalankan `setup.bat`
   - Aplikasi siap digunakan!

## 💡 Fitur Offline Mode

✅ **100% Offline** - Tidak perlu internet
✅ **Local Server** - Berjalan di localhost
✅ **Auto Browser** - Browser terbuka otomatis
✅ **Data Privacy** - Semua data tetap di PC lokal
✅ **No Cloud** - Tidak ada data yang dikirim ke internet
✅ **Fast** - Lebih cepat karena berjalan lokal

## 🔧 Troubleshooting

### Error: "Tesseract is not installed"
**Solusi:**
1. Download Tesseract dari: https://github.com/UB-Mannheim/tesseract/wiki
2. Install ke default location
3. Restart aplikasi

### Error: "Module not found"
**Solusi:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Error: "Port already in use"
**Solusi:**
- Aplikasi otomatis cari port lain yang free
- Atau close aplikasi lain yang menggunakan Streamlit

### Browser tidak terbuka otomatis
**Solusi:**
- Buka manual: `http://localhost:8501`
- Atau cek console output untuk port yang digunakan

## 📊 Performa

- **Startup Time:** ~3-5 detik
- **Memory Usage:** ~200-300MB
- **CPU Usage:** ~5-10% (idle)
- **Storage:** ~500MB (termasuk dependencies)

## 🎓 Tips Penggunaan

1. **Pertama kali:** Setup virtual environment otomatis
2. **Data tersimpan:** File Excel di folder yang sama
3. **Close aplikasi:** Tutup console window atau Ctrl+C
4. **Backup data:** Copy file `Rekap.xlsx` secara berkala

---

**Author:** Abdurrahman Wahid, ST
**Project:** AKTUALISASI LATSAR CPNS 2026
**Version:** 1.0
