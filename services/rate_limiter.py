"""
API Rate Limiting Service
Implements rate limiting to prevent abuse
"""

from datetime import datetime, timedelta
import mysql.connector
from config import DB_CONFIG

# Rate limit configurations
RATE_LIMITS = {
    'default': {'requests': 100, 'window_minutes': 15},
    'auth': {'requests': 5, 'window_minutes': 15},
    'export': {'requests': 10, 'window_minutes': 60},
    'ml': {'requests': 20, 'window_minutes': 60},
    'upload': {'requests': 5, 'window_minutes': 60}
}


def get_db_connection():
    """Get database connection"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def get_rate_limit_config(endpoint):
    """Get rate limit configuration for an endpoint"""
    if '/api/auth/' in endpoint:
        return RATE_LIMITS['auth']
    elif '/export' in endpoint or 'export' in endpoint:
        return RATE_LIMITS['export']
    elif '/api/ml/' in endpoint:
        return RATE_LIMITS['ml']
    elif '/upload' in endpoint or 'ingestion' in endpoint:
        return RATE_LIMITS['upload']
    else:
        return RATE_LIMITS['default']


def check_rate_limit(user_id, ip_address, endpoint):
    """Check if request is within rate limit"""
    conn = get_db_connection()
    if not conn:
        return True, 0  # Allow if DB connection fails
    
    cursor = conn.cursor(dictionary=True)
    try:
        config = get_rate_limit_config(endpoint)
        window_start = datetime.now() - timedelta(minutes=config['window_minutes'])
        
        # Clean old records
        cursor.execute(
            "DELETE FROM api_rate_limits WHERE window_start < %s",
            (window_start,)
        )
        
        # Check current count
        if user_id:
            cursor.execute(
                """SELECT SUM(request_count) as total 
                   FROM api_rate_limits 
                   WHERE user_id = %s AND endpoint = %s AND window_start >= %s""",
                (user_id, endpoint, window_start)
            )
        else:
            cursor.execute(
                """SELECT SUM(request_count) as total 
                   FROM api_rate_limits 
                   WHERE ip_address = %s AND endpoint = %s AND window_start >= %s""",
                (ip_address, endpoint, window_start)
            )
        
        result = cursor.fetchone()
        current_count = result['total'] or 0
        
        if current_count >= config['requests']:
            conn.commit()
            return False, config['requests'] - current_count
        
        # Increment counter
        window_start = datetime.now()
        if user_id:
            # Check if record exists
            cursor.execute(
                """SELECT id, request_count FROM api_rate_limits 
                   WHERE user_id = %s AND endpoint = %s AND window_start >= %s
                   ORDER BY window_start DESC LIMIT 1""",
                (user_id, endpoint, window_start - timedelta(minutes=config['window_minutes']))
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE api_rate_limits SET request_count = request_count + 1 WHERE id = %s",
                    (existing['id'],)
                )
            else:
                cursor.execute(
                    """INSERT INTO api_rate_limits (user_id, ip_address, endpoint, request_count, window_start)
                       VALUES (%s, %s, %s, 1, %s)""",
                    (user_id, ip_address, endpoint, window_start)
                )
        else:
            # Check if record exists
            cursor.execute(
                """SELECT id, request_count FROM api_rate_limits 
                   WHERE ip_address = %s AND endpoint = %s AND window_start >= %s
                   ORDER BY window_start DESC LIMIT 1""",
                (ip_address, endpoint, window_start - timedelta(minutes=config['window_minutes']))
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE api_rate_limits SET request_count = request_count + 1 WHERE id = %s",
                    (existing['id'],)
                )
            else:
                cursor.execute(
                    """INSERT INTO api_rate_limits (ip_address, endpoint, request_count, window_start)
                       VALUES (%s, %s, 1, %s)""",
                    (ip_address, endpoint, window_start)
                )
        
        conn.commit()
        remaining = config['requests'] - current_count - 1
        return True, remaining
        
    except Exception as e:
        print(f"Rate limit check error: {e}")
        conn.rollback()
        return True, 0  # Allow on error
    finally:
        cursor.close()
        conn.close()


def rate_limit(f):
    """Decorator for rate limiting"""
    from functools import wraps
    from flask import request, jsonify
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = None
        if hasattr(request, 'current_user'):
            user_id = request.current_user.get('user_id')
        
        ip_address = request.remote_addr
        endpoint = request.endpoint or request.path
        
        allowed, remaining = check_rate_limit(user_id, ip_address, endpoint)
        
        if not allowed:
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': f'Too many requests. Please try again later.',
                'retry_after': 60
            }), 429
        
        # Add rate limit headers
        response = f(*args, **kwargs)
        if hasattr(response, 'headers'):
            response.headers['X-RateLimit-Remaining'] = str(remaining)
        return response
    
    return decorated_function

