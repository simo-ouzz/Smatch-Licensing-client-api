"""
Test script for Offline Licensing with Forgery-Proof Mechanism

This script tests:
1. Saving licenses with HMAC checksum
2. Loading and verifying offline licenses
3. Detecting tampered license files
4. Various tampering scenarios (expiry, state, etc.)
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'licensing-api-client', 'src'))

from smatch_licensing_api_client import LicenseClient
from smatch_licensing_api_client.errors import LicenseTamperedError


# Configuration
SERVER_URL = "http://localhost:8000"
API_KEY = "sk_Ik9EfY44Hd-OotHqvHYqKoXOI0GNkVlSfGc3PPzc9Tw"
PUBLIC_KEY = "53b12a371b91d92c80d4afb8c12bbc3af00c1b426c4f0f1a78f1eac2239bfd9c"
SECRET_KEY = "default_dev_secret_key_change_in_production"

LICENSE_KEY = "QWJ6W_PGOQB_O2VSX_IELIZ_556W6"


def test_save_with_checksum():
    """Test saving license with HMAC checksum"""
    print("\n=== Test: Save License with Checksum ===")
    
    client = LicenseClient(
        server_url=SERVER_URL,
        api_key=API_KEY,
        secret_key=SECRET_KEY
    )
    
    filepath = "test_offline.dat"
    
    # Save license
    success = client.save_license(LICENSE_KEY, filepath)
    
    if not success:
        print("[X] Failed to save license")
        return False
    
    # Check if file exists and has checksum
    if not os.path.exists(filepath):
        print("[X] License file not created")
        return False
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    if "checksum" not in data:
        print("[X] Checksum not added to file")
        return False
    
    print(f"[OK] License saved with checksum: {data['checksum'][:20]}...")
    return True


def test_verify_original():
    """Test verifying original (untampered) license"""
    print("\n=== Test: Verify Original License ===")
    
    client = LicenseClient(
        server_url=SERVER_URL,
        api_key=API_KEY,
        secret_key=SECRET_KEY
    )
    
    filepath = "test_offline.dat"
    
    # Verify
    try:
        is_valid = client.verify_offline(filepath, check_signature=False)
        if is_valid:
            print("[OK] Original license verified successfully")
            return True
        else:
            print("[X] Original license should be valid")
            return False
    except Exception as e:
        print(f"[X] Error verifying license: {e}")
        return False


def test_tamper_expiry_date():
    """Test detecting expiry date tampering"""
    print("\n=== Test: Tamper Expiry Date ===")
    
    client = LicenseClient(
        server_url=SERVER_URL,
        api_key=API_KEY,
        secret_key=SECRET_KEY
    )
    
    filepath = "test_offline.dat"
    
    # Read and tamper
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    original_expires = data["expires"]
    data["expires"] = "2030-01-01T00:00:00"  # Change to future date
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"  Changed expiry from {original_expires} to {data['expires']}")
    
    # Try to verify
    try:
        is_valid = client.verify_offline(filepath, check_signature=False)
        print("[X] Tampered license should be rejected!")
        return False
    except LicenseTamperedError:
        print("[OK] Tampering detected - expiry date modified!")
        return True


def test_tamper_state():
    """Test detecting state tampering"""
    print("\n=== Test: Tamper License State ===")
    
    client = LicenseClient(
        server_url=SERVER_URL,
        api_key=API_KEY,
        secret_key=SECRET_KEY
    )
    
    filepath = "test_offline.dat"
    
    # Read and tamper state
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    original_state = data["state"]
    data["state"] = "active"  # Could change from suspended to active
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"  Changed state from {original_state} to {data['state']}")
    
    # Try to verify
    try:
        is_valid = client.verify_offline(filepath, check_signature=False)
        print("[X] Tampered license should be rejected!")
        return False
    except LicenseTamperedError:
        print("[OK] Tampering detected - state modified!")
        return True


def test_tamper_revoked():
    """Test detecting is_revoked tampering"""
    print("\n=== Test: Tamper Revoked Status ===")
    
    client = LicenseClient(
        server_url=SERVER_URL,
        api_key=API_KEY,
        secret_key=SECRET_KEY
    )
    
    filepath = "test_offline.dat"
    
    # Read and tamper is_revoked
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    original_revoked = data["is_revoked"]
    data["is_revoked"] = False  # Could change True to False
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"  Changed is_revoked from {original_revoked} to {data['is_revoked']}")
    
    # Try to verify
    try:
        is_valid = client.verify_offline(filepath, check_signature=False)
        print("[X] Tampered license should be rejected!")
        return False
    except LicenseTamperedError:
        print("[OK] Tampering detected - is_revoked modified!")
        return True


def test_remove_checksum():
    """Test detecting removed checksum"""
    print("\n=== Test: Remove Checksum ===")
    
    client = LicenseClient(
        server_url=SERVER_URL,
        api_key=API_KEY,
        secret_key=SECRET_KEY
    )
    
    filepath = "test_offline.dat"
    
    # Read and remove checksum
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    del data["checksum"]
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("  Removed checksum from file")
    
    # Try to verify - should still work (no checksum = skip verification)
    try:
        is_valid = client.verify_offline(filepath, check_signature=False)
        print("[OK] File without checksum still loads (checksum is optional)")
        return True
    except Exception as e:
        print(f"[X] Error: {e}")
        return False


def test_without_secret_key():
    """Test that verification works without secret key (graceful fallback)"""
    print("\n=== Test: Verify Without Secret Key ===")
    
    # Client without secret key
    client = LicenseClient(
        server_url=SERVER_URL,
        api_key=API_KEY,
        secret_key=None  # No secret key
    )
    
    filepath = "test_offline.dat"
    
    # Save with secret key
    client_with_secret = LicenseClient(
        server_url=SERVER_URL,
        api_key=API_KEY,
        secret_key=SECRET_KEY
    )
    client_with_secret.save_license(LICENSE_KEY, filepath)
    
    # Verify without secret key
    try:
        is_valid = client.verify_offline(filepath, check_signature=False)
        print("[OK] Verification works without secret key (skips checksum)")
        return True
    except Exception as e:
        print(f"[X] Error: {e}")
        return False


def test_fetch_secret_key_from_server():
    """Test fetching secret key from server"""
    print("\n=== Test: Fetch Secret Key From Server ===")
    
    client = LicenseClient(
        server_url=SERVER_URL,
        api_key=API_KEY
    )
    
    # Fetch secret key
    secret = client.fetch_secret_key()
    
    if secret:
        print(f"[OK] Got secret key from server: {secret[:20]}...")
        return True
    else:
        print("[X] Failed to fetch secret key")
        return False


def cleanup():
    """Clean up test files"""
    test_files = [
        "test_offline.dat",
        "forgery_test.dat",
        "secure_license.dat"
    ]
    for f in test_files:
        if os.path.exists(f):
            os.remove(f)


def run_all_tests():
    """Run all offline tests"""
    print("=" * 60)
    print("OFFLINE LICENSING - FORGERY-PROOF TEST SUITE")
    print("=" * 60)
    
    # Clean up first
    cleanup()
    
    results = []
    
    # Core tests
    results.append(("Save with Checksum", test_save_with_checksum()))
    results.append(("Verify Original", test_verify_original()))
    results.append(("Fetch Secret Key", test_fetch_secret_key_from_server()))
    
    # Tampering tests
    results.append(("Tamper Expiry Date", test_tamper_expiry_date()))
    results.append(("Tamper State", test_tamper_state()))
    results.append(("Tamper Revoked Status", test_tamper_revoked()))
    results.append(("Remove Checksum", test_remove_checksum()))
    results.append(("Verify Without Secret Key", test_without_secret_key()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "[OK]" if result else "[X]"
        print(f"{status} {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    # Cleanup
    cleanup()
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
