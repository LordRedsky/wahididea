"""
Medical Scan Data Extractor - Streamlit Application
Extract patient data from CT scan dose report images and save to Excel
"""

import streamlit as st
from PIL import Image
from ocr_extractor import MedicalScanExtractor, HAS_DICOM
from excel_handler import ExcelHandler
import os
import subprocess
import platform
import tempfile
import io
import re

try:
    import pydicom
except ImportError:
    pydicom = None


# Page configuration
st.set_page_config(
    page_title="Medical Scan Data Extractor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #E8F5E9;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
    }
    .data-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f5f5f5;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)


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


def extract_from_dicom_text(txt_content):
    """Extract data from DICOM text dump format"""
    result = {
        'nama_pasien': None,
        'tanggal_pemeriksaan': None,
        'id_pasien': None,
        'umur_pasien': None,
        'jenis_kelamin': None,
        'jenis_pemeriksaan': None,
        'kv': None,
        'ctdi_vol': None,
        'total_dlp': None,
    }
    
    lines = txt_content.split('\n')
    full_text = '\n'.join(lines)
    
    # Extract Patient Name - look for (0010,0010) Patient Name
    for line in lines:
        if '(0010,0010)' in line and 'Patient Name' in line:
            # Format: (0010,0010)       Patient Name                        PN  1   16         ABDUL RAHMAN. TN
            match = re.search(r'\(0010,0010\).*?PN\s+\d+\s+(\d+)\s+(.+?)(?:\n|$)', line)
            if match:
                name = match.group(2).strip()
                if name and len(name) > 2:
                    result['nama_pasien'] = name
                    break
    
    # Extract Patient ID - look for (0010,0020) Patient ID
    for line in lines:
        if '(0010,0020)' in line and 'Patient ID' in line:
            match = re.search(r'\(0010,0020\).*?LO\s+\d+\s+(\d+)\s+(.+?)(?:\n|$)', line)
            if match:
                pid = match.group(2).strip()
                if pid and pid.isdigit():
                    result['id_pasien'] = pid
                    break
    
    # Extract Patient Age - look for (0010,1010) Patient Age
    for line in lines:
        if '(0010,1010)' in line and 'Patient Age' in line:
            # Format: (0010,1010)       Patient Age                         AS  1   4          026Y
            # Match the value at the end of line (number + unit without space)
            match = re.search(r'\(0010,1010\).*?AS.*?(\d+)([A-Z])\s*$', line)
            if match:
                age_num = match.group(1).strip()
                age_unit = match.group(2).strip()
                # Convert to readable format
                if age_unit == 'Y':
                    result['umur_pasien'] = f"{int(age_num)} Tahun"
                elif age_unit == 'M':
                    result['umur_pasien'] = f"{int(age_num)} Bulan"
                elif age_unit == 'W':
                    result['umur_pasien'] = f"{int(age_num)} Minggu"
                elif age_unit == 'D':
                    result['umur_pasien'] = f"{int(age_num)} Hari"
                else:
                    result['umur_pasien'] = f"{age_num} {age_unit}"
                break
    
    # Extract Patient Sex - look for (0010,0040) Patient Sex
    for line in lines:
        if '(0010,0040)' in line and 'Patient Sex' in line:
            # Format: (0010,0040)       Patient Sex                         CS  1   2          M
            match = re.search(r'\(0010,0040\).*?CS\s+\d+\s+(\d+)\s+([A-Z])', line)
            if match:
                sex_code = match.group(2).strip()
                sex_map = {'M': 'Laki-laki', 'F': 'Perempuan', 'U': 'Unknown', 'O': 'Other'}
                result['jenis_kelamin'] = sex_map.get(sex_code, sex_code)
                break
    
    # Extract Study Date - look for (0008,0020) Study Date
    for line in lines:
        if '(0008,0020)' in line and 'Study Date' in line:
            # Format: (0008,0020)          Study Date                              DA      1       8               20260202
            match = re.search(r'\(0008,0020\).*?DA\s+\d+\s+\d+\s+(\d{8})', line)
            if match:
                date_str = match.group(1).strip()
                if date_str and len(date_str) == 8:
                    result['tanggal_pemeriksaan'] = convert_date(date_str)
                    break
    
    # Extract Study Description - look for (0008,1030) Study Description
    for line in lines:
        if '(0008,1030)' in line and 'Study Description' in line:
            match = re.search(r'\(0008,1030\).*?LO\s+\d+\s+\d+\s+(.+?)(?:\n|$)', line)
            if match:
                desc = match.group(1).strip()
                if desc:
                    result['jenis_pemeriksaan'] = desc
                    break
    
    # Extract kV from (0018,0060) KVP - take the last value (from Helical scan)
    kv_values = []
    for line in lines:
        if '(0018,0060)' in line and 'KVP' in line:
            # Format: (0018,0060)       KVP                                 DS  1   4          120
            match = re.search(r'\(0018,0060\).*?DS\s+\d+\s+(\d+)\s+(\d+)', line)
            if match:
                kv_values.append(match.group(2).strip())
    if kv_values:
        result['kv'] = kv_values[-1]  # Take the last value (usually from Helical)
    
    # Extract CTDIvol from (0018,9345) CTDIvol - get all values and take max
    # There can be multiple CTDIvol values in the Exposure Dose Sequence
    ctdi_values = []
    for line in lines:
        if '(0018,9345)' in line and 'CTD' in line.upper():
            # Match the numeric value at the end of the line (after all the tabs/spaces)
            # Format: (0018,9345)    CTD Ivol    FD  1  8  44.38
            match = re.search(r'\(0018,9345\).*?FD\s+\d+\s+\d+\s+([\d\.]+)', line)
            if match:
                try:
                    val = float(match.group(1).strip())
                    if val > 0:
                        ctdi_values.append(val)
                except (ValueError, TypeError):
                    pass
    if ctdi_values:
        result['ctdi_vol'] = str(max(ctdi_values))  # Take highest value (usually from Helical)
    
    # Extract Total DLP from Comments On Radiation Dose (0040,0310)
    total_dlp_match = re.search(r'TotalDLP[=:\s]*([\d\.]+)', full_text)
    if total_dlp_match:
        result['total_dlp'] = total_dlp_match.group(1)
    
    # If Total DLP not found, sum individual DLP events
    if not result['total_dlp']:
        dlp_events = re.findall(r'Event[=:\s]*\d+\s+DLP[=:\s]*([\d\.]+)', full_text)
        if dlp_events:
            total = sum(float(d) for d in dlp_events)
            result['total_dlp'] = str(round(total, 2))
    
    return result


