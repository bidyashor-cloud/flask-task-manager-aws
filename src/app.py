from flask import Flask, render_template_string, request, jsonify
import pymysql.cursors
from pymysql import pooling
import os
import logging
import time
from datetime import datetime
from contextlib import contextmanager

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Secure Database Configuration (loaded from environment variables)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'your-database-endpoint'),
    'user': os.getenv('DB_USER', 'your-username'),
    'password': os.getenv('DB_PASSWORD', 'your-password'),
    'database': os.getenv('DB_NAME', 'your-database'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'charset': 'utf8mb4',
    'autocommit': True
}

# ✅ Create connection pool (safe for production)
connection_pool = pooling.ConnectionPool(
    size=5,
    name='flask_pool',
    **DB_CONFIG
)

# Application metrics
app_metrics = {
    'requests_total': 0,
    'requests_success': 0,
    'requests_error': 0,
    'db_connections_total': 0,
    'db_connections_success': 0,
    'db_connections_error': 0,
    'start_time': time.time()
}

@contextmanager
def get_db_connection():
    """Context manager for database connections with automatic cleanup"""
    connection = None
    try:
        app_metrics['db_connections_total'] += 1
        connection = connection_pool.get_connection()
        app_metrics['db_connections_success'] += 1
        yield connection
    except Exception as e:
        app_metrics['db_connections_error'] += 1
        logger.error(f"Database connection error: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()

def check_db():
    """Database health check with connection pooling"""
    start_time = time.time()
    try:
        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        duration = round((time.time() - start_time) * 1000, 2)
        return True, f"Connected ✅ ({duration}ms)"
    except Exception as e:
        duration = round((time.time() - start_time) * 1000, 2)
        return False, f"Error ({duration}ms): {str(e)}"

def get_connection_pool_stats():
    """Get connection pool statistics"""
    try:
        return {
            'pool_size': connection_pool.size,
            'pool_name': connection_pool.name,
        }
    except Exception as e:
        return {'error': str(e)}

@app.before_request
def before_request():
    app_metrics['requests_total'] += 1
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if response.status_code < 400:
        app_metrics['requests_success'] += 1
    else:
        app_metrics['requests_error'] += 1
    return response

@app.route('/')
def home():
    db_connected, db_message = check_db()
    pool_stats = get_connection_pool_stats()
    return render_template_string('''
    <html>
    <head><title>Flask Task Manager</title></head>
    <body style="font-family: Arial; margin: 40px;">
        <h1>🚀 Flask Task Manager</h1>
        <div style="background:#e7f3ff;padding:10px;border-radius:5px;">
            <strong>Database:</strong> {{ db_message }}<br>
            <strong>Connection Pool:</strong> {{ pool_stats.pool_size }} connections
        </div>
        <p><strong>Architecture:</strong> Multi-Tier Flask + AWS (EC2, RDS, ALB)</p>
        <button onclick="window.open('/health')">Health Check</button>
        <button onclick="window.open('/metrics')">Metrics</button>
    </body>
    </html>
    ''',
    db_connected=db_connected,
    db_message=db_message,
    pool_stats=pool_stats
    )

@app.route('/health')
def health():
    db_connected, db_message = check_db()
    pool_stats = get_connection_pool_stats()
    status = 'healthy' if db_connected else 'unhealthy'
    return jsonify({
        'status': status,
        'database': db_message,
        'pool_stats': pool_stats,
        'timestamp': datetime.utcnow().isoformat()
    }), 200 if db_connected else 503

@app.route('/metrics')
def metrics():
    uptime = time.time() - app_metrics['start_time']
    return jsonify({
        'uptime_seconds': uptime,
        'requests': {
            'total': app_metrics['requests_total'],
            'success': app_metrics['requests_success'],
            'error': app_metrics['requests_error']
        },
        'database': {
            'connections_total': app_metrics['db_connections_total'],
            'success': app_metrics['db_connections_success'],
            'error': app_metrics['db_connections_error']
        }
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
