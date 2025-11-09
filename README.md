# Healthcare Analytics Data Warehouse

A comprehensive healthcare analytics platform built with Python (Flask) and MySQL, featuring a premium web interface for analyzing Indian healthcare data.

## Features

- **Dashboard Overview**: Real-time statistics and key metrics with instant filtering
- **Advanced Analytics**: 
  - Disease analysis and trends with exportable CSV reports
  - Hospital performance metrics with state, specialization and date filters
  - Geographic distribution analysis with drill-down to city level
  - Temporal trends (monthly/quarterly) with custom date range selection
  - Specialization analytics and visit type heatmap
  - Predictive analytics for high-cost visits using machine learning
- **Data Management**: 
  - Patient records management
  - Visit tracking with filtered pagination and export
  - Data entry forms
  - Bulk CSV/Excel ingestion pipeline with validation, staging and audit trail
- **Premium UI**: Modern, responsive design with interactive charts and filter panel
- **Indian Healthcare Dataset**: Pre-populated with realistic Indian healthcare data

## Technology Stack

- **Backend**: Python 3.8+, Flask, pandas, scikit-learn
- **Database**: MySQL 8.0+
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Charts**: Chart.js
- **Machine Learning**: scikit-learn Random Forest
- **ETL**: Pandas-based ingestion with MySQL staging tables

## Prerequisites

1. Python 3.8 or higher
2. MySQL 8.0 or higher
3. pip (Python package manager)

## Installation & Setup

### Step 1: Clone or Download the Project

Navigate to the project directory:
```bash
cd "Datawarehouse for healthcare analytics"
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

> The requirements now include pandas, numpy, scikit-learn, openpyxl and joblib for the analytics pipeline.

### Step 3: MySQL Database Setup

1. **Start MySQL Server**
   - Make sure MySQL is running on your system
   - Default configuration expects:
     - Host: `localhost`
     - User: `root`
     - Password: `root`
     - Database: `healthcare_analytics` (will be created automatically)

2. **Update Database Configuration** (if needed)
   
   Edit `app.py` and `database/init_data.py` to match your MySQL credentials:
   ```python
   DB_CONFIG = {
       'host': 'localhost',
       'user': 'root',
       'password': 'your_password',  # Change this
       'database': 'healthcare_analytics'
   }
   ```

3. **Create Database Schema**
   
   Open MySQL command line or MySQL Workbench and run:
   ```bash
   mysql -u root -p < database/schema.sql
   ```
   
   Or manually execute the SQL file in your MySQL client.

### Step 4: Populate Sample Data

Run the data initialization script to populate the database with Indian healthcare data. You can rerun this script or upload additional data through the **Bulk Upload** tab on the dashboard.

### Step 5: Run the Application

Start the Flask development server:

```bash
python app.py
```

The application will be available at: `http://localhost:5000`

> The server exposes new REST endpoints for metadata, ingestion, and machine learning. See **API Endpoints** for details.

## Project Structure

```
Datawarehouse for healthcare analytics/
│
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
│
├── database/
│   ├── schema.sql        # Database schema definition
│   └── init_data.py      # Data population script
│
├── templates/
│   └── index.html        # Main HTML template
│
└── static/
    ├── css/
    │   └── style.css     # Stylesheet
    └── js/
        └── app.js        # Frontend JavaScript
```

## Database Schema

The data warehouse follows a star schema design:

### Dimension Tables
- **patients**: Patient demographic information
- **hospitals**: Hospital details and location
- **doctors**: Doctor information and specializations
- **diseases**: Disease catalog
- **treatments**: Treatment procedures
- **medications**: Medication inventory
- **date_dimension**: Time dimension for temporal analysis

### Fact Tables
- **patient_visits**: Main fact table with visit details
- **hospital_statistics**: Aggregated hospital metrics

## Usage Guide

### Dashboard
- View overall statistics: total patients, hospitals, doctors, visits, revenue
- Analyze visits by type (OPD, Emergency, IPD, Follow-up)
- Review revenue by payment method
- Apply global filters (state, hospital, visit type, date range, disease, specialization)
- Export current analytics view as CSV with a single click

