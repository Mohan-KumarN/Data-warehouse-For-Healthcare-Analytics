"""
Setup script for Healthcare Analytics Data Warehouse
This script helps set up the database and populate initial data
"""
import mysql.connector
from mysql.connector import Error
import os
import sys

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root'),
    'database': os.getenv('DB_NAME', 'healthcare_analytics')
}

def test_connection():
    """Test MySQL connection"""
    try:
        # Try connecting without database first
        config = DB_CONFIG.copy()
        config.pop('database', None)
        conn = mysql.connector.connect(**config)
        print("✓ MySQL connection successful")
        conn.close()
        return True
    except Error as e:
        print(f"✗ MySQL connection failed: {e}")
        print("\nPlease check:")
        print("1. MySQL server is running")
        print("2. Database credentials are correct")
        print("3. Update DB_CONFIG in this file or set environment variables")
        return False

def create_database():
    """Create database if it doesn't exist"""
    try:
        config = DB_CONFIG.copy()
        config.pop('database', None)
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        print(f"✓ Database '{DB_CONFIG['database']}' ready")
        
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print(f"✗ Error creating database: {e}")
        return False

def execute_schema():
    """Execute schema.sql file"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        schema_file = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')
        
        if not os.path.exists(schema_file):
            print(f"✗ Schema file not found: {schema_file}")
            return False
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Execute statements one by one
        for statement in schema_sql.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                except Error as e:
                    if 'already exists' not in str(e).lower():
                        print(f"Warning: {e}")
        
        conn.commit()
        print("✓ Database schema created successfully")
        
        cursor.close()
        conn.close()
        return True
    except Error as e:
        print(f"✗ Error executing schema: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("Healthcare Analytics Data Warehouse - Setup")
    print("=" * 60)
    print()
    
    # Test connection
    if not test_connection():
        sys.exit(1)
    
    # Create database
    if not create_database():
        sys.exit(1)
    
    # Execute schema
    if not execute_schema():
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("Setup completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Run: python database/init_data.py (to populate sample data)")
    print("2. Run: python app.py (to start the web server)")
    print()
    print("Note: Update DB_CONFIG in config.py if your MySQL")
    print("      credentials are different from defaults")
    print()

if __name__ == '__main__':
    main()

