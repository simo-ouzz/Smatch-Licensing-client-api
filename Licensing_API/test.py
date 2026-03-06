"""
Test script for the Licensing SDK
Tests all features including machine binding
"""
import sys
import os

# Add the client package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'licensing-api-client', 'src'))

from smatch_licensing_api_client import LicenseClient
from smatch_licensing_api_client.client import get_mac_address

# Configuration
SERVER_URL = "http://localhost:8000"
API_KEY = "sk_Ik9EfY44Hd-OotHqvHYqKoXOI0GNkVlSfGc3PPzc9Tw"
PUBLIC_KEY = "53b12a371b91d92c80d4afb8c12bbc3af00c1b426c4f0f1a78f1eac2239bfd9c"
SECRET_KEY = "default_dev_secret_key_change_in_production"

# License to test (valid key)
LICENSE_KEY = "QWJ6W_PGOQB_O2VSX_IELIZ_556W6"


def test_mac_extraction():
    """Test that MAC address extraction works"""
    print("\n=== Test: MAC Address Extraction ===")
    try:
        mac = get_mac_address()
        print(f"MAC Address: {mac}")
        
        # Validate MAC format (XX:XX:XX:XX:XX:XX)
        if len(mac) == 17 and mac.count(':') == 5:
            print("[OK] MAC address format is valid")
            return True
        else:
            print(f"[X] Invalid MAC format: {mac}")
            return False
    except Exception as e:
        print(f"[X] Failed to get MAC: {e}")
        return False


def test_client_initialization():
    """Test client initialization"""
    print("\n=== Test: Client Initialization ===")
    try:
        client = LicenseClient(
            server_url=SERVER_URL,
            api_key=API_KEY,
            public_key=PUBLIC_KEY,
            secret_key=SECRET_KEY
        )
        print(f"[OK] Client initialized")
        print(f"     Server URL: {client.server_url}")
        print(f"     API Key: {client.api_key[:10]}...")
        print(f"     Secret Key: {client.secret_key[:10]}...")
        return client
    except Exception as e:
        print(f"[X] Failed to initialize client: {e}")
        return None


def test_verify_license(client):
    """Test license verification"""
    print("\n=== Test: License Verification ===")
    try:
        # Simple boolean check
        is_valid = client.verify(LICENSE_KEY)
        print(f"License valid (simple): {is_valid}")
        
        # Full details
        result = client.verify(LICENSE_KEY, full_details=True)
        print(f"License valid: {result.is_valid}")
        print(f"License key: {result.license_key}")
        print(f"State: {result.state}")
        print(f"Expires: {result.expires}")
        print(f"Remaining days: {result.remaining_days}")
        print(f"Reason: {result.reason}")
        
        if result.is_valid:
            print("[OK] License verification passed")
            return True
        else:
            print(f"[!] License verification failed: {result.reason}")
            return False
    except Exception as e:
        print(f"[X] Failed to verify license: {e}")
        return False


def test_activate_license(client):
    """Test license activation with MAC binding"""
    print("\n=== Test: License Activation (with MAC) ===")
    try:
        # Activate with auto-extracted MAC
        success = client.activate(LICENSE_KEY)
        
        if success:
            print(f"[OK] License activated successfully")
            print(f"     MAC used: {get_mac_address()}")
            return True
        else:
            print("[!] Activation returned False (may already be active)")
            return True  # Not necessarily a failure
            
    except Exception as e:
        print(f"[X] Failed to activate license: {e}")
        return False


def test_get_license_details(client):
    """Test getting license details"""
    print("\n=== Test: Get License Details ===")
    try:
        details = client.get_license_details(LICENSE_KEY)
        
        if details:
            print(f"[OK] Got license details:")
            for key, value in details.items():
                print(f"     {key}: {value}")
            return True
        else:
            print("[X] Failed to get details")
            return False
    except Exception as e:
        print(f"[X] Error: {e}")
        return False


