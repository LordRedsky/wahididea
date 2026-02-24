import cv2
import pytesseract
import numpy as np

# Configure tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Read image
img = cv2.imread('data hasil scan.jpeg')
print(f'Image loaded: {img is not None}')
if img is not None:
    h, w = img.shape[:2]
    print(f'Image size: {w}x{h}')
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Invert colors (dark background to white background for better OCR)
    inverted = 255 - gray
    
    # Apply Otsu thresholding
    _, thresh = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Save for debugging
    cv2.imwrite('debug_preprocessed.png', thresh)
    print('Preprocessed image saved to debug_preprocessed.png')
    
    # OCR with different configs
    configs = [
        ('--oem 3 --psm 6', 'Uniform block'),
        ('--oem 3 --psm 4', 'Column of text'),
        ('--oem 3 --psm 11', 'Sparse text'),
        ('--oem 3 --psm 3', 'Fully automatic'),
    ]
    
    for config, desc in configs:
        print(f'\n=== {desc} ({config}) ===')
        text = pytesseract.image_to_string(thresh, config=config)
        print(text[:500] if len(text) > 500 else text)