def main():
    # Header
    st.markdown('<p class="main-header">🏥 Medical Scan Data Extractor</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Extract patient data from CT scan dose report images using OCR</p>', unsafe_allow_html=True)
    
    # Initialize handlers
    extractor = MedicalScanExtractor()
    excel_handler = ExcelHandler()
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Statistics")
        record_count = excel_handler.get_record_count()
        st.metric("Total Records", record_count)

        st.divider()

        # Tesseract Verification
        st.header("🔍 System Status")
        try:
            # Check if tesseract is available
            result = subprocess.run(
                ['tesseract', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                st.success("✅ Tesseract installed")
                version_line = result.stdout.split('\n')[0]
                st.caption(version_line)
            else:
                st.error("❌ Tesseract not found")
        except FileNotFoundError:
            st.error("❌ Tesseract not found")
            st.caption("Installing from packages.txt...")
            st.caption("First deployment takes 5-10 minutes")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

        st.divider()

        # Debug options
        st.header("🐛 Debug")
        debug_mode = st.checkbox("Enable OCR Debug", value=False, help="Show OCR text output")
        if debug_mode:
            st.session_state['debug_ocr'] = True
            st.info("Debug mode enabled")
        else:
            st.session_state['debug_ocr'] = False

        st.divider()

        st.header("ℹ️ Information")
        st.markdown("""
        **Extracted Fields:**
        - Nama Pasien
        - Tanggal Pemeriksaan
        - ID Pasien
        - Umur Pasien
        - Jenis Kelamin
        - Jenis Pemeriksaan
        - Tegangan (kV)
        - CTDIvol (mGy)
        - Total DLP (mGy·cm)
        """)

        st.divider()

        if st.button("🗑️ Clear All Data", type="secondary", use_container_width=True):
            excel_handler.clear_all_data()
            st.success("All data cleared!")
            st.rerun()
    
    # Main content - two columns
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.header("📤 Upload File")

        uploaded_file = st.file_uploader(
            "Choose a CT scan dose report file",
            type=["jpg", "jpeg", "png", "dcm", "dicom", "txt"],
            help="Upload a clear image of the CT scan dose report (JPG, PNG, DICOM, or TXT format)"
        )
        
        if uploaded_file is not None:
            # Get file bytes
            file_bytes = uploaded_file.read()
            file_name = uploaded_file.name
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # Reset file pointer
            uploaded_file.seek(0)
            
            # Check if it's a DICOM file by magic number
            is_dicom = file_bytes[128:132] == b'DICM' if len(file_bytes) > 132 else False
            
            # Handle TXT file (DICOM text dump)
            if file_ext == '.txt':
                st.info("📄 TXT file detected (DICOM text dump)")
                
                # Read content with encoding fallback
                try:
                    # Try UTF-8 first
                    try:
                        txt_content = file_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        # Fallback to latin-1 (can decode any byte sequence)
                        txt_content = file_bytes.decode('latin-1')
                    
                    # Extract button
                    if st.button("🔍 Extract Data", type="primary", use_container_width=True):
                        with st.spinner("Processing TXT file... Please wait."):
                            extracted_data = extract_from_dicom_text(txt_content)
                            
                            # Store in session state
                            st.session_state['extracted_data'] = extracted_data
                            st.session_state['image_uploaded'] = True
                            st.session_state['is_dicom'] = False

                        st.success("Data extracted successfully!")
                        
                except Exception as e:
                    st.error(f"Error reading TXT file: {str(e)}")
            
            # Handle DICOM file
            elif is_dicom or file_ext in ['.dcm', '.dicom']:
                # Handle DICOM file
                st.info("📋 DICOM file detected")

                # Save to temporary file for processing
                with tempfile.NamedTemporaryFile(delete=False, suffix='.dcm') as tmp_file:
                    tmp_file.write(file_bytes)
                    temp_dicom_path = tmp_file.name

                try:
                    # Extract metadata from DICOM
                    if HAS_DICOM and pydicom:
                        ds = pydicom.dcmread(temp_dicom_path)

                        # Extract button for DICOM
                        if st.button("🔍 Extract Data", type="primary", use_container_width=True):
                            with st.spinner("Processing DICOM file... Please wait."):
                                debug_mode = st.session_state.get('debug_ocr', False)
                                extracted_data = extractor.extract_from_dicom(temp_dicom_path, return_debug=debug_mode)

                                # Clean up temp file
                                os.unlink(temp_dicom_path)

                                # Store in session state
                                st.session_state['extracted_data'] = extracted_data
                                st.session_state['image_uploaded'] = True
                                st.session_state['is_dicom'] = True

                            st.success("Data extracted successfully!")
                            
                            # Show debug info if enabled
                            if debug_mode:
                                st.warning("🐛 **Debug Mode Enabled**")
                                with st.expander("📝 View OCR Text Output", expanded=True):
                                    ocr_text = extracted_data.get('_debug_ocr_text', 'No OCR text available')
                                    st.text(ocr_text)
                    else:
                        st.warning("pydicom not installed. Cannot preview DICOM metadata.")
                except Exception as e:
                    st.error(f"Error reading DICOM: {str(e)}")
            
            else:
                # Handle regular image (JPG, PNG)
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_container_width=True)

                # Extract button
                if st.button("🔍 Extract Data", type="primary", use_container_width=True):
                    with st.spinner("Processing image... Please wait."):
                        # Extract data with debug info if enabled
                        debug_mode = st.session_state.get('debug_ocr', False)
                        extracted_data = extractor.extract_from_pil_image(image, return_debug=debug_mode)

                        # Store in session state
                        st.session_state['extracted_data'] = extracted_data
                        st.session_state['image_uploaded'] = True
                        st.session_state['is_dicom'] = False

                    st.success("Data extracted successfully!")
                    
                    # Show debug info if enabled
                    if debug_mode:
                        st.warning("🐛 **Debug Mode Enabled**")
                        with st.expander("📝 View OCR Text Output", expanded=True):
                            ocr_text = extracted_data.get('_debug_ocr_text', 'No OCR text available')
                            st.text(ocr_text)
                        
                        with st.expander("📋 Helical Lines Detected"):
                            helical_lines = extracted_data.get('_debug_helical_lines', [])
                            if helical_lines:
                                for i, line in enumerate(helical_lines):
                                    st.text(f"Line {i+1}: {line}")
                            else:
                                st.warning("No Helical lines detected in OCR text")
                        
                        st.info(f"""
                        **Extraction Summary:**
                        - CTDIvol: `{extracted_data.get('ctdi_vol', 'Not detected')}` mGy
                        - Total DLP: `{extracted_data.get('total_dlp', 'Not detected')}` mGy·cm
                        - Helical lines found: {len(extracted_data.get('_debug_helical_lines', []))}
                        """)
    
    with col2:
        st.header("📋 Extracted Data")
        
        if 'extracted_data' in st.session_state and st.session_state.get('image_uploaded', False):
            data = st.session_state['extracted_data']
            
            # Display extracted data in cards
            st.markdown("##### Patient Information")
            
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"**Nama Pasien:** {data.get('nama_pasien', 'Not detected')}")
                st.info(f"**Tanggal Pemeriksaan:** {data.get('tanggal_pemeriksaan', 'Not detected')}")
                st.info(f"**ID Pasien:** {data.get('id_pasien', 'Not detected')}")
                st.info(f"**Umur Pasien:** {data.get('umur_pasien', 'Not detected')}")
                st.info(f"**Jenis Kelamin:** {data.get('jenis_kelamin', 'Not detected')}")
            
            with c2:
                st.info(f"**Jenis Pemeriksaan:** {data.get('jenis_pemeriksaan', 'Not detected')}")
                st.info(f"**Tegangan (kV):** {data.get('kv', 'Not detected')}")
                st.warning(f"**CTDIvol:** {data.get('ctdi_vol', 'Not detected')} mGy")
                st.error(f"**Total DLP:** {data.get('total_dlp', 'Not detected')} mGy·cm")
            
            st.divider()
            
            # Save to Excel button
            col_save, col_view = st.columns([1, 1])
            
            with col_save:
                if st.button("💾 Save to Excel", type="primary", use_container_width=True):
                    try:
                        row_num = excel_handler.add_record(data)
                        st.success(f"✅ Data saved to Rekap.xlsx (Row {row_num + 1})")
                        
                        # Clear session state after saving
                        st.session_state['extracted_data'] = None
                        st.session_state['image_uploaded'] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving data: {str(e)}")
            
            with col_view:
                if st.button("📊 View Excel Data", use_container_width=True):
                    st.session_state['show_excel'] = True
        
        else:
            st.info("👆 Upload an image and click 'Extract Data' to see results here")
            
            # Sample display structure
            st.markdown("##### Expected Output:")
            st.markdown("""
            - **Nama Pasien:** Patient name from scan
            - **Tanggal Pemeriksaan:** Examination date
            - **ID Pasien:** Patient ID number
            - **Umur Pasien:** Patient age
            - **Jenis Kelamin:** Patient sex
            - **Jenis Pemeriksaan:** Exam description/type
            - **Tegangan (kV):** Tube voltage
            - **CTDIvol:** Radiation dose value (mGy)
            - **Total DLP:** Total dose value (mGy·cm)
            """)
    
    # Excel data viewer section - Always visible
    st.divider()
    st.header("📊 Data Preview & Download")
    
    # Show data preview
    records = excel_handler.get_all_records()
    
    if records:
        # Display statistics
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        with col_stats1:
            st.metric("Total Records", len(records))
        with col_stats2:
            unique_patients = len(set(r.get('Nama Pasien', '') for r in records if r.get('Nama Pasien')))
            st.metric("Unique Patients", unique_patients)
        with col_stats3:
            unique_exams = len(set(r.get('Jenis Pemeriksaan', '') for r in records if r.get('Jenis Pemeriksaan')))
            st.metric("Exam Types", unique_exams)
        
        st.divider()
        
        # Data table with search
        st.subheader("📋 Saved Records")
        
        # Search functionality
        search_term = st.text_input("🔍 Search", placeholder="Search by patient name, exam type, or ID...")
        
        if search_term:
            filtered_records = [
                r for r in records 
                if search_term.lower() in str(r.get('Nama Pasien', '')).lower()
                or search_term.lower() in str(r.get('Jenis Pemeriksaan', '')).lower()
                or search_term.lower() in str(r.get('ID Pasien', '')).lower()
            ]
            if filtered_records:
                st.success(f"Found {len(filtered_records)} record(s) matching '{search_term}'")
                st.dataframe(filtered_records, use_container_width=True, hide_index=True)
            else:
                st.warning(f"No records found matching '{search_term}'")
                st.dataframe(records, use_container_width=True, hide_index=True)
        else:
            st.dataframe(records, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Download section
        st.subheader("📥 Download Options")
        
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            with open("Rekap.xlsx", "rb") as file:
                st.download_button(
                    label="📥 Download Excel (.xlsx)",
                    data=file,
                    file_name=f"Rekap_{st.session_state.get('download_timestamp', '')}.xlsx" if st.session_state.get('download_timestamp') else "Rekap.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        with col_dl2:
            # CSV download option
            import csv
            import io
            
            if records:
                # Convert to CSV
                csv_buffer = io.StringIO()
                if records:
                    fieldnames = list(records[0].keys())
                    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(records)
                
                st.download_button(
                    label="📄 Download CSV (.csv)",
                    data=csv_buffer.getvalue(),
                    file_name="Rekap.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    else:
        st.info("📭 No data in Excel file yet. Upload an image and extract data to get started.")
    
    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
            <p>Built with Streamlit | OCR powered by Tesseract</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
