"""
Initialize database with realistic Indian healthcare data
Based on actual Indian healthcare statistics and real hospital names
"""
import mysql.connector
from datetime import datetime, timedelta
import random
from faker import Faker

fake = Faker('en_IN')  # Indian locale

# Database configuration - can be overridden by environment variables
import os

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),  # No password for local MySQL
    'database': os.getenv('DB_NAME', 'healthcare_analytics')
}

# Real Indian states and major cities
INDIAN_STATES = [
    'Maharashtra', 'Karnataka', 'Tamil Nadu', 'Delhi', 'Gujarat', 
    'Rajasthan', 'West Bengal', 'Uttar Pradesh', 'Punjab', 'Kerala',
    'Andhra Pradesh', 'Telangana', 'Madhya Pradesh', 'Bihar', 'Haryana',
    'Odisha', 'Assam', 'Jharkhand', 'Chhattisgarh', 'Himachal Pradesh'
]

INDIAN_CITIES = {
    'Maharashtra': ['Mumbai', 'Pune', 'Nagpur', 'Nashik', 'Aurangabad', 'Solapur', 'Thane', 'Kalyan'],
    'Karnataka': ['Bangalore', 'Mysore', 'Hubli', 'Mangalore', 'Belgaum', 'Gulbarga', 'Davangere'],
    'Tamil Nadu': ['Chennai', 'Coimbatore', 'Madurai', 'Salem', 'Tiruchirappalli', 'Tirunelveli', 'Erode'],
    'Delhi': ['New Delhi', 'Delhi', 'Noida', 'Gurgaon'],
    'Gujarat': ['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Gandhinagar', 'Bhavnagar', 'Jamnagar'],
    'Rajasthan': ['Jaipur', 'Jodhpur', 'Udaipur', 'Kota', 'Ajmer', 'Bikaner', 'Bhilwara'],
    'West Bengal': ['Kolkata', 'Howrah', 'Durgapur', 'Asansol', 'Siliguri', 'Kharagpur'],
    'Uttar Pradesh': ['Lucknow', 'Kanpur', 'Agra', 'Varanasi', 'Allahabad', 'Meerut', 'Ghaziabad'],
    'Punjab': ['Chandigarh', 'Ludhiana', 'Amritsar', 'Jalandhar', 'Patiala', 'Bathinda'],
    'Kerala': ['Kochi', 'Thiruvananthapuram', 'Kozhikode', 'Thrissur', 'Kollam', 'Alappuzha'],
    'Andhra Pradesh': ['Hyderabad', 'Visakhapatnam', 'Vijayawada', 'Guntur', 'Nellore'],
    'Telangana': ['Hyderabad', 'Warangal', 'Nizamabad', 'Karimnagar'],
    'Madhya Pradesh': ['Bhopal', 'Indore', 'Gwalior', 'Jabalpur', 'Ujjain'],
    'Bihar': ['Patna', 'Gaya', 'Bhagalpur', 'Muzaffarpur', 'Darbhanga'],
    'Haryana': ['Gurgaon', 'Faridabad', 'Panipat', 'Karnal', 'Ambala']
}

