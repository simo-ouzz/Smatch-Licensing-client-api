"""
Database migration script for Security & Authentication tables.
Run this script to create the necessary tables.

Note: This migration is superseded by 000_complete_schema.py
Use that file for a fresh database setup.
"""

import os
import psycopg2
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "licenses_db"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "@@MOHAMMED12@@
    )


def run_migration():
    print("Starting database migration...")
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Create users table
            print("Creating users table...")
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
            cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            
            # Create api_keys table
            print("Creating api_keys table...")
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
            
            # Create ip_whitelist table
            print("Creating ip_whitelist table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ip_whitelist (
                    id SERIAL PRIMARY KEY,
                    ip_address VARCHAR(45) NOT NULL,
                    api_key_id INTEGER REFERENCES api_keys(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("Migration completed successfully!")


def create_admin_user(email: str = "newadmin@test.com", password: str = "admin123"):
    """Create a default admin user if not exists."""
    password_hash = pwd_context.hash(password)
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                print(f"Admin user already exists: {email}")
                return
            
            cur.execute("""
                INSERT INTO users (email, password_hash, is_admin)
                VALUES (%s, %s, %s)
            """, (email, password_hash, True))
            
            conn.commit()
            print(f"Admin user created: {email} / {password}")


if __name__ == "__main__":
    run_migration()
    create_admin_user()
