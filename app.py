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
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils import convert_date, extract_from_dicom_text, load_css

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

# Initialize states
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'light'
if 'page' not in st.session_state:
    st.session_state['page'] = 'dashboard'

st.markdown(load_css('style.css'), unsafe_allow_html=True)

def prepare_dashboard_data(records):
    """Prepare data for dashboard visualization"""
    if not records:
        return pd.DataFrame()
    
    df = pd.DataFrame(records)
    
    # Clean and process data - support both short and long header names
    ctdi_col = 'CTDIvol' if 'CTDIvol' in df.columns else 'CTDIvol (mGy)'
    dlp_col = 'Total DLP' if 'Total DLP' in df.columns else 'Total DLP (mGy·cm)'
    age_col = 'Umur Pasien'
    
    if age_col in df.columns:
        # Extract numeric age
        df['Age'] = df[age_col].astype(str).str.extract(r'(\d+)').astype(float)
    
    if ctdi_col in df.columns:
        df['CTDIvol_val'] = pd.to_numeric(df[ctdi_col], errors='coerce')
    else:
        df['CTDIvol_val'] = 0
        
    if dlp_col in df.columns:
        df['Total_DLP_val'] = pd.to_numeric(df[dlp_col], errors='coerce')
    else:
        df['Total_DLP_val'] = 0
    
    return df


def render_dashboard():
    """Render the dashboard page with charts and filters"""
    excel_handler = ExcelHandler()
    records = excel_handler.get_all_records()
    
    # Header
    st.markdown("""
        <div class="app-header">
            <h1 class="app-title">🏥 Radiation Dose Dashboard</h1>
            <p class="app-subtitle">Interactive visualization of patient radiation dose data</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("📤 Upload Data", type="primary", use_container_width=True):
            st.session_state['page'] = 'upload'
            st.rerun()
    with col_btn2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    if not records:
        st.info("📭 No data available yet. Click 'Upload Data' to start extracting patient data.")
        return
    
    # Prepare data
    df = prepare_dashboard_data(records)
    
    # Filters
    st.markdown("### 🔍 Filters")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        gender_options = ['All'] + list(df['Jenis Kelamin'].dropna().unique()) if 'Jenis Kelamin' in df.columns else ['All']
        selected_gender = st.selectbox("Jenis Kelamin", gender_options)
    
    with col_f2:
        exam_options = ['All'] + list(df['Jenis Pemeriksaan'].dropna().unique()) if 'Jenis Pemeriksaan' in df.columns else ['All']
        selected_exam = st.selectbox("Jenis Pemeriksaan", exam_options)
    
    with col_f3:
        if 'Age' in df.columns:
            age_min = int(df['Age'].min())
            age_max = int(df['Age'].max())
            # Handle case where min equals max
            if age_min == age_max:
                age_min = max(0, age_min - 10)
                age_max = age_max + 10
            age_range = (age_min, age_max)
            selected_age = st.slider("Usia (Tahun)", age_min, age_max, age_range)
        else:
            selected_age = None
    
    # Apply filters
    filtered_df = df.copy()
    if selected_gender != 'All':
        filtered_df = filtered_df[filtered_df['Jenis Kelamin'] == selected_gender]
    if selected_exam != 'All':
        filtered_df = filtered_df[filtered_df['Jenis Pemeriksaan'] == selected_exam]
    if selected_age:
        filtered_df = filtered_df[(filtered_df['Age'] >= selected_age[0]) & (filtered_df['Age'] <= selected_age[1])]
    
    # Summary Stats
    st.markdown("---")
    st.markdown("### 📊 Summary Statistics")
    
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.875rem; color: #64748b;">Total Patients</div>
                <div style="font-size: 2rem; font-weight: 700; color: #0ea5e9;">{len(filtered_df)}</div>
            </div>
        """, unsafe_allow_html=True)
    with col_s2:
        avg_age = filtered_df['Age'].mean() if 'Age' in filtered_df.columns and not filtered_df['Age'].empty else 0
        st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.875rem; color: #64748b;">Avg Age</div>
                <div style="font-size: 2rem; font-weight: 700; color: #0ea5e9;">{avg_age:.0f}</div>
            </div>
        """, unsafe_allow_html=True)
    with col_s3:
        avg_ctdi = filtered_df['CTDIvol_val'].mean() if 'CTDIvol_val' in filtered_df.columns and not filtered_df['CTDIvol_val'].empty else 0
        st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.875rem; color: #64748b;">Avg CTDIvol</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #ea580c;">{avg_ctdi:.1f} mGy</div>
            </div>
        """, unsafe_allow_html=True)
    with col_s4:
        avg_dlp = filtered_df['Total_DLP_val'].mean() if 'Total_DLP_val' in filtered_df.columns and not filtered_df['Total_DLP_val'].empty else 0
        st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 0.875rem; color: #64748b;">Avg DLP</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #dc2626;">{avg_dlp:.1f} mGy·cm</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Charts
    st.markdown("---")
    st.markdown("### 📈 Data Visualization")
    
    # Row 1: Gender & Exam Type
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("#### 👥 Gender Distribution")
        if 'Jenis Kelamin' in filtered_df.columns and not filtered_df['Jenis Kelamin'].empty:
            gender_counts = filtered_df['Jenis Kelamin'].value_counts()
            fig = px.pie(
                values=gender_counts.values,
                names=gender_counts.index,
                color_discrete_sequence=['#0ea5e9', '#f472b6', '#a78bfa'],
                hole=0.4
            )
            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No gender data available")
    
    with col_c2:
        st.markdown("#### 🔬 Exam Type Distribution")
        if 'Jenis Pemeriksaan' in filtered_df.columns and not filtered_df['Jenis Pemeriksaan'].empty:
            exam_counts = filtered_df['Jenis Pemeriksaan'].value_counts().head(10)
            fig = px.bar(
                x=exam_counts.values,
                y=exam_counts.index,
                orientation='h',
                color=exam_counts.values,
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis_title="Count",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No exam type data available")
    
    # Row 2: Age Distribution & CTDIvol vs DLP
    col_c3, col_c4 = st.columns(2)
    
    with col_c3:
        st.markdown("#### 🎂 Age Distribution")
        if 'Age' in filtered_df.columns and not filtered_df['Age'].dropna().empty:
            fig = px.histogram(
                filtered_df,
                x='Age',
                nbins=20,
                color_discrete_sequence=['#0ea5e9']
            )
            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis_title="Age (Years)",
                yaxis_title="Count"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No age data available")
    
    with col_c4:
        st.markdown("#### ⚡ CTDIvol vs Total DLP")
        if 'CTDIvol_val' in filtered_df.columns and 'Total_DLP_val' in filtered_df.columns:
            valid_data = filtered_df.dropna(subset=['CTDIvol_val', 'Total_DLP_val'])
            if not valid_data.empty:
                fig = px.scatter(
                    valid_data,
                    x='CTDIvol_val',
                    y='Total_DLP_val',
                    size='CTDIvol_val',
                    color='Jenis Kelamin' if 'Jenis Kelamin' in valid_data.columns else None,
                    hover_data=['Nama Pasien'] if 'Nama Pasien' in valid_data.columns else None,
                    color_discrete_sequence=['#0ea5e9', '#f472b6', '#a78bfa']
                )
                fig.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=20, b=20),
                    xaxis_title="CTDIvol (mGy)",
                    yaxis_title="Total DLP (mGy·cm)"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No dose data available")
        else:
            st.info("No dose data available")
    
    # Data Table and Management
    st.markdown("---")
    col_t1, col_t2 = st.columns([4, 1])
    with col_t1:
        st.markdown("### 📋 Patient Data Table")
    with col_t2:
        if st.button("🗑️ Clear All", type="secondary", use_container_width=True, help="Hapus semua data"):
            st.session_state['confirm_delete_all'] = True
    
    if st.session_state.get('confirm_delete_all'):
        st.warning("⚠️ Apakah Anda yakin ingin menghapus SELURUH data? Tindakan ini tidak dapat dibatalkan.")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("✅ Ya, Hapus Semua", type="primary", use_container_width=True):
                excel_handler.clear_all_data()
                st.session_state['confirm_delete_all'] = False
                st.success("Data berhasil dikosongkan.")
                st.rerun()
        with col_c2:
            if st.button("❌ Batal", use_container_width=True):
                st.session_state['confirm_delete_all'] = False
                st.rerun()

    # Show only relevant columns
    display_cols = ['No', 'Nama Pasien', 'Jenis Kelamin', 'Umur Pasien', 'Jenis Pemeriksaan', 'CTDIvol', 'Total DLP']
    display_df = filtered_df[[c for c in display_cols if c in filtered_df.columns]]
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Individual Deletion Section
    with st.expander("🗑️ Hapus Data Individu"):
        st.write("Pilih data yang ingin dihapus berdasarkan nomor urut (No):")
        no_to_delete = st.number_input("Masukkan nomor (No)", min_value=1, max_value=int(df['No'].max()) if not df.empty else 1, step=1)
        if st.button("🗑️ Hapus Record Ini", type="secondary"):
            if not hasattr(excel_handler, 'delete_record'):
                st.error("Error: Fungsi penghapusan tidak ditemukan di module Excel. Silakan perbarui file excel_handler.py di server.")
            elif excel_handler.delete_record(int(no_to_delete)):
                st.success(f"Record No {no_to_delete} berhasil dihapus.")
                st.rerun()
            else:
                st.error("Gagal menghapus record. Pastikan nomor benar.")