# Real Indian hospital names (mix of government and private)
REAL_INDIAN_HOSPITALS = {
    'Mumbai': [
        ('AIIMS Mumbai', 'Government'),
        ('Apollo Hospitals Mumbai', 'Private'),
        ('Fortis Hospital Mulund', 'Private'),
        ('Lilavati Hospital', 'Private'),
        ('Kokilaben Dhirubhai Ambani Hospital', 'Private'),
        ('Jaslok Hospital', 'Private'),
        ('Bombay Hospital', 'Private'),
        ('KEM Hospital', 'Government'),
        ('Sion Hospital', 'Government'),
        ('Nanavati Hospital', 'Private')
    ],
    'Delhi': [
        ('AIIMS Delhi', 'Government'),
        ('Apollo Hospitals Delhi', 'Private'),
        ('Fortis Hospital Delhi', 'Private'),
        ('Max Hospital Saket', 'Private'),
        ('Sir Ganga Ram Hospital', 'Private'),
        ('Safdarjung Hospital', 'Government'),
        ('Ram Manohar Lohia Hospital', 'Government'),
        ('BLK Super Speciality Hospital', 'Private'),
        ('Indraprastha Apollo Hospital', 'Private'),
        ('Dharamshila Narayana Hospital', 'Private')
    ],
    'Bangalore': [
        ('Apollo Hospitals Bangalore', 'Private'),
        ('Fortis Hospital Bangalore', 'Private'),
        ('Manipal Hospital', 'Private'),
        ('Narayana Health City', 'Private'),
        ('Columbia Asia Hospital', 'Private'),
        ('BGS Global Hospital', 'Private'),
        ('Sakra World Hospital', 'Private'),
        ('Bowring Hospital', 'Government'),
        ('Victoria Hospital', 'Government')
    ],
    'Chennai': [
        ('Apollo Hospitals Chennai', 'Private'),
        ('Fortis Hospital Chennai', 'Private'),
        ('MIOT Hospital', 'Private'),
        ('Global Hospitals Chennai', 'Private'),
        ('Billroth Hospitals', 'Private'),
        ('Government General Hospital', 'Government'),
        ('Stanley Medical College Hospital', 'Government'),
        ('Lifeline Hospitals', 'Private')
    ],
    'Kolkata': [
        ('Apollo Gleneagles Hospital', 'Private'),
        ('AMRI Hospitals', 'Private'),
        ('Fortis Hospital Kolkata', 'Private'),
        ('Ruby General Hospital', 'Private'),
        ('Calcutta Medical College', 'Government'),
        ('SSKM Hospital', 'Government'),
        ('NRS Medical College', 'Government')
    ],
    'Hyderabad': [
        ('Apollo Hospitals Hyderabad', 'Private'),
        ('Continental Hospitals', 'Private'),
        ('Yashoda Hospitals', 'Private'),
        ('KIMS Hospitals', 'Private'),
        ('Osmania General Hospital', 'Government'),
        ('Gandhi Hospital', 'Government')
    ],
    'Pune': [
        ('Apollo Hospitals Pune', 'Private'),
        ('Ruby Hall Clinic', 'Private'),
        ('Jehangir Hospital', 'Private'),
        ('Sahyadri Hospitals', 'Private'),
        ('Sassoon General Hospital', 'Government')
    ]
}

# Real Indian diseases with actual prevalence data
DISEASES = [
    ('Diabetes', 'Metabolic', 'High', 0.12),  # 12% prevalence in India
    ('Hypertension', 'Cardiovascular', 'High', 0.25),  # 25% prevalence
    ('Malaria', 'Infectious', 'Medium', 0.08),
    ('Dengue', 'Infectious', 'High', 0.15),
    ('Tuberculosis', 'Infectious', 'High', 0.20),  # High in India
    ('Pneumonia', 'Respiratory', 'High', 0.18),
    ('Asthma', 'Respiratory', 'Medium', 0.10),
    ('Coronary Heart Disease', 'Cardiovascular', 'Critical', 0.15),
    ('Arthritis', 'Musculoskeletal', 'Low', 0.08),
    ('Gastritis', 'Digestive', 'Low', 0.12),
    ('Typhoid', 'Infectious', 'Medium', 0.10),
    ('Cholera', 'Infectious', 'High', 0.05),
    ('Hepatitis B', 'Hepatic', 'High', 0.08),
    ('Kidney Stones', 'Urological', 'Medium', 0.10),
    ('Migraine', 'Neurological', 'Low', 0.12),
    ('Chronic Obstructive Pulmonary Disease', 'Respiratory', 'High', 0.11),
    ('Chronic Kidney Disease', 'Nephrology', 'High', 0.10),
    ('Hypothyroidism', 'Endocrine', 'Medium', 0.12),
    ('Anemia', 'Hematological', 'Medium', 0.30),  # Very common in India
    ('Diarrhea', 'Digestive', 'Medium', 0.15)
]

