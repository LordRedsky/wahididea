# Streamlit Cloud Deployment Guide

## ✅ Files Ready for Deployment

Make sure these files are committed and pushed to GitHub:

```
wahid-idea/
├── app.py                 # Main Streamlit app
├── ocr_extractor.py       # OCR extraction logic
├── excel_handler.py       # Excel handling
├── requirements.txt       # Python packages (includes opencv-python-headless)
├── packages.txt           # System packages (Tesseract OCR) ⭐ IMPORTANT
├── .streamlit/
│   ├── config.toml        # Streamlit config
│   └── packages.txt       # Additional system packages
└── README.md              # Documentation
```

## 🚀 Deployment Steps

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Fix: Streamlit Cloud deployment with Tesseract OCR"
git push origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to [https://share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Select your GitHub repository: `wahid-idea`
4. Configure:
   - **Main file path:** `app.py`
   - **Python version:** `3.10` or higher
5. Click **"Deploy!"**

### Step 3: Wait for Installation ⏰

**IMPORTANT:** The first deployment will take **5-10 minutes** because:
- Streamlit Cloud installs Tesseract OCR from `packages.txt`
- This is a system-level installation that takes time

**DO NOT** refresh or cancel the deployment. Wait for it to complete.

### Step 4: Verify Tesseract Installation

After deployment:
1. Open your deployed app
2. Check the sidebar under **"🔍 System Status"**
3. You should see: **"✅ Tesseract installed"** with version info

If you see **"❌ Tesseract not found"**:
- Wait a few more minutes (installation may still be in progress)
- Check deployment logs in Streamlit Cloud dashboard
- Ensure `packages.txt` is in your repository root

### Step 5: Test OCR Functionality

1. Upload a test image (e.g., `data hasil scan.jpeg`)
2. Click **"🔍 Extract Data"**
3. Wait for processing
4. Verify extracted data appears
5. Click **"💾 Save to Excel"** to save

## 📋 packages.txt Content

This file tells Streamlit Cloud to install Tesseract OCR:

```
tesseract-ocr
libtesseract-dev
tesseract-ocr-eng
tesseract-ocr-ind
tesseract-ocr-osd
```

**DO NOT** rename this file to `apt-packages.txt` - Streamlit Cloud only recognizes `packages.txt`.

## 🔧 requirements.txt Content

Python dependencies (note: `opencv-python-headless` for cloud compatibility):

```
streamlit>=1.28.0
pytesseract>=0.3.10
Pillow>=10.0.0
opencv-python-headless>=4.8.0
numpy>=1.24.0
openpyxl>=3.1.0
```

## ⚠️ Common Issues & Solutions

### Issue 1: "TesseractNotFoundError"
**Cause:** Tesseract not installed yet or `packages.txt` missing

**Solution:**
1. Verify `packages.txt` exists in repository root
2. Check deployment logs for installation errors
3. Wait 5-10 minutes for first deployment
4. Redeploy if necessary

### Issue 2: "cv2.bootstrap error"
**Cause:** Using `opencv-python` instead of `opencv-python-headless`

**Solution:**
1. Ensure `requirements.txt` has `opencv-python-headless`
2. Remove `opencv-python` if present
3. Redeploy

### Issue 3: Deployment stuck at "Installing packages"
**Cause:** Normal behavior - Tesseract installation takes time

**Solution:**
- Wait patiently (5-10 minutes)
- Check logs in Streamlit Cloud dashboard
- Do not cancel deployment

### Issue 4: OCR works locally but not on Streamlit Cloud
**Cause:** Different OS (Windows vs Linux) or missing Tesseract

**Solution:**
1. Verify `packages.txt` is committed to GitHub
2. Check Streamlit Cloud deployment logs
3. Verify Tesseract installation in sidebar

## 📊 Monitoring Deployment

1. Go to Streamlit Cloud dashboard
2. Select your app
3. Click **"Logs"** tab
4. Look for:
   - `Installing tesseract-ocr` - Normal, wait for completion
   - `Setting up dependencies` - In progress
   - `Your app is running` - Success!

## 🎉 Success Indicators

Your deployment is successful when:
- ✅ App loads without errors
- ✅ Sidebar shows "✅ Tesseract installed"
- ✅ Image upload works
- ✅ OCR extraction completes successfully
- ✅ Data saves to Excel

## 📞 Support

If issues persist:
1. Check Streamlit Cloud community forum: [discuss.streamlit.io](https://discuss.streamlit.io)
2. Review Streamlit Cloud docs: [docs.streamlit.io](https://docs.streamlit.io)
3. Check deployment logs for specific error messages

## 🔄 Updating After Initial Deployment

After the initial deployment, subsequent updates are faster:
1. Make changes locally
2. `git push` to GitHub
3. Streamlit Cloud auto-redeploys (usually 1-2 minutes)
4. No need to reinstall Tesseract unless `packages.txt` changes

---

**Good luck with your deployment! 🚀**
