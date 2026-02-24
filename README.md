# Medical Scan Data Extractor

A Streamlit application that extracts patient data from CT scan dose report images using OCR and saves the data to Excel.

## Features

- 📤 Upload CT scan dose report images (JPG, PNG)
- 🔍 Automatic data extraction using OCR (Tesseract)
- 📋 Extract fields:
  - Nama Pasien (Patient Name)
  - Tanggal Pemeriksaan (Examination Date)
  - ID Pasien (Patient ID)
  - Jenis Pemeriksaan (Exam Description)
  - CTDIvol (Radiation Dose)
  - Total DLP (Total Dose)
- 💾 Save extracted data to Excel (Rekap.xlsx)
- 📊 View and download Excel data

## Prerequisites

### 1. Python 3.10+
Make sure you have Python 3.10 or higher installed.

### 2. Tesseract OCR (Required)
Download and install Tesseract OCR:

**Windows:**
1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (recommended: `tesseract-ocr-w64-setup-5.x.x.exe`)
3. Install to default location: `C:\Program Files\Tesseract-OCR`
4. Add to PATH (optional during installation)

**Verify installation:**
```bash
tesseract --version
```

## Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Verify Tesseract installation:**
```bash
tesseract --version
```

## Usage

1. **Run the Streamlit app:**
```bash
streamlit run app.py
```

2. **Open your browser:**
The app will automatically open at `http://localhost:8501`

3. **Upload an image:**
   - Click "Browse files" or drag & drop a CT scan dose report image
   - Wait for the image to upload

4. **Extract data:**
   - Click "🔍 Extract Data" button
   - Wait for OCR processing

5. **Save to Excel:**
   - Review the extracted data
   - Click "💾 Save to Excel" to save to Rekap.xlsx

## Project Structure

```
wahid idea/
├── app.py                  # Main Streamlit application
├── ocr_extractor.py        # OCR extraction module
├── excel_handler.py        # Excel file handling
├── requirements.txt        # Python dependencies
├── Rekap.xlsx             # Output Excel file (auto-generated)
└── README.md              # This file
```

## Configuration

### Tesseract Path (Windows)
If Tesseract is not in your PATH, edit `ocr_extractor.py` and uncomment:

```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Future Enhancements

- Google Sheets integration for cloud storage
- Batch image processing
- Data validation and correction interface
- Export to multiple formats (CSV, PDF)
- User authentication
- Historical data analytics

## Troubleshooting

### OCR not working properly:
- Ensure Tesseract OCR is installed
- Check if Tesseract is in system PATH
- Verify image quality (clear, high contrast images work best)

### Poor extraction accuracy:
- Use higher resolution images
- Ensure text is clearly visible
- Avoid glare or shadows in the image

### Excel file not created:
- Check write permissions in the application directory
- Ensure no other program has the Excel file open

## License

This project is for educational and research purposes.

## Support

For issues or questions, please create an issue in the project repository.