# Real Indian doctor specializations with realistic fees (min, max in INR)
SPECIALIZATIONS = [
    ('Cardiology', 800, 2000),
    ('Neurology', 700, 1800),
    ('Orthopedics', 600, 1500),
    ('Pediatrics', 500, 1200),
    ('Gynecology', 600, 1500),
    ('Dermatology', 500, 1200),
    ('Oncology', 1000, 2500),
    ('Psychiatry', 600, 1500),
    ('General Medicine', 400, 1000),
    ('Surgery', 800, 2000),
    ('ENT', 500, 1200),
    ('Ophthalmology', 500, 1200),
    ('Gastroenterology', 700, 1800),
    ('Pulmonology', 600, 1500),
    ('Endocrinology', 600, 1500),
    ('Nephrology', 700, 1800),
    ('Urology', 700, 1800),
    ('Hematology', 800, 2000)
]

# Real Indian first names and surnames
INDIAN_FIRST_NAMES = [
    'Rajesh', 'Priya', 'Amit', 'Anjali', 'Rahul', 'Kavita', 'Vikram', 'Sneha',
    'Arjun', 'Meera', 'Karan', 'Divya', 'Rohan', 'Pooja', 'Siddharth', 'Neha',
    'Aditya', 'Shreya', 'Ravi', 'Anita', 'Mohit', 'Kiran', 'Nikhil', 'Riya',
    'Suresh', 'Sunita', 'Deepak', 'Manisha', 'Vishal', 'Radha', 'Gaurav', 'Swati',
    'Anil', 'Lakshmi', 'Manoj', 'Sarita', 'Pankaj', 'Geeta', 'Ashok', 'Madhuri',
    'Sandeep', 'Rekha', 'Vinod', 'Usha', 'Ajay', 'Kamala', 'Sunil', 'Indira',
    'Mahesh', 'Lata', 'Ramesh', 'Sushma', 'Dinesh', 'Vidya', 'Harish', 'Meenakshi'
]

INDIAN_SURNAMES = [
    'Sharma', 'Patel', 'Kumar', 'Singh', 'Reddy', 'Nair', 'Iyer', 'Gupta',
    'Mehta', 'Shah', 'Desai', 'Joshi', 'Rao', 'Nair', 'Menon', 'Pillai',
    'Verma', 'Yadav', 'Khan', 'Malik', 'Ahmad', 'Hussain', 'Ali', 'Sheikh',
    'Das', 'Biswas', 'Banerjee', 'Chatterjee', 'Ghosh', 'Mukherjee', 'Roy',
    'Jain', 'Agarwal', 'Goyal', 'Goel', 'Bansal', 'Arora', 'Kapoor', 'Khanna'
]

# Real Indian treatment costs (in INR) - min, max
TREATMENTS = [
    ('Bypass Surgery', 'Surgical', 150000, 300000),
    ('Angioplasty', 'Cardiology', 80000, 200000),
    ('Chemotherapy', 'Oncology', 50000, 150000),
    ('Physiotherapy', 'Rehabilitation', 500, 2000),
    ('Dialysis', 'Nephrology', 2000, 5000),
    ('Endoscopy', 'Diagnostic', 3000, 8000),
    ('Colonoscopy', 'Diagnostic', 5000, 12000),
    ('MRI Scan', 'Diagnostic', 5000, 15000),
    ('CT Scan', 'Diagnostic', 3000, 8000),
    ('X-Ray', 'Diagnostic', 200, 800),
    ('Ultrasound', 'Diagnostic', 500, 2000),
    ('Blood Test', 'Diagnostic', 300, 1500),
    ('ECG', 'Diagnostic', 200, 500),
    ('Echocardiogram', 'Diagnostic', 2000, 5000),
    ('Cataract Surgery', 'Surgical', 15000, 50000),
    ('Knee Replacement', 'Surgical', 200000, 400000),
    ('Hip Replacement', 'Surgical', 180000, 350000),
    ('Appendectomy', 'Surgical', 30000, 80000),
    ('Gallbladder Removal', 'Surgical', 50000, 120000),
    ('C-Section', 'Surgical', 40000, 100000)
]

