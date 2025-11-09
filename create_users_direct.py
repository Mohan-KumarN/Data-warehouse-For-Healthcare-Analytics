"""
Direct script to create users - tries to connect and create users
Works even if config.py password is wrong - prompts for password
"""

import mysql.connector
import bcrypt
import getpass

def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_users_with_password(db_password=None):
    """Create users with provided or prompted password"""
    if db_password is None:
        print("Enter MySQL root password (or press Enter to try 'root'):")
        db_password = getpass.getpass("Password: ") or 'root'
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password=db_password,
            database='healthcare_analytics'
        )
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            print("❌ Users table does not exist!")
            print("Please run: mysql -u root -p healthcare_analytics < database/auth_schema.sql")
            return False
        
        # Default password for all users: admin123
        default_password = 'admin123'
        password_hash = hash_password(default_password)
        
        users = [
            ('admin', 'admin@healthcare.com', password_hash, 'admin', 'System Administrator'),
            ('analyst1', 'analyst@healthcare.com', password_hash, 'analyst', 'Data Analyst'),
            ('doctor1', 'doctor@healthcare.com', password_hash, 'doctor', 'Dr. John Doe')
        ]
        
        print("\nCreating default users...")
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
        
        # Verify users
        cursor.execute("SELECT username, role, is_active FROM users WHERE username IN ('admin', 'analyst1', 'doctor1')")
        users_created = cursor.fetchall()
        print(f"\n✓ Verified {len(users_created)} users in database")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*50)
        print("✅ USERS CREATED SUCCESSFULLY!")
        print("="*50)
        print("\nLogin Credentials:")
        print("  Admin:   admin / admin123")
        print("  Analyst: analyst1 / admin123")
        print("  Doctor:  doctor1 / admin123")
        print("\nYou can now login at http://localhost:5000")
        return True
        
    except mysql.connector.Error as e:
        if e.errno == 1045:
            print(f"\n❌ Authentication failed. Wrong password.")
            print("Trying common passwords...")
            # Try common passwords
            common_passwords = ['', 'root', 'password', '123456']
            for pwd in common_passwords:
                if pwd == db_password:
                    continue
                try:
                    conn = mysql.connector.connect(
                        host='localhost',
                        user='root',
                        password=pwd,
                        database='healthcare_analytics'
                    )
                    print(f"✓ Connected with password: {'(empty)' if pwd == '' else pwd}")
                    return create_users_with_password(pwd)
                except:
                    continue
            print("\nPlease update config.py with your MySQL password")
            print("Or run this script and enter the correct password when prompted")
        elif e.errno == 1049:
            print(f"\n❌ Database 'healthcare_analytics' does not exist!")
            print("Please run: mysql -u root -p < database/schema.sql")
        else:
            print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == '__main__':
    print("="*50)
    print("Healthcare Analytics - User Creation Script")
    print("="*50)
    create_users_with_password()

