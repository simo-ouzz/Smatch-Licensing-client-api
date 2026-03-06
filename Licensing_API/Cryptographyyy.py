import os
import base64
import secrets
import psycopg2
from typing import Optional
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError
from datetime import datetime, timedelta, timezone

# Offline license secret key for HMAC checksum
# In production, generate a random key: secrets.token_hex(32)
OFFLINE_SECRET_KEY = os.getenv("OFFLINE_SECRET_KEY", "default_dev_secret_key_change_in_production")



def get_connection():
    return psycopg2.connect(
        host = os.getenv("DB_HOST", "localhost"),
        port = os.getenv("DB_PORT", 5432),
        database = os.getenv("DB_NAME", "licenses_db"),
        user = os.getenv("DB_USER", "admin"),
        password = os.getenv("DB_PASSWORD", "@@MOHAMMED12@@")
    )

def insert_license(
    license_key,
    license_id_hex,
    signature_hex,
    company_name,
    email_comp,
    product_id,
    license_type,
    period_days,
    grace_period_days,
    max_machines = -1
):

    creation_date = datetime.now(timezone.utc)
    expiry_date = creation_date + timedelta(days=period_days)

    period_in_sec = period_days * 86400
    period_in_unix_epoch = int(expiry_date.timestamp())

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO public.licenses (
                    license_key,
                    company_name,
                    license_type,
                    email_comp,
                    creation_date,
                    activation_date,
                    expiry_date,
                    period_in_days,
                    period_in_sec,
                    period_in_uni_epoch,
                    state,
                    grace_period_in_days,
                    is_revoked,
                    product_id,
                    signature_hex,
                    license_id_hex,
                    max_machines
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
            """, (
                license_key,
                company_name,
                license_type,
                email_comp,
                creation_date,
                None,
                expiry_date,
                period_days,
                period_in_sec,
                period_in_unix_epoch,
                "inactive",
                grace_period_days,
                False,
                product_id,
                signature_hex,
                license_id_hex,
                max_machines
            ))
# ==========================================================
# STEP 1: GENERATE KEYPAIR (RUN ONCE, THEN SAVE KEYS)
# ==========================================================

def generate_keypair():
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key

    print("PRIVATE KEY (STORE SECURELY):")
    print(signing_key.encode().hex())

    print("\nPUBLIC KEY (SAFE TO DISTRIBUTE):")
    print(verify_key.encode().hex())


# Uncomment once to generate keys
#generate_keypair()
# exit()


# ==========================================================
# 🔐 CONFIG (PASTE YOUR REAL KEYS HERE)
# ==========================================================

PRIVATE_KEY_HEX = os.getenv("PRIVATE_KEY_HEX", "110bae3e844f7f41a0d692c01cefe1cc7384ab927b155319cb7469f624abb7da")
PUBLIC_KEY_HEX = os.getenv("PUBLIC_KEY_HEX", "53b12a371b91d92c80d4afb8c12bbc3af00c1b426c4f0f1a78f1eac2239bfd9c")

signing_key = SigningKey(bytes.fromhex(PRIVATE_KEY_HEX))
verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY_HEX))


# ==========================================================
# LICENSE GENERATION (BACKEND ONLY)
# ==========================================================

def generate_license():
    # 16 random bytes (128 bits)
    license_id_bytes = secrets.token_bytes(16)

    # Base32 encode
    encoded = base64.b32encode(license_id_bytes).decode().rstrip("=")

    # Force exactly 25 characters
    encoded = encoded[:25]

    # Format XXXXX_XXXXX_XXXXX_XXXXX_XXXXX
    formatted_key = "_".join(
        encoded[i:i+5] for i in range(0, 25, 5)
    )

    # Sign FULL 16 bytes (NOT the trimmed string)
    signature = signing_key.sign(license_id_bytes).signature

    return {
        "license_key": formatted_key,
        "license_id_hex": license_id_bytes.hex(),
        "signature_hex": signature.hex()
    }


# ==========================================================
# LICENSE VERIFICATION
# ==========================================================

def verify_license(license_key, license_id_hex, signature_hex):
    try:
        license_id_bytes = bytes.fromhex(license_id_hex)
        signature = bytes.fromhex(signature_hex)

        # 1️⃣ Verify signature cryptographically
        verify_key.verify(license_id_bytes, signature)

        # 2️⃣ Ensure license_key matches ID
        encoded = base64.b32encode(license_id_bytes).decode().rstrip("=")
        encoded = encoded[:25]

        expected_key = "_".join(
            encoded[i:i+5] for i in range(0, 25, 5)
        )

        if expected_key != license_key:
            return False

        return True

    except BadSignatureError:
        return False
    except Exception:
        return False

def create_license():

    print("=== CREATE NEW LICENSE ===")

    company_name = input("Company Name: ").strip()
    email_comp = input("Company Email: ").strip()
    product_id = int(input("Product ID: "))
    license_type = input("License Type (enum value): ").strip()
    period_in_days = int(input("License period (days): "))
    grace_period_days = int(input("Grace period (default 0): ") or 0)

    license_key, license_id_hex, signature_hex = generate_license()

    creation_date = datetime.utcnow()
    expiry_date = creation_date + timedelta(days=period_in_days)

    period_in_sec = period_in_days * 86400
    period_in_unix_epoch = int(expiry_date.timestamp())

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    INSERT INTO public.licenses (
                        license_key,
                        company_name,
                        license_type,
                        email_comp,
                        creation_date,
                        activation_date,
                        expiry_date,
                        period_in_days,
                        period_in_sec,
                        period_in_uni_epoch,
                        state,
                        grace_period_in_days,
                        is_revoked,
                        product_id,
                        signature_hex,
                        license_id_hex
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                """, (
                    license_key,
                    company_name,
                    license_type,
                    email_comp,
                    creation_date,
                    None,
                    expiry_date,
                    period_in_days,
                    period_in_sec,
                    period_in_unix_epoch,
                    "inactive",
                    grace_period_days,
                    False,
                    product_id,
                    signature_hex,
                    license_id_hex
                ))

        print("\n✅ License created successfully!")
        print("License Key:", license_key)
        print("Expires at:", expiry_date)

    except psycopg2.errors.UniqueViolation:
        print("❌ License collision occurred (very rare). Try again.")

    except Exception as e:
        print("❌ Database error:", e)

