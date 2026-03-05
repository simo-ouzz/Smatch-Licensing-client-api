"""
Database migration script for Security & Authentication tables.
Run this script to create the necessary tables.
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
        port=os.getenv("DB_PORT", 5432),
        database=os.getenv("DB_NAME", "licenses_db"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "@@MOHAMMED12@@")
    )


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def run_migration():
    print("Starting database migration...")
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Create users table
            print("Creating users table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'user',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create refresh_tokens table
            print("Creating refresh_tokens table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    token_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                    token_hash VARCHAR(255) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create api_keys table
            print("Creating api_keys table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                    key_hash VARCHAR(255) NOT NULL,
                    secret_hash VARCHAR(255),
                    name VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP
                );
            """)
            
            # Create index on refresh_tokens for faster lookups
            print("Creating indexes...")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id 
                ON refresh_tokens(user_id);
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash 
                ON refresh_tokens(token_hash);
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_user_id 
                ON api_keys(user_id);
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash 
                ON api_keys(key_hash);
            """)
            
            conn.commit()
            print("Migration completed successfully!")


def create_admin_user():
    """Create a default admin user if not exists."""
    import hashlib
    import secrets
    
    password = "admin"
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    password_hash = f"$pbkdf2-sha256${salt}${password_hash}"
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check if admin exists
            cur.execute("SELECT user_id FROM users WHERE email = 'admin@example.com'")
            if cur.fetchone():
                print("Admin user already exists.")
                return
            
            # Create admin user
            cur.execute("""
                INSERT INTO users (email, password_hash, role, is_active)
                VALUES (%s, %s, %s, %s)
            """, ("admin@example.com", password_hash, "admin", True))
            
            conn.commit()
            print("Admin user created: admin@licensing.api / admin123")


if __name__ == "__main__":
    run_migration()
    create_admin_user()
