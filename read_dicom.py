"""
Read DICOM files from DCOM folder and extract data for Rekap.xlsx
Extracts: Nama Pasien, Tanggal Pemeriksaan, ID Pasien, Jenis Pemeriksaan, CTDIvol, Total DLP
"""

import os
import pydicom
from datetime import datetime
from ocr_extractor import MedicalScanExtractor
from excel_handler import ExcelHandler


def convert_date(study_date):
    """Convert DICOM date format (YYYYMMDD) to DD Mon YYYY"""
    if not study_date or len(study_date) != 8:
        return study_date
    
    try:
        year = study_date[0:4]
        month = study_date[4:6]
        day = study_date[6:8]
        
        month_names = {
            '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
            '05': 'Mei', '06': 'Jun', '07': 'Jul', '08': 'Agu',
            '09': 'Sep', '10': 'Okt', '11': 'Nov', '12': 'Des'
        }
        month_name = month_names.get(month, month)
        return f"{day} {month_name} {year}"
    except Exception:
        return study_date


def extract_dicom_data(dicom_path):
    """Extract data from DICOM file for Rekap.xlsx"""
    ds = pydicom.dcmread(dicom_path)
    
    # Initialize result with None values
    result = {
        'nama_pasien': None,
        'tanggal_pemeriksaan': None,
        'id_pasien': None,
        'jenis_pemeriksaan': None,
        'ctdi_vol': None,
        'total_dlp': None,
    }
    
    # Extract from DICOM metadata
    if hasattr(ds, 'PatientName') and ds.PatientName:
        result['nama_pasien'] = str(ds.PatientName)
    
    if hasattr(ds, 'PatientID') and ds.PatientID:
        result['id_pasien'] = str(ds.PatientID)
    
    if hasattr(ds, 'StudyDate') and ds.StudyDate:
        result['tanggal_pemeriksaan'] = convert_date(str(ds.StudyDate))
    
    if hasattr(ds, 'StudyDescription') and ds.StudyDescription:
        result['jenis_pemeriksaan'] = str(ds.StudyDescription)
    elif hasattr(ds, 'Modality') and ds.Modality:
        result['jenis_pemeriksaan'] = str(ds.Modality)
    
    # Try to get CTDIvol and DLP from DICOM metadata
    # Method 1: Direct CTDIvol and DLP attributes
    if hasattr(ds, 'CTDIvol') and ds.CTDIvol is not None:
        result['ctdi_vol'] = str(ds.CTDIvol)
    
    if hasattr(ds, 'DLP') and ds.DLP is not None:
        result['total_dlp'] = str(ds.DLP)
    
    # Method 2: Search in Exposure Dose Sequence (0040,030E)
    if hasattr(ds, 'ExposureDoseSequence'):
        try:
            for item in ds.ExposureDoseSequence:
                if hasattr(item, 'CTDIvol') and item.CTDIvol:
                    # Take the highest CTDIvol (usually from Helical scan)
                    ctdi_val = float(item.CTDIvol)
                    if not result['ctdi_vol'] or ctdi_val > float(result['ctdi_vol']):
                        result['ctdi_vol'] = str(ctdi_val)
        except Exception:
            pass
    
    # Method 3: Search in Comments On Radiation Dose (0040,0310)
    if hasattr(ds, 'CommentsOnRadiationDose') and ds.CommentsOnRadiationDose:
        comments = str(ds.CommentsOnRadiationDose)
        
        # Parse TotalDLP from comments
        import re
        total_dlp_match = re.search(r'TotalDLP[=:\s]*([\d\.]+)', comments)
        if total_dlp_match and not result['total_dlp']:
            result['total_dlp'] = total_dlp_match.group(1)
        
        # Also check for individual DLP events
        dlp_events = re.findall(r'DLP[=:\s]*([\d\.]+)', comments)
        if dlp_events and not result['total_dlp']:
            # Sum all DLP values
            total = sum(float(d) for d in dlp_events)
            result['total_dlp'] = str(round(total, 2))
    
    # Method 4: Search all DICOM elements for CTDIvol and DLP
    if not result['ctdi_vol'] or not result['total_dlp']:
        for elem in ds:
            elem_name = elem.name.upper() if elem.name else ''
            
            # Look for CTDIvol
            if not result['ctdi_vol'] and 'CTDIVOL' in elem_name:
                try:
                    val = float(elem.value)
                    if val > 0:
                        result['ctdi_vol'] = str(val)
                except (ValueError, TypeError):
                    pass
            
            # Look for DLP in element names
            if not result['total_dlp'] and 'DLP' in elem_name and 'TOTAL' not in elem_name:
                try:
                    val = float(elem.value)
                    if val > 0:
                        # Accumulate DLP values
                        if result['total_dlp']:
                            current = float(result['total_dlp'])
                            result['total_dlp'] = str(round(current + val, 2))
                        else:
                            result['total_dlp'] = str(val)
                except (ValueError, TypeError):
                    pass
    
    # If still not found, try OCR on pixel data
    if (not result['ctdi_vol'] or not result['total_dlp']) and hasattr(ds, 'pixel_array'):
        try:
            import cv2
            import numpy as np
            import tempfile
            
            pixel_array = ds.pixel_array
            
            # Convert to uint8 if needed
            if pixel_array.dtype != np.uint8:
                pixel_array = ((pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
            
            # Convert to BGR for OpenCV
            if len(pixel_array.shape) == 2:
                img_bgr = cv2.cvtColor(pixel_array, cv2.COLOR_GRAY2BGR)
            else:
                img_bgr = cv2.cvtColor(pixel_array, cv2.COLOR_RGB2BGR)
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                temp_path = tmp.name
                cv2.imwrite(temp_path, img_bgr)
            
            # Extract data using OCR
            extractor = MedicalScanExtractor()
            ocr_result = extractor.extract_data(temp_path, return_debug=False)
            
            # Use OCR results if metadata didn't have values
            if not result['ctdi_vol'] and ocr_result.get('ctdi_vol'):
                result['ctdi_vol'] = ocr_result['ctdi_vol']
            
            if not result['total_dlp'] and ocr_result.get('total_dlp'):
                result['total_dlp'] = ocr_result['total_dlp']
            
            # Clean up
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"  ⚠️ OCR failed: {e}")
    
    return result


def list_dicom_files(folder_path):
    """List all DICOM files in folder"""
    dicom_files = []
    
    if not os.path.exists(folder_path):
        return dicom_files
    
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        
        # Skip directories
        if os.path.isdir(filepath):
            continue
        
        # Check by extension
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.dcm', '.dicom']:
            dicom_files.append(filepath)
    
    return sorted(dicom_files)


def main():
    """Main function to read DICOM files from DCOM folder"""
    folder_path = "DCOM"
    excel_filename = "Rekap.xlsx"
    
    print("=" * 60)
    print("🏥 DICOM Reader - DCOM Folder")
    print("=" * 60)
    
    # List DICOM files
    dicom_files = list_dicom_files(folder_path)
    
    if not dicom_files:
        print(f"\n❌ No .dcm files found in '{folder_path}' folder!")
        return
    
    print(f"\n📁 Found {len(dicom_files)} DICOM file(s):")
    for i, f in enumerate(dicom_files, 1):
        print(f"  {i}. {os.path.basename(f)}")
    
    # Ask user to select file
    print("\nSelect file to read:")
    try:
        choice = input(f"Enter number (1-{len(dicom_files)}) or 'a' for all: ").strip()
        
        if choice.lower() == 'a':
            selected_files = dicom_files
        else:
            idx = int(choice) - 1
            if 0 <= idx < len(dicom_files):
                selected_files = [dicom_files[idx]]
            else:
                print("Invalid choice")
                return
    except Exception as e:
        print(f"Error: {e}")
        return
    
    # Initialize Excel handler
    excel_handler = ExcelHandler(excel_filename)
    
    # Check if Excel file exists and clear for fresh batch
    if os.path.exists(excel_filename):
        existing_count = excel_handler.get_record_count()
        print(f"\n⚠️  Excel file '{excel_filename}' already exists with {existing_count} record(s).")
        print("   Clearing existing data for fresh batch...")
        excel_handler.clear_all_data()
    else:
        print(f"   Creating new Excel file: {excel_filename}")
    
    print("\n" + "=" * 60)
    print("🚀 Processing DICOM files...")
    print("=" * 60)
    
    success_count = 0
    failed_count = 0
    
    for i, dicom_path in enumerate(selected_files, 1):
        filename = os.path.basename(dicom_path)
        print(f"\n[{i}/{len(selected_files)}] Processing: {filename}")
        
        try:
            # Extract data
            extracted_data = extract_dicom_data(dicom_path)
            
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
                print(f"  ✅ Success! (Row {row_num + 1})")
                print(f"     - Nama Pasien: {extracted_data.get('nama_pasien', 'N/A')}")
                print(f"     - Tanggal Pemeriksaan: {extracted_data.get('tanggal_pemeriksaan', 'N/A')}")
                print(f"     - ID Pasien: {extracted_data.get('id_pasien', 'N/A')}")
                print(f"     - Jenis Pemeriksaan: {extracted_data.get('jenis_pemeriksaan', 'N/A')}")
                print(f"     - CTDIvol: {extracted_data.get('ctdi_vol', 'N/A')} mGy")
                print(f"     - Total DLP: {extracted_data.get('total_dlp', 'N/A')} mGy·cm")
                success_count += 1
            else:
                print(f"  ⚠️  No meaningful data extracted")
                failed_count += 1
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Processing Summary")
    print("=" * 60)
    print(f"   Total Files: {len(selected_files)}")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📁 Output File: {excel_filename}")
    print("=" * 60)
    
    if success_count > 0:
        print(f"\n✅ Batch processing completed! {success_count} record(s) saved to '{excel_filename}'")
    else:
        print("\n⚠️  No data was successfully extracted.")


if __name__ == "__main__":
    main()