# ==========================================================
# HELPER: Remaining Time
# ==========================================================

def calculate_remaining(expiry_date):
    now = datetime.now(timezone.utc)

    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)

    delta = expiry_date - now
    seconds = int(delta.total_seconds())
    days = seconds // 86400

    return max(seconds, 0), max(days, 0)


# ==========================================================
# 1️⃣ GET LICENSE DETAILS
# ==========================================================

def get_license_details(license_key):

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    l.license_key,
                    l.company_name,
                    l.email_comp,
                    l.license_type,
                    l.state,
                    l.is_revoked,
                    l.revoked_reason,
                    l.creation_date,
                    l.activation_date,
                    l.expiry_date,
                    l.grace_period_in_days,
                    p.product_id,
                    l.license_id_hex,
                    l.signature_hex,
                    l.max_machines
                FROM public.licenses l
                JOIN public.products p 
                    ON l.product_id = p.product_id
                WHERE l.license_key = %s
            """, (license_key,))

            row = cur.fetchone()

    if not row:
        return None

    remaining_sec, remaining_days = calculate_remaining(row[9])

    # Get the first bound machine (activation MAC)
    activation_mac = None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT mac_address FROM public.license_machines
                WHERE license_key = %s AND is_active = TRUE
                ORDER BY bound_at ASC
                LIMIT 1
            """, (license_key,))
            mac_row = cur.fetchone()
            if mac_row:
                activation_mac = mac_row[0]

    return {
        "license_key": row[0],
        "company_name": row[1],
        "email": row[2],
        "license_type": row[3],
        "state": row[4],
        "is_revoked": row[5],
        "revoked_reason": row[6],
        "creation_date": row[7],
        "activation_date": row[8],
        "activation_mac": activation_mac,
        "expiry_date": row[9],
        "remaining_seconds": remaining_sec,
        "remaining_days": remaining_days,
        "grace_period_days": row[10],
        "product_id": row[11],
        "license_id_hex": row[12],
        "signature_hex": row[13],
        "max_machines": row[14] if row[14] is not None else -1
    }


# ==========================================================
# 2️⃣ LIST LICENSES (Paginated)
# ==========================================================

def list_licenses(limit=50, offset=0):

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT license_key, company_name, state, expiry_date
                FROM public.licenses
                ORDER BY creation_date DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))

            return cur.fetchall()


# ==========================================================
# 3️⃣ ACTIVATE LICENSE
# ==========================================================

