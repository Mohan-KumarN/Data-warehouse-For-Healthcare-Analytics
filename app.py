"""
Healthcare Analytics Data Warehouse - Flask Application
Main backend API server
"""
from flask import Flask, render_template, jsonify, request, Response, send_file
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import json
import io
import os
import csv
from werkzeug.utils import secure_filename

from services.etl_service import (
    process_patient_visits_file,
    get_ingestion_jobs,
    DataValidationError,
)
from services.ml_service import train_cost_risk_model, predict_cost_risk
from services.auth_service import (
    authenticate_user,
    generate_token,
    verify_token,
    require_auth,
    require_role,
    has_permission,
    encrypt_pii,
    decrypt_pii
)
from services.rate_limiter import rate_limit

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Database configuration - can be overridden by environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),  # No password for local MySQL
    'database': os.getenv('DB_NAME', 'healthcare_analytics')
}

def get_db_connection():
    """Create and return database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def parse_date_param(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def build_visit_filters(args):
    filters = []
    params = []

    start_date = parse_date_param(args.get('start_date'))
    end_date = parse_date_param(args.get('end_date'))
    state = args.get('state')
    patient_state = args.get('patient_state')
    hospital_state = args.get('hospital_state')
    disease = args.get('disease')
    specialization = args.get('specialization')
    hospital_id = args.get('hospital_id')
    visit_type = args.get('visit_type')

    if start_date:
        filters.append("dd.full_date >= %s")
        params.append(start_date)
    if end_date:
        filters.append("dd.full_date <= %s")
        params.append(end_date)
    if state:
        filters.append("h.state = %s")
        params.append(state)
    if patient_state:
        filters.append("p.state = %s")
        params.append(patient_state)
    if hospital_state:
        filters.append("h.state = %s")
        params.append(hospital_state)
    if disease:
        filters.append("d.disease_name = %s")
        params.append(disease)
    if specialization:
        filters.append("doc.specialization = %s")
        params.append(specialization)
    if hospital_id:
        filters.append("h.hospital_id = %s")
        params.append(hospital_id)
    if visit_type:
        filters.append("pv.visit_type = %s")
        params.append(visit_type)

    return filters, params


def export_csv_response(filename, headers, rows):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)

    csv_data = output.getvalue()
    output.close()
    response = Response(csv_data, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@app.route('/api/dashboard/stats', methods=['GET'])
@require_auth
@rate_limit
def get_dashboard_stats():
    """Get overall dashboard statistics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    stats = {}
    
    # Total patients
    cursor.execute("SELECT COUNT(*) as count FROM patients")
    stats['total_patients'] = cursor.fetchone()['count']
    
    # Total hospitals
    cursor.execute("SELECT COUNT(*) as count FROM hospitals")
    stats['total_hospitals'] = cursor.fetchone()['count']
    
    # Total doctors
    cursor.execute("SELECT COUNT(*) as count FROM doctors")
    stats['total_doctors'] = cursor.fetchone()['count']
    
    # Total visits
    cursor.execute("SELECT COUNT(*) as count FROM patient_visits")
    stats['total_visits'] = cursor.fetchone()['count']
    
    # Total revenue
    cursor.execute("SELECT SUM(total_cost) as revenue FROM patient_visits")
    result = cursor.fetchone()
    stats['total_revenue'] = float(result['revenue']) if result['revenue'] else 0
    
    # Average visit cost
    cursor.execute("SELECT AVG(total_cost) as avg_cost FROM patient_visits")
    result = cursor.fetchone()
    stats['avg_visit_cost'] = float(result['avg_cost']) if result['avg_cost'] else 0
    
    # Visits by type
    cursor.execute("""
        SELECT visit_type, COUNT(*) as count 
        FROM patient_visits 
        GROUP BY visit_type
    """)
    stats['visits_by_type'] = {row['visit_type']: row['count'] for row in cursor.fetchall()}
    
    # Revenue by payment method
    cursor.execute("""
        SELECT payment_method, SUM(total_cost) as revenue 
        FROM patient_visits 
        GROUP BY payment_method
    """)
    stats['revenue_by_payment'] = {row['payment_method']: float(row['revenue']) for row in cursor.fetchall()}
    
    cursor.close()
    conn.close()
    
    return jsonify(stats)