def render_upload_page():
    """Render the upload and extraction page"""
    extractor = MedicalScanExtractor()
    excel_handler = ExcelHandler()
    
    # Back button
    if st.button("← Back to Dashboard", key="back_to_dashboard"):
        st.session_state['page'] = 'dashboard'
        st.rerun()
    
    # Header
    st.markdown("""
        <div class="app-header">
            <h1 class="app-title">📤 Upload & Extract Data</h1>
            <p class="app-subtitle">Upload CT scan dose report images to extract patient data</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Quick Stats
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
        
        # Individual Deletion in Upload Page
        with st.expander("🗑️ Hapus Data Individu"):
            st.write("Masukkan nomor urut (No) dari tabel di atas untuk menghapus:")
            del_no = st.number_input("No Record", min_value=1, key="del_no_upload")
            if st.button("🗑️ Hapus", key="del_btn_upload"):
                if not hasattr(excel_handler, 'delete_record'):
                    st.error("Error: Fungsi penghapusan tidak ditemukan di module Excel. Silakan perbarui file excel_handler.py di server.")
                elif excel_handler.delete_record(int(del_no)):
                    st.success(f"Record {del_no} dihapus.")
                    st.rerun()
                else:
                    st.error("Gagal menghapus.")
        
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


def main():
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
    
    # Route to appropriate page
    if st.session_state.get('page') == 'upload':
        render_upload_page()
    else:
        render_dashboard()
    
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
