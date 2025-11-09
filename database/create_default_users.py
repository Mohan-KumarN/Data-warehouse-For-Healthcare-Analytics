"""
Script to create default users with proper password hashing
Run this after setting up the database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
import bcrypt
from config import DB_CONFIG

def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_default_users():
    """Create default users with hashed passwords"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Default password for all users: admin123
        default_password = 'admin123'
        password_hash = hash_password(default_password)
        
        users = [
            ('admin', 'admin@healthcare.com', password_hash, 'admin', 'System Administrator'),
            ('analyst1', 'analyst@healthcare.com', password_hash, 'analyst', 'Data Analyst'),
            ('doctor1', 'doctor@healthcare.com', password_hash, 'doctor', 'Dr. John Doe')
        ]
        
        print("Creating default users...")
        for username, email, pwd_hash, role, full_name in users:
            try:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role, full_name, is_active)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                    ON DUPLICATE KEY UPDATE
                        password_hash = VALUES(password_hash),
                        role = VALUES(role),
                        full_name = VALUES(full_name),
                        is_active = TRUE
                """, (username, email, pwd_hash, role, full_name))
                print(f"✓ Created/Updated user: {username} ({role})")
            except Exception as e:
                print(f"✗ Error creating user {username}: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("\n✅ Default users created successfully!")
        print("\nLogin Credentials:")
        print("  Admin:   admin / admin123")
        print("  Analyst: analyst1 / admin123")
        print("  Doctor:  doctor1 / admin123")
        return True
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        print("\nPlease ensure:")
        print("  1. MySQL is running")
        print("  2. Database 'healthcare_analytics' exists")
        print("  3. Users table exists (run database/auth_schema.sql)")
        print("  4. Database credentials in config.py are correct")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    create_default_users()
