import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

img = cv2.imread('data hasil scan.jpeg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
inverted = 255 - gray
_, thresh = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# Save for visual debugging
cv2.imwrite('debug_thresh.png', thresh)

# Get full text
text = pytesseract.image_to_string(thresh, config='--oem 3 --psm 6')
print("=== FULL TEXT ===")
print(text)

print("\n=== SEARCH FOR PATIENT ID ===")
import re
pattern = r'Patient\s*ID\s*:\s*(\d+)'
match = re.search(pattern, text, re.IGNORECASE)
if match:
    print(f"Found Patient ID: {match.group(1)}")
else:
    print("Patient ID not found with pattern")
    
print("\n=== SEARCH FOR TOTAL DLP ===")
pattern = r'Total\s*Exam\s*DLP\s*:\s*([\d\.]+)'
match = re.search(pattern, text, re.IGNORECASE)
if match:
    print(f"Found Total DLP: {match.group(1)}")
else:
    print("Total DLP not found with pattern")

# Print lines containing Total or DLP
print("\n=== LINES WITH TOTAL OR DLP ===")
for line in text.split('\n'):
    if 'Total' in line or 'DLP' in line or '718' in line:
        print(f"'{line}'")
