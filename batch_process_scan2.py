"""
Batch Process Script for Medical Scan Images from "hasil scan 2" folder
Processes all DICOM files (with or without extension) and saves to Rekap.xlsx
Supports: DICOM files (.dcm) and medical scan files without extension
"""

import os
import sys
from datetime import datetime
from ocr_extractor import MedicalScanExtractor
from excel_handler import ExcelHandler


def is_dicom_file(filepath: str) -> bool:
    """Check if a file is DICOM format by reading magic number (DICM at offset 128)"""
    try:
        with open(filepath, 'rb') as f:
            # DICOM files have 'DICM' marker at byte offset 128
            f.seek(128)
            magic = f.read(4)
            return magic == b'DICM'
    except Exception:
        return False


def get_dicom_files(folder_path: str) -> list:
    """Get all DICOM files from folder (including files without extension)"""
    dicom_files = []

    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        
        # Skip directories
        if os.path.isdir(filepath):
            continue
            
        ext = os.path.splitext(filename)[1].lower()
        
        # Check if it's a DICOM file by extension or by magic number
        if ext in {'.dcm', '.dcm', '.dicom'}:
            dicom_files.append(filepath)
        elif ext == '':
            # Files without extension - check if DICOM
            if is_dicom_file(filepath):
                dicom_files.append(filepath)
        elif ext in {'.jpg', '.jpeg', '.png', '.bmp'}:
            # Also include regular images
            dicom_files.append(filepath)

    return sorted(dicom_files)


def main():
    """Main batch processing function for hasil scan 2 folder"""
    # Configuration
    scan_folder = "hasil scan 2"
    excel_filename = "Rekap.xlsx"
    
    # Check if folder exists
    if not os.path.exists(scan_folder):
        print(f"❌ Error: Folder '{scan_folder}' not found!")
        return
    
    # Get all DICOM files
    dicom_files = get_dicom_files(scan_folder)
    
    if not dicom_files:
        print(f"❌ No DICOM files found in '{scan_folder}' folder!")
        print("   Supported formats: DICOM (.dcm), DICOM (no extension), JPEG, PNG")
        return
    
    print(f"📁 Found {len(dicom_files)} file(s) to process:")
    for i, img in enumerate(dicom_files, 1):
        ext = os.path.splitext(img)[1].upper()
        file_size = os.path.getsize(img)
        print(f"   {i}. {os.path.basename(img)} ({ext or 'NO EXT'}, {file_size:,} bytes)")
    print()
    
    # Initialize handlers
    print("🔧 Initializing OCR extractor and Excel handler...")
    extractor = MedicalScanExtractor()
    excel_handler = ExcelHandler(excel_filename)
    
    # Check if Excel file exists
    if os.path.exists(excel_filename):
        existing_count = excel_handler.get_record_count()
        print(f"⚠️  Excel file '{excel_filename}' already exists with {existing_count} record(s).")
        print("   Clearing existing data for fresh batch...")
        excel_handler.clear_all_data()
    else:
        print(f"   Creating new Excel file: {excel_filename}")
    
    print()
    print("=" * 60)
    print("🚀 Starting batch processing...")
    print("=" * 60)
    print()
    
    # Process each image
    success_count = 0
    failed_count = 0
    dicom_count = 0
    results = []
    
    for i, image_path in enumerate(dicom_files, 1):
        filename = os.path.basename(image_path)
        ext = os.path.splitext(filename)[1].lower()
        
        print(f"[{i}/{len(dicom_files)}] Processing: {filename}")
        
        try:
            # Check if DICOM file (by extension or magic number)
            is_dicom = ext == '.dcm' or (ext == '' and is_dicom_file(image_path))
            
            if is_dicom:
                dicom_count += 1
                print(f"   📋 Detected: DICOM file (magic number at offset 128)")
                # Use extract_from_dicom which combines metadata + OCR
                extracted_data = extractor.extract_from_dicom(image_path)
                print(f"   📋 Source: DICOM metadata + OCR")
            else:
                extracted_data = extractor.extract_data(image_path)
            
            # Check if we got meaningful data
            has_data = any([
                extracted_data.get('nama_pasien'),
                extracted_data.get('id_pasien'),
                extracted_data.get('ctdi_vol'),
                extracted_data.get('total_dlp')
            ])
            
            if has_data:
                # Add to Excel
                row_num = excel_handler.add_record(extracted_data)
                
                # Display results
                print(f"   ✅ Success! (Row {row_num + 1})")
                print(f"      - Nama Pasien: {extracted_data.get('nama_pasien', 'N/A')}")
                print(f"      - Tanggal Pemeriksaan: {extracted_data.get('tanggal_pemeriksaan', 'N/A')}")
                print(f"      - ID Pasien: {extracted_data.get('id_pasien', 'N/A')}")
                print(f"      - CTDIvol: {extracted_data.get('ctdi_vol', 'N/A')} mGy")
                print(f"      - Total DLP: {extracted_data.get('total_dlp', 'N/A')} mGy·cm")
                success_count += 1
                results.append({
                    'file': filename,
                    'status': 'success',
                    'data': extracted_data
                })
            else:
                print(f"   ⚠️  No meaningful data extracted")
                failed_count += 1
                results.append({
                    'file': filename,
                    'status': 'failed',
                    'reason': 'No data extracted'
                })
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            failed_count += 1
            results.append({
                'file': filename,
                'status': 'error',
                'error': str(e)
            })
        
        print()
    
    # Summary
    print("=" * 60)
    print("📊 Processing Summary")
    print("=" * 60)
    print(f"   Total Files: {len(dicom_files)}")
    print(f"   DICOM Files: {dicom_count}")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📁 Output File: {excel_filename}")
    print("=" * 60)
    
    if success_count > 0:
        print(f"\n✅ Batch processing completed! {success_count} record(s) saved to '{excel_filename}'")
    else:
        print("\n⚠️  No data was successfully extracted. Please check the images and try again.")
    
    return results


if __name__ == "__main__":
    main()
