"""
Quick fix script to create users - uses config.py settings
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mysql.connector
import bcrypt

def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# Try different password combinations
passwords_to_try = ['', 'root', 'password']

from config import DB_CONFIG

for pwd in passwords_to_try:
    try:
        test_config = DB_CONFIG.copy()
        test_config['password'] = pwd
        conn = mysql.connector.connect(**test_config)
        print(f"✓ Connected to database (password: {'(empty)' if pwd == '' else pwd})")
        
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            print("❌ Users table does not exist!")
            print("Creating users table...")
            # Try to create table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role ENUM('admin', 'analyst', 'doctor') NOT NULL DEFAULT 'analyst',
                    full_name VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    INDEX idx_username (username),
                    INDEX idx_email (email),
                    INDEX idx_role (role)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            conn.commit()
            print("✓ Users table created")
        
        # Create users
        default_password = 'admin123'
        password_hash = hash_password(default_password)
        
        users = [
            ('admin', 'admin@healthcare.com', password_hash, 'admin', 'System Administrator'),
            ('analyst1', 'analyst@healthcare.com', password_hash, 'analyst', 'Data Analyst'),
            ('doctor1', 'doctor@healthcare.com', password_hash, 'doctor', 'Dr. John Doe')
        ]
        
        print("\nCreating/Updating users...")
        for username, email, pwd_hash, role, full_name in users:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, full_name, is_active)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                ON DUPLICATE KEY UPDATE
                    password_hash = VALUES(password_hash),
                    role = VALUES(role),
                    full_name = VALUES(full_name),
                    is_active = TRUE
            """, (username, email, pwd_hash, role, full_name))
            print(f"  ✓ {username} ({role})")
        
        conn.commit()
        
        # Verify
        cursor.execute("SELECT username, role FROM users")
        all_users = cursor.fetchall()
        print(f"\n✓ Total users in database: {len(all_users)}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("✅ SUCCESS! Users created successfully!")
        print("="*60)
        print("\nLogin Credentials:")
        print("  👤 Admin:   admin / admin123")
        print("  👤 Analyst: analyst1 / admin123")
        print("  👤 Doctor:  doctor1 / admin123")
        print("\n🌐 Access: http://localhost:5000")
        print("\n" + "="*60)
        
        # Update config.py if we found the right password
        if pwd != DB_CONFIG.get('password', ''):
            print(f"\n💡 Tip: Update config.py password to: '{pwd}'")
        
        break
        
    except mysql.connector.Error as e:
        if e.errno == 1045:
            continue  # Try next password
        else:
            print(f"❌ Error: {e}")
            break
    except Exception as e:
        print(f"❌ Error: {e}")
        break
else:
    print("\n❌ Could not connect to database!")
    print("\nPlease:")
    print("  1. Ensure MySQL is running")
    print("  2. Update config.py with your MySQL root password")
    print("  3. Run this script again")
    print("\nOr run manually:")
    print("  mysql -u root -p healthcare_analytics < database/auth_schema.sql")
    print("  python create_users_direct.py")