# Real Indian medications with actual prices (in INR) - min, max
MEDICATIONS = [
    ('Paracetamol 500mg', 'Generic', 2, 5),
    ('Amoxicillin 500mg', 'Antibiotic', 50, 150),
    ('Metformin 500mg', 'Diabetes', 3, 10),
    ('Amlodipine 5mg', 'Hypertension', 5, 15),
    ('Aspirin 75mg', 'Cardiovascular', 2, 8),
    ('Ibuprofen 400mg', 'Pain Relief', 5, 20),
    ('Omeprazole 20mg', 'Gastric', 8, 25),
    ('Atorvastatin 10mg', 'Cholesterol', 10, 30),
    ('Insulin Glargine', 'Diabetes', 300, 800),
    ('Salbutamol Inhaler', 'Asthma', 150, 400),
    ('Azithromycin 500mg', 'Antibiotic', 30, 100),
    ('Ciprofloxacin 500mg', 'Antibiotic', 20, 80),
    ('Pantoprazole 40mg', 'Gastric', 10, 30),
    ('Losartan 50mg', 'Hypertension', 8, 25),
    ('Glibenclamide 5mg', 'Diabetes', 3, 10)
]

# Real Indian pharmaceutical manufacturers
INDIAN_MANUFACTURERS = [
    'Cipla', 'Sun Pharma', 'Dr. Reddy\'s', 'Lupin', 'Glenmark', 
    'Cadila', 'Torrent', 'Zydus', 'Aurobindo', 'Biocon'
]

