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

### 2. Tesseract OCR (Required for Local Development)
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

### Local Development

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Verify Tesseract installation:**
```bash
tesseract --version
```

### Deploy to Streamlit Cloud

**No Tesseract installation needed!** The `apt-packages.txt` file will automatically install Tesseract on Streamlit Cloud.

1. Push your code to GitHub

2. Go to [share.streamlit.io](https://share.streamlit.io)

3. Click "New app" and select your repository

4. Configure:
   - **Main file path:** `app.py`
   - **Python version:** 3.10 or higher

5. Click "Deploy!"

> **Note:** The `apt-packages.txt` file tells Streamlit Cloud to install Tesseract OCR automatically.

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
├── apt-packages.txt        # Linux packages for Streamlit Cloud (Tesseract)
├── .streamlit/
│   └── config.toml         # Streamlit configuration
├── Rekap.xlsx              # Output Excel file (auto-generated)
└── README.md               # This file
```

## Configuration

### Tesseract Path
The application automatically detects the Tesseract path based on your operating system:

- **Windows:** `C:\Program Files\Tesseract-OCR\tesseract.exe`
- **Linux:** `/usr/bin/tesseract`
- **macOS:** `/opt/homebrew/bin/tesseract`

No manual configuration needed!

## Deployment Options

### Option 1: Streamlit Cloud (Recommended)

**Pros:** Free, easy setup, automatic Tesseract installation via `apt-packages.txt`

**Steps:**
1. Push code to GitHub
2. Deploy at [share.streamlit.io](https://share.streamlit.io)
3. Select your repository and deploy

### Option 2: Self-hosted on VPS

**Pros:** Full control, custom domain

**Requirements:**
- Ubuntu/Debian server
- Python 3.10+

**Installation:**
```bash
# Install Tesseract
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-ind

# Install Python dependencies
pip install -r requirements.txt

# Run with Streamlit
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Option 3: Docker

Create a `Dockerfile`:
```dockerfile
FROM python:3.10-slim

# Install Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

## Future Enhancements

- Google Sheets integration for cloud storage
- Batch image processing
- Data validation and correction interface
- Export to multiple formats (CSV, PDF)
- User authentication
- Historical data analytics

## Troubleshooting

### OCR not working on Streamlit Cloud:
- Ensure `apt-packages.txt` exists in your repository root
- Check deployment logs for Tesseract installation errors
- Verify `requirements.txt` includes `pytesseract`

### OCR not working locally:
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

### "Tesseract not found" error:
- **Local:** Install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki
- **Streamlit Cloud:** Ensure `apt-packages.txt` is in your repository

## License

This project is for educational and research purposes.

## Support

For issues or questions, please create an issue in the project repository.
