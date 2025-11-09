-- Database Indexes for Performance Optimization
-- Run this script to add indexes for common query patterns

USE healthcare_analytics;

-- Indexes for patient_visits table (most queried table)
CREATE INDEX IF NOT EXISTS idx_visit_date ON patient_visits(visit_date_id);
CREATE INDEX IF NOT EXISTS idx_visit_patient ON patient_visits(patient_id);
CREATE INDEX IF NOT EXISTS idx_visit_hospital ON patient_visits(hospital_id);
CREATE INDEX IF NOT EXISTS idx_visit_doctor ON patient_visits(doctor_id);
CREATE INDEX IF NOT EXISTS idx_visit_disease ON patient_visits(disease_id);
CREATE INDEX IF NOT EXISTS idx_visit_type ON patient_visits(visit_type);
CREATE INDEX IF NOT EXISTS idx_visit_payment ON patient_visits(payment_method);
CREATE INDEX IF NOT EXISTS idx_visit_cost ON patient_visits(total_cost);

-- Composite indexes for common filter combinations
CREATE INDEX IF NOT EXISTS idx_visit_date_type ON patient_visits(visit_date_id, visit_type);
CREATE INDEX IF NOT EXISTS idx_visit_hospital_date ON patient_visits(hospital_id, visit_date_id);
CREATE INDEX IF NOT EXISTS idx_visit_patient_date ON patient_visits(patient_id, visit_date_id);

-- Indexes for patients table
CREATE INDEX IF NOT EXISTS idx_patient_state ON patients(state);
CREATE INDEX IF NOT EXISTS idx_patient_city ON patients(city);
CREATE INDEX IF NOT EXISTS idx_patient_name ON patients(patient_name);

-- Indexes for hospitals table
CREATE INDEX IF NOT EXISTS idx_hospital_state ON hospitals(state);
CREATE INDEX IF NOT EXISTS idx_hospital_city ON hospitals(city);
CREATE INDEX IF NOT EXISTS idx_hospital_type ON hospitals(hospital_type);

-- Indexes for doctors table
CREATE INDEX IF NOT EXISTS idx_doctor_specialization ON doctors(specialization);

-- Indexes for date_dimension (for date range queries)
CREATE INDEX IF NOT EXISTS idx_date_full ON date_dimension(full_date);
CREATE INDEX IF NOT EXISTS idx_date_year_month ON date_dimension(year, month);

-- Indexes for staging table (ETL operations)
CREATE INDEX IF NOT EXISTS idx_staging_status ON staging_patient_visits(status);
CREATE INDEX IF NOT EXISTS idx_staging_source ON staging_patient_visits(source_file);
CREATE INDEX IF NOT EXISTS idx_staging_processed ON staging_patient_visits(processed_at);

-- Indexes for ingestion_jobs
CREATE INDEX IF NOT EXISTS idx_jobs_status ON ingestion_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON ingestion_jobs(created_at);



