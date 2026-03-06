# Database Migrations

This directory contains database migration scripts for the licensing system.

## Quick Start - Fresh Database

For a **new database**, run the complete schema migration:

```bash
python migrations/000_complete_schema.py
```

This will create all tables and a default admin user:
- **Email:** newadmin@test.com
- **Password:** admin123

## Migration Files

| File | Description |
|------|-------------|
| `000_complete_schema.py` | Creates entire database from scratch (recommended for fresh setup) |
| `001_security_auth.py` | Users, API keys, IP whitelist tables |
| `002_machine_binding.py` | Machine binding (license_machines table) |
| `003_audit_logs.py` | Audit logs table |

## Running Migrations

### Option 1: Complete Schema (Recommended for Fresh DB)
```bash
python migrations/000_complete_schema.py
```

### Option 2: Individual Migrations (For Existing DB)
```bash
python migrations/001_security_auth.py
python migrations/002_machine_binding.py
python migrations/003_audit_logs.py
```

### Option 3: Docker
The `entrypoint.sh` automatically runs migrations when the container starts.

## Drop and Recreate

To drop all tables and recreate from scratch:

```bash
python migrations/000_complete_schema.py --drop
```

⚠️ **Warning:** This will delete all data!

## Database Schema

```
users
├── id (PK)
├── email
├── password_hash
├── is_admin
└── created_at

api_keys
├── id (PK)
├── key_id
├── hashed_key
├── secret_hash
├── name
├── user_id (FK)
├── created_at
├── expires_at
└── is_active

ip_whitelist
├── id (PK)
├── ip_address
├── api_key_id (FK)
└── created_at

products
├── id (PK)
├── name
├── description
├── created_at
└── is_active

licenses
├── id (PK)
├── license_key
├── company_name
├── license_type
├── email_comp
├── creation_date
├── activation_date
├── expiry_date
├── period_in_days
├── period_in_sec
├── period_in_uni_epoch
├── state
├── grace_period_in_days
├── is_revoked
├── revoked_reason
├── product_id (FK)
├── signature_hex
├── license_id_hex
└── max_machines

license_machines
├── id (PK)
├── license_key
├── product_id
├── mac_address
├── machine_name
├── bound_at
├── last_seen_at
└── is_active

audit_logs
├── id (PK)
├── event_type
├── license_key
├── machine_id
├── mac_address
├── ip_address
├── user_agent
├── success
├── details (JSONB)
├── is_offline
└── timestamp
```

## Environment Variables

Make sure your `.env` file has the correct database credentials:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=licenses_db
DB_USER=admin
DB_PASSWORD=your_password_here
```
