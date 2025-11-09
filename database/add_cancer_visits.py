"""
Script to add sample patient visits with cancer diseases
This ensures cancer diseases appear with data in analytics
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
import random
from datetime import datetime, timedelta
from config import DB_CONFIG

# Top 3 most common cancers in India
TOP_3_CANCERS = [
    'Breast Cancer',
    'Cervical Cancer', 
    'Oral Cancer'
]

def add_cancer_visits():
    """Add patient visits with top 3 cancer diseases"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get cancer disease IDs
        cursor.execute("""
            SELECT disease_id, disease_name FROM diseases 
            WHERE disease_category = 'Oncology' 
            AND disease_name IN (%s, %s, %s)
        """, tuple(TOP_3_CANCERS))
        cancer_diseases = cursor.fetchall()
        
        if not cancer_diseases:
            print("No cancer diseases found. Please run add_cancer_diseases.py first.")
            return False
        
        cancer_disease_ids = {name: did for did, name in cancer_diseases}
        print(f"Found {len(cancer_disease_ids)} cancer diseases")
        
        # Get other required IDs
        cursor.execute("SELECT patient_id FROM patients ORDER BY RAND() LIMIT 100")
        patient_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT doctor_id FROM doctors WHERE specialization = 'Oncology' OR specialization LIKE '%Oncology%'")
        oncology_doctors = cursor.fetchall()
        if not oncology_doctors:
            cursor.execute("SELECT doctor_id FROM doctors ORDER BY RAND() LIMIT 50")
            oncology_doctors = cursor.fetchall()
        doctor_ids = [row[0] for row in oncology_doctors]
        
        cursor.execute("SELECT hospital_id FROM hospitals ORDER BY RAND() LIMIT 20")
        hospital_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT date_id FROM date_dimension WHERE full_date >= '2023-01-01' ORDER BY RAND() LIMIT 100")
        date_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT treatment_id FROM treatments WHERE treatment_type = 'Oncology' OR treatment_name LIKE '%Cancer%' OR treatment_name LIKE '%Chemotherapy%'")
        cancer_treatments = cursor.fetchall()
        if not cancer_treatments:
            cursor.execute("SELECT treatment_id, average_cost FROM treatments WHERE treatment_name IN ('Chemotherapy', 'Radiation Therapy', 'Cancer Surgery')")
            cancer_treatments = cursor.fetchall()
        treatment_ids = [row[0] for row in cancer_treatments] if cancer_treatments else [None]
        
        # Add visits for each top 3 cancer
        visit_count = 0
        for cancer_name in TOP_3_CANCERS:
            if cancer_name not in cancer_disease_ids:
                continue
                
            disease_id = cancer_disease_ids[cancer_name]
            # Add 50-100 visits per cancer type
            num_visits = random.randint(50, 100)
            
            for _ in range(num_visits):
                visit_date_id = random.choice(date_ids)
                visit_type = random.choice(['OPD', 'IPD', 'Emergency'])
                treatment_id = random.choice(treatment_ids) if treatment_ids else None
                
                # Calculate cost - cancer treatments are expensive
                base_cost = random.randint(5000, 15000)  # Consultation
                if treatment_id:
                    cursor.execute("SELECT average_cost FROM treatments WHERE treatment_id = %s", (treatment_id,))
                    treatment_cost = cursor.fetchone()
                    if treatment_cost:
                        base_cost += int(treatment_cost[0])
                
                # IPD and Emergency cost more
                if visit_type == 'IPD':
                    base_cost += random.randint(10000, 50000)
                elif visit_type == 'Emergency':
                    base_cost += random.randint(2000, 10000)
                
                payment_method = random.choice(['Insurance', 'Cash', 'Card'])
                
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
                    f"Diagnosis and treatment for {cancer_name}",
                    treatment_id,
                    None,  # No medication for now
                    None,
                    round(base_cost, 2),
                    payment_method,
                    random.randint(30, 120),
                    'Completed'
                ))
                visit_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n{'='*60}")
        print(f"Cancer patient visits added successfully!")
        print(f"{'='*60}")
        print(f"Added {visit_count} patient visits for top 3 cancers:")
        for cancer in TOP_3_CANCERS:
            print(f"  - {cancer}")
        print(f"\nNow cancer diseases will show up with data in analytics!")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Adding patient visits for top 3 cancer diseases...")
    print("="*60)
    add_cancer_visits()