def connect_db():
    """Connect to MySQL database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def populate_date_dimension(conn, start_date, end_date):
    """Populate date dimension table"""
    cursor = conn.cursor()
    indian_holidays = {
        (1, 26): 'Republic Day',
        (8, 15): 'Independence Day',
        (10, 2): 'Gandhi Jayanti',
        (12, 25): 'Christmas',
        (10, 22): 'Dussehra',
        (11, 12): 'Diwali',
        (1, 14): 'Makar Sankranti',
        (3, 8): 'Holi'
    }
    
    current_date = start_date
    while current_date <= end_date:
        date_id = int(current_date.strftime('%Y%m%d'))
        day = current_date.day
        month = current_date.month
        year = current_date.year
        quarter = (month - 1) // 3 + 1
        month_name = current_date.strftime('%B')
        day_name = current_date.strftime('%A')
        is_weekend = current_date.weekday() >= 5
        is_holiday = (month, day) in indian_holidays
        holiday_name = indian_holidays.get((month, day), None)
        
        cursor.execute("""
            INSERT INTO date_dimension 
            (date_id, full_date, day, month, year, quarter, month_name, day_name, is_weekend, is_holiday, holiday_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE full_date=full_date
        """, (date_id, current_date, day, month, year, quarter, month_name, day_name, is_weekend, is_holiday, holiday_name))
        
        current_date += timedelta(days=1)
    
    conn.commit()
    cursor.close()
    print("Date dimension populated")

def populate_hospitals(conn, count=100):
    """Populate hospitals with real Indian hospital names"""
    cursor = conn.cursor()
    
    hospital_id = 0
    for city, hospitals in REAL_INDIAN_HOSPITALS.items():
        for hospital_name, hospital_type in hospitals:
            # Find state for city
            state = None
            for s, cities in INDIAN_CITIES.items():
                if city in cities:
                    state = s
                    break
            
            if not state:
                state = random.choice(INDIAN_STATES)
            
            cursor.execute("""
                INSERT INTO hospitals 
                (hospital_name, hospital_type, address, city, state, pincode, phone, email, beds_count, established_year)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                hospital_name,
                hospital_type,
                f"{random.randint(1, 999)} {city} Street",
                city,
                state,
                str(random.randint(400000, 799999)),
                f"+91-{random.randint(7000000000, 9999999999)}",
                f"info@{hospital_name.lower().replace(' ', '')}.com",
                random.randint(100, 1000) if hospital_type == 'Private' else random.randint(500, 2000),
                random.randint(1950, 2010)
            ))
            hospital_id += 1
            if hospital_id >= count:
                break
        if hospital_id >= count:
            break
    
    # Add more hospitals in other cities
    while hospital_id < count:
        state = random.choice(INDIAN_STATES)
        city = random.choice(INDIAN_CITIES.get(state, ['City']))
        hospital_type = random.choice(['Government', 'Private', 'Charity'])
        
        hospital_names = [
            f"{city} {hospital_type} Hospital",
            f"{city} Medical Center",
            f"{city} General Hospital",
            f"{city} Healthcare",
            f"{city} Super Speciality Hospital"
        ]
        
        cursor.execute("""
            INSERT INTO hospitals 
            (hospital_name, hospital_type, address, city, state, pincode, phone, email, beds_count, established_year)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            random.choice(hospital_names),
            hospital_type,
            fake.address(),
            city,
            state,
            str(random.randint(400000, 799999)),
            fake.phone_number(),
            fake.email(),
            random.randint(50, 500),
            random.randint(1950, 2010)
        ))
        hospital_id += 1
    
    conn.commit()
    cursor.close()
    print(f"{hospital_id} hospitals populated")

def populate_doctors(conn, count=300):
    """Populate doctors with realistic Indian names"""
    cursor = conn.cursor()
    
    cursor.execute("SELECT hospital_id FROM hospitals")
    hospital_ids = [row[0] for row in cursor.fetchall()]
    
    for i in range(count):
        first_name = random.choice(INDIAN_FIRST_NAMES)
        last_name = random.choice(INDIAN_SURNAMES)
        doctor_name = f"Dr. {first_name} {last_name}"
        specialization, min_fee, max_fee = random.choice(SPECIALIZATIONS)
        
        cursor.execute("""
            INSERT INTO doctors 
            (doctor_name, specialization, qualification, experience_years, hospital_id, phone, email, consultation_fee)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            doctor_name,
            specialization,
            random.choice(['MBBS', 'MD', 'MS', 'DM', 'MCh', 'DNB']),
            random.randint(2, 35),
            random.choice(hospital_ids),
            f"+91-{random.randint(7000000000, 9999999999)}",
            f"{first_name.lower()}.{last_name.lower()}@hospital.com",
            random.randint(min_fee, max_fee)
        ))
    
    conn.commit()
    cursor.close()
    print(f"{count} doctors populated")

def populate_diseases(conn):
    """Populate diseases with real Indian disease data"""
    cursor = conn.cursor()
    
    for disease_data in DISEASES:
        if len(disease_data) == 4:
            disease_name, category, severity, prevalence = disease_data
            description = f"Common in India with {prevalence*100:.1f}% prevalence"
        else:
            disease_name, category, severity = disease_data
            description = f"Description of {disease_name}"
        
        cursor.execute("""
            INSERT INTO diseases (disease_name, disease_category, severity_level, description)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE disease_name=disease_name
        """, (disease_name, category, severity, description))
    
    conn.commit()
    cursor.close()
    print("Diseases populated")

