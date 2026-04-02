# DICOM Support Documentation

## Overview

The Medical Scan Data Extractor now supports **DICOM (Digital Imaging and Communications in Medicine)** format in addition to JPEG and PNG images.

## Supported File Formats

| Format | Extension | Extraction Method |
|--------|-----------|-------------------|
| DICOM | `.dcm`, `.DCM` | Metadata + OCR |
| JPEG | `.jpg`, `.jpeg` | OCR only |
| PNG | `.png` | OCR only |
| BMP | `.bmp` | OCR only |

## DICOM Extraction Features

### Data Extracted from DICOM Metadata

DICOM files contain structured metadata that can be extracted with **100% accuracy**:

| Field | DICOM Tag | Description |
|-------|-----------|-------------|
| Patient Name | (0010,0010) | Name of the patient |
| Patient ID | (0010,0020) | Unique patient identifier |
| Study Date | (0008,0020) | Date of examination (YYYYMMDD) |
| Modality | (0008,0060) | Type of exam (CT, MR, etc.) |
| Study Description | (0008,1030) | Detailed exam description |

### Data Extracted via OCR

For dose-specific values that may not be in standard DICOM tags:

| Field | Method | Description |
|-------|--------|-------------|
| CTDIvol | OCR | Radiation dose index (mGy) |
| Total DLP | OCR | Total radiation dose (mGy·cm) |

## How It Works

### Extraction Process

```
┌─────────────────────────────────────────────────────────┐
│                  DICOM File (.dcm)                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Read DICOM Metadata   │
        │  (pydicom library)     │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │  Extract Available     │
        │  Fields from Tags      │
        └────────┬───────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │  Have All Fields?      │
        │  (CTDIvol, DLP, etc.)  │
        └────────┬───────────────┘
                 │
        ┌────────┴────────┐
        │                 │
       YES               NO
        │                 │
        │                 ▼
        │      ┌────────────────────────┐
        │      │  Extract Pixel Array   │
        │      │  Convert to Image      │
        │      └────────┬───────────────┘
        │               │
        │               ▼
        │      ┌────────────────────────┐
        │      │  Perform OCR on Image  │
        │      │  (Tesseract)           │
        │      └────────┬───────────────┘
        │               │
        │               ▼
        │      ┌────────────────────────┐
        │      │  Merge Results         │
        │      │  (Metadata priority)   │
        │      └────────┬───────────────┘
        │               │
        └───────────────┘
                │
                ▼
        ┌────────────────────────┐
        │  Final Extracted Data  │
        │  - nama_pasien         │
        │  - tanggal_pemeriksaan │
        │  - id_pasien           │
        │  - jenis_pemeriksaan   │
        │  - ctdi_vol            │
        │  - total_dlp           │
        └────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.10+
- Tesseract OCR installed
- Required Python packages (see `requirements.txt`)

### Install Dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:
```
pydicom>=3.0.0        # DICOM file support
pytesseract>=0.3.10   # OCR
Pillow>=10.0.0        # Image processing
opencv-python-headless>=4.8.0  # Image processing
openpyxl>=3.1.0       # Excel file support
```

## Usage

### Batch Processing (Recommended)

1. **Place your files** in the `hasil scan` folder:
   - DICOM files (.dcm)
   - Or dose report images (JPEG, PNG)

2. **Run the batch processor**:
   ```bash
   python batch_process.py
   ```

3. **Results** will be saved to `Rekap.xlsx`

### Example Output

```
📁 Found 5 file(s) to process:
   1. CT001.dcm (DCM)
   2. CT002.dcm (DCM)
   3. scan_report.jpg (JPG)
   4. dose_report.png (PNG)
   5. CT003.dcm (DCM)

============================================================
🚀 Starting batch processing...
============================================================

