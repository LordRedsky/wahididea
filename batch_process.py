"""
Batch Process Script for Medical Scan Images
Processes all images in 'hasil scan' folder and saves to Rekap.xlsx
Supports: JPEG, PNG, and DICOM (.dcm or no extension) formats
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


def get_image_files(folder_path: str) -> list:
    """Get all image files from folder (JPEG, PNG, DICOM)"""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.dcm', '.DCM'}
    image_files = []

    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        
        # Skip directories
        if os.path.isdir(filepath):
            continue
            
        ext = os.path.splitext(filename)[1].lower()
        
        # Check if it's a valid image extension
        if ext in valid_extensions:
            image_files.append(filepath)
        # Also check for DICOM files without extension (medical scans from "hasil scan 2")
        elif ext == '' or ext not in {'.txt', '.exe', '.pdf', '.doc', '.xls'}:
            # Try to detect DICOM by magic number
            if is_dicom_file(filepath):
                image_files.append(filepath)

    return sorted(image_files)


def main():
    """Main batch processing function"""
    # Configuration
    scan_folder = "hasil scan"
    excel_filename = "Rekap.xlsx"
    
    # Check if folder exists
    if not os.path.exists(scan_folder):
        print(f"❌ Error: Folder '{scan_folder}' not found!")
        return
    
    # Get all image files
    image_files = get_image_files(scan_folder)
    
    if not image_files:
        print(f"❌ No image files found in '{scan_folder}' folder!")
        print("   Supported formats: JPEG, PNG, DICOM (.dcm)")
        return
    
    print(f"📁 Found {len(image_files)} file(s) to process:")
    for i, img in enumerate(image_files, 1):
        ext = os.path.splitext(img)[1].upper()
        print(f"   {i}. {os.path.basename(img)} ({ext})")
    print()
    
    # Initialize handlers
    print("🔧 Initializing OCR extractor and Excel handler...")
    extractor = MedicalScanExtractor()
    excel_handler = ExcelHandler(excel_filename)
    
    # Check if Excel file exists and clear it for fresh data
    if os.path.exists(excel_filename):
        existing_count = excel_handler.get_record_count()
        print(f"⚠️  Excel file '{excel_filename}' already exists with {existing_count} record(s).")
        print("   Clearing existing data for fresh batch...")
        excel_handler.clear_all_data()
    
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
    
    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        ext = os.path.splitext(filename)[1].lower()
        
        print(f"[{i}/{len(image_files)}] Processing: {filename}")
        
        try:
            # Check if DICOM file
            if ext == '.dcm':
                dicom_count += 1
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
    print(f"   Total Files: {len(image_files)}")
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