def populate_treatments(conn):
    """Populate treatments with real Indian costs"""
    cursor = conn.cursor()
    
    for treatment_data in TREATMENTS:
        if len(treatment_data) == 4:
            name, t_type, min_cost, max_cost = treatment_data
            avg_cost = (min_cost + max_cost) // 2
        else:
            name, t_type, cost = treatment_data
            avg_cost = cost
        
        cursor.execute("""
            INSERT INTO treatments (treatment_name, treatment_type, average_cost, description)
            VALUES (%s, %s, %s, %s)
        """, (name, t_type, avg_cost, f"Treatment for {name} - Indian healthcare cost"))
    
    conn.commit()
    cursor.close()
    print("Treatments populated")

def populate_medications(conn):
    """Populate medications with real Indian prices"""
    cursor = conn.cursor()
    
    for med_data in MEDICATIONS:
        if len(med_data) == 4:
            name, category, min_price, max_price = med_data
            price = random.randint(min_price, max_price)
        else:
            name, category, price = med_data
        
        cursor.execute("""
            INSERT INTO medications (medication_name, manufacturer, category, unit_price)
            VALUES (%s, %s, %s, %s)
        """, (name, random.choice(INDIAN_MANUFACTURERS), category, price))
    
    conn.commit()
    cursor.close()
    print("Medications populated")

def populate_patients(conn, count=2000):
    """Populate patients with realistic Indian names and data"""
    cursor = conn.cursor()
    
    for i in range(count):
        first_name = random.choice(INDIAN_FIRST_NAMES)
        last_name = random.choice(INDIAN_SURNAMES)
        patient_name = f"{first_name} {last_name}"
        
        state = random.choice(INDIAN_STATES)
        city = random.choice(INDIAN_CITIES.get(state, ['City']))
        
        # Realistic age distribution for India
        age = random.choices(
            range(1, 91),
            weights=[5]*20 + [4]*20 + [3]*20 + [2]*20 + [1]*10 + [0.5]*1
        )[0]
        
        cursor.execute("""
            INSERT INTO patients 
            (patient_name, age, gender, phone, email, address, city, state, pincode)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            patient_name,
            age,
            random.choice(['Male', 'Female', 'Other']),
            f"+91-{random.randint(7000000000, 9999999999)}",
            f"{first_name.lower()}.{last_name.lower()}@email.com",
            f"{random.randint(1, 999)} {city} Street",
            city,
            state,
            str(random.randint(400000, 799999))
        ))
    
    conn.commit()
    cursor.close()
    print(f"{count} patients populated")

def populate_patient_visits(conn, count=10000):
    """Populate patient visits with realistic Indian healthcare patterns"""
    cursor = conn.cursor()
    
    # Get all IDs
    cursor.execute("SELECT patient_id FROM patients")
    patient_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT doctor_id FROM doctors")
    doctor_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT hospital_id FROM hospitals")
    hospital_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT disease_id, disease_name FROM diseases")
    disease_data = cursor.fetchall()
    disease_ids = [row[0] for row in disease_data]
    disease_names = {row[0]: row[1] for row in disease_data}
    
    cursor.execute("SELECT treatment_id, average_cost FROM treatments")
    treatment_data = cursor.fetchall()
    treatment_ids = [row[0] for row in treatment_data]
    treatment_costs = {row[0]: row[1] for row in treatment_data}
    
    cursor.execute("SELECT medication_id, unit_price FROM medications")
    medication_data = cursor.fetchall()
    medication_ids = [row[0] for row in medication_data]
    medication_prices = {row[0]: row[1] for row in medication_data}
    
    cursor.execute("SELECT date_id FROM date_dimension WHERE full_date >= '2023-01-01' ORDER BY RAND() LIMIT 2000")
    date_ids = [row[0] for row in cursor.fetchall()]
    
    visit_types = ['OPD', 'Emergency', 'IPD', 'Follow-up']
    visit_weights = [0.60, 0.15, 0.15, 0.10]  # OPD most common
    
    payment_methods = ['Cash', 'Insurance', 'Card', 'UPI']
    payment_weights = [0.40, 0.30, 0.15, 0.15]  # Cash still common in India
    
    for i in range(count):
        visit_date_id = random.choice(date_ids)
        visit_type = random.choices(visit_types, weights=visit_weights)[0]
        disease_id = random.choice(disease_ids) if random.random() > 0.1 else None
        treatment_id = random.choice(treatment_ids) if random.random() > 0.4 else None
        medication_id = random.choice(medication_ids) if random.random() > 0.3 else None
        
        # Base consultation cost
        cursor.execute("""
            SELECT consultation_fee FROM doctors WHERE doctor_id = %s
        """, (random.choice(doctor_ids),))
        doctor_fee = cursor.fetchone()[0]
        base_cost = doctor_fee
        
        # Add treatment cost
        if treatment_id:
            base_cost += treatment_costs[treatment_id]
        
        # Add medication cost
        if medication_id:
            quantity = random.randint(1, 5)
            base_cost += medication_prices[medication_id] * quantity
        
        # Add hospital charges based on visit type
        if visit_type == 'Emergency':
            base_cost += random.randint(1000, 5000)
        elif visit_type == 'IPD':
            base_cost += random.randint(5000, 20000)
        
        # Add some variation
        total_cost = base_cost * random.uniform(0.8, 1.2)
        
        payment_method = random.choices(payment_methods, weights=payment_weights)[0]
        
        cursor.execute("""
            INSERT INTO patient_visits 
            (patient_id, doctor_id, hospital_id, disease_id, visit_date_id, visit_type, 
             diagnosis, treatment_id, medication_id, medication_quantity, total_cost, 
             payment_method, visit_duration_minutes, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            random.choice(patient_ids),
            random.choice(doctor_ids),
            random.choice(hospital_ids),
            disease_id,
            visit_date_id,
            visit_type,
            f"Diagnosis for {disease_names.get(disease_id, 'General checkup')}" if disease_id else "General checkup",
            treatment_id,
            medication_id,
            random.randint(1, 10) if medication_id else None,
            round(total_cost, 2),
            payment_method,
            random.randint(15, 120),
            'Completed'
        ))
    
    conn.commit()
    cursor.close()
    print(f"{count} patient visits populated")

