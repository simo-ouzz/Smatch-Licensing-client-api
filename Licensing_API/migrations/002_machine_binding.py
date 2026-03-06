"""
Database migration for Multi-Machine License Binding.
Run this script to add machine binding support.

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
    print("Starting machine binding migration...")
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Add max_machines column to licenses if not exists
            print("Adding max_machines column to licenses...")
            cur.execute("""
                ALTER TABLE licenses 
                ADD COLUMN IF NOT EXISTS max_machines INTEGER DEFAULT -1
            """)
            
            # Add revoked_reason column if not exists
            print("Adding revoked_reason column to licenses...")
            cur.execute("""
                ALTER TABLE licenses 
                ADD COLUMN IF NOT EXISTS revoked_reason VARCHAR(512)
            """)
            
            # Create license_machines table (rename from machines if exists)
            print("Creating license_machines table...")
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
            
            # Create indexes
            print("Creating indexes...")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_license_machines_license_key 
                ON license_machines(license_key)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_license_machines_mac_address 
                ON license_machines(mac_address)
            """)
            
            conn.commit()
            print("Migration completed successfully!")


if __name__ == "__main__":
    run_migration()