def activate_license(license_key):

    now = datetime.now(timezone.utc)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE public.licenses
                SET activation_date = %s,
                    state = 'active'
                WHERE license_key = %s
                RETURNING license_key
            """, (now, license_key))

            result = cur.fetchone()

        conn.commit()

    return result is not None


# ==========================================================
# 4️⃣ REVOKE LICENSE
# ==========================================================

def revoke_license(license_key, reason):

    now = datetime.now(timezone.utc)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE public.licenses
                SET is_revoked = TRUE,
                    revoked_at = %s,
                    revoked_reason = %s,
                    state = 'revoked'
                WHERE license_key = %s
                RETURNING license_key
            """, (now, reason, license_key))

            result = cur.fetchone()

        conn.commit()

    return result is not None


# ==========================================================
# 5️⃣ RESTORE LICENSE
# ==========================================================

def restore_license(license_key):

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE public.licenses
                SET is_revoked = FALSE,
                    revoked_at = NULL,
                    revoked_reason = NULL,
                    state = 'active'
                WHERE license_key = %s
                RETURNING license_key
            """, (license_key,))

            result = cur.fetchone()

        conn.commit()

    return result is not None


# ==========================================================
# 6️⃣ SUSPEND LICENSE
# ==========================================================

def suspend_license(license_key):

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE public.licenses
                SET state = 'suspended'
                WHERE license_key = %s
                RETURNING license_key
            """, (license_key,))

            result = cur.fetchone()

        conn.commit()

    return result is not None


# ==========================================================
# 7️⃣ UNSUSPEND LICENSE
# ==========================================================

def unsuspend_license(license_key):

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE public.licenses
                SET state = 'active'
                WHERE license_key = %s
                RETURNING license_key
            """, (license_key,))

            result = cur.fetchone()

        conn.commit()

    return result is not None


# ==========================================================
# 8️⃣ EXTEND LICENSE
# ==========================================================

def extend_license(license_key, extra_days):

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT expiry_date
                FROM public.licenses
                WHERE license_key = %s
            """, (license_key,))

            row = cur.fetchone()

            if not row:
                return False

            new_expiry = row[0] + timedelta(days=extra_days)
            new_epoch = int(new_expiry.timestamp())
            new_sec = (new_expiry - datetime.now(timezone.utc)).total_seconds()

            cur.execute("""
                UPDATE public.licenses
                SET expiry_date = %s,
                    period_in_days = period_in_days + %s,
                    period_in_sec = period_in_sec + %s,
                    period_in_uni_epoch = %s
                WHERE license_key = %s
            """, (
                new_expiry,
                extra_days,
                int(extra_days * 86400),
                new_epoch,
                license_key
            ))

        conn.commit()

    return True


# ==========================================================
# 9️⃣ UPDATE LICENSE TYPE
# ==========================================================

def update_license_type(license_key, new_type):

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE public.licenses
                SET license_type = %s
                WHERE license_key = %s
                RETURNING license_key
            """, (new_type, license_key))

            result = cur.fetchone()

        conn.commit()

    return result is not None

# ----------------------------------------------------------
# 1️⃣ CREATE PRODUCT
# ----------------------------------------------------------

def create_product(product_name, product_code):

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO public.products (product_name, product_code)
                VALUES (%s, %s)
                RETURNING product_id, product_name, product_code, creation_date
            """, (product_name, product_code))

            row = cur.fetchone()

    return {
        "product_id": row[0],
        "product_name": row[1],
        "product_code": row[2],
        "creation_date": row[3]
    }


# ----------------------------------------------------------
# 2️⃣ GET PRODUCT DETAILS
# ----------------------------------------------------------

def get_product(product_id):

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT product_id, product_name, product_code, creation_date
                FROM public.products
                WHERE product_id = %s
            """, (product_id,))

            row = cur.fetchone()

    if not row:
        return None

    return {
        "product_id": row[0],
        "product_name": row[1],
        "product_code": row[2],
        "creation_date": row[3]
    }


# ----------------------------------------------------------
# 3️⃣ LIST PRODUCTS
# ----------------------------------------------------------

def list_products():

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT product_id, product_name, product_code, creation_date
                FROM public.products
                ORDER BY creation_date DESC
            """)

            return cur.fetchall()


# ----------------------------------------------------------
# 4️⃣ UPDATE PRODUCT
# ----------------------------------------------------------

