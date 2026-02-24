"""
OCR Extractor Module for Medical Scan Data
Extracts patient information from CT scan dose report images
"""

import re
import cv2
import numpy as np
import pytesseract
from PIL import Image
from typing import Dict, Optional


class MedicalScanExtractor:
    """Extract patient data from CT scan dose report images"""
    
    def __init__(self):
        # Configure tesseract path for Windows (Tesseract OCR 5.5.0)
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for better OCR results
        Optimized for medical scan dose report images with dark backgrounds
        """
        # Read image
        img = cv2.imread(image_path)

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Invert colors (dark background to white background for better OCR)
        # Medical scan displays typically have white text on dark background
        inverted = 255 - gray

        # Apply Otsu thresholding for automatic threshold selection
        _, thresh = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Apply morphological operations to connect text characters
        kernel = np.ones((2, 2), np.uint8)
        denoised = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        return denoised
    
    def extract_data(self, image_path: str) -> Dict[str, Optional[str]]:
        """
        Extract patient data from the image

        Returns:
            Dictionary with extracted fields
        """
        # Preprocess image
        processed_img = self.preprocess_image(image_path)

        # Perform OCR with different configurations for better accuracy
        # Config 1: Standard config for general text
        config1 = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(processed_img, config=config1)

        # Config 2: Sparse text config for better field extraction
        config2 = r'--oem 3 --psm 11'
        text_sparse = pytesseract.image_to_string(processed_img, config=config2)

        # Combine both texts for better coverage
        combined_text = text + "\n" + text_sparse

        # Also get detailed data with bounding boxes
        data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)

        # Extract fields using multiple methods
        result = {
            'nama_pasien': self._extract_patient_name(combined_text, data),
            'tanggal_pemeriksaan': self._extract_exam_date(combined_text),
            'id_pasien': self._extract_patient_id(combined_text, data),
            'jenis_pemeriksaan': self._extract_exam_description(image_path, combined_text, data),
            'ctdi_vol': self._extract_ctdi_vol(combined_text, data),
            'total_dlp': self._extract_total_dlp(combined_text, data)
        }

        return result
    
    def _extract_patient_name(self, text: str, data: Dict) -> Optional[str]:
        """Extract patient name from OCR text"""
        # Look for "Patient Name:" pattern - more flexible pattern
        pattern = r'Patient\s*Name\s*:\s*([A-Z,\s\.\']+?)(?:\n|$)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up the name - remove extra words that aren't part of the name
            # Names typically contain letters, commas, periods, and spaces
            name_parts = re.findall(r'[A-Z]+(?:\.[A-Z]+)*|[A-Z]+(?:,[A-Z]+)*', name)
            if name_parts:
                return ' '.join(name_parts).strip()
            if name and len(name) > 2:
                return name

        # Alternative: search in data blocks using bounding box data
        for i, word in enumerate(data.get('text', [])):
            if 'patient' in word.lower() and i + 1 < len(data['text']):
                if 'name' in data['text'][i + 1].lower():
                    # Get next few words (skip colon if present)
                    name_parts = []
                    for j in range(i + 2, min(i + 8, len(data['text']))):
                        word_text = data['text'][j].strip()
                        if word_text and word_text != ':':
                            # Check if it looks like part of a name (uppercase letters, commas, periods)
                            # Stop at words that don't look like names
                            if re.match(r'^[A-Z]+[,\.\']?$', word_text) or word_text in ['NY', 'TN', 'NK', 'AN']:
                                name_parts.append(word_text)
                            elif name_parts:
                                break
                    if name_parts:
                        return ' '.join(name_parts).strip()

        # Fallback: Look for "Name:" followed by uppercase text
        pattern = r'Name\s*:\s*([A-Z,\s\.\']+?)(?:\n|$)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            name_parts = re.findall(r'[A-Z]+(?:\.[A-Z]+)*|[A-Z]+(?:,[A-Z]+)*', name)
            if name_parts:
                return ' '.join(name_parts).strip()
            if name and len(name) > 2:
                return name

        return None
    
    def _extract_exam_date(self, text: str) -> Optional[str]:
        """Extract examination date from OCR text"""
        # Look for date patterns (e.g., "16 Dec 2025")
        patterns = [
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Sep|Okt|Nov|Dec|Des|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_patient_id(self, text: str, data: Dict = None) -> Optional[str]:
        """Extract patient ID from OCR text"""
        # Priority 1: Look for "Patient ID:" pattern (with OCR error tolerance)
        patterns = [
            r'Patient\s*ID\s*:\s*(\d+)',
            r'Patient\s*vo\s*:\s*(\d+)',  # OCR error: ID -> vo
            r'Patient\s*lD\s*:\s*(\d+)',  # OCR error: ID -> lD
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Priority 2: Search in data blocks for Patient ID
        if data:
            for i, word in enumerate(data.get('text', [])):
                if 'patient' in word.lower() or 'palbent' in word.lower():
                    # Check next few words for ID pattern
                    for j in range(i + 1, min(i + 4, len(data['text']))):
                        next_word = data['text'][j].strip()
                        if next_word.lower() in ['id', 'vo', 'ld']:
                            # Get the number after ID
                            for k in range(j + 1, min(j + 3, len(data['text']))):
                                val = data['text'][k].strip()
                                if val.isdigit() and len(val) >= 4:
                                    return val

        # Priority 3: Accession Number as fallback (only if Patient ID not found)
        pattern = r'Accession\s*Number\s*:\s*(\d+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return None
    
    def _extract_exam_description(self, image_path: str, text: str, data: Dict) -> Optional[str]:
        """Extract examination type/description from OCR text using multiple methods"""
        
        # Method 1: Look for "Exam Description:" pattern in text
        pattern = r'Exam\s*Description\s*:\s*(.+?)(?:\n|$)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result = match.group(1).strip()
            if result and len(result) > 2:
                return result

        # Method 2: Alternative pattern for Exam Description
        pattern = r'Exam\s*Description\s*:\s*([A-Z0-9\+\-\s\.\,]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result = match.group(1).strip()
            if result and len(result) > 2:
                return result

        # Method 3: Search using bounding box data - find "Exam Description" and get next words
        exam_desc_index = -1
        for i, word in enumerate(data.get('text', [])):
            if 'exam' in word.lower() or 'Exam' in word:
                # Check if next few words contain "Description"
                for j in range(i+1, min(i+3, len(data['text']))):
                    if 'description' in data['text'][j].lower() or 'Description' in data['text'][j]:
                        exam_desc_index = j
                        break
                if exam_desc_index > 0:
                    break
        
        if exam_desc_index > 0:
            # Get words after "Exam Description" (skip the colon if present)
            desc_parts = []
            for j in range(exam_desc_index + 1, min(exam_desc_index + 10, len(data['text']))):
                word = data['text'][j].strip()
                if word and word != ':':
                    # Check if this looks like part of exam description (uppercase, numbers, + sign)
                    if word.isupper() or word == '+' or re.match(r'^[A-Z0-9\+\-\.]+$', word):
                        desc_parts.append(word)
                    elif desc_parts:  # Stop at first lowercase word after getting some parts
                        break
            
            if desc_parts:
                return ' '.join(desc_parts).strip()

        # Method 4: Crop the top region of the image and re-OCR specifically for Exam Description
        try:
            img = cv2.imread(image_path)
            if img is not None:
                height, width = img.shape[:2]
                # Crop top 30% of image where Exam Description is typically located
                y1, y2 = int(height * 0.1), int(height * 0.4)
                x1, x2 = int(width * 0.1), int(width * 0.9)
                cropped_region = img[y1:y2, x1:x2]
                
                # Preprocess cropped region
                gray_crop = cv2.cvtColor(cropped_region, cv2.COLOR_BGR2GRAY)
                _, thresh_crop = cv2.threshold(gray_crop, 150, 255, cv2.THRESH_BINARY)
                
                # OCR on cropped region
                crop_text = pytesseract.image_to_string(thresh_crop, config=r'--oem 3 --psm 7')
                
                # Search for Exam Description in cropped text
                pattern = r'Exam\s*Description\s*:\s*(.+?)(?:\n|$)'
                match = re.search(pattern, crop_text, re.IGNORECASE)
                if match:
                    result = match.group(1).strip()
                    if result and len(result) > 2:
                        return result
        except Exception:
            pass  # Fallback to text-based methods if image processing fails

        # Method 5: Line by line search
        lines = text.split('\n')
        for line in lines:
            if 'Exam Description' in line and ':' in line:
                desc = line.split(':', 1)[1].strip()
                if desc and len(desc) > 2:
                    return desc

        return None
    
    def _extract_ctdi_vol(self, text: str, data: Dict) -> Optional[str]:
        """Extract CTDIvol value from OCR text"""
        ctdi_values = []

        # Pattern 1: Look for Helical scan rows - these contain the main CTDIvol values
        # The format is typically: "Helical <scan_range> <ctdi_vol> <dlp>"
        helical_pattern = r'Helical\s+([\d\.]+\-[\d\.]+)\s+(\d+\.\d+)\s+(\d+\.\d+)'
        helical_matches = re.findall(helical_pattern, text)
        for match in helical_matches:
            if len(match) >= 2:
                ctdi_vol = match[1]  # Second number after scan range is CTDIvol
                if ctdi_vol and float(ctdi_vol) > 0:
                    ctdi_values.append(ctdi_vol)

        # Pattern 2: Look for lines with CTDIvol header and extract values below
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'CTDIvol' in line or 'CTDI' in line:
                # Look for numeric values in the next few lines (table rows)
                for j in range(i + 1, min(i + 6, len(lines))):
                    # Find decimal numbers that could be CTDIvol values (typically 0-100 range)
                    numbers = re.findall(r'\b(\d+\.\d+)\b', lines[j])
                    for num in numbers:
                        try:
                            val = float(num)
                            if 0.01 < val < 100:  # CTDIvol is typically in this range
                                ctdi_values.append(num)
                        except ValueError:
                            pass

        # Pattern 3: Use bounding box data to find CTDIvol column values
        # Find the column position of CTDIvol header
        ctdi_positions = []
        for i, word in enumerate(data.get('text', [])):
            if 'ctdi' in word.lower() or 'CTDI' in word:
                # Get the vertical position (top) of this word
                if i < len(data.get('top', [])):
                    ctdi_positions.append(data['top'][i])

        # Pattern 4: Look for standalone decimal values that could be CTDIvol
        # These are typically small values (0.01 - 50 mGy)
        decimal_pattern = r'\b(\d+\.\d+)\b'
        all_decimals = re.findall(decimal_pattern, text)
        for num in all_decimals:
            try:
                val = float(num)
                if 0.01 < val < 50:  # CTDIvol range
                    # Check if it's not part of a scan range (which has format like 6.770-1413.230)
                    if not re.search(rf'{num}[\d\-\.]+', text):
                        ctdi_values.append(num)
            except ValueError:
                pass

        # Return the most common CTDIvol value (main scan value)
        if ctdi_values:
            # Filter valid values
            valid_values = [v for v in ctdi_values if v and float(v) > 0]
            if valid_values:
                # Return the most frequent value or the maximum
                from collections import Counter
                most_common = Counter(valid_values).most_common(1)
                if most_common:
                    return most_common[0][0]

        return None

    def _extract_total_dlp(self, text: str, data: Dict = None) -> Optional[str]:
        """Extract Total DLP value from OCR text"""
        # Pattern 1: Look for "Total Exam DLP:" pattern (with OCR error tolerance)
        patterns = [
            r'Total\s*Exam\s*DLP\s*:\s*([\d\.]+)',
            r'Total\s*Exam\s*O8P\s*:\s*([\d\.]+)',  # OCR error: DLP -> O8P
            r'Total\s*Exam\s*OLP\s*:\s*([\d\.]+)',  # OCR error: DLP -> OLP
            r'Total\s*Exam\s*DLP\s+([\d\.]+)',
            r'Total\s*Exam\s*O8P\s+([\d\.]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Pattern 2: Search line by line for "Total" and "DLP" on same line
        lines = text.split('\n')
        for line in lines:
            if ('Total' in line or 'total' in line) and ('DLP' in line or 'O8P' in line or 'OLP' in line):
                # Extract all numbers from this line
                numbers = re.findall(r'(\d+\.\d+)', line)
                if numbers:
                    return numbers[-1]  # Usually the last number is the DLP value
        
        # Pattern 3: Look for "Total" followed by "Exam" and then a number
        for line in lines:
            if ('Total' in line or 'total' in line) and 'Exam' in line:
                numbers = re.findall(r'(\d+\.\d+)', line)
                if numbers:
                    return numbers[-1]

        # Pattern 4: Alternative pattern "Total DLP:"
        pattern = r'Total\s*DLP\s*:\s*([\d\.]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Pattern 5: Use bounding box data if available
        if data:
            for i, word in enumerate(data.get('text', [])):
                if 'total' in word.lower() or 'Total' in word:
                    # Check if next few words contain DLP (or OCR errors)
                    next_words = data['text'][i+1:i+6]
                    if any('dlp' in w.lower() or 'DLP' in w or 'o8p' in w.lower() for w in next_words):
                        # Find the first number after DLP
                        for w in next_words:
                            if re.match(r'^\d+\.\d+$', w):
                                return w

        return None
    
    def extract_from_pil_image(self, image: Image.Image) -> Dict[str, Optional[str]]:
        """
        Extract data from PIL Image object (for Streamlit uploaded files)
        """
        # Convert PIL to OpenCV format
        img_array = np.array(image)
        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Save temporarily for processing
        temp_path = 'temp_upload.png'
        cv2.imwrite(temp_path, img_rgb)
        
        result = self.extract_data(temp_path)
        
        # Clean up
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return result
