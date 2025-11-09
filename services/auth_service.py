"""
Authentication Service
Handles JWT token generation, validation, and user authentication
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
import mysql.connector
from config import DB_CONFIG

# JWT Configuration
JWT_SECRET_KEY = 'your-secret-key-change-in-production'  # Change this in production!
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Role permissions mapping
ROLE_PERMISSIONS = {
    'admin': {
        'dashboard': True,
        'analytics': True,
        'patients': True,
        'visits': True,
        'data_entry': True,
        'export_all': True,
        'manage_users': True,
        'ml_training': True
    },
    'analyst': {
        'dashboard': True,
        'analytics': True,
        'patients': True,
        'visits': True,
        'data_entry': True,
        'export_all': True,
        'manage_users': False,
        'ml_training': True
    },
    'doctor': {
        'dashboard': True,
        'analytics': False,
        'patients': True,  # Can view but limited
        'visits': True,   # Can view but limited
        'data_entry': True,
        'export_all': False,
        'manage_users': False,
        'ml_training': False
    }
}


def get_db_connection():
    """Get database connection"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def generate_token(user_id, username, role):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def authenticate_user(username, password):
    """Authenticate user and return user data"""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT user_id, username, email, password_hash, role, full_name, is_active FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            return None
        
        if not user['is_active']:
            return None
        
        if not verify_password(password, user['password_hash']):
            return None
        
        # Update last login
        cursor.execute(
            "UPDATE users SET last_login = %s WHERE user_id = %s",
            (datetime.now(), user['user_id'])
        )
        conn.commit()
        
        return {
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'full_name': user['full_name']
        }
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT user_id, username, email, role, full_name, is_active FROM users WHERE user_id = %s",
            (user_id,)
        )
        return cursor.fetchone()
    except Exception as e:
        print(f"Error getting user: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header'}), 401
        
        # Check for token in cookies
        if not token:
            token = request.cookies.get('auth_token')
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user info to request context
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated_function


def require_role(*allowed_roles):
    """Decorator to require specific role(s)"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user_role = request.current_user.get('role')
            if user_role not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def has_permission(user_role, permission):
    """Check if user role has a specific permission"""
    return ROLE_PERMISSIONS.get(user_role, {}).get(permission, False)


def encrypt_pii(data):
    """Encrypt PII data (simplified - use proper encryption in production)"""
    # In production, use proper encryption like AES-256
    # For now, this is a placeholder
    import base64
    from cryptography.fernet import Fernet
    import os
    
    # Get or create encryption key
    key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key().decode())
    if isinstance(key, str):
        key = key.encode()
    
    f = Fernet(key)
    encrypted = f.encrypt(data.encode() if isinstance(data, str) else data)
    return base64.b64encode(encrypted).decode()


def decrypt_pii(encrypted_data):
    """Decrypt PII data"""
    import base64
    from cryptography.fernet import Fernet
    import os
    
    key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key().decode())
    if isinstance(key, str):
        key = key.encode()
    
    try:
        f = Fernet(key)
        decrypted = base64.b64decode(encrypted_data)
        return f.decrypt(decrypted).decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return None