[1/5] Processing: CT001.dcm
   📋 Source: DICOM metadata + OCR
   ✅ Success! (Row 2)
      - Nama Pasien: JOHN DOE
      - Tanggal Pemeriksaan: 15 Mar 2026
      - ID Pasien: 123456
      - CTDIvol: 7.89 mGy
      - Total DLP: 410.12 mGy·cm

...

============================================================
📊 Processing Summary
============================================================
   Total Files: 5
   DICOM Files: 3
   ✅ Successful: 5
   ❌ Failed: 0
   📁 Output File: Rekap.xlsx
============================================================

✅ Batch processing completed! 5 record(s) saved to 'Rekap.xlsx'
```

### Programmatic Usage

```python
from ocr_extractor import MedicalScanExtractor

# Initialize extractor
extractor = MedicalScanExtractor()

# Extract from DICOM file
result = extractor.extract_from_dicom("path/to/file.dcm")

print(result)
# Output:
# {
#     'nama_pasien': 'JOHN DOE',
#     'tanggal_pemeriksaan': '15 Mar 2026',
#     'id_pasien': '123456',
#     'jenis_pemeriksaan': 'CT ABDOMEN',
#     'ctdi_vol': '7.89',
#     'total_dlp': '410.12'
# }

# Extract from image (JPEG/PNG)
result = extractor.extract_data("path/to/image.jpg")
```

## Advantages of DICOM Format

### vs. Image (JPEG/PNG)

| Aspect | DICOM | Image (JPEG/PNG) |
|--------|-------|------------------|
| **Patient Name** | ✅ 100% accurate | ⚠️ OCR dependent |
| **Patient ID** | ✅ 100% accurate | ⚠️ OCR dependent |
| **Exam Date** | ✅ 100% accurate | ⚠️ OCR dependent |
| **CTDIvol** | ⚠️ From OCR | ⚠️ From OCR |
| **Total DLP** | ⚠️ From OCR | ⚠️ From OCR |
| **Image Quality** | ✅ Original data | ⚠️ Photo quality |
| **Processing Speed** | ✅ Fast | ⚠️ Slower (OCR) |

### Why DICOM is Better

1. **No OCR Errors**: Metadata is digital text, not affected by image quality
2. **Standardized Format**: DICOM tags are consistent across manufacturers
3. **Complete Data**: All patient information is included
4. **Original Quality**: No loss from photographing screens

## Troubleshooting

### DICOM File Not Reading

**Problem**: `pydicom.errors.InvalidDicomError`

**Solution**: Ensure the file is a valid DICOM file. Some files may be DICOM images without dose report data.

### Missing CTDIvol/DLP from DICOM

**Problem**: These fields are `None` even with DICOM

**Solution**: CTDIvol and DLP are typically not in standard DICOM tags. They're extracted from the dose report image using OCR. Ensure the DICOM file contains the dose report image.

### Poor OCR Results

**Problem**: Patient name or other fields are incorrect

**Solution**: 
1. Use DICOM files instead of photos (metadata is 100% accurate)
2. If using images, ensure:
   - Good lighting
   - High resolution (HD)
   - No blur or shadows
   - Screen is flat (no angle)

## File Structure

```
wahid idea/
├── ocr_extractor.py       # Main extraction module
├── batch_process.py       # Batch processing script
├── excel_handler.py       # Excel file handling
├── requirements.txt       # Python dependencies
├── test_dicom.py         # DICOM support test script
├── DICOM_SUPPORT.md      # This documentation
└── hasil scan/           # Input folder
    ├── CT001.dcm
    ├── CT002.dcm
    └── scan_report.jpg
```

## Next Steps

1. **Test with your DICOM files**: Place files in `hasil scan` folder
2. **Run batch processing**: `python batch_process.py`
3. **Review results**: Open `Rekap.xlsx` to see extracted data
4. **Provide feedback**: Report any issues or suggestions

## Support

For issues or questions:
- Check this documentation
- Run `python test_dicom.py` to verify setup
- Review error messages in console output
