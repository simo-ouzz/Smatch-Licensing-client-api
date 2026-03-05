import os
import base64
import secrets
import psycopg2
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError
from datetime import datetime, timedelta, timezone



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
    grace_period_days
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
                period_days,
                period_in_sec,
                period_in_unix_epoch,
                "inactive",
                grace_period_days,
                False,
                product_id,
                signature_hex,
                license_id_hex
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
                    p.product_id
                FROM public.licenses l
                JOIN public.products p 
                    ON l.product_id = p.product_id
                WHERE l.license_key = %s
            """, (license_key,))

            row = cur.fetchone()

    if not row:
        return None

    remaining_sec, remaining_days = calculate_remaining(row[9])

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
        "expiry_date": row[9],
        "remaining_seconds": remaining_sec,
        "remaining_days": remaining_days,
        "grace_period_days": row[10],
        "product_id": row[11]
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

    #print("Valid:", is_valid)q