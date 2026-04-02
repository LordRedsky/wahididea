"""
OCR Extractor Module for Medical Scan Data
Extracts patient information from CT scan dose report images
Supports: JPEG, PNG, and DICOM (.dcm) formats
"""

import re
import cv2
import numpy as np
import pytesseract
from PIL import Image
from typing import Dict, Optional
import platform
import os
import sys

try:
    import pydicom
    HAS_DICOM = True
except ImportError:
    HAS_DICOM = False
    pydicom = None


def get_tesseract_path():
    """Get the appropriate Tesseract path based on platform and execution mode"""
    
    # When running as compiled executable (PyInstaller)
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = sys._MEIPASS
        tesseract_path = os.path.join(application_path, 'tesseract', 'tesseract.exe')
        if os.path.exists(tesseract_path):
            return tesseract_path
    
    # Platform-specific paths
    system = platform.system()
    
    if system == "Windows":
        # First check if tesseract exists in the same directory as the executable
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            exe_dir = os.path.dirname(sys.executable)
            tesseract_path = os.path.join(exe_dir, 'tesseract', 'tesseract.exe')
            if os.path.exists(tesseract_path):
                return tesseract_path
        
        # Check common installation paths
        common_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'Tesseract-OCR', 'tesseract.exe'),
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # Fallback to default path
        return r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
    elif system == "Linux":
        # Linux path (standard installation path)
        return '/usr/bin/tesseract'
        
    elif system == "Darwin":  # macOS
        return '/opt/homebrew/bin/tesseract'
    
    # For other systems, pytesseract will use the default path
    return None