def update_product(product_id, new_name):

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE public.products
                SET product_name = %s
                WHERE product_id = %s
                RETURNING product_id
            """, (new_name, product_id))

            result = cur.fetchone()

        conn.commit()

    return result is not None

def validate_license_server_side(license_key):
    from datetime import datetime, timedelta, timezone

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    license_id_hex,
                    signature_hex,
                    state,
                    is_revoked,
                    expiry_date,
                    grace_period_in_days
                FROM public.licenses
                WHERE license_key = %s
            """, (license_key,))

            row = cur.fetchone()

            if not row:
                return {"valid": False, "reason": "not_found"}

            license_id_hex, signature_hex, state, is_revoked, expiry_date, grace_days = row

    # 🔐 Cryptographic verification
    if not verify_license(license_key, license_id_hex, signature_hex):
        return {"valid": False, "reason": "tampered"}

    now = datetime.now(timezone.utc)

    # Make expiry_date timezone-aware if it's naive
    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)

    if is_revoked:
        return {"valid": False, "reason": "revoked"}

    if now > expiry_date:
        grace_limit = expiry_date + timedelta(days=grace_days)
        if now > grace_limit:
            return {"valid": False, "reason": "expired"}

    return {
        "valid": True,
        "state": state,
        "expires_at": expiry_date.isoformat()
    }
# ----------------------------------------------------------
# 5️⃣ DELETE PRODUCT (SAFE DELETE)
# ----------------------------------------------------------

def delete_product(product_id):

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Check if any licenses use this product
            cur.execute("""
                SELECT COUNT(*)
                FROM public.licenses
                WHERE product_id = %s
            """, (product_id,))

            count = cur.fetchone()[0]

            if count > 0:
                return {
                    "success": False,
                    "reason": "Product has active licenses. Cannot delete."
                }

            cur.execute("""
                DELETE FROM public.products
                WHERE product_id = %s
                RETURNING product_id
            """, (product_id,))

            result = cur.fetchone()

        conn.commit()

    if not result:
        return {"success": False, "reason": "Product not found"}

    return {"success": True}

# ==========================================================
# MACHINE BINDING FUNCTIONS
# ==========================================================

def get_license_product_id(license_key: str) -> Optional[int]:
    """Get product_id for a license."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT product_id FROM public.licenses
                WHERE license_key = %s
            """, (license_key,))
            row = cur.fetchone()
            return row[0] if row else None


def bind_machine_to_license(license_key: str, mac_address: str, machine_name: str = None) -> dict:
    """
    Bind a machine (MAC address) to a license.
    
    Returns:
        dict with success True/False and reason if failed
    """
    product_id = get_license_product_id(license_key)
    if not product_id:
        return {"success": False, "reason": "license_not_found"}
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check if license exists
            cur.execute("""
                SELECT max_machines FROM public.licenses
                WHERE license_key = %s
            """, (license_key,))
            row = cur.fetchone()
            if not row:
                return {"success": False, "reason": "license_not_found"}
            
            max_machines = row[0]
            
            # Check if MAC already bound to another license in same product
            cur.execute("""
                SELECT license_key FROM public.license_machines
                WHERE mac_address = %s AND product_id = %s AND is_active = TRUE
            """, (mac_address, product_id))
            existing = cur.fetchone()
            if existing and existing[0] != license_key:
                return {"success": False, "reason": "mac_bound_to_other_license", "other_license": existing[0]}
            
            # Check if MAC already bound to this license
            cur.execute("""
                SELECT id, is_active FROM public.license_machines
                WHERE license_key = %s AND mac_address = %s
            """, (license_key, mac_address))
            existing_bound = cur.fetchone()
            
            if existing_bound:
                # Update last_seen and reactivate if inactive
                cur.execute("""
                    UPDATE public.license_machines
                    SET last_seen_at = NOW(), is_active = TRUE
                    WHERE id = %s
                """, (existing_bound[0],))
                conn.commit()
                return {"success": True, "action": "reactivated"}
            
            # Check max_machines limit (0 or NULL = unlimited)
            if max_machines is not None and max_machines > 0:
                cur.execute("""
                    SELECT COUNT(*) FROM public.license_machines
                    WHERE license_key = %s AND is_active = TRUE
                """, (license_key,))
                current_count = cur.fetchone()[0]
                
                if current_count >= max_machines:
                    return {"success": False, "reason": "max_machines_reached", "max": max_machines}
            
            # Bind new machine
            cur.execute("""
                INSERT INTO public.license_machines (license_key, product_id, mac_address, machine_name, bound_at, last_seen_at, is_active)
                VALUES (%s, %s, %s, %s, NOW(), NOW(), TRUE)
            """, (license_key, product_id, mac_address, machine_name))
            conn.commit()
            
            return {"success": True, "action": "bound"}