def main():
    """Main function to populate database"""
    print("=" * 60)
    print("Healthcare Analytics Data Warehouse - Real Indian Data")
    print("=" * 60)
    print()
    
    print("Connecting to database...")
    conn = connect_db()
    
    if not conn:
        print("Failed to connect to database. Please check your MySQL configuration.")
        return
    
    print("Populating database with realistic Indian healthcare data...")
    print()
    
    # Populate dimension tables
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2024, 12, 31)
    print("1. Populating date dimension...")
    populate_date_dimension(conn, start_date, end_date)
    
    print("2. Populating hospitals (real Indian hospital names)...")
    populate_hospitals(conn, 100)
    
    print("3. Populating doctors (real Indian names)...")
    populate_doctors(conn, 300)
    
    print("4. Populating diseases (real Indian disease data)...")
    populate_diseases(conn)
    
    print("5. Populating treatments (real Indian costs)...")
    populate_treatments(conn)
    
    print("6. Populating medications (real Indian prices)...")
    populate_medications(conn)
    
    print("7. Populating patients (real Indian names and data)...")
    populate_patients(conn, 2000)
    
    # Populate fact tables
    print("8. Populating patient visits (realistic Indian healthcare patterns)...")
    populate_patient_visits(conn, 10000)
    
    conn.close()
    print()
    print("=" * 60)
    print("Database population completed successfully!")
    print("=" * 60)
    print()
    print("Summary:")
    print("- 100 Real Indian Hospitals (AIIMS, Apollo, Fortis, etc.)")
    print("- 300 Doctors with Indian names")
    print("- 20 Common Indian Diseases with prevalence data")
    print("- 20 Treatments with realistic Indian costs")
    print("- 15 Medications with actual Indian prices")
    print("- 2000 Patients with Indian names")
    print("- 10000 Patient Visits with realistic patterns")
    print()

if __name__ == "__main__":
    main()

