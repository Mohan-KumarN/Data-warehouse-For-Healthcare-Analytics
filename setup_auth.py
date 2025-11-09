"""
Setup script for authentication system
Run this after setting up the main database schema
"""

import mysql.connector
import os
from config import DB_CONFIG

def setup_auth():
    """Setup authentication tables and default users"""
    print("Setting up authentication system...")
    
    # Read and execute auth schema
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        with open('database/auth_schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
            # Split by semicolons and execute each statement
            statements = schema_sql.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                    except mysql.connector.Error as e:
                        if 'already exists' not in str(e).lower():
                            print(f"Warning: {e}")
        
        conn.commit()
        print("✓ Authentication tables created")
        
        # Create default users
        from database.create_default_users import create_default_users
        create_default_users()
        
        cursor.close()
        conn.close()
        
        print("\n✅ Authentication setup complete!")
        print("\nDefault users created:")
        print("  - admin / admin123 (Admin)")
        print("  - analyst1 / admin123 (Analyst)")
        print("  - doctor1 / admin123 (Doctor)")
        print("\n⚠️  IMPORTANT: Change default passwords in production!")
        
    except Exception as e:
        print(f"❌ Error setting up authentication: {e}")
        return False
    
    return True

if __name__ == '__main__':
    setup_auth()


