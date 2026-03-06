"""
Database migration for License Audit Logs.
Run this script to add audit logging support.

Note: This migration is superseded by 000_complete_schema.py
Use that file for a fresh database setup.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "licenses_db"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "default_password")
    )


def run_migration():
    print("Starting audit logs migration...")
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Create audit_logs table
            print("Creating audit_logs table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(100) NOT NULL,
                    license_key VARCHAR(255),
                    machine_id VARCHAR(255),
                    mac_address VARCHAR(17),
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    details JSONB,
                    is_offline BOOLEAN DEFAULT FALSE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            print("Creating indexes...")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_license_key 
                ON audit_logs(license_key)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type 
                ON audit_logs(event_type)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp 
                ON audit_logs(timestamp DESC)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_is_offline 
                ON audit_logs(is_offline)
            """)
            
            conn.commit()
            print("Migration completed successfully!")


if __name__ == "__main__":
    run_migration()
