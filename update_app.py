import sys

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

import_line = 'from utils import convert_date, extract_from_dicom_text, load_css\n'

# Find imports
insert_idx = 0
for i, line in enumerate(lines):
    if line.startswith('import numpy as np'):
        insert_idx = i + 1
        break

lines.insert(insert_idx, import_line)

# Remove CSS and functions
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if '# Custom CSS - Clean Medical Theme' in line:
        start_idx = i
    if 'def prepare_dashboard_data(records):' in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_lines = lines[:start_idx] + ["st.markdown(load_css('style.css'), unsafe_allow_html=True)\n\n"] + lines[end_idx:]
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print('app.py updated successfully.')
else:
    print('Could not find start or end index')
    print('Start:', start_idx, 'End:', end_idx)
