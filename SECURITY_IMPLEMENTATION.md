# Security & Authentication Implementation

## ✅ Completed Features

### 1. User Authentication with JWT Tokens
- **JWT-based authentication** using PyJWT
- **Token expiration**: 24 hours
- **Secure token storage**: HttpOnly cookies + localStorage
- **Token validation** on all protected routes

### 2. Role-Based Access Control (RBAC)
Three user roles with different permissions:

#### Admin
- ✅ Full access to all features
- ✅ User management
- ✅ Data entry and ETL
- ✅ ML training and predictions
- ✅ Export all data

#### Analyst
- ✅ Dashboard and analytics
- ✅ Data entry and ETL
- ✅ ML training and predictions
- ✅ Export all data
- ❌ User management

#### Doctor
- ✅ Dashboard (limited)
- ✅ View patients and visits
- ✅ Data entry (own patients)
- ✅ ML predictions
- ❌ Analytics
- ❌ Export all data
- ❌ ML training
- ❌ ETL uploads

### 3. API Rate Limiting
- **Per-endpoint rate limits**:
  - Authentication: 5 requests / 15 minutes
  - Export: 10 requests / 60 minutes
  - ML: 20 requests / 60 minutes
  - Upload: 5 requests / 60 minutes
  - Default: 100 requests / 15 minutes
- **IP-based and user-based tracking**
- **Automatic cleanup** of old records

### 4. PII Data Encryption
- **Encryption service** using Fernet (symmetric encryption)
- **Encryption key** stored in environment variable
- **Functions available** for encrypting/decrypting sensitive data
- **Ready for integration** with patient data fields

## 📁 Files Created/Modified

### New Files
1. `services/auth_service.py` - Authentication and authorization logic
2. `services/rate_limiter.py` - API rate limiting
3. `database/auth_schema.sql` - User and session tables
4. `database/create_default_users.py` - Script to create default users
5. `templates/login.html` - Login page
6. `setup_auth.py` - Setup script for authentication

### Modified Files
1. `app.py` - Added authentication decorators to all API routes
2. `static/js/app.js` - Added authentication logic and token management
3. `templates/index.html` - Added logout button and user info
4. `static/css/style.css` - Added styles for logout button
5. `requirements.txt` - Already includes required packages

## 🚀 Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database
```bash
# Run main schema
mysql -u root -p healthcare_analytics < database/schema.sql

# Run auth schema
mysql -u root -p healthcare_analytics < database/auth_schema.sql

# Create default users
python database/create_default_users.py
```

Or use the setup script:
```bash
python setup_auth.py
```

### 3. Set Environment Variables (Optional)
```bash
# For production, set these:
export JWT_SECRET_KEY="your-secret-key-here"
export ENCRYPTION_KEY="your-encryption-key-here"
```

### 4. Run Application
```bash
python app.py
```

## 🔐 Default Credentials

**⚠️ CHANGE THESE IN PRODUCTION!**

- **Admin**: `admin` / `admin123`
- **Analyst**: `analyst1` / `admin123`
- **Doctor**: `doctor1` / `admin123`

## 🔒 Security Features

### Authentication Flow
1. User submits credentials on login page
2. Server validates credentials against database
3. JWT token generated with user info and role
4. Token stored in HttpOnly cookie and localStorage
5. Token included in Authorization header for all API requests
6. Server validates token on each request

### Protected Routes
All API endpoints (except `/api/auth/login`) require authentication:
- `@require_auth` - Requires valid JWT token
- `@require_role('admin', 'analyst')` - Requires specific role(s)
- `@rate_limit` - Applies rate limiting

### Rate Limiting
- Tracks requests per user/IP per endpoint
- Returns 429 (Too Many Requests) when limit exceeded
- Includes `X-RateLimit-Remaining` header

### PII Encryption
- Ready-to-use encryption functions
- Can be integrated with patient data fields
- Uses Fernet symmetric encryption
- Key stored in environment variable

## 📝 Usage Examples

### Frontend - Check Authentication
```javascript
// Token automatically added to all fetch requests
fetch('/api/dashboard/stats')
  .then(response => response.json())
  .then(data => console.log(data));
```

### Backend - Protect Route
```python
@app.route('/api/sensitive-data')
@require_auth
@require_role('admin')
@rate_limit
def get_sensitive_data():
    return jsonify({'data': 'sensitive'})
```

### Encrypt PII
```python
from services.auth_service import encrypt_pii, decrypt_pii

# Encrypt
encrypted_phone = encrypt_pii(patient_phone)

# Decrypt (only authorized users)
phone = decrypt_pii(encrypted_phone)
```

## ⚠️ Security Best Practices

1. **Change default passwords** in production
2. **Use strong JWT secret key** (at least 32 characters)
3. **Use HTTPS** in production
4. **Set secure cookie flags** (already implemented)
5. **Rotate encryption keys** periodically
6. **Monitor rate limit violations**
7. **Log authentication failures**
8. **Implement password complexity requirements**
9. **Add two-factor authentication** (future enhancement)
10. **Regular security audits**

## 🔄 Next Steps

1. Add password reset functionality
2. Implement session management
3. Add audit logging
4. Implement two-factor authentication
5. Add password complexity requirements
6. Add account lockout after failed attempts
7. Implement OAuth2 for external authentication

