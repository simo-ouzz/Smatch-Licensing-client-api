#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 2
done

echo "PostgreSQL is up - running migrations..."

cd /app

echo "Running migrations..."
python -c "
from Cryptographyyy import get_connection

conn = get_connection()
cur = conn.cursor()

# Users table
cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        is_admin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# API Keys table
cur.execute('''
    CREATE TABLE IF NOT EXISTS api_keys (
        id SERIAL PRIMARY KEY,
        key_id VARCHAR(50) UNIQUE NOT NULL,
        hashed_key VARCHAR(255) NOT NULL,
        secret_hash VARCHAR(255),
        name VARCHAR(255),
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    )
''')

# IP Whitelist table
cur.execute('''
    CREATE TABLE IF NOT EXISTS ip_whitelist (
        id SERIAL PRIMARY KEY,
        ip_address VARCHAR(45) NOT NULL,
        api_key_id INTEGER REFERENCES api_keys(id) ON DELETE CASCADE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Products table
cur.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    )
''')

# Licenses table
cur.execute('''
    CREATE TABLE IF NOT EXISTS licenses (
        id SERIAL PRIMARY KEY,
        license_key VARCHAR(255) UNIQUE NOT NULL,
        company_name VARCHAR(255),
        license_type VARCHAR(50),
        email_comp VARCHAR(255),
        creation_date TIMESTAMP,
        activation_date TIMESTAMP,
        expiry_date TIMESTAMP,
        period_in_days INTEGER,
        period_in_sec INTEGER,
        period_in_uni_epoch INTEGER,
        state VARCHAR(50),
        grace_period_in_days INTEGER,
        is_revoked BOOLEAN DEFAULT FALSE,
        revoked_reason VARCHAR(512),
        product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
        signature_hex TEXT,
        license_id_hex VARCHAR(255),
        max_machines INTEGER DEFAULT -1
    )
''')

# License Machines table (for machine binding)
cur.execute('''
    CREATE TABLE IF NOT EXISTS license_machines (
        id SERIAL PRIMARY KEY,
        license_key VARCHAR(255) NOT NULL,
        product_id INTEGER,
        mac_address VARCHAR(17) NOT NULL,
        machine_name VARCHAR(255),
        bound_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen_at TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE,
        UNIQUE(license_key, mac_address)
    )
''')

# Audit Logs table
cur.execute('''
    CREATE TABLE IF NOT EXISTS audit_logs (
        id SERIAL PRIMARY KEY,
        event_type VARCHAR(100) NOT NULL,
        license_key VARCHAR(255),
        machine_id VARCHAR(255),
        mac_address VARCHAR(17),
        ip_address VARCHAR(45),
        user_agent TEXT,
        is_offline BOOLEAN DEFAULT FALSE,
        success BOOLEAN DEFAULT TRUE,
        details JSONB,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Create indexes
cur.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_key_id ON api_keys(key_id)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_licenses_license_key ON licenses(license_key)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_licenses_product_id ON licenses(product_id)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_licenses_state ON licenses(state)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_licenses_expiry_date ON licenses(expiry_date)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_license_machines_license_key ON license_machines(license_key)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_license_machines_mac_address ON license_machines(mac_address)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_license_key ON audit_logs(license_key)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_is_offline ON audit_logs(is_offline)')

conn.commit()
cur.close()
conn.close()

print('Database tables created/verified successfully!')
"

# Create default admin user if not exists
python -c "
from licensing_api.services.auth_service import get_password_hash
from Cryptographyyy import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute('SELECT id FROM users WHERE email = %s', ('newadmin@test.com',))
if not cur.fetchone():
    password_hash = get_password_hash('admin123')
    cur.execute('''
        INSERT INTO users (email, password_hash, is_admin)
        VALUES (%s, %s, %s)
    ''', ('newadmin@test.com', password_hash, True))
    conn.commit()
    print('Default admin user created: newadmin@test.com / admin123')
else:
    print('Admin user already exists')

cur.close()
conn.close()
"

# Create sample product if not exists
python -c "
from Cryptographyyy import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute('SELECT id FROM products LIMIT 1')
if not cur.fetchone():
    cur.execute('''
        INSERT INTO products (name, description, is_active)
        VALUES (%s, %s, %s)
    ''', ('Default Product', 'Sample product for licensing', True))
    conn.commit()
    print('Sample product created')
else:
    print('Products already exist')

cur.close()
conn.close()
"

echo "Starting uvicorn server..."
exec uvicorn licensing_api.main:app --host 0.0.0.0 --port 8000
