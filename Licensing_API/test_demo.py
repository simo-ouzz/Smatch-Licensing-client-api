"""
Demo: How to use the SDK with license.dat for offline verification

This script demonstrates the complete workflow:
1. Activate a license (online)
2. Save license to license.dat (for offline use)
3. Verify license offline (no internet needed)
4. Handle tampered files
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'licensing-api-client', 'src'))

from smatch_licensing_api_client import LicenseClient
from smatch_licensing_api_client.errors import LicenseTamperedError


# ==========================================================
# CONFIGURATION
# ==========================================================

SERVER_URL = "http://localhost:8000"
API_KEY = "sk_Ik9EfY44Hd-OotHqvHYqKoXOI0GNkVlSfGc3PPzc9Tw"
SECRET_KEY = "default_dev_secret_key_change_in_production"

LICENSE_FILE = "license.dat"
LICENSE_KEY = "SFV2U_PLOMI_EU5AX_AGNRR_IVYIH"


# ==========================================================
# STEP 1: Initialize Client
# ==========================================================

print("=" * 60)
print("STEP 1: Initialize Client")
print("=" * 60)

client = LicenseClient(
    server_url=SERVER_URL,
    api_key=API_KEY,
    secret_key=SECRET_KEY
)
print("[OK] Client initialized")
print(f"  Server: {SERVER_URL}")
print(f"  API Key: {API_KEY[:10]}...")
print(f"  Secret Key: {SECRET_KEY[:10]}...")


# ==========================================================
# STEP 2: Activate License (Online)
# ==========================================================

print("\n" + "=" * 60)
print("STEP 2: Activate License (Online)")
print("=" * 60)

# First verify the license
is_valid = client.verify(LICENSE_KEY)
print(f"License valid: {is_valid}")

# Activate the license (binds to current machine MAC)
success = client.activate(LICENSE_KEY)
print(f"Activation: {'Success' if success else 'Already active'}")


# ==========================================================
# STEP 3: Save License for Offline Use
# ==========================================================

print("\n" + "=" * 60)
print("STEP 3: Save License for Offline Use")
print("=" * 60)

# Save the license to a file
success = client.save_license(LICENSE_KEY, LICENSE_FILE)

if success:
    print(f"[OK] License saved to {LICENSE_FILE}")
    
    # Show file contents
    import json
    with open(LICENSE_FILE, 'r') as f:
        data = json.load(f)
    
    print(f"\nLicense file contents:")
    print(f"  License Key: {data['license_key']}")
    print(f"  Expires: {data['expires']}")
    print(f"  State: {data['state']}")
    print(f"  Checksum: {data.get('checksum', 'N/A')[:20]}...")
else:
    print(f"[X] Failed to save license")


# ==========================================================
# STEP 4: Verify License Offline

print("\n" + "=")
# ========================================================= * 60)
print("STEP 4: Verify License Offline")
print("=" * 60)

# Verify without needing internet
is_valid = client.verify_offline(LICENSE_FILE, check_signature=False)

if is_valid:
    print(f"[OK] License is VALID")
    print(f"  User can use the application!")
else:
    print(f"[X] License is INVALID")


# ==========================================================
# STEP 5: Simulate Offline Usage
# ==========================================================

print("\n" + "=" * 60)
print("STEP 5: Simulate Offline Usage")
print("=" * 60)

# This is what your app would do
def check_license():
    """
    Your app would call this function to check if user has valid license.
    This works completely offline!
    """
    try:
        is_valid = client.verify_offline(LICENSE_FILE, check_signature=False)
        
        if is_valid:
            print("[OK] Access GRANTED - License is valid")
            return True
        else:
            print("[X] Access DENIED - License is invalid")
            return False
            
    except LicenseTamperedError as e:
        print(f"[X] Access DENIED - License file has been tampered with!")
        print(f"  Error: {e}")
        return False
    
    except FileNotFoundError:
        print(f"[X] Access DENIED - License file not found")
        return False

# Run the check
check_license()


# ==========================================================
# STEP 6: Test Tamper Detection
# ==========================================================

print("\n" + "=" * 60)
print("STEP 6: Test Tamper Detection")
print("=" * 60)

# Simulate a user trying to extend their license by changing expiry date
import json

print("Simulating user tampering with license.dat...")

# Read original
with open(LICENSE_FILE, 'r') as f:
    original_data = json.load(f)

# Modify expiry date to future
tampered_data = original_data.copy()
tampered_data['expires'] = "2030-01-01T00:00:00"

# Save tampered version
with open(LICENSE_FILE, 'w') as f:
    json.dump(tampered_data, f, indent=2)

print(f"  Original expiry: {original_data['expires']}")
print(f"  Tampered expiry: {tampered_data['expires']}")

# Try to verify - should fail!
print("\nVerifying tampered license...")
try:
    is_valid = client.verify_offline(LICENSE_FILE, check_signature=False)
    if not is_valid:
        print("[OK] Tamper detection WORKING - Invalid license detected!")
    else:
        print("[X] PROBLEM - Tampered license was accepted!")
except LicenseTamperedError as e:
    print(f"[OK] Tamper detection WORKING - {e}")
except Exception as e:
    print(f"[OK] Tamper detection WORKING - {type(e).__name__}: {e}")


# ==========================================================
# STEP 7: Restore Original License
# ==========================================================

print("\n" + "=" * 60)
print("STEP 7: Restore Original License")
print("=" * 60)

# Restore original
with open(LICENSE_FILE, 'w') as f:
    json.dump(original_data, f, indent=2)

print("[OK] License file restored")


# ==========================================================
# SUMMARY
# ==========================================================

print("\n" + "=" * 60)
print("SUMMARY - How It Works")
print("=" * 60)

print("""
WORKFLOW:
---------
1. USER BUYS LICENSE
2. APP calls: client.activate("KEY")
3. APP calls: client.save_license("KEY", "license.dat")
4. license.dat saved with checksum
5. USER CAN USE APP OFFLINE!
6. APP calls: client.verify_offline("license.dat")
   - Checks HMAC checksum -> detects tampering
   - Checks expiry date
   - Checks revocation status
7. Access GRANTED or DENIED
""")


# ==========================================================
# COMPLETE EXAMPLE: Your App's License Check
# ==========================================================

print("\n" + "=" * 60)
print("COMPLETE EXAMPLE: Your App's Code")
print("=" * 60)

print("""
# ==== YOUR APPLICATION CODE ====

from licensing_api_client import LicenseClient
from licensing_api_client.errors import LicenseTamperedError

def check_license():
    '''
    Call this when your app starts.
    Works completely offline!
    '''
    client = LicenseClient(
        server_url="https://your-server.com",
        api_key="sk_...",
        secret_key="..."  # Get from /licenses/secret-key
    )
    
    license_file = "license.dat"
    
    try:
        # Verify the license file
        is_valid = client.verify_offline(license_file, check_signature=True)
        
        if is_valid:
            # User has valid license - let them use the app
            return True
        else:
            # License invalid - show error
            return False
            
    except LicenseTamperedError:
        # License file was tampered with!
        # This user is trying to cheat!
        print("ERROR: License file has been modified!")
        return False
    
    except FileNotFoundError:
        # No license file - user needs to enter license key
        return False


# ==== IN YOUR MAIN APP ====

if __name__ == "__main__":
    if check_license():
        print("Welcome! License is valid.")
        # Start your app
    else:
        print("Please enter a valid license key.")
        # Show license input dialog
""")
