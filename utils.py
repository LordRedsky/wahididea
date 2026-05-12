import re

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
            match = re.search(r'\(0010,1010\).*?AS.*?(\d+)([A-Z])\s*$', line)
            if match:
                age_num = match.group(1).strip()
                age_unit = match.group(2).strip()
                if age_unit in ['Y', 'M', 'W', 'D']:
                    result['umur_pasien'] = int(age_num)
                else:
                    result['umur_pasien'] = int(age_num)
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
            match = re.search(r'\(0018,0060\).*?DS\s+\d+\s+(\d+)\s+(\d+)', line)
            if match:
                kv_values.append(match.group(2).strip())
    if kv_values:
        result['kv'] = kv_values[-1]  # Take the last value (usually from Helical)
    
    # Extract CTDIvol from (0018,9345) CTDIvol - get all values and take max
    ctdi_values = []
    for line in lines:
        if '(0018,9345)' in line and 'CTD' in line.upper():
            match = re.search(r'\(0018,9345\).*?FD\s+\d+\s+\d+\s+([\d\.]+)', line)
            if match:
                try:
                    val = float(match.group(1).strip())
                    if val > 0:
                        ctdi_values.append(val)
                except (ValueError, TypeError):
                    pass
    if ctdi_values:
        result['ctdi_vol'] = str(max(ctdi_values))
    
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

def load_css(file_path):
    with open(file_path) as f:
        return f"<style>{f.read()}</style>"