class MedicalScanExtractor:
    """Extract patient data from CT scan dose report images"""

    def __init__(self):
        # Configure tesseract path based on platform and execution mode
        tesseract_path = get_tesseract_path()
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for better OCR results
        Enhanced for low-quality, blurry medical scan images
        """
        # Load image (handles both regular images and DICOM files)
        img = self.load_image_for_ocr(image_path)
        if img is None:
            raise ValueError(f"Unsupported image format or unable to load: {image_path}")

        # Apply bilateral filter to reduce noise while preserving edges
        denoised = cv2.bilateralFilter(img, 9, 75, 75)

        # Convert to grayscale
        gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # This improves contrast in local regions
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Apply Gaussian blur to reduce remaining noise
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)

        # Invert colors (dark background to white background for better OCR)
        inverted = 255 - blurred

        # Apply adaptive thresholding with larger block size for blurry images
        thresh = cv2.adaptiveThreshold(
            inverted, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            15, 5  # Larger block size and C value for smoother threshold
        )

        # Apply morphological operations to connect broken characters
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=1)
        eroded = cv2.erode(dilated, kernel, iterations=1)

        # Apply closing to fill gaps in characters
        closed = cv2.morphologyEx(eroded, cv2.MORPH_CLOSE, kernel)

        return closed

    def preprocess_image_strong(self, image_path: str) -> np.ndarray:
        """
        Strong preprocessing for very low quality images
        Uses more aggressive enhancement techniques
        """
        img = cv2.imread(image_path)
        if img is None:
            return None

        # Apply non-local means denoising (stronger than bilateral)
        denoised = cv2.fastNlMeansDenoising(img, None, 30, 7, 21)

        # Convert to grayscale
        gray = cv2.cvtColor(denoised, cv2.COLOR_BGR2GRAY)

        # Apply strong CLAHE
        clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(16, 16))
        enhanced = clahe.apply(gray)

        # Sharpen the image
        kernel_sharpen = np.array([[-1, -1, -1],
                                   [-1,  9, -1],
                                   [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel_sharpen)

        # Invert colors
        inverted = 255 - sharpened

        # Apply Otsu thresholding after Gaussian blur
        blur = cv2.GaussianBlur(inverted, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Morphological operations
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        eroded = cv2.erode(dilated, kernel, iterations=1)

        return eroded

    def extract_from_top_region(self, image_path: str) -> str:
        """
        Extract text specifically from the top region of the image
        where patient info is typically located
        """
        img = cv2.imread(image_path)
        if img is None:
            return ""
        
        height, width = img.shape[:2]
        
        # Crop top 25% of image where patient info is located
        y1, y2 = int(height * 0.05), int(height * 0.30)
        x1, x2 = int(width * 0.05), int(width * 0.95)
        top_region = img[y1:y2, x1:x2]
        
        # Preprocess the cropped region
        gray = cv2.cvtColor(top_region, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        inverted = 255 - blurred
        thresh = cv2.adaptiveThreshold(
            inverted, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
        
        # OCR with single block config
        text = pytesseract.image_to_string(thresh, config=r'--oem 3 --psm 6')
        return text

    def preprocess_image_alternative(self, image_path: str) -> np.ndarray:
        """
        Alternative preprocessing with adaptive thresholding
        Better for images with varying lighting conditions
        """
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        inverted = 255 - gray

        # Use adaptive thresholding instead of Otsu
        adaptive = cv2.adaptiveThreshold(
            inverted, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )

        return adaptive

    def is_dicom_file(self, filepath: str) -> bool:
        """Check if a file is DICOM format by reading magic number (DICM at offset 128)"""
        try:
            with open(filepath, 'rb') as f:
                f.seek(128)
                magic = f.read(4)
                return magic == b'DICM'
        except Exception:
            return False

    def load_image_for_ocr(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load image for OCR processing, handling both regular images and DICOM files
        
        Args:
            image_path: Path to the image file (JPEG, PNG, DICOM, etc.)
            
        Returns:
            numpy array of the image or None if loading fails
        """
        ext = os.path.splitext(image_path)[1].lower()
        
        # Handle DICOM files
        if ext == '.dcm' or self.is_dicom_file(image_path):
            if not HAS_DICOM:
                raise ValueError("pydicom not installed. Cannot process DICOM files.")
            
            # Read DICOM file
            dicom_data = pydicom.dcmread(image_path)
            
            # Try to get pixel data
            try:
                pixel_array = dicom_data.pixel_array
                # Convert to uint8 if needed
                if pixel_array.dtype != np.uint8:
                    # Normalize to 0-255
                    pixel_array = ((pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
                # Convert to BGR for OpenCV (if grayscale, convert to 3-channel)
                if len(pixel_array.shape) == 2:
                    pixel_array = cv2.cvtColor(pixel_array, cv2.COLOR_GRAY2BGR)
                return pixel_array
            except Exception as e:
                # If pixel data extraction fails, try to save as temporary image
                # Some DICOM files contain embedded JPEG/PNG data
                return None
        else:
            # Handle regular images (JPEG, PNG, etc.)
            return cv2.imread(image_path)

    def extract_data(self, image_path: str, return_debug: bool = False) -> Dict[str, Optional[str]]:
        """
        Extract patient data from the image

        Args:
            image_path: Path to the image file
            return_debug: If True, include debug info in result

        Returns:
            Dictionary with extracted fields (and debug info if requested)
        """
        # Preprocess image with primary method (handles DICOM too)
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
        # Use PSM 6 for general data (better for structured text)
        data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
        # Use PSM 11 for Patient ID (better for sparse text fields)
        data_sparse = pytesseract.image_to_data(processed_img, config=config2, output_type=pytesseract.Output.DICT)

        # Try alternative preprocessing for Patient ID (more robust across platforms)
        try:
            alt_img = self.preprocess_image_alternative(image_path)
            alt_text_sparse = pytesseract.image_to_string(alt_img, config=config2)
            alt_data_sparse = pytesseract.image_to_data(alt_img, config=config2, output_type=pytesseract.Output.DICT)

            # Combine with original sparse data
            combined_text_for_id = combined_text + "\n" + alt_text_sparse
            combined_data_sparse = {
                'text': data_sparse['text'] + alt_data_sparse['text'],
                'top': data_sparse['top'] + alt_data_sparse['top'],
                'left': data_sparse['left'] + alt_data_sparse['left'],
                'width': data_sparse['width'] + alt_data_sparse['width'],
                'height': data_sparse['height'] + alt_data_sparse['height'],
                'conf': data_sparse['conf'] + alt_data_sparse['conf'],
            }
        except Exception:
            # Fallback to original if alternative fails
            combined_text_for_id = combined_text
            combined_data_sparse = data_sparse

        # Extract fields using multiple methods
        result = {
            'nama_pasien': self._extract_patient_name(combined_text, data),
            'tanggal_pemeriksaan': self._extract_exam_date(combined_text),
            'id_pasien': self._extract_patient_id(combined_text_for_id, combined_data_sparse),  # Use enhanced data for ID
            'jenis_pemeriksaan': self._extract_exam_description(image_path, combined_text, data),
            'ctdi_vol': self._extract_ctdi_vol(combined_text, data),
            'total_dlp': self._extract_total_dlp(combined_text, data)
        }

        # Add debug info if requested
        if return_debug:
            result['_debug_ocr_text'] = combined_text
            result['_debug_helical_lines'] = [
                line.strip() for line in combined_text.split('\n')
                if re.search(r'\bHelical\b', line.strip(), re.IGNORECASE)
            ]

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
        # OCR often misreads ID as 'vo', 'lD', 'IO', 'lO'
        # OCR also misreads "Patient ID" as "Padiena vo", "Palbent ID", etc.
        patterns = [
            r'Patient\s*ID\s*:\s*(\d+)',
            r'Patient\s*vo\s*:\s*(\d+)',           # OCR error: ID -> vo
            r'Patient\s*lD\s*:\s*(\d+)',           # OCR error: ID -> lD
            r'Patient\s*IO\s*:\s*(\d+)',           # OCR error: ID -> IO
            r'Patient\s*lO\s*:\s*(\d+)',           # OCR error: ID -> lO
            r'Padiena\s+vo\s*:\s*(\d+)',           # OCR error: Patient ID -> Padiena vo
            r'Palbent\s*ID\s*:\s*(\d+)',           # OCR error: Patient -> Palbent
            r'Palbent\s*vo\s*:\s*(\d+)',           # OCR error: Patient ID -> Palbent vo
            r'Palhent\s*vo\s*:\s*(\d+)',           # OCR error: Patient ID -> Palhent vo
            r'Patent\s+vo\s*:\s*(\d+)',            # OCR error: Patient -> Patent
            r'Paoent\s+vo\s*:\s*(\d+)',            # OCR error: Patient -> Paoent
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Priority 2: Search in data blocks for Patient ID using bounding box data
        # This is more reliable as it uses spatial information
        if data:
            for i, word in enumerate(data.get('text', [])):
                word_lower = word.lower()
                # Look for "Patient" or OCR errors (palbent, pa bent, padiena, palhent, etc.)
                if any(x in word_lower for x in ['patient', 'palbent', 'padiena', 'palhent', 'patent', 'paoent']):
                    # Check next few words for ID pattern (ID, vo, lD, IO, etc.)
                    for j in range(i + 1, min(i + 5, len(data['text']))):
                        next_word = data['text'][j].strip().lower()
                        # Check for ID variants (with or without colon)
                        if next_word in ['id', 'vo', 'ld', 'io', 'lO', 'IO', 'id:', 'vo:', 'ld:', 'io:', 'lO:', 'IO:']:
                            # Get the number after ID (skip colon if present)
                            for k in range(j + 1, min(j + 5, len(data['text']))):
                                val = data['text'][k].strip()
                                # Remove any non-digit characters
                                clean_val = re.sub(r'[^\d]', '', val)
                                if clean_val.isdigit() and len(clean_val) >= 4:
                                    return clean_val

        # Priority 3: Line-by-line search for patterns like "| Padiena vo: 678003"
        lines = text.split('\n')
        for line in lines:
            if any(x in line.lower() for x in ['padiena vo', 'palbent vo', 'palhent vo', 'patient vo', 'patent vo']):
                # Extract number after colon
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        number = parts[1].strip()
                        id_match = re.search(r'(\d+)', number)
                        if id_match:
                            patient_id = id_match.group(1).strip()
                            if len(patient_id) >= 4:
                                return patient_id

        # Priority 4: Search for any 6-digit number near "Patient" context
        # This is a fallback for heavily distorted OCR
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(x in line.lower() for x in ['patient', 'padiena', 'palbent', 'palhent']):
                # Look for 6-digit numbers in this line or next 2 lines
                search_text = ' '.join(lines[i:min(i+3, len(lines))])
                numbers = re.findall(r'\b(\d{6,})\b', search_text)
                for num in numbers:
                    # Exclude common non-ID numbers
                    if num not in ['000000', '111111', '123456']:
                        return num

        # Priority 5: Accession Number as fallback - DISABLED
        # We do NOT want to return Accession Number as Patient ID
        # These are different identifiers in medical records
        # pattern = r'Accession\s*Number\s*:\s*(\d+)'
        # match = re.search(pattern, text, re.IGNORECASE)
        # if match:
        #     pass  # Do not return Accession Number as Patient ID

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
        """Extract CTDIvol value from OCR text - ONLY from Helical scan type"""
        ctdi_values = []
        helical_lines = []

        # Step 1: Find all lines containing "Helical" keyword (case insensitive)
        lines = text.split('\n')
        for line in lines:
            line_stripped = line.strip()
            # ONLY process lines that contain Helical (case insensitive, with word boundary)
            if re.search(r'\bHelical\b', line_stripped, re.IGNORECASE):
                helical_lines.append(line_stripped)

        # Step 2: Extract CTDIvol from Helical lines only using strict patterns
        for helical_line in helical_lines:
            # Skip lines that only contain "Helical" without any numbers
            if not re.search(r'\d', helical_line):
                continue

            # Pattern 1: Helical with range format (most common)
            # Format: "Helical <range> <ctdi_vol> <dlp>" or "[num] Helical <range> <ctdi_vol> <dlp>"
            # Examples:
            # - "2 Helical $60.575-1439.425 11.09 601.69 Body 32"
            # - "Helical 6.770-1413.230 7.72 718.65"
            pattern1 = r'Helical\s+\$?(\d+\.?\d*)\-?(\d+\.?\d*)\s+(\d+\.\d+)\s+(\d+\.?\d*)'
            match = re.search(pattern1, helical_line)
            if match:
                # Group 3 is CTDIvol (first value after the range)
                ctdi_vol = match.group(3)
                if ctdi_vol:
                    try:
                        val = float(ctdi_vol)
                        # CTDIvol is typically in range 0.01 - 100 mGy
                        if 0.01 < val < 100:
                            ctdi_values.append(ctdi_vol)
                    except ValueError:
                        pass
                continue  # Found with pattern 1, move to next line

            # Pattern 2: Simpler Helical pattern without range
            # Format: "Helical ... <number> <number>" where first small number is CTDIvol
            if 'Helical' in helical_line:
                # Extract all decimal numbers from this line
                numbers = re.findall(r'(\d+\.\d+)', helical_line)
                if len(numbers) >= 2:
                    # Typically: [range_end, ctdi_vol, dlp]
                    # CTDIvol is usually the second number (index 1) and is small (< 100)
                    for num in numbers[1:3]:  # Check 2nd and 3rd numbers
                        try:
                            val = float(num)
                            # CTDIvol is typically 0.01 - 100 mGy
                            # DLP is typically larger (> 100)
                            if 0.01 < val < 100:
                                ctdi_values.append(num)
                                break  # Take the first valid CTDIvol
                        except ValueError:
                            pass

        # Step 3: If no Helical lines found, return None (do NOT fallback to non-Helical)
        # This ensures we ONLY extract from Helical scans
        if not helical_lines:
            return None

        # Step 4: Return the most common/consistent CTDIvol value from Helical scans only
        if ctdi_values:
            # Filter valid values
            valid_values = [v for v in ctdi_values if v and float(v) > 0]
            if valid_values:
                # Return the most frequent value (mode)
                from collections import Counter
                most_common = Counter(valid_values).most_common(1)
                if most_common:
                    return most_common[0][0]

        return None

    def _extract_total_dlp(self, text: str, data: Dict = None) -> Optional[str]:
        """Extract Total DLP value from OCR text"""
        # Pattern 1: Look for "Total Exam DLP:" pattern (with OCR error tolerance)
        # OCR errors: Total -> Totl, DLP -> OLP, O8P, missing spaces
        patterns = [
            r'Total\s*Exam\s*DLP\s*:\s*([\d\.]+)',
            r'Total\s*Exam\s*OLP\s*:\s*([\d\.]+)',  # OCR error: DLP -> OLP
            r'Total\s*Exam\s*O8P\s*:\s*([\d\.]+)',  # OCR error: DLP -> O8P
            r'Totl\s*Exam\s*OLP\s*:\s*([\d\.]+)',   # OCR error: Total -> Totl
            r'TotlExam\s*OLP\s*:\s*([\d\.]+)',      # OCR error: missing space
            r'Total\s*Exam\s*OLP\s+([\d\.]+)',
            r'Total\s*Exam\s*O8P\s+([\d\.]+)',
            r'TotalExam\s*OLP\s*:\s*([\d\.]+)',     # OCR error: missing space
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Pattern 2: Search line by line for "Total" and "DLP/OLP/O8P" on same line
        lines = text.split('\n')
        for line in lines:
            if ('Total' in line or 'Totl' in line or 'total' in line) and \
               ('DLP' in line or 'OLP' in line or 'O8P' in line or '718' in line):
                # Extract all numbers from this line
                numbers = re.findall(r'(\d+\.\d+)', line)
                if numbers:
                    return numbers[-1]  # Usually the last number is the DLP value

        # Pattern 3: Look for "Total" followed by "Exam" and then a number
        for line in lines:
            if ('Total' in line or 'Totl' in line or 'total' in line) and 'Exam' in line:
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
                if 'total' in word.lower() or 'Total' in word or 'Totl' in word:
                    # Check if next few words contain DLP (or OCR errors)
                    next_words = data['text'][i+1:i+6]
                    if any('dlp' in w.lower() or 'DLP' in w or 'olp' in w.lower() or 'OLP' in w or 'o8p' in w.lower() for w in next_words):
                        # Find the first number after DLP
                        for w in next_words:
                            if re.match(r'^\d+\.\d+$', w):
                                return w

        return None

    def extract_from_pil_image(self, image: Image.Image, return_debug: bool = False) -> Dict[str, Optional[str]]:
        """
        Extract data from PIL Image object (for Streamlit uploaded files)
        
        Args:
            image: PIL Image object
            return_debug: If True, include debug info in result
            
        Returns:
            Dictionary with extracted fields (and debug info if requested)
        """
        # Convert PIL to OpenCV format
        img_array = np.array(image)
        img_rgb = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        # Save temporarily for processing
        temp_path = 'temp_upload.png'
        cv2.imwrite(temp_path, img_rgb)

        result = self.extract_data(temp_path, return_debug=return_debug)

        # Clean up
        import os
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return result

    def extract_from_dicom(self, dicom_path: str, return_debug: bool = False) -> Dict[str, Optional[str]]:
        """
        Extract data from DICOM file
        
        DICOM files can contain both pixel data (images) and metadata
        
        Args:
            dicom_path: Path to the DICOM file (.dcm)
            return_debug: If True, include debug info in result
            
        Returns:
            Dictionary with extracted fields (and debug info if requested)
        """
        if not HAS_DICOM:
            raise ImportError("pydicom is required for DICOM support. Install with: pip install pydicom")
        
        result = {}
        
        try:
            # Read DICOM file
            ds = pydicom.dcmread(dicom_path)
            
            # Try to extract data from DICOM metadata first (more accurate)
            # Patient Name
            if hasattr(ds, 'PatientName') and ds.PatientName:
                result['nama_pasien'] = str(ds.PatientName)
            
            # Patient ID
            if hasattr(ds, 'PatientID') and ds.PatientID:
                result['id_pasien'] = str(ds.PatientID)
            
            # Study Date (format: YYYYMMDD)
            if hasattr(ds, 'StudyDate') and ds.StudyDate:
                date_str = str(ds.StudyDate)
                if len(date_str) == 8:
                    # Convert YYYYMMDD to DD Mon YYYY
                    year = date_str[0:4]
                    month = date_str[4:6]
                    day = date_str[6:8]
                    month_names = {
                        '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
                        '05': 'Mei', '06': 'Jun', '07': 'Jul', '08': 'Agu',
                        '09': 'Sep', '10': 'Okt', '11': 'Nov', '12': 'Des'
                    }
                    month_name = month_names.get(month, month)
                    result['tanggal_pemeriksaan'] = f"{day} {month_name} {year}"
            
            # Modality (Exam type)
            if hasattr(ds, 'Modality') and ds.Modality:
                result['jenis_pemeriksaan'] = str(ds.Modality)
            
            # Study Description (more detailed exam description)
            if hasattr(ds, 'StudyDescription') and ds.StudyDescription:
                study_desc = str(ds.StudyDescription)
                if study_desc and (not result.get('jenis_pemeriksaan') or len(study_desc) > len(result.get('jenis_pemeriksaan', ''))):
                    result['jenis_pemeriksaan'] = study_desc
            
            # Check if we have all required fields from metadata
            has_all_data = all([
                result.get('nama_pasien'),
                result.get('tanggal_pemeriksaan'),
                result.get('id_pasien'),
                result.get('ctdi_vol'),
                result.get('total_dlp')
            ])
            
            # If we don't have all data from metadata, try OCR on the image
            if not has_all_data and hasattr(ds, 'pixel_array'):
                # Get pixel data
                pixel_array = ds.pixel_array
                
                # Convert to uint8 if needed
                if pixel_array.dtype != np.uint8:
                    pixel_array = ((pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
                
                # Convert to RGB if grayscale
                if len(pixel_array.shape) == 2:
                    img_rgb = cv2.cvtColor(pixel_array, cv2.COLOR_GRAY2BGR)
                else:
                    img_rgb = cv2.cvtColor(pixel_array, cv2.COLOR_RGB2BGR)
                
                # Save temporarily for OCR processing
                temp_path = 'temp_dicom.png'
                cv2.imwrite(temp_path, img_rgb)
                
                # Extract data using OCR
                ocr_result = self.extract_data(temp_path, return_debug=False)
                
                # Merge OCR results with metadata (metadata takes precedence)
                for key in ['nama_pasien', 'tanggal_pemeriksaan', 'id_pasien', 'jenis_pemeriksaan', 'ctdi_vol', 'total_dlp']:
                    if key not in result or not result[key]:
                        result[key] = ocr_result.get(key)
                
                # Clean up
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            # Fill in missing fields with None
            for key in ['nama_pasien', 'tanggal_pemeriksaan', 'id_pasien', 'jenis_pemeriksaan', 'ctdi_vol', 'total_dlp']:
                if key not in result:
                    result[key] = None
            
            # Add debug info if requested
            if return_debug:
                result['_debug_source'] = 'DICOM metadata + OCR'
                result['_debug_dicom_tags'] = {
                    'PatientName': str(ds.PatientName) if hasattr(ds, 'PatientName') else None,
                    'PatientID': str(ds.PatientID) if hasattr(ds, 'PatientID') else None,
                    'StudyDate': str(ds.StudyDate) if hasattr(ds, 'StudyDate') else None,
                    'Modality': str(ds.Modality) if hasattr(ds, 'Modality') else None,
                    'StudyDescription': str(ds.StudyDescription) if hasattr(ds, 'StudyDescription') else None,
                }
            
        except Exception as e:
            # If DICOM processing fails, return empty result
            result = {
                'nama_pasien': None,
                'tanggal_pemeriksaan': None,
                'id_pasien': None,
                'jenis_pemeriksaan': None,
                'ctdi_vol': None,
                'total_dlp': None,
            }
            if return_debug:
                result['_debug_error'] = str(e)
                result['_debug_source'] = 'DICOM failed'
        
        return result
