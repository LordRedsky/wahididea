"""
Medical Scan Data Extractor - Streamlit Application
Extract patient data from CT scan dose report images and save to Excel
"""

import streamlit as st
from PIL import Image
from ocr_extractor import MedicalScanExtractor
from excel_handler import ExcelHandler
import os
import subprocess
import platform


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

        st.header("ℹ️ Information")
        st.markdown("""
        **Extracted Fields:**
        - Nama Pasien
        - Tanggal Pemeriksaan
        - ID Pasien
        - Jenis Pemeriksaan
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
        st.header("📤 Upload Image")
        
        uploaded_file = st.file_uploader(
            "Choose a CT scan dose report image",
            type=["jpg", "jpeg", "png"],
            help="Upload a clear image of the CT scan dose report"
        )
        
        if uploaded_file is not None:
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)
            
            # Extract button
            if st.button("🔍 Extract Data", type="primary", use_container_width=True):
                with st.spinner("Processing image... Please wait."):
                    # Extract data
                    extracted_data = extractor.extract_from_pil_image(image)
                    
                    # Store in session state
                    st.session_state['extracted_data'] = extracted_data
                    st.session_state['image_uploaded'] = True
                
                st.success("Data extracted successfully!")
    
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
            
            with c2:
                st.info(f"**Jenis Pemeriksaan:** {data.get('jenis_pemeriksaan', 'Not detected')}")
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
            - **Jenis Pemeriksaan:** Exam description/type
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
