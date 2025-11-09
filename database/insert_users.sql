-- Insert default users with pre-hashed passwords
-- Password for all users: admin123
-- Run this after creating the users table

USE healthcare_analytics;

-- Delete existing users if any
DELETE FROM users WHERE username IN ('admin', 'analyst1', 'doctor1');

-- Insert users with bcrypt hashed passwords
-- Password: admin123
INSERT INTO users (username, email, password_hash, role, full_name, is_active) VALUES
('admin', 'admin@healthcare.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5', 'admin', 'System Administrator', TRUE),
('analyst1', 'analyst@healthcare.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5', 'analyst', 'Data Analyst', TRUE),
('doctor1', 'doctor@healthcare.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5', 'doctor', 'Dr. John Doe', TRUE);

-- Verify users were created
SELECT username, email, role, full_name, is_active FROM users;

