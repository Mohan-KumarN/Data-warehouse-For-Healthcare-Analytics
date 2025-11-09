"""
Script to add cancer diseases to an existing database
Run this if you want to add cancer diseases without reinitializing the entire database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from config import DB_CONFIG

# Cancer diseases to add
CANCER_DISEASES = [
    ('Breast Cancer', 'Oncology', 'Critical', 0.0028),
    ('Cervical Cancer', 'Oncology', 'Critical', 0.0018),
    ('Oral Cancer', 'Oncology', 'Critical', 0.0025),
    ('Lung Cancer', 'Oncology', 'Critical', 0.0015),
    ('Stomach Cancer', 'Oncology', 'Critical', 0.0012),
    ('Colorectal Cancer', 'Oncology', 'Critical', 0.0010),
    ('Liver Cancer', 'Oncology', 'Critical', 0.0008),
    ('Prostate Cancer', 'Oncology', 'Critical', 0.0006),
    ('Ovarian Cancer', 'Oncology', 'Critical', 0.0005),
    ('Blood Cancer (Leukemia)', 'Oncology', 'Critical', 0.0004),
    ('Lymphoma', 'Oncology', 'Critical', 0.0004),
    ('Brain Tumor', 'Oncology', 'Critical', 0.0003),
    ('Thyroid Cancer', 'Oncology', 'High', 0.0005),
    ('Pancreatic Cancer', 'Oncology', 'Critical', 0.0003),
    ('Esophageal Cancer', 'Oncology', 'Critical', 0.0004),
    ('Kidney Cancer', 'Oncology', 'Critical', 0.0003),
    ('Bladder Cancer', 'Oncology', 'High', 0.0004),
    ('Skin Cancer', 'Oncology', 'High', 0.0002),
    ('Bone Cancer', 'Oncology', 'Critical', 0.0001)
]

def add_cancer_diseases():
    """Add cancer diseases to the database"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        added_count = 0
        skipped_count = 0
        
        for disease_data in CANCER_DISEASES:
            disease_name, category, severity, prevalence = disease_data
            description = f"Cancer disease common in India with {prevalence*100:.2f}% prevalence"
            
            try:
                cursor.execute("""
                    INSERT INTO diseases (disease_name, disease_category, severity_level, description)
                    VALUES (%s, %s, %s, %s)
                """, (disease_name, category, severity, description))
                added_count += 1
                print(f"✓ Added: {disease_name}")
            except mysql.connector.IntegrityError:
                skipped_count += 1
                print(f"⊘ Skipped (already exists): {disease_name}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n{'='*60}")
        print(f"Cancer diseases added successfully!")
        print(f"{'='*60}")
        print(f"Added: {added_count} diseases")
        print(f"Skipped: {skipped_count} diseases (already exist)")
        print(f"Total: {len(CANCER_DISEASES)} cancer diseases")
        
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Adding cancer diseases to the database...")
    print("="*60)
    add_cancer_diseases()