def unbind_machine_from_license(license_key: str, mac_address: str) -> bool:
    """Unbind a machine from a license."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE public.license_machines
                SET is_active = FALSE
                WHERE license_key = %s AND mac_address = %s
                RETURNING id
            """, (license_key, mac_address))
            result = cur.fetchone()
            conn.commit()
            return result is not None


def reset_all_machines(license_key: str) -> bool:
    """Unbind all machines from a license."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE public.license_machines
                SET is_active = FALSE
                WHERE license_key = %s
            """, (license_key,))
            conn.commit()
            return True


def list_license_machines(license_key: str) -> list:
    """List all machines bound to a license."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, mac_address, machine_name, bound_at, last_seen_at, is_active
                FROM public.license_machines
                WHERE license_key = %s
                ORDER BY bound_at DESC
            """, (license_key,))
            rows = cur.fetchall()
            
            result = []
            for row in rows:
                result.append({
                    "id": row[0],
                    "mac_address": row[1],
                    "machine_name": row[2],
                    "bound_at": row[3].isoformat() if row[3] else None,
                    "last_seen_at": row[4].isoformat() if row[4] else None,
                    "is_active": row[5]
                })
            return result


def update_max_machines(license_key: str, max_machines: int) -> bool:
    """
    Update max_machines limit for a license.
    Use 0 or NULL for unlimited.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE public.licenses
                SET max_machines = %s
                WHERE license_key = %s
                RETURNING license_key
            """, (max_machines, license_key))
            result = cur.fetchone()
            conn.commit()
            return result is not None


def check_machine_binding(license_key: str, mac_address: str) -> dict:
    """
    Check if a machine is bound to a license.
    
    Returns:
        dict with is_bound, is_active
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT is_active FROM public.license_machines
                WHERE license_key = %s AND mac_address = %s
            """, (license_key, mac_address))
            row = cur.fetchone()
            
            if not row:
                return {"is_bound": False, "is_active": False}
            
            return {"is_bound": True, "is_active": row[0]}


def get_machine_count(license_key: str) -> int:
    """Get count of active machines bound to a license."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM public.license_machines
                WHERE license_key = %s AND is_active = TRUE
            """, (license_key,))
            return cur.fetchone()[0]


# ==========================================================
# TEST
# ==========================================================



if __name__ == "__main__":
    create_license()
    
    
    
    
    
    # data = generate_license()

    # print("Generated License Key:", data["license_key"] + "\n" + "License ID (hex):", data["license_id_hex"] + "\n" + "Signature (hex):", data["signature_hex"])

    # is_valid = verify_license(
    #     "5YVX3_OZE2V_VBF32_JVRD3_7GSU3",
    #     data["license_id_hex"],
    #     data["signature_hex"]
    # )

    #print("Valid:", is_valid)


# ==========================================================
# AUDIT LOG FUNCTIONS
# ==========================================================

def log_audit_event(
    license_key: str,
    event_type: str,
    mac_address: str = None,
    ip_address: str = None,
    user_agent: str = None,
    success: bool = True,
    details: dict = None,
    is_offline: bool = False
):
    """
    Log a license audit event.
    
    Args:
        license_key: The license key
        event_type: Type of event (activation, verification, offline_check, suspend, revoke, extend)
        mac_address: MAC address of the machine
        ip_address: IP address of the request
        user_agent: User agent string
        success: Whether the operation was successful
        details: Additional details as JSON
        is_offline: Whether this was an offline operation
    """
    import json
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO license_audit_logs 
                (license_key, event_type, mac_address, ip_address, user_agent, success, details, is_offline)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                license_key,
                event_type,
                mac_address,
                ip_address,
                user_agent,
                success,
                json.dumps(details) if details else None,
                is_offline
            ))
            conn.commit()


