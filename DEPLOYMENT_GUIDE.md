# Deployment Guide for VBC Hydraulics Pump Report App

## Quick Setup for Streamlit Community Cloud

### Step 1: Prepare Your Files
Create these files in your project folder:

1. **requirements.txt** (already exists, but verify)
2. **README.md** (for documentation)
3. **.gitignore** (to exclude unnecessary files)

### Step 2: Create GitHub Repository
1. Go to github.com and create free account
2. Create new repository: "pump-test-report-analyzer"
3. Upload all your files

### Step 3: Deploy to Streamlit Cloud
1. Go to share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set main file path: "app.py"
6. Click "Deploy"

### Step 4: Share with QC Team
You'll get a public URL like:
https://pump-test-analyzer-vbc.streamlit.app

### Benefits:
- ✅ Always available online
- ✅ No server maintenance
- ✅ Auto-updates when you change code
- ✅ Free forever
- ✅ Professional URL
- ✅ SSL certificate included

### Usage for QC Staff:
1. Visit the URL
2. Upload Excel files
3. Generate reports
4. Download PDFs
5. No software installation needed

## Alternative: Local Network Deployment
If you prefer internal-only access:

```bash
# Run on company server/computer
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Then QC staff access via: http://YOUR_COMPUTER_IP:8501
