# Quick Start Guide

## Fast Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database
```bash
python setup.py
```

### 3. Populate Sample Data
```bash
python database/init_data.py
```

### 4. Run Application & Explore
```bash
python app.py
```
- Open `http://localhost:5000`
- Apply filters on the analytics tabs and export CSV summaries
- Use the **Predictions** tab to train the ML model and score visits
- Visit the **Bulk Upload** tab to run the ingestion pipeline

## Bulk Data Ingestion
1. Download the CSV template from **Bulk Upload > Download template**
2. Populate patient, doctor, hospital and visit columns
3. Upload the file—validation happens automatically
4. Monitor job status and review failed rows with detailed messages

## Machine Learning Predictions
1. Navigate to the **Predictions** tab
2. Click **Train Model** (requires minimum 100 historical visits)
3. Enter visit attributes and click **Predict Risk**
4. Review probability and risk classification instantly

## Default MySQL Settings

If your MySQL uses different credentials, update them in:
- `app.py` (line 17-21)
- `database/init_data.py` (line 14-18)
- `setup.py` (line 10-14)

Or set environment variables:
```bash
# Windows PowerShell
$env:DB_PASSWORD="your_password"

# Linux/Mac
export DB_PASSWORD="your_password"
```

## Troubleshooting

**MySQL Connection Error?**
- Make sure MySQL is running
- Check username/password
- Verify MySQL is accessible on localhost

**Module Not Found?**
- Run: `pip install -r requirements.txt`

**Port Already in Use?**
- Change port in `app.py` (line 594)
- Or set: `$env:PORT=5001`

## What's Included

✅ Complete database schema (star schema design)
✅ 50 hospitals across India
✅ 200 doctors with specializations
✅ 1000 patients from Indian cities
✅ 5000 patient visits
✅ Premium web interface
✅ Advanced analytics dashboard

Enjoy analyzing healthcare data! 🏥📊