def get_license_audit_logs(
    license_key: str,
    limit: int = 100,
    offset: int = 0
) -> list:
    """
    Get audit logs for a specific license.
    
    Args:
        license_key: The license key
        limit: Number of records to return
        offset: Offset for pagination
        
    Returns:
        List of audit log records
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, license_key, event_type, mac_address, ip_address, 
                       user_agent, success, details, is_offline, created_at
                FROM license_audit_logs
                WHERE license_key = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (license_key, limit, offset))
            
            rows = cur.fetchall()
            
            result = []
            for row in rows:
                result.append({
                    "id": row[0],
                    "license_key": row[1],
                    "event_type": row[2],
                    "mac_address": row[3],
                    "ip_address": row[4],
                    "user_agent": row[5],
                    "success": row[6],
                    "details": row[7],
                    "is_offline": row[8],
                    "created_at": row[9].isoformat() if row[9] else None
                })
            
            return result


def get_all_audit_logs(
    search: str = None,
    event_type: str = None,
    license_key: str = None,
    is_offline: bool = None,
    from_date: str = None,
    to_date: str = None,
    limit: int = 100,
    offset: int = 0
) -> list:
    """
    Get all audit logs with filters.
    
    Args:
        search: Search in license_key, mac_address, ip_address
        event_type: Filter by event type
        license_key: Filter by license key
        is_offline: Filter by offline status
        from_date: Filter from date (ISO format)
        to_date: Filter to date (ISO format)
        limit: Number of records
        offset: Offset for pagination
        
    Returns:
        List of audit log records
    """
    import json
    
    query = """
        SELECT id, license_key, event_type, mac_address, ip_address, 
               user_agent, success, details, is_offline, created_at
        FROM license_audit_logs
        WHERE 1=1
    """
    params = []
    
    if search:
        query += " AND (license_key ILIKE %s OR mac_address ILIKE %s OR ip_address ILIKE %s)"
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern])
    
    if event_type:
        query += " AND event_type = %s"
        params.append(event_type)
    
    if license_key:
        query += " AND license_key = %s"
        params.append(license_key)
    
    if is_offline is not None:
        query += " AND is_offline = %s"
        params.append(is_offline)
    
    if from_date:
        query += " AND created_at >= %s"
        params.append(from_date)
    
    if to_date:
        query += " AND created_at <= %s"
        params.append(to_date)
    
    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            
            result = []
            for row in rows:
                result.append({
                    "id": row[0],
                    "license_key": row[1],
                    "event_type": row[2],
                    "mac_address": row[3],
                    "ip_address": row[4],
                    "user_agent": row[5],
                    "success": row[6],
                    "details": row[7],
                    "is_offline": row[8],
                    "created_at": row[9].isoformat() if row[9] else None
                })
            
            return result


def get_audit_stats(license_key: str = None) -> dict:
    """
    Get audit statistics.
    
    Args:
        license_key: Optional license key to filter by
        
    Returns:
        Dictionary with statistics
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Total count
            if license_key:
                cur.execute("SELECT COUNT(*) FROM license_audit_logs WHERE license_key = %s", (license_key,))
            else:
                cur.execute("SELECT COUNT(*) FROM license_audit_logs")
            total = cur.fetchone()[0]
            
            # By event type
            if license_key:
                cur.execute("""
                    SELECT event_type, COUNT(*) 
                    FROM license_audit_logs 
                    WHERE license_key = %s
                    GROUP BY event_type
                """, (license_key,))
            else:
                cur.execute("""
                    SELECT event_type, COUNT(*) 
                    FROM license_audit_logs 
                    GROUP BY event_type
                """)
            by_event = {row[0]: row[1] for row in cur.fetchall()}
            
            # Offline vs Online
            if license_key:
                cur.execute("""
                    SELECT is_offline, COUNT(*) 
                    FROM license_audit_logs 
                    WHERE license_key = %s
                    GROUP BY is_offline
                """, (license_key,))
            else:
                cur.execute("""
                    SELECT is_offline, COUNT(*) 
                    FROM license_audit_logs 
                    GROUP BY is_offline
                """)
            by_online = {row[0]: row[1] for row in cur.fetchall()}
            
            # Recent activity (last 24 hours)
            if license_key:
                cur.execute("""
                    SELECT COUNT(*) FROM license_audit_logs 
                    WHERE license_key = %s 
                    AND created_at >= NOW() - INTERVAL '24 hours'
                """, (license_key,))
            else:
                cur.execute("""
                    SELECT COUNT(*) FROM license_audit_logs 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
            last_24h = cur.fetchone()[0]
            
            return {
                "total": total,
                "by_event_type": by_event,
                "offline_vs_online": by_online,
                "last_24h": last_24h
            }