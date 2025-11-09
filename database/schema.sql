-- Healthcare Data Warehouse Schema
-- Database: healthcare_analytics

CREATE DATABASE IF NOT EXISTS healthcare_analytics;
USE healthcare_analytics;

-- Patients Dimension Table
CREATE TABLE IF NOT EXISTS patients (
    patient_id INT PRIMARY KEY AUTO_INCREMENT,
    patient_name VARCHAR(255) NOT NULL,
    age INT NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Hospitals Dimension Table
CREATE TABLE IF NOT EXISTS hospitals (
    hospital_id INT PRIMARY KEY AUTO_INCREMENT,
    hospital_name VARCHAR(255) NOT NULL,
    hospital_type ENUM('Government', 'Private', 'Charity') NOT NULL,
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    phone VARCHAR(20),
    email VARCHAR(255),
    beds_count INT,
    established_year INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Doctors Dimension Table
CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INT PRIMARY KEY AUTO_INCREMENT,
    doctor_name VARCHAR(255) NOT NULL,
    specialization VARCHAR(255) NOT NULL,
    qualification VARCHAR(255),
    experience_years INT,
    hospital_id INT,
    phone VARCHAR(20),
    email VARCHAR(255),
    consultation_fee DECIMAL(10, 2),
    FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Diseases Dimension Table
CREATE TABLE IF NOT EXISTS diseases (
    disease_id INT PRIMARY KEY AUTO_INCREMENT,
    disease_name VARCHAR(255) NOT NULL UNIQUE,
    disease_category VARCHAR(100),
    severity_level ENUM('Low', 'Medium', 'High', 'Critical'),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Treatments Dimension Table
CREATE TABLE IF NOT EXISTS treatments (
    treatment_id INT PRIMARY KEY AUTO_INCREMENT,
    treatment_name VARCHAR(255) NOT NULL,
    treatment_type VARCHAR(100),
    description TEXT,
    average_cost DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medications Dimension Table
CREATE TABLE IF NOT EXISTS medications (
    medication_id INT PRIMARY KEY AUTO_INCREMENT,
    medication_name VARCHAR(255) NOT NULL,
    manufacturer VARCHAR(255),
    category VARCHAR(100),
    unit_price DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Date Dimension Table
CREATE TABLE IF NOT EXISTS date_dimension (
    date_id INT PRIMARY KEY AUTO_INCREMENT,
    full_date DATE NOT NULL UNIQUE,
    day INT,
    month INT,
    year INT,
    quarter INT,
    month_name VARCHAR(20),
    day_name VARCHAR(20),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    holiday_name VARCHAR(100)
);

-- Fact Table: Patient Visits
CREATE TABLE IF NOT EXISTS patient_visits (
    visit_id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    hospital_id INT NOT NULL,
    disease_id INT,
    visit_date_id INT NOT NULL,
    visit_type ENUM('OPD', 'Emergency', 'IPD', 'Follow-up') NOT NULL,
    diagnosis TEXT,
    treatment_id INT,
    medication_id INT,
    medication_quantity INT,
    total_cost DECIMAL(10, 2) NOT NULL,
    payment_method ENUM('Cash', 'Insurance', 'Card', 'UPI') NOT NULL,
    visit_duration_minutes INT,
    status ENUM('Completed', 'Cancelled', 'Pending') DEFAULT 'Completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
    FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id),
    FOREIGN KEY (disease_id) REFERENCES diseases(disease_id),
    FOREIGN KEY (visit_date_id) REFERENCES date_dimension(date_id),
    FOREIGN KEY (treatment_id) REFERENCES treatments(treatment_id),
    FOREIGN KEY (medication_id) REFERENCES medications(medication_id)
);

-- Fact Table: Hospital Statistics
CREATE TABLE IF NOT EXISTS hospital_statistics (
    stat_id INT PRIMARY KEY AUTO_INCREMENT,
    hospital_id INT NOT NULL,
    date_id INT NOT NULL,
    total_patients INT DEFAULT 0,
    total_revenue DECIMAL(12, 2) DEFAULT 0,
    opd_count INT DEFAULT 0,
    emergency_count INT DEFAULT 0,
    ipd_count INT DEFAULT 0,
    avg_occupancy_rate DECIMAL(5, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id),
    FOREIGN KEY (date_id) REFERENCES date_dimension(date_id)
);

-- Indexes for better performance
CREATE INDEX idx_patient_visits_date ON patient_visits(visit_date_id);
CREATE INDEX idx_patient_visits_patient ON patient_visits(patient_id);
CREATE INDEX idx_patient_visits_hospital ON patient_visits(hospital_id);
CREATE INDEX idx_patient_visits_disease ON patient_visits(disease_id);
CREATE INDEX idx_patients_state ON patients(state);
CREATE INDEX idx_patients_city ON patients(city);
CREATE INDEX idx_hospitals_state ON hospitals(state);
CREATE INDEX idx_hospitals_city ON hospitals(city);

-- Staging table for patient visits ETL
CREATE TABLE IF NOT EXISTS staging_patient_visits (
    staging_id INT PRIMARY KEY AUTO_INCREMENT,
    raw_payload JSON NOT NULL,
    source_file VARCHAR(255),
    status ENUM('PENDING', 'VALIDATED', 'FAILED', 'PROCESSED') DEFAULT 'PENDING',
    error_message TEXT,
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL
);

-- Ingestion job audit table
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    job_id INT PRIMARY KEY AUTO_INCREMENT,
    job_type ENUM('PATIENT_VISITS') NOT NULL,
    source_file VARCHAR(255),
    total_records INT DEFAULT 0,
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED') DEFAULT 'PENDING',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    error_message TEXT
);

CREATE INDEX idx_ingestion_jobs_status ON ingestion_jobs(status);