@app.route('/')
def index():
    """Main application route - check authentication"""
    token = request.cookies.get('auth_token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return render_template('login.html')
    
    payload = verify_token(token)
    if not payload:
        return render_template('login.html')
    
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')

@app.route('/api/auth/login', methods=['POST'])
@rate_limit
def login():
    """User login endpoint"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = authenticate_user(username, password)
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401
    
    token = generate_token(user['user_id'], user['username'], user['role'])
    
    response = jsonify({
        'token': token,
        'user': {
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'full_name': user['full_name']
        }
    })
    
    # Set cookie
    response.set_cookie('auth_token', token, max_age=86400, httponly=True, samesite='Lax')
    return response

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """User logout endpoint"""
    response = jsonify({'message': 'Logged out successfully'})
    response.set_cookie('auth_token', '', expires=0)
    return response

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user information"""
    user_id = request.current_user['user_id']
    from services.auth_service import get_user_by_id
    user = get_user_by_id(user_id)
    if user:
        return jsonify({
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'full_name': user['full_name']
        })
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/download/full_patient_visits')
def download_full_patient_visits():
    """Download the full patient visits excel file"""
    try:
        return send_file(
            'full_patient_visits.xlsx',
            as_attachment=True,
            download_name='full_patient_visits.xlsx'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/analytics/diseases', methods=['GET'])
def get_disease_analytics():
    """Get disease analytics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    filters, params = build_visit_filters(request.args)
    
    # Check if filtering by category
    category_filter = request.args.get('category', '')
    
    # Build WHERE clauses
    where_clauses = []
    all_params = []
    
    # Category filter
    if category_filter:
        where_clauses.append("d.disease_category = %s")
        all_params.append(category_filter)
    
    # Visit filters
    if filters:
        where_clauses.extend(filters)
        if params:
            all_params.extend(params)
    
    # Build WHERE clause string
    where_sql = ""
    if where_clauses:
        where_sql = " WHERE " + " AND ".join(where_clauses)
    
    # Limit: if filtering by Oncology, show only top 3, otherwise show 50
    if category_filter == 'Oncology':
        limit = 3
    else:
        limit = request.args.get('limit', 50, type=int)
    
    # Build HAVING clause to filter out diseases with 0 occurrences
    having_clause = "HAVING occurrence_count > 0"
    if not category_filter:
        # For all diseases view, exclude Oncology diseases with 0 occurrences
        # This is handled in HAVING clause
        pass
    
    query = f"""
        SELECT d.disease_name, d.disease_category, d.severity_level,
               COUNT(pv.visit_id) as occurrence_count,
               COALESCE(AVG(pv.total_cost), 0) as avg_cost
        FROM diseases d
        LEFT JOIN patient_visits pv ON d.disease_id = pv.disease_id
        LEFT JOIN patients p ON pv.patient_id = p.patient_id
        LEFT JOIN doctors doc ON pv.doctor_id = doc.doctor_id
        LEFT JOIN hospitals h ON pv.hospital_id = h.hospital_id
        LEFT JOIN date_dimension dd ON pv.visit_date_id = dd.date_id
        {where_sql}
        GROUP BY d.disease_id, d.disease_name, d.disease_category, d.severity_level
        {having_clause}
        ORDER BY occurrence_count DESC, d.disease_name ASC
        LIMIT %s
    """

    cursor.execute(query, all_params + [limit] if all_params else [limit])
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    diseases = [{
        'name': row['disease_name'],
        'category': row['disease_category'],
        'severity': row['severity_level'],
        'occurrence': row['occurrence_count'],
        'avg_cost': float(row['avg_cost']) if row['avg_cost'] else 0
    } for row in rows]

    if request.args.get('format') == 'csv':
        headers = ['Disease Name', 'Category', 'Severity', 'Occurrences', 'Average Cost']
        csv_rows = [[
            row['disease_name'],
            row['disease_category'],
            row['severity_level'],
            row['occurrence_count'],
            row['avg_cost'] or 0
        ] for row in rows]
        return export_csv_response('disease_analytics.csv', headers, csv_rows)

    return jsonify(diseases)

@app.route('/api/analytics/hospitals', methods=['GET'])
@require_auth
@rate_limit
def get_hospital_analytics():
    """Get hospital analytics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    filters, params = build_visit_filters(request.args)
    where_clauses = ["pv.visit_id IS NOT NULL"]
    if filters:
        where_clauses.extend(filters)
    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    sort_map = {
        'revenue': 'total_revenue',
        'visits': 'visit_count',
        'patients': 'patient_count',
        'avg_cost': 'avg_visit_cost',
    }
    sort_by = request.args.get('sort', 'revenue')
    order_column = sort_map.get(sort_by, 'total_revenue')
    limit = request.args.get('limit', 20, type=int)

    query = f"""
        SELECT h.hospital_id, h.hospital_name, h.hospital_type, h.city, h.state,
               COUNT(DISTINCT pv.patient_id) as patient_count,
               COUNT(pv.visit_id) as visit_count,
               SUM(pv.total_cost) as total_revenue,
               AVG(pv.total_cost) as avg_visit_cost
        FROM hospitals h
        LEFT JOIN patient_visits pv ON h.hospital_id = pv.hospital_id
        LEFT JOIN patients p ON pv.patient_id = p.patient_id
        LEFT JOIN doctors doc ON pv.doctor_id = doc.doctor_id
        LEFT JOIN diseases d ON pv.disease_id = d.disease_id
        LEFT JOIN date_dimension dd ON pv.visit_date_id = dd.date_id
        {where_sql}
        GROUP BY h.hospital_id, h.hospital_name, h.hospital_type, h.city, h.state
        ORDER BY {order_column} DESC
        LIMIT %s
    """

    cursor.execute(query, params + [limit] if params else [limit])
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    hospitals = [{
        'hospital_id': row['hospital_id'],
        'name': row['hospital_name'],
        'type': row['hospital_type'],
        'city': row['city'],
        'state': row['state'],
        'patient_count': row['patient_count'],
        'visit_count': row['visit_count'],
        'total_revenue': float(row['total_revenue']) if row['total_revenue'] else 0,
        'avg_visit_cost': float(row['avg_visit_cost']) if row['avg_visit_cost'] else 0
    } for row in rows]

    if request.args.get('format') == 'csv':
        headers = ['Hospital ID', 'Hospital Name', 'Type', 'City', 'State', 'Patients', 'Visits', 'Total Revenue', 'Average Visit Cost']
        csv_rows = [[
            row['hospital_id'],
            row['hospital_name'],
            row['hospital_type'],
            row['city'],
            row['state'],
            row['patient_count'],
            row['visit_count'],
            row['total_revenue'] or 0,
            row['avg_visit_cost'] or 0
        ] for row in rows]
        return export_csv_response('hospital_analytics.csv', headers, csv_rows)

    return jsonify(hospitals)

@app.route('/api/analytics/geographic', methods=['GET'])
@require_auth
@rate_limit
def get_geographic_analytics():
    """Get geographic analytics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    filters, params = build_visit_filters(request.args)
    where_clauses = ["pv.visit_id IS NOT NULL"]
    if filters:
        where_clauses.extend(filters)
    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # State-wise statistics
    state_query = f"""
        SELECT p.state,
               COUNT(DISTINCT p.patient_id) as patient_count,
               COUNT(pv.visit_id) as visit_count,
               SUM(pv.total_cost) as total_revenue
        FROM patients p
        LEFT JOIN patient_visits pv ON p.patient_id = pv.patient_id
        LEFT JOIN hospitals h ON pv.hospital_id = h.hospital_id
        LEFT JOIN doctors doc ON pv.doctor_id = doc.doctor_id
        LEFT JOIN diseases d ON pv.disease_id = d.disease_id
        LEFT JOIN date_dimension dd ON pv.visit_date_id = dd.date_id
        {where_sql}
        GROUP BY p.state
        ORDER BY visit_count DESC
    """

    cursor.execute(state_query, params)
    state_rows = cursor.fetchall()

    # City-wise statistics
    city_query = f"""
        SELECT p.city, p.state,
               COUNT(DISTINCT p.patient_id) as patient_count,
               COUNT(pv.visit_id) as visit_count,
               SUM(pv.total_cost) as total_revenue
        FROM patients p
        LEFT JOIN patient_visits pv ON p.patient_id = pv.patient_id
        LEFT JOIN hospitals h ON pv.hospital_id = h.hospital_id
        LEFT JOIN doctors doc ON pv.doctor_id = doc.doctor_id
        LEFT JOIN diseases d ON pv.disease_id = d.disease_id
        LEFT JOIN date_dimension dd ON pv.visit_date_id = dd.date_id
        {where_sql}
        GROUP BY p.city, p.state
        ORDER BY visit_count DESC
        LIMIT %s
    """

    limit = request.args.get('limit', 20, type=int)
    cursor.execute(city_query, (params + [limit]) if params else [limit])
    city_rows = cursor.fetchall()
    cursor.close()
    conn.close()

    state_stats = [{
        'state': row['state'],
        'patient_count': row['patient_count'],
        'visit_count': row['visit_count'],
        'total_revenue': float(row['total_revenue']) if row['total_revenue'] else 0
    } for row in state_rows]

    city_stats = [{
        'city': row['city'],
        'state': row['state'],
        'patient_count': row['patient_count'],
        'visit_count': row['visit_count'],
        'total_revenue': float(row['total_revenue']) if row['total_revenue'] else 0
    } for row in city_rows]

    if request.args.get('format') == 'csv':
        level = request.args.get('level', 'state')
        if level == 'city':
            headers = ['City', 'State', 'Unique Patients', 'Visits', 'Total Revenue']
            csv_rows = [[
                row['city'],
                row['state'],
                row['patient_count'],
                row['visit_count'],
                row['total_revenue'] or 0
            ] for row in city_rows]
            return export_csv_response('geographic_city_analytics.csv', headers, csv_rows)
        else:
            headers = ['State', 'Unique Patients', 'Visits', 'Total Revenue']
            csv_rows = [[
                row['state'],
                row['patient_count'],
                row['visit_count'],
                row['total_revenue'] or 0
            ] for row in state_rows]
            return export_csv_response('geographic_state_analytics.csv', headers, csv_rows)

    return jsonify({
        'states': state_stats,
        'cities': city_stats
    })

@app.route('/api/analytics/temporal', methods=['GET'])
@require_auth
@rate_limit
def get_temporal_analytics():
    """Get temporal analytics (time-based)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    filters, params = build_visit_filters(request.args)
    where_clauses = ["pv.visit_id IS NOT NULL"]
    if filters:
        where_clauses.extend(filters)
    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Monthly trends
    monthly_query = f"""
        SELECT dd.year, dd.month, dd.month_name,
               COUNT(pv.visit_id) as visit_count,
               SUM(pv.total_cost) as revenue
        FROM date_dimension dd
        LEFT JOIN patient_visits pv ON dd.date_id = pv.visit_date_id
        LEFT JOIN patients p ON pv.patient_id = p.patient_id
        LEFT JOIN hospitals h ON pv.hospital_id = h.hospital_id
        LEFT JOIN doctors doc ON pv.doctor_id = doc.doctor_id
        LEFT JOIN diseases d ON pv.disease_id = d.disease_id
        {where_sql}
        GROUP BY dd.year, dd.month, dd.month_name
        ORDER BY dd.year, dd.month
    """

    cursor.execute(monthly_query, params)
    monthly_rows = cursor.fetchall()

    # Quarterly trends
    quarterly_query = f"""
        SELECT dd.year, dd.quarter,
               COUNT(pv.visit_id) as visit_count,
               SUM(pv.total_cost) as revenue
        FROM date_dimension dd
        LEFT JOIN patient_visits pv ON dd.date_id = pv.visit_date_id
        LEFT JOIN patients p ON pv.patient_id = p.patient_id
        LEFT JOIN hospitals h ON pv.hospital_id = h.hospital_id
        LEFT JOIN doctors doc ON pv.doctor_id = doc.doctor_id
        LEFT JOIN diseases d ON pv.disease_id = d.disease_id
        {where_sql}
        GROUP BY dd.year, dd.quarter
        ORDER BY dd.year, dd.quarter
    """

    cursor.execute(quarterly_query, params)
    quarterly_rows = cursor.fetchall()
    cursor.close()
    conn.close()

    monthly_data = [{
        'year': row['year'],
        'month': row['month'],
        'month_name': row['month_name'],
        'visit_count': row['visit_count'],
        'revenue': float(row['revenue']) if row['revenue'] else 0
    } for row in monthly_rows]

    quarterly_data = [{
        'year': row['year'],
        'quarter': row['quarter'],
        'visit_count': row['visit_count'],
        'revenue': float(row['revenue']) if row['revenue'] else 0
    } for row in quarterly_rows]

    if request.args.get('format') == 'csv':
        interval = request.args.get('interval', 'monthly')
        if interval == 'quarterly':
            headers = ['Year', 'Quarter', 'Visits', 'Revenue']
            csv_rows = [[
                row['year'],
                row['quarter'],
                row['visit_count'],
                row['revenue'] or 0
            ] for row in quarterly_rows]
            return export_csv_response('temporal_quarterly_analytics.csv', headers, csv_rows)
        else:
            headers = ['Year', 'Month', 'Month Name', 'Visits', 'Revenue']
            csv_rows = [[
                row['year'],
                row['month'],
                row['month_name'],
                row['visit_count'],
                row['revenue'] or 0
            ] for row in monthly_rows]
            return export_csv_response('temporal_monthly_analytics.csv', headers, csv_rows)

    return jsonify({
        'monthly': monthly_data,
        'quarterly': quarterly_data
    })

@app.route('/api/analytics/specializations', methods=['GET'])
@require_auth
@rate_limit
def get_specialization_analytics():
    """Get specialization analytics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    filters, params = build_visit_filters(request.args)
    where_clauses = ["pv.visit_id IS NOT NULL"]
    if filters:
        where_clauses.extend(filters)
    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    query = f"""
        SELECT doc.specialization,
               COUNT(DISTINCT doc.doctor_id) as doctor_count,
               COUNT(pv.visit_id) as visit_count,
               AVG(pv.total_cost) as avg_cost,
               SUM(pv.total_cost) as total_revenue
        FROM doctors doc
        LEFT JOIN patient_visits pv ON doc.doctor_id = pv.doctor_id
        LEFT JOIN patients p ON pv.patient_id = p.patient_id
        LEFT JOIN hospitals h ON pv.hospital_id = h.hospital_id
        LEFT JOIN diseases d ON pv.disease_id = d.disease_id
        LEFT JOIN date_dimension dd ON pv.visit_date_id = dd.date_id
        {where_sql}
        GROUP BY doc.specialization
        ORDER BY visit_count DESC
    """

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    specializations = [{
        'specialization': row['specialization'],
        'doctor_count': row['doctor_count'],
        'visit_count': row['visit_count'],
        'avg_cost': float(row['avg_cost']) if row['avg_cost'] else 0,
        'total_revenue': float(row['total_revenue']) if row['total_revenue'] else 0
    } for row in rows]

    if request.args.get('format') == 'csv':
        headers = ['Specialization', 'Doctor Count', 'Visit Count', 'Average Cost', 'Total Revenue']
        csv_rows = [[
            row['specialization'],
            row['doctor_count'],
            row['visit_count'],
            row['avg_cost'] or 0,
            row['total_revenue'] or 0
        ] for row in rows]
        return export_csv_response('specialization_analytics.csv', headers, csv_rows)

    return jsonify(specializations)


@app.route('/api/metadata/options', methods=['GET'])
def get_metadata_options():
    """Return metadata options for filters"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT DISTINCT state FROM patients WHERE state IS NOT NULL ORDER BY state")
    patient_states = [row['state'] for row in cursor.fetchall() if row['state']]

    cursor.execute("SELECT DISTINCT state FROM hospitals WHERE state IS NOT NULL ORDER BY state")
    hospital_states = [row['state'] for row in cursor.fetchall() if row['state']]

    cursor.execute("SELECT disease_name FROM diseases ORDER BY disease_name")
    diseases = [row['disease_name'] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT specialization FROM doctors ORDER BY specialization")
    specializations = [row['specialization'] for row in cursor.fetchall()]

    cursor.execute("SELECT hospital_id, hospital_name, city, state FROM hospitals ORDER BY hospital_name")
    hospitals = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        'patient_states': patient_states,
        'hospital_states': hospital_states,
        'diseases': diseases,
        'specializations': specializations,
        'hospitals': hospitals,
    })


