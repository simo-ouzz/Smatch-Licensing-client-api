"""
Complete Database Schema Migration
=================================
This migration creates all tables needed for the licensing system.
Run this file to create the entire database from scratch.

Usage:
    python migrations/000_complete_schema.py

Or import and run:
    from migrations.000_complete_schema import run_migration
    run_migration()
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Get database connection using environment variables."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "licenses_db"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "@@MOHAMMED12@@
    )


def run_migration(drop_existing: bool = False):
    """
    Run the complete database migration.
    
    Args:
        drop_existing: If True, drops existing tables before creating new ones.
                     Use with caution - all data will be lost!
    """
    print("=" * 60)
    print("Starting Complete Database Migration")
    print("=" * 60)
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        if drop_existing:
            print("\n⚠️  Dropping existing tables (if any)...")
            cur.execute("DROP TABLE IF EXISTS audit_logs CASCADE")
            cur.execute("DROP TABLE IF EXISTS license_machines CASCADE")
            cur.execute("DROP TABLE IF EXISTS licenses CASCADE")
            cur.execute("DROP TABLE IF EXISTS products CASCADE")
            cur.execute("DROP TABLE IF EXISTS ip_whitelist CASCADE")
            cur.execute("DROP TABLE IF EXISTS api_keys CASCADE")
            cur.execute("DROP TABLE IF EXISTS users CASCADE")
            conn.commit()
            print("✅ Existing tables dropped")
        
        # ========================================
        # USERS TABLE
        # ========================================
        print("\n📋 Creating users table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create users index
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email 
            ON users(email)
        """)
        print("✅ users table created")
        
        # ========================================
        # API KEYS TABLE
        # ========================================
        print("📋 Creating api_keys table...")
        cur.execute("""
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
        """)
        
        # Create api_keys indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_key_id ON api_keys(key_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active)")
        print("✅ api_keys table created")
        
        # ========================================
        # IP WHITELIST TABLE
        # ========================================
        print("📋 Creating ip_whitelist table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ip_whitelist (
                id SERIAL PRIMARY KEY,
                ip_address VARCHAR(45) NOT NULL,
                api_key_id INTEGER REFERENCES api_keys(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ip_whitelist_api_key ON ip_whitelist(api_key_id)")
        print("✅ ip_whitelist table created")
        
        # ========================================
        # PRODUCTS TABLE
        # ========================================
        print("📋 Creating products table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active)")
        print("✅ products table created")
        
        # ========================================
        # LICENSES TABLE
        # ========================================
        print("📋 Creating licenses table...")
        cur.execute("""
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
        """)
        
        # Create licenses indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_licenses_license_key ON licenses(license_key)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_licenses_product_id ON licenses(product_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_licenses_state ON licenses(state)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_licenses_expiry_date ON licenses(expiry_date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_licenses_email_comp ON licenses(email_comp)")
        print("✅ licenses table created")
        
        # ========================================
        # LICENSE MACHINES TABLE (Machine Binding)
        # ========================================
        print("📋 Creating license_machines table...")
        cur.execute("""
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
        """)
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_license_machines_license_key ON license_machines(license_key)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_license_machines_mac_address ON license_machines(mac_address)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_license_machines_product_id ON license_machines(product_id)")
        print("✅ license_machines table created")
        
        # ========================================
        # AUDIT LOGS TABLE
        # ========================================
        print("📋 Creating audit_logs table...")
        cur.execute("""
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
        """)
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_license_key ON audit_logs(license_key)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_is_offline ON audit_logs(is_offline)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_mac_address ON audit_logs(mac_address)")
        print("✅ audit_logs table created")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✅ Complete Database Migration Finished Successfully!")
        print("=" * 60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def create_admin_user(email: str = "newadmin@test.com", password: str = "admin123"):
    """Create default admin user if not exists."""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    password_hash = pwd_context.hash(password)
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            print(f"ℹ️  Admin user already exists: {email}")
            return
        
        cur.execute("""
            INSERT INTO users (email, password_hash, is_admin)
            VALUES (%s, %s, %s)
        """, (email, password_hash, True))
        
        conn.commit()
        print(f"✅ Admin user created: {email} / {password}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to create admin user: {e}")
    finally:
        cur.close()
        conn.close()


def create_sample_product():
    """Create a sample product if none exists."""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id FROM products LIMIT 1")
        if cur.fetchone():
            print("ℹ️  Products already exist, skipping sample product creation")
            return
        
        cur.execute("""
            INSERT INTO products (name, description, is_active)
            VALUES (%s, %s, %s)
        """, ("Default Product", "Sample product for licensing", True))
        
        conn.commit()
        print("✅ Sample product created")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to create sample product: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Complete Database Migration")
    parser.add_argument("--drop", action="store_true", 
                       help="Drop existing tables before creating new ones (WARNING: all data will be lost!)")
    parser.add_argument("--skip-admin", action="store_true",
                       help="Skip admin user creation")
    parser.add_argument("--skip-product", action="store_true",
                       help="Skip sample product creation")
    
    args = parser.parse_args()
    
    run_migration(drop_existing=args.drop)
    
    if not args.skip_admin:
        create_admin_user()
    
    if not args.skip_product:
        create_sample_product()
    
    print("\n🎉 Database setup complete!")