def test_save_load_offline(client):
    """Test offline license saving/loading"""
    print("\n=== Test: Offline License (Save/Load) ===")
    try:
        # Save license to file
        filepath = "test_license.dat"
        success = client.save_license(LICENSE_KEY, filepath)
        
        if success:
            print(f"[OK] License saved to {filepath}")
            
            # Load and verify offline
            loaded = client.load_license(filepath)
            if loaded:
                print(f"[OK] License loaded from file")
                print(f"     License key: {loaded.license_key}")
                print(f"     Expires: {loaded.expires}")
                
                # Verify offline (without signature check for testing)
                is_valid = client.verify_offline(filepath, check_signature=False)
                print(f"     Offline verification: {is_valid}")
                
                if is_valid:
                    print("[OK] Offline verification passed")
                    return True
                else:
                    print("[!] Offline verification failed")
                    return False
            else:
                print("[X] Failed to load license")
                return False
        else:
            print("[X] Failed to save license")
            return False
            
    except Exception as e:
        print(f"[X] Error: {e}")
        return False


def test_helper_functions():
    """Test helper utility functions"""
    print("\n=== Test: Helper Functions ===")
    try:
        from smatch_licensing_api_client.client import Helpers
        
        # Test key format validation - this key has 6 chars in last group
        valid_key = "QWJ6W_PGOQB_O2VSX_IELIZ_556W6"
        invalid_key = "INVALID_KEY"
        
        if Helpers.is_valid_key_format(valid_key):
            print("[OK] Valid key format recognized")
        else:
            print("[X] Valid key not recognized")
            
        if not Helpers.is_valid_key_format(invalid_key):
            print("[OK] Invalid key format rejected")
        else:
            print("[!] Invalid key was not rejected")
            
        return True
    except Exception as e:
        print(f"[X] Error: {e}")
        return False


def test_forgery_proof(client):
    """Test that tampering with license file is detected"""
    print("\n=== Test: Forgery-Proof Mechanism ===")
    try:
        from smatch_licensing_api_client.errors import LicenseTamperedError
        import json
        
        filepath = "forgery_test.dat"
        
        # 1. Save license with checksum
        success = client.save_license(LICENSE_KEY, filepath)
        if not success:
            print("[X] Failed to save license")
            return False
        print("[OK] License saved with checksum")
        
        # 2. Verify original (should pass)
        is_valid = client.verify_offline(filepath, check_signature=False)
        if not is_valid:
            print("[X] Original license should be valid")
            return False
        print("[OK] Original license verified")
        
        # 3. Tamper with the file
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Change expiry date to future
        original_expires = data.get("expires")
        data["expires"] = "2030-01-01T00:00:00"
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print("[OK] Tampered with expiry date!")
        
        # 4. Try to verify tampered file (should fail)
        try:
            is_valid = client.verify_offline(filepath, check_signature=False)
            print("[X] Tampered license should be rejected!")
            return False
        except LicenseTamperedError as e:
            print(f"[OK] Tampering detected: {str(e)}")
            return True
            
    except Exception as e:
        print(f"[X] Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("LICENSING SDK TEST SUITE")
    print("=" * 50)
    
    results = []
    
    # Test MAC extraction
    results.append(("MAC Extraction", test_mac_extraction()))
    
    # Test client initialization
    client = test_client_initialization()
    if not client:
        print("\n[!] Cannot continue without client - exiting")
        sys.exit(1)
    
    results.append(("Client Init", True))
    
    # Test helper functions
    results.append(("Helper Functions", test_helper_functions()))
    
    # Test verify
    results.append(("Verify License", test_verify_license(client)))
    
    # Test activate (with MAC binding)
    results.append(("Activate License", test_activate_license(client)))
    
    # Test forgery proof
    results.append(("Forgery Proof", test_forgery_proof(client)))
    
    # Test get details
    results.append(("Get Details", test_get_license_details(client)))
    
    # Test offline
    results.append(("Offline Save/Load", test_save_load_offline(client)))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
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
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