@app.route('/api/patients', methods=['GET'])
@require_auth
@rate_limit
def get_patients():
    """Get patients list with pagination"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    offset = (page - 1) * per_page
    state = request.args.get('state')
    city = request.args.get('city')
    search = request.args.get('search')

    filters = []
    params = []

    if state:
        filters.append("state = %s")
        params.append(state)
    if city:
        filters.append("city = %s")
        params.append(city)
    if search:
        filters.append("patient_name LIKE %s")
        params.append(f"%{search}%")
    
    # Get total count
    count_query = "SELECT COUNT(*) as total FROM patients"
    if filters:
        count_query += " WHERE " + " AND ".join(filters)
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    
    # Get patients
    select_query = """
        SELECT patient_id, patient_name, age, gender, city, state, phone, email
        FROM patients
    """
    if filters:
        select_query += " WHERE " + " AND ".join(filters)
    select_query += " ORDER BY patient_id DESC"

    if request.args.get('format') == 'csv':
        csv_limit = request.args.get('limit', 1000, type=int)
        cursor.execute(select_query + " LIMIT %s", params + [csv_limit] if params else [csv_limit])
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        headers = ['Patient ID', 'Patient Name', 'Age', 'Gender', 'City', 'State', 'Phone', 'Email']
        csv_rows = [[
            row['patient_id'],
            row['patient_name'],
            row['age'],
            row['gender'],
            row['city'],
            row['state'],
            row['phone'],
            row['email']
        ] for row in rows]
        return export_csv_response('patients.csv', headers, csv_rows)

    select_query += " LIMIT %s OFFSET %s"
    query_params = params + [per_page, offset]
    cursor.execute(select_query, query_params)
    patients = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'patients': patients,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })

@app.route('/api/patients', methods=['POST'])
@require_auth
@require_role('admin', 'analyst')
@rate_limit
def add_patient():
    """Add new patient"""
    data = request.json
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO patients 
            (patient_name, age, gender, phone, email, address, city, state, pincode)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('patient_name'),
            data.get('age'),
            data.get('gender'),
            data.get('phone'),
            data.get('email'),
            data.get('address'),
            data.get('city'),
            data.get('state'),
            data.get('pincode')
        ))
        
        conn.commit()
        patient_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'patient_id': patient_id}), 201
    except Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'error': str(e)}), 400

@app.route('/api/visits/export', methods=['GET'])
@require_auth
@rate_limit
def export_visits():
    """Export visits as CSV - supports all=true parameter to ignore filters"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    # Check if all data requested
    export_all = request.args.get('all', 'false').lower() == 'true'
    
    if export_all:
        # Export all data without filters
        query = """
            SELECT 
                pv.visit_id,
                p.patient_name,
                p.age,
                p.gender,
                p.city,
                p.state,
                d.doctor_name,
                d.specialization,
                h.hospital_name,
                h.hospital_type,
                h.state as hospital_state,
                pv.visit_type,
                dd.full_date as visit_date,
                pv.total_cost,
                pv.payment_method,
                dis.disease_name as diagnosis
            FROM patient_visits pv
            JOIN patients p ON pv.patient_id = p.patient_id
            JOIN doctors d ON pv.doctor_id = d.doctor_id
            JOIN hospitals h ON pv.hospital_id = h.hospital_id
            JOIN date_dimension dd ON pv.visit_date_id = dd.date_id
            LEFT JOIN diseases dis ON pv.disease_id = dis.disease_id
            ORDER BY pv.visit_id
        """
        cursor.execute(query)
    else:
        # Use existing filter logic
        filters, params = build_visit_filters(request.args)
        query = f"""
            SELECT 
                pv.visit_id,
                p.patient_name,
                p.age,
                p.gender,
                p.city,
                p.state,
                d.doctor_name,
                d.specialization,
                h.hospital_name,
                h.hospital_type,
                h.state as hospital_state,
                pv.visit_type,
                dd.full_date as visit_date,
                pv.total_cost,
                pv.payment_method,
                dis.disease_name as diagnosis
            FROM patient_visits pv
            JOIN patients p ON pv.patient_id = p.patient_id
            JOIN doctors d ON pv.doctor_id = d.doctor_id
            JOIN hospitals h ON pv.hospital_id = h.hospital_id
            JOIN date_dimension dd ON pv.visit_date_id = dd.date_id
            LEFT JOIN diseases dis ON pv.disease_id = dis.disease_id
            {'WHERE ' + ' AND '.join(filters) if filters else ''}
            ORDER BY pv.visit_id
        """
        cursor.execute(query, params)
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Generate CSV
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    
    response = Response(output.getvalue(), mimetype='text/csv')
    filename = 'all_patient_visits.csv' if export_all else 'patient_visits.csv'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@app.route('/api/visits', methods=['GET'])