### Analytics
1. **Diseases**: Analyze disease occurrence, severity, costs (with filters & export)
2. **Hospitals**: Compare hospital performance metrics (sortable, filterable)
3. **Geographic**: View state and city-wise distribution with filter sync
4. **Temporal**: Analyze trends over time (monthly/quarterly) with export
5. **Specializations**: Review doctor specialization analytics and heatmap
6. **Predictions**: Train ML model and score new patient visits for cost risk

### Data Entry
- **Add Patient**: Register new patients with complete information
- **Add Visit**: Record new patient visits with all relevant details
- **Bulk Upload**: Upload CSV/Excel files, monitor ingestion jobs, and view errors

### Data Ingestion Workflow
1. Download the ingestion template from the **Bulk Upload** tab
2. Fill in patient, doctor, hospital and visit details
3. Upload the file—records are validated, staged, and inserted automatically
4. Review ingestion job status and error logs directly in the UI

### Machine Learning Workflow
1. Navigate to the **Predictions** analytics tab
2. Click **Train Model** to build/update the Random Forest classifier
3. Enter patient visit attributes and click **Predict Risk**
4. View probability scores and high/low risk classification instantly

## API Endpoints

### Analytics & Metadata
- `GET /api/metadata/options` - Get lists of states, diseases, specializations, hospitals
- `GET /api/analytics/diseases` - Disease analytics (supports filters & CSV export)
- `GET /api/analytics/hospitals` - Hospital analytics (filters, sorting, export)
- `GET /api/analytics/geographic` - Geographic analytics (filters, export)
- `GET /api/analytics/temporal` - Temporal analytics (filters, export)
- `GET /api/analytics/specializations` - Specialization analytics (filters, export)

### Ingestion
- `POST /api/ingestion/patient-visits` - Upload CSV/Excel for ETL
- `GET /api/ingestion/jobs` - List ingestion jobs
- `GET /api/ingestion/jobs/<job_id>/errors` - View failed records and reasons
- `GET /api/ingestion/template` - Download ingestion template CSV

### Machine Learning
- `POST /api/ml/train` - Train or re-train the cost risk prediction model
- `POST /api/ml/predict` - Predict cost risk for a patient visit payload

### Data Management
- `GET /api/patients` - Get patients (with optional filters, pagination, CSV export)
- `POST /api/patients` - Add new patient
- `GET /api/visits` - Get visits (supports filters, sorting, CSV export)
- `POST /api/visits` - Add new visit
- `GET /api/hospitals` - Get hospitals list
- `GET /api/doctors` - Get doctors list
- `GET /api/diseases` - Get diseases list

## Customization

### Adding More Data
You can add more data by:
1. Modifying `database/init_data.py` to increase counts
2. Running the script again (it will add more records)
3. Or manually inserting data through the web interface

### Modifying Database Configuration
Update the `DB_CONFIG` dictionary in:
- `app.py` (line ~15)
- `database/init_data.py` (line ~10)

### Changing Port
Edit `app.py` at the bottom:
```python
app.run(debug=True, host='0.0.0.0', port=5000)  # Change port here
```

## Troubleshooting

### Database Connection Error
- Verify MySQL is running: `mysql --version`
- Check credentials in `app.py` and `database/init_data.py`
- Ensure database exists or schema.sql has been executed

### Module Not Found Error
- Install dependencies: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.8+)

### Port Already in Use
- Change port in `app.py` or stop the process using port 5000

### Data Not Loading
- Ensure `init_data.py` completed successfully
- Check MySQL connection and permissions
- Verify tables exist: `SHOW TABLES;` in MySQL

## Features Highlights

✅ **End-to-End ETL**: Upload, validate, stage, and ingest healthcare visits
✅ **Smart Filters & Exports**: Apply filters once, and export any analytics view to CSV
✅ **Predictive Analytics**: Train and use a cost-risk model directly from the UI
✅ **Error Transparency**: View detailed ingestion failures with payload context
✅ **Responsive UX**: Filter panel, secondary actions, and rich UI feedback
✅ **Indian Dataset**: Realistic data suited for healthcare analytics in India

## Future Enhancements

- Real-time ETL job scheduling & notifications
- Model performance dashboard and versioning
- Advanced filter builder and saved filter sets
- Additional predictive models (readmission risk, length-of-stay)
- Role-based access control for ingestion and ML modules

## License

This project is created for educational and demonstration purposes.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify all prerequisites are installed
3. Ensure database is properly configured
4. Review error messages in the console

---

**Developed with ❤️ for Healthcare Analytics**

