"""
Configuration file for Healthcare Analytics Data Warehouse
Update these settings according to your MySQL setup
"""

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Change this to your MySQL password (empty for no password)
    'database': 'healthcare_analytics'
}

# Flask Configuration
FLASK_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True
}

# Application Settings
APP_NAME = 'Healthcare Analytics Data Warehouse'
APP_VERSION = '1.0.0'