@require_auth
@rate_limit
def get_visits():
    """Get patient visits with pagination"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    offset = (page - 1) * per_page
    order_direction = request.args.get('order', 'desc').lower()
    order_direction = 'ASC' if order_direction == 'asc' else 'DESC'

    filters, params = build_visit_filters(request.args)
    base_from = """
        FROM patient_visits pv
        LEFT JOIN patients p ON pv.patient_id = p.patient_id
        LEFT JOIN doctors doc ON pv.doctor_id = doc.doctor_id
        LEFT JOIN hospitals h ON pv.hospital_id = h.hospital_id
        LEFT JOIN diseases d ON pv.disease_id = d.disease_id
        LEFT JOIN date_dimension dd ON pv.visit_date_id = dd.date_id
    """

    where_clauses = []
    if filters:
        where_clauses.extend(filters)
    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    count_query = "SELECT COUNT(*) as total " + base_from + where_sql
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']

    select_query = """
        SELECT pv.visit_id, p.patient_name, doc.doctor_name, h.hospital_name,
               d.disease_name, pv.visit_type, pv.total_cost, pv.payment_method,
               dd.full_date as visit_date, pv.status,
               doc.specialization, h.state AS hospital_state
    """ + base_from + where_sql

    if request.args.get('format') == 'csv':
        csv_limit = request.args.get('limit', 5000, type=int)
        cursor.execute(
            select_query + f" ORDER BY dd.full_date {order_direction}, pv.visit_id {order_direction} LIMIT %s",
            params + [csv_limit] if params else [csv_limit]
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        headers = ['Visit ID', 'Patient', 'Doctor', 'Hospital', 'Disease', 'Visit Type', 'Visit Date', 'Total Cost', 'Payment Method', 'Status', 'Specialization', 'Hospital State']
        csv_rows = [[
            row['visit_id'],
            row['patient_name'],
            row['doctor_name'],
            row['hospital_name'],
            row['disease_name'],
            row['visit_type'],
            row['visit_date'].strftime('%Y-%m-%d') if row['visit_date'] else '',
            row['total_cost'],
            row['payment_method'],
            row['status'],
            row['specialization'],
            row['hospital_state']
        ] for row in rows]
        return export_csv_response('patient_visits.csv', headers, csv_rows)

    select_query += f" ORDER BY dd.full_date {order_direction}, pv.visit_id {order_direction} LIMIT %s OFFSET %s"
    query_params = params + [per_page, offset]
    cursor.execute(select_query, query_params)
    visits = cursor.fetchall()
    
    for visit in visits:
        if visit['visit_date']:
            visit['visit_date'] = visit['visit_date'].strftime('%Y-%m-%d')
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'visits': visits,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })

@app.route('/api/visits', methods=['POST'])
@require_auth
@require_role('admin', 'analyst', 'doctor')
@rate_limit
def add_visit():
    """Add new patient visit"""
    data = request.json
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    try:
        # Get date_id for the visit date
        visit_date = datetime.strptime(data.get('visit_date'), '%Y-%m-%d').date()
        cursor.execute("SELECT date_id FROM date_dimension WHERE full_date = %s", (visit_date,))
        date_result = cursor.fetchone()
        
        if not date_result:
            # Create date entry if not exists
            date_id = int(visit_date.strftime('%Y%m%d'))
            cursor.execute("""
                INSERT INTO date_dimension 
                (date_id, full_date, day, month, year, quarter, month_name, day_name, is_weekend)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                date_id, visit_date, visit_date.day, visit_date.month, visit_date.year,
                (visit_date.month - 1) // 3 + 1, visit_date.strftime('%B'),
                visit_date.strftime('%A'), visit_date.weekday() >= 5
            ))
        else:
            date_id = date_result[0]
        
        cursor.execute("""
            INSERT INTO patient_visits 
            (patient_id, doctor_id, hospital_id, disease_id, visit_date_id, visit_type,
             diagnosis, treatment_id, medication_id, medication_quantity, total_cost,
             payment_method, visit_duration_minutes, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('patient_id'),
            data.get('doctor_id'),
            data.get('hospital_id'),
            data.get('disease_id'),
            date_id,
            data.get('visit_type'),
            data.get('diagnosis'),
            data.get('treatment_id'),
            data.get('medication_id'),
            data.get('medication_quantity'),
            data.get('total_cost'),
            data.get('payment_method'),
            data.get('visit_duration_minutes'),
            data.get('status', 'Completed')
        ))
        
        conn.commit()
        visit_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'visit_id': visit_id}), 201
    except Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'error': str(e)}), 400

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    """Get hospitals list"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT hospital_id, hospital_name, hospital_type, city, state, beds_count
        FROM hospitals
        ORDER BY hospital_name
    """)
    
    hospitals = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify(hospitals)

@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    """Get doctors list"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT doctor_id, doctor_name, specialization, hospital_id, consultation_fee
        FROM doctors
        ORDER BY doctor_name
    """)
    
    doctors = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify(doctors)

@app.route('/api/diseases', methods=['GET'])
def get_diseases():
    """Get diseases list"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT disease_id, disease_name, disease_category, severity_level
        FROM diseases
        ORDER BY disease_name
    """)
    
    diseases = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify(diseases)

@app.route('/api/ingestion/patient-visits', methods=['POST'])
@require_auth
@require_role('admin', 'analyst')
@rate_limit
def ingest_patient_visits():
    """Upload patient visit data for ETL processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    upload = request.files['file']
    if upload.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(upload.filename)
    file_bytes = upload.read()
    if not file_bytes:
        return jsonify({'error': 'Uploaded file is empty'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        result = process_patient_visits_file(conn, file_bytes, filename)
        return jsonify({'message': 'File processed successfully', 'job_summary': result})
    except DataValidationError as exc:
        conn.rollback()
        return jsonify({'error': str(exc)}), 400
    except Error as exc:
        conn.rollback()
        return jsonify({'error': f'Database error: {exc}'}), 500
    finally:
        conn.close()

@app.route('/api/ingestion/jobs', methods=['GET'])
def list_ingestion_jobs():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    limit = request.args.get('limit', 20, type=int)
    jobs = get_ingestion_jobs(conn, limit=limit)
    conn.close()
    return jsonify(jobs)

@app.route('/api/ingestion/jobs/<int:job_id>/errors', methods=['GET'])
def list_ingestion_errors(job_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT staging_id, raw_payload, status, error_message, processed_at
        FROM staging_patient_visits
        WHERE status = 'FAILED' AND source_file IN (
            SELECT source_file FROM ingestion_jobs WHERE job_id = %s
        )
        ORDER BY processed_at DESC
        LIMIT 200
        """,
        (job_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    for row in rows:
        try:
            row['raw_payload'] = json.loads(row['raw_payload'])
        except (TypeError, json.JSONDecodeError):
            pass

    return jsonify(rows)

@app.route('/api/ingestion/template', methods=['GET'])
def download_ingestion_template():
    """Download CSV template file"""
    template_path = os.path.join('data', 'patient_visit_template.csv')
    
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            csv_data = f.read()
        response = Response(csv_data, mimetype='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=patient_visit_template.csv'
        return response
    else:
        # Fallback to generating template
        headers = [
            'patient_name', 'age', 'gender', 'phone', 'email', 'address', 'city', 'state', 'pincode',
            'doctor_name', 'specialization', 'hospital_name', 'hospital_type', 'hospital_state',
            'visit_type', 'visit_date', 'total_cost', 'payment_method', 'diagnosis'
        ]
        rows = [[
            'Rajesh Sharma', '45', 'Male', '+91-9876543210', 'rajesh.sharma@email.com', '123 MG Road Andheri',
            'Mumbai', 'Maharashtra', '400053', 'Dr. Priya Nair', 'Cardiology', 'Apollo Hospitals Mumbai',
            'Private', 'Maharashtra', 'OPD', '2024-05-15', '2500', 'UPI', 'Routine heart checkup'
        ]]
        return export_csv_response('patient_visit_template.csv', headers, rows)

@app.route('/api/ingestion/sample1', methods=['GET'])
def download_sample1():
    """Download sample CSV file 1"""
    sample_path = os.path.join('data', 'sample_patient_visits_1.csv')
    
    if os.path.exists(sample_path):
        with open(sample_path, 'r', encoding='utf-8') as f:
            csv_data = f.read()
        response = Response(csv_data, mimetype='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=sample_patient_visits_1.csv'
        return response
    else:
        return jsonify({'error': 'Sample file not found'}), 404

@app.route('/api/ingestion/sample2', methods=['GET'])
def download_sample2():
    """Download sample CSV file 2"""
    sample_path = os.path.join('data', 'sample_patient_visits_2.csv')
    
    if os.path.exists(sample_path):
        with open(sample_path, 'r', encoding='utf-8') as f:
            csv_data = f.read()
        response = Response(csv_data, mimetype='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=sample_patient_visits_2.csv'
        return response
    else:
        return jsonify({'error': 'Sample file not found'}), 404

@app.route('/api/ml/train', methods=['POST'])
@require_auth
@require_role('admin', 'analyst')
@rate_limit
def ml_train():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        result = train_cost_risk_model(conn)
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    finally:
        conn.close()

@app.route('/api/ml/predict', methods=['POST'])
@require_auth
@require_role('admin', 'analyst', 'doctor')
@rate_limit
def ml_predict():
    payload = request.json or {}
    try:
        prediction = predict_cost_risk(payload)
        return jsonify(prediction)
    except FileNotFoundError:
        return jsonify({'error': 'Model not trained yet. Train the model first.'}), 400
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)

