# 🏥 Cara Membuat Installer .exe - Radiation Dose Recorder

## 📋 Langkah-langkah (Step by Step)

### Step 1: Install Prerequisites

#### 1.1 Install Inno Setup (WAJIB)
Inno Setup adalah tool gratis untuk membuat installer Windows profesional.

**Download:** https://jrsoftware.org/isdl.php

**Install:**
1. Download `innosetup-6.x.x.exe`
2. Jalankan installer
3. Install ke default location
4. Selesai!

#### 1.2 Install PyInstaller
```bash
pip install pyinstaller
```

### Step 2: Build Aplikasi

Jalankan script build otomatis:

```bash
python build_installer.py
```

Script ini akan:
1. ✅ Cek semua prerequisites
2. 🔨 Build aplikasi dengan PyInstaller
3. 📦 Compile installer dengan Inno Setup
4. ✨ Hasil: `installer_output/RadiationDoseRecorder_Setup.exe`

### Step 3: Distribusi Installer

File installer ada di:
```
installer_output/RadiationDoseRecorder_Setup.exe
```

**Bagikan file ini ke user!**

## 🎯 Cara User Menginstall

User tinggal:
1. **Download** file `RadiationDoseRecorder_Setup.exe`
2. **Double-click** file installer
3. **Klik Next** pada wizard installation
4. **Finish** - Aplikasi terinstall dan siap digunakan!

## 📁 Output Structure

Setelah build berhasil:
```
installer_output/
└── RadiationDoseRecorder_Setup.exe  ← BAGIKAN FILE INI
```

## 🔧 Troubleshooting

### Error: "Inno Setup not found"
**Solusi:**
1. Download dari: https://jrsoftware.org/isdl.php
2. Install ke default location
3. Jalankan `build_installer.py` lagi

### Error: "PyInstaller not found"
**Solusi:**
```bash
pip install pyinstaller
```

### Build gagal di tengah
**Solusi:**
1. Pastikan semua dependencies terinstall: `pip install -r requirements.txt`
2. Hapus folder `build` dan `dist`
3. Jalankan `build_installer.py` lagi

## 💡 Tips

- **File size:** Installer sekitar 100-200MB (termasuk semua dependencies)
- **Custom icon:** Tambahkan file `.ico` dan update `SetupIconFile` di `.iss`
- **Version number:** Update di bagian `#define` di file `.iss`
- **Language:** Installer support Bahasa Indonesia & English

## 📊 Fitur Installer

✅ **Professional Wizard** - Seperti installer Windows biasa
✅ **Auto Tesseract Check** - Cek & prompt install Tesseract jika belum ada
✅ **Desktop Shortcut** - Otomatis buat shortcut di desktop
✅ **Start Menu Entry** - Tambah ke Start Menu
✅ **Uninstaller** - Bisa uninstall via Control Panel
✅ **Silent Install** - Support `/SILENT` dan `/VERYSILENT` flag

## 🎨 Customisasi Installer

Edit file `radiation_dose_recorder.iss` untuk:
- Ganti nama aplikasi
- Ganti versi
- Ganti publisher name
- Tambah license agreement
- Ganti icon installer
- Custom installation path

## 📤 Distribusi

### Opsi 1: Direct Download
Upload file `.exe` ke:
- Google Drive
- Dropbox
- Website perusahaan
- Email attachment (jika < 25MB)

### Opsi 2: Cloud Storage
Upload ke cloud dan share link download

### Opsi 3: USB Flash Drive
Copy file `.exe` ke USB dan distribusikan secara fisik

---

**Author:** Abdurrahman Wahid, ST
**Project:** AKTUALISASI LATSAR CPNS 2026
**Version:** 1.0
