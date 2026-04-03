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
from datetime import datetime

try:
    import pydicom
except ImportError:
    pydicom = None


# Page configuration - Set default theme to light
st.set_page_config(
    page_title="Radiation Dose Recorder",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add viewport meta tag for mobile responsiveness
st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
""", unsafe_allow_html=True)

# Initialize theme state
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'light'

# Custom CSS - Clean Medical Theme with Dark Mode Support & Mobile Responsive
st.markdown("""
    <style>
    /* Light Mode - Default (always active with !important to override Streamlit) */
    .main {
        background-color: #f8fafc !important;
    }

    .app-header {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
    }

    .app-title {
        color: white !important;
    }

    .app-subtitle {
        color: #e0f2fe !important;
    }

    .data-card {
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
    }

    .card-label {
        color: #64748b !important;
    }

    .card-value {
        color: #0f172a !important;
    }

    .upload-section {
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
    }

    .metric-card {
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    }

    /* Dark Mode - Only active when .dark class is present */
    .dark .main {
        background-color: #0f172a !important;
    }

    .dark .app-header {
        background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%) !important;
    }

    .dark .app-title {
        color: #f8fafc !important;
    }

    .dark .app-subtitle {
        color: #bfdbfe !important;
    }

    .dark .data-card {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }

    .dark .card-label {
        color: #94a3b8 !important;
    }

    .dark .card-value {
        color: #f1f5f9 !important;
    }

    .dark .upload-section {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }

    .dark .metric-card {
        background: #1e293b !important;
        border: 1px solid #334155 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
    }

    /* Common styles */
    .app-header {
        text-align: center;
        padding: 2rem 0;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .app-subtitle {
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        font-weight: 400;
    }
    
    .data-card {
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .card-label {
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.25rem;
    }
    
    .card-value {
        font-size: 1.125rem;
        font-weight: 600;
    }
    
    .upload-section {
        border-radius: 10px;
        padding: 2rem;
    }
    
    .metric-card {
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    
    /* Hide default Streamlit elements for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Button styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Theme toggle button */
    .theme-toggle {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 1000;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 50px;
        padding: 0.5rem 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .theme-toggle:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: scale(1.05);
    }
    
    .dark .theme-toggle {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(100, 116, 139, 0.3);
    }
    
    .dark .theme-toggle:hover {
        background: rgba(30, 41, 59, 0.9);
    }
    
    /* Mobile Responsive Design */
    @media (max-width: 768px) {
        .app-header {
            padding: 1.5rem 1rem;
            margin-bottom: 1rem;
            border-radius: 8px;
        }
        
        .app-title {
            font-size: 1.75rem;
            letter-spacing: 0;
        }
        
        .app-subtitle {
            font-size: 0.9rem;
            padding: 0 0.5rem;
        }
        
        .metric-card {
            padding: 0.75rem;
            margin-bottom: 0.5rem;
        }
        
        .metric-card > div:first-child {
            font-size: 0.75rem !important;
        }
        
        .metric-card > div:last-child {
            font-size: 1.5rem !important;
        }
        
        .data-card {
            padding: 1rem;
            margin-bottom: 0.75rem;
        }
        
        .card-label {
            font-size: 0.75rem;
        }
        
        .card-value {
            font-size: 1rem;
        }
        
        .upload-section {
            padding: 1rem;
        }
        
        /* Make columns stack on mobile */
        .stColumn > div {
            margin-bottom: 0.5rem;
        }
        
        /* Better touch targets for mobile */
        .stButton>button {
            min-height: 44px;
            padding: 0.75rem 1rem;
        }
        
        /* Improve file uploader on mobile */
        .stFileUploader > div {
            min-height: 100px;
        }
        
        /* Make text inputs more touch-friendly */
        .stTextInput input,
        .stTextArea textarea {
            font-size: 16px !important; /* Prevents zoom on iOS */
        }
        
        /* Better spacing for sections */
        h3 {
            font-size: 1.25rem !important;
            margin-top: 1rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Optimize data table for mobile */
        .dataframe {
            font-size: 0.875rem;
        }
        
        /* Make download buttons full width on mobile */
        .stDownloadButton>button {
            width: 100%;
            min-height: 44px;
        }
    }
    
    /* Tablet optimizations */
    @media (min-width: 769px) and (max-width: 1024px) {
        .app-title {
            font-size: 2rem;
        }
        
        .app-subtitle {
            font-size: 1rem;
        }
        
        .metric-card {
            padding: 0.875rem;
        }
    }
    
    /* Ensure smooth transitions */
    * {
        transition: background-color 0.3s ease, color 0.3s ease;
    }
    
    /* Prevent horizontal scroll */
    .block-container {
        max-width: 100%;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    @media (min-width: 1200px) {
        .block-container {
            max-width: 1200px;
            padding-left: 2rem;
            padding-right: 2rem;
        }
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
    # Initialize handlers
    extractor = MedicalScanExtractor()
    excel_handler = ExcelHandler()
    
    # Theme toggle button
    current_theme = st.session_state.get('theme', 'light')
    new_theme = 'dark' if current_theme == 'light' else 'light'
    theme_icon = "🌙" if current_theme == 'light' else "☀️"
    theme_label = "Dark Mode" if current_theme == 'light' else "Light Mode"
    
    if st.button(f"{theme_icon} {theme_label}", key="theme_toggle"):
        st.session_state['theme'] = new_theme
        st.rerun()
    
    # Apply theme class
    theme_class = st.session_state.get('theme', 'light')
    st.markdown(f'<div class="{theme_class}">', unsafe_allow_html=True)
    
    # Header Section - Clean & Elegant
    st.markdown("""
        <div class="app-header">
            <h1 class="app-title">🏥 Radiation Dose Recorder</h1>
            <p class="app-subtitle">Extract and manage patient radiation dose data from CT scan reports</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Quick Stats Bar
    record_count = excel_handler.get_record_count()
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.875rem; color: #64748b;">Total Records</div>
                <div style="font-size: 2rem; font-weight: 700; color: #0ea5e9;">{record_count}</div>
            </div>
        """, unsafe_allow_html=True)
    with col_s2:
        if record_count > 0:
            records = excel_handler.get_all_records()
            unique_patients = len(set(r.get('Nama Pasien', '') for r in records if r.get('Nama Pasien')))
            st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 0.875rem; color: #64748b;">Patients</div>
                    <div style="font-size: 2rem; font-weight: 700; color: #0ea5e9;">{unique_patients}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 0.875rem; color: #64748b;">Patients</div>
                    <div style="font-size: 2rem; font-weight: 700; color: #0ea5e9;">0</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Main Workflow Section
    # Step 1: Upload
    st.markdown("### 📤 Step 1: Upload CT Scan Report")
    st.markdown("<p style='color: #64748b; margin-top: -1rem;'>Upload a clear image of the dose report (JPG, PNG, DICOM, or TXT)</p>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "",
        type=["jpg", "jpeg", "png", "dcm", "dicom", "txt"],
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name
        file_ext = os.path.splitext(file_name)[1].lower()
        uploaded_file.seek(0)
        
        is_dicom = file_bytes[128:132] == b'DICM' if len(file_bytes) > 132 else False
        
        # Display uploaded file
        col_preview, col_action = st.columns([2, 1])
        
        with col_preview:
            if file_ext == '.txt':
                st.info("📄 Text file (DICOM dump)")
            elif is_dicom or file_ext in ['.dcm', '.dicom']:
                st.info("📋 DICOM file detected")
            else:
                image = Image.open(uploaded_file)
                st.image(image, use_container_width=True)
        
        with col_action:
            st.markdown("**Ready to extract**")
            if st.button("🔍 Extract Data", type="primary", use_container_width=True):
                with st.spinner("Processing..."):
                    extracted_data = None
                    
                    if file_ext == '.txt':
                        try:
                            try:
                                txt_content = file_bytes.decode('utf-8')
                            except UnicodeDecodeError:
                                txt_content = file_bytes.decode('latin-1')
                            extracted_data = extract_from_dicom_text(txt_content)
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    
                    elif is_dicom or file_ext in ['.dcm', '.dicom']:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.dcm') as tmp_file:
                            tmp_file.write(file_bytes)
                            temp_dicom_path = tmp_file.name
                        
                        try:
                            if HAS_DICOM and pydicom:
                                debug_mode = st.session_state.get('debug_ocr', False)
                                extracted_data = extractor.extract_from_dicom(temp_dicom_path, return_debug=debug_mode)
                                os.unlink(temp_dicom_path)
                            else:
                                st.error("pydicom not installed")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    
                    else:
                        image = Image.open(uploaded_file)
                        debug_mode = st.session_state.get('debug_ocr', False)
                        extracted_data = extractor.extract_from_pil_image(image, return_debug=debug_mode)
                    
                    if extracted_data:
                        st.session_state['extracted_data'] = extracted_data
                        st.session_state['image_uploaded'] = True
                        st.success("✅ Extraction complete!")
        
        # Step 2: Review Extracted Data
        if 'extracted_data' in st.session_state and st.session_state.get('image_uploaded', False):
            st.markdown("---")
            st.markdown("### 👁️ Step 2: Review Extracted Data")
            
            data = st.session_state['extracted_data']
            
            # Clean card layout
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                st.markdown(f"""
                    <div class="data-card">
                        <div class="card-label">👤 Patient Name</div>
                        <div class="card-value">{data.get('nama_pasien', 'Not detected')}</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="data-card">
                        <div class="card-label">🆔 Patient ID</div>
                        <div class="card-value">{data.get('id_pasien', 'Not detected')}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col_p2:
                st.markdown(f"""
                    <div class="data-card">
                        <div class="card-label">📅 Examination Date</div>
                        <div class="card-value">{data.get('tanggal_pemeriksaan', 'Not detected')}</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="data-card">
                        <div class="card-label">🔬 Exam Type</div>
                        <div class="card-value">{data.get('jenis_pemeriksaan', 'Not detected')}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col_p3:
                st.markdown(f"""
                    <div class="data-card">
                        <div class="card-label">⚡ CTDIvol</div>
                        <div class="card-value" style="color: #ea580c;">{data.get('ctdi_vol', 'Not detected')} mGy</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div class="data-card">
                        <div class="card-label">📊 Total DLP</div>
                        <div class="card-value" style="color: #dc2626;">{data.get('total_dlp', 'Not detected')} mGy·cm</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Additional info
            col_add1, col_add2, col_add3 = st.columns(3)
            with col_add1:
                st.markdown(f"""
                    <div class="data-card">
                        <div class="card-label">🎂 Age</div>
                        <div class="card-value">{data.get('umur_pasien', 'N/A')}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col_add2:
                st.markdown(f"""
                    <div class="data-card">
                        <div class="card-label">⚧ Sex</div>
                        <div class="card-value">{data.get('jenis_kelamin', 'N/A')}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col_add3:
                st.markdown(f"""
                    <div class="data-card">
                        <div class="card-label">⚡ kV</div>
                        <div class="card-value">{data.get('kv', 'N/A')}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Save action
            st.markdown("---")
            st.markdown("### 💾 Step 3: Save to Excel")
            
            col_save1, col_save2 = st.columns([1, 3])
            with col_save1:
                if st.button("💾 Save Record", type="primary", use_container_width=True):
                    try:
                        row_num = excel_handler.add_record(data)
                        st.success(f"✅ Saved to row {row_num + 1}")
                        
                        # Clear session
                        st.session_state['extracted_data'] = None
                        st.session_state['image_uploaded'] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    else:
        # No file uploaded - show placeholder
        st.markdown("""
            <div style="text-align: center; padding: 3rem; background: white; border-radius: 10px; border: 2px dashed #e2e8f0;">
                <p style="font-size: 3rem; margin: 0;">📄</p>
                <p style="color: #64748b; margin: 0.5rem 0;">Upload a CT scan dose report image to begin</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Excel Data Section
    st.markdown("---")
    st.markdown("### 📊 Saved Records")
    
    records = excel_handler.get_all_records()
    
    if records:
        # Search
        search_term = st.text_input("", placeholder="🔍 Search by patient name, exam type, or ID...", label_visibility="collapsed")
        
        if search_term:
            filtered = [
                r for r in records 
                if search_term.lower() in str(r.get('Nama Pasien', '')).lower()
                or search_term.lower() in str(r.get('Jenis Pemeriksaan', '')).lower()
                or search_term.lower() in str(r.get('ID Pasien', '')).lower()
            ]
            if filtered:
                st.success(f"Found {len(filtered)} record(s)")
                st.dataframe(filtered, use_container_width=True, hide_index=True)
            else:
                st.warning("No matching records")
        else:
            st.dataframe(records, use_container_width=True, hide_index=True)
        
        # Download buttons
        st.markdown("---")
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            with open("Rekap.xlsx", "rb") as file:
                st.download_button(
                    label="📥 Download Excel",
                    data=file,
                    file_name="Rekap.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        with col_dl2:
            import csv
            csv_buffer = io.StringIO()
            fieldnames = list(records[0].keys())
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
            
            st.download_button(
                label="📄 Download CSV",
                data=csv_buffer.getvalue(),
                file_name="Rekap.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.info("📭 No records yet. Upload and extract your first CT scan report.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #94a3b8; padding: 1rem; font-size: 0.875rem;'>
            <p>Radiation Dose Recorder • Built with Streamlit • OCR by Tesseract</p>
            <p>AKTUALISASI LATSAR CPNS 2026</p>
            <p>by Abdurrahman Wahid, ST</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Close theme wrapper
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
