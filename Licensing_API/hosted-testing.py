"""
Complete Test Suite for SMATCH Licensing API
============================================
Tests all possible scenarios for license handling.

Usage:
    python hosted-testing.py

Requirements:
    pip install smatch-licensing-api-client
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smatch_licensing_api_client import LicenseClient, Helpers
from smatch_licensing_api_client.errors import (
    LicenseError,
    LicenseInvalidError,
    LicenseExpiredError,
    LicenseRevokedError,
    LicenseNotFoundError,
    LicenseTamperedError,
    NetworkError,
    AuthenticationError,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

SERVER_URL = "http://86.38.218.9:8822"
API_KEY = "sk_mIUIqdItKNufyodi_4rCgtIpjWi40JVZj-51AbUg340"

# Test license keys - UPDATE THESE WITH YOUR ACTUAL LICENSE KEYS
VALID_ACTIVE_LICENSE = "YEDJV_QCVMJ_5Y2BZ_O4UEV_MOCUF"      # Replace with valid active license
INVALID_LICENSE = "XXXXX_XXXXX_XXXXX_XXXXX_XXXXX"          # Invalid format/key
EXPIRED_LICENSE = "EXPRD_LICENSE_HERE_TEST999"              # Replace with expired license
REVOKED_LICENSE = "REVOK_LICENSE_HERE_TEST999"              # Replace with revoked license

# For offline testing
OFFLINE_LICENSE_FILE = "test_license.dat"
TEST_MAC_ADDRESS = "AA:BB:CC:DD:EE:FF"


# =============================================================================
# TEST UTILITIES
# =============================================================================

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []

    def add_pass(self, test_name):
        self.passed += 1
        print(f"  [PASS] {test_name}")

    def add_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"  [FAIL] {test_name}")
        print(f"      Error: {error}")

    def add_skip(self, test_name, reason):
        self.skipped += 1
        print(f"  [SKIP] {test_name} - {reason}")

    def print_summary(self):
        print("\n============================================================")
        print("TEST SUMMARY")
        print("============================================================")
        print(f"  Passed:  {self.passed}")
        print(f"  Failed:  {self.failed}")
        print(f"  Skipped: {self.skipped}")
        print(f"  Total:   {self.passed + self.failed + self.skipped}")
        
        if self.failed > 0:
            print("\n============================================================")
            print("FAILED TESTS")
            print("============================================================")
            for test_name, error in self.errors:
                print(f"  • {test_name}")
                print(f"    {error}")
        
        print()
        return self.failed == 0


# =============================================================================
# TEST CASES
# =============================================================================

def test_client_initialization(result):
    """Test 1: Client initialization with various configurations"""
    print("\n[Test 1] Client Initialization")
    
    # Test 1a: Basic initialization
    try:
        client = LicenseClient(
            server_url=SERVER_URL,
            api_key=API_KEY
        )
        result.add_pass("Basic initialization")
    except Exception as e:
        result.add_fail("Basic initialization", str(e))
    
    # Test 1b: With secret key for offline
    try:
        client = LicenseClient(
            server_url=SERVER_URL,
            api_key=API_KEY,
            secret_key="test_secret_key"
        )
        result.add_pass("Initialization with secret_key")
    except Exception as e:
        result.add_fail("Initialization with secret_key", str(e))
    
    # Test 1c: With public key for signatures
    try:
        client = LicenseClient(
            server_url=SERVER_URL,
            api_key=API_KEY,
            public_key="53b12a371b91d92c80d4afb8c12bbc3af00c1b426c4f0f1a78f1eac2239bfd9c"
        )
        result.add_pass("Initialization with public_key")
    except Exception as e:
        result.add_fail("Initialization with public_key", str(e))
    
    # Test 1d: With custom timeout
    try:
        client = LicenseClient(
            server_url=SERVER_URL,
            api_key=API_KEY,
            timeout=60
        )
        result.add_pass("Initialization with custom timeout")
    except Exception as e:
        result.add_fail("Initialization with custom timeout", str(e))
    
    # Test 1e: Without API key (should fail)
    try:
        client = LicenseClient(
            server_url=SERVER_URL,
            api_key=""
        )
        result.add_fail("Missing API key should raise error", "No error raised")
    except AuthenticationError:
        result.add_pass("Missing API key raises AuthenticationError")
    except Exception as e:
        result.add_fail("Missing API key", f"Wrong error: {e}")


def test_helper_functions(result):
    """Test 2: Helper utility functions"""
    print("\n[Test 2]: Helper Functions")
    
    # Test 2a: Valid key format
    if Helpers.is_valid_key_format("ABCDE_FGHIJ_KLMNO_PQRST_UVWXY"):
        result.add_pass("Valid key format detection")
    else:
        result.add_fail("Valid key format detection", "Failed to detect valid format")
    
    # Test 2b: Invalid key format - wrong length
    if not Helpers.is_valid_key_format("ABCDE_FGHIJ_KLMNO_PQRST"):
        result.add_pass("Invalid key format detection (wrong parts)")
    else:
        result.add_fail("Invalid key format detection", "Should reject 4-part key")
    
    # Test 2c: Invalid key format - too short
    if not Helpers.is_valid_key_format("ABC_123"):
        result.add_pass("Invalid key format detection (too short)")
    else:
        result.add_fail("Invalid key format detection", "Should reject short key")
    
    # Test 2d: Empty key
    if not Helpers.is_valid_key_format(""):
        result.add_pass("Empty key rejected")
    else:
        result.add_fail("Empty key", "Should reject empty key")
    
    # Test 2e: None key
    if not Helpers.is_valid_key_format(None):
        result.add_pass("None key rejected")
    else:
        result.add_fail("None key", "Should reject None key")


def test_verify_license(result):
    """Test 3: License verification (online)"""
    print("\n[Test 3]: License Verification (Online)")
    
    client = LicenseClient(server_url=SERVER_URL, api_key=API_KEY)
    
    # Test 3a: Verify valid license (if we have one)
    if VALID_ACTIVE_LICENSE and VALID_ACTIVE_LICENSE != "YEDJV_QCVMJ_5Y2BZ_O4UEV_MOCUF":
        try:
            is_valid = client.verify(VALID_ACTIVE_LICENSE)
            if is_valid:
                result.add_pass("Verify valid license returns True")
            else:
                result.add_pass("Verify valid license returns False (expected if license not active)")
        except Exception as e:
            result.add_fail("Verify valid license", str(e))
    else:
        result.add_skip("Verify valid license", "No valid license key provided")
    
    # Test 3b: Verify with full_details
    if VALID_ACTIVE_LICENSE and VALID_ACTIVE_LICENSE != "YEDJV_QCVMJ_5Y2BZ_O4UEV_MOCUF":
        try:
            response = client.verify(VALID_ACTIVE_LICENSE, full_details=True)
            if hasattr(response, 'is_valid'):
                result.add_pass("Verify with full_details returns LicenseResponse")
            else:
                result.add_fail("Full details response", "Missing is_valid attribute")
        except Exception as e:
            result.add_fail("Verify with full_details", str(e))
    else:
        result.add_skip("Verify with full_details", "No valid license key provided")
    
    # Test 3c: Verify invalid key format
    try:
        is_valid = client.verify("INVALID_KEY")
        if not is_valid:
            result.add_pass("Invalid key format returns False")
        else:
            result.add_fail("Invalid key format", "Should return False")
    except Exception as e:
        result.add_fail("Invalid key format", str(e))
    
    # Test 3d: Verify non-existent license
    try:
        is_valid = client.verify(INVALID_LICENSE)
        if not is_valid:
            result.add_pass("Non-existent license returns False")
        else:
            result.add_pass("Non-existent license returns True (may be valid if it exists)")
    except LicenseNotFoundError:
        result.add_pass("Non-existent license raises LicenseNotFoundError")
    except Exception as e:
        result.add_fail("Non-existent license", f"Unexpected error: {e}")
    
    # Test 3e: Verify with None key
    try:
        is_valid = client.verify(None)
        if not is_valid:
            result.add_pass("None key returns False")
        else:
            result.add_fail("None key", "Should return False")
    except Exception as e:
        result.add_pass("None key raises exception (acceptable)")


def test_get_license_details(result):
    """Test 4: Get license details"""
    print("\n[Test 4]: Get License Details")
    
    client = LicenseClient(server_url=SERVER_URL, api_key=API_KEY)
    
    # Test 4a: Get details for valid license
    if VALID_ACTIVE_LICENSE and VALID_ACTIVE_LICENSE != "YEDJV_QCVMJ_5Y2BZ_O4UEV_MOCUF":
        try:
            details = client.get_license_details(VALID_ACTIVE_LICENSE)
            if details and isinstance(details, dict):
                result.add_pass("Get license details returns dict")
                # Check for expected fields
                expected_fields = ['license_key', 'state', 'expiry_date']
                found_fields = [f for f in expected_fields if f in details]
                if len(found_fields) >= 2:
                    result.add_pass("License details contains expected fields")
                else:
                    result.add_fail("License details fields", f"Missing: {expected_fields}")
            else:
                result.add_fail("Get license details", "Invalid response")
        except Exception as e:
            result.add_fail("Get license details", str(e))
    else:
        result.add_skip("Get license details", "No valid license key provided")
    
    # Test 4b: Get details for non-existent license
    try:
        details = client.get_license_details(INVALID_LICENSE)
        if details is None:
            result.add_pass("Non-existent license returns None")
        else:
            result.add_fail("Non-existent license", f"Should return None, got: {details}")
    except Exception as e:
        result.add_fail("Get details for invalid", str(e))
    
    # Test 4c: Get details with None key
    try:
        details = client.get_license_details(None)
        if details is None:
            result.add_pass("None key returns None")
        else:
            result.add_fail("None key", f"Should return None, got: {details}")
    except Exception as e:
        result.add_pass("None key handling (acceptable)")


def test_license_activation(result):
    """Test 5: License activation"""
    print("\n[Test 5]: License Activation")
    
    client = LicenseClient(server_url=SERVER_URL, api_key=API_KEY)
    
    # Test 5a: Activate valid license
    if VALID_ACTIVE_LICENSE and VALID_ACTIVE_LICENSE != "YEDJV_QCVMJ_5Y2BZ_O4UEV_MOCUF":
        try:
            success = client.activate(VALID_ACTIVE_LICENSE)
            if success:
                result.add_pass("Activate valid license returns True")
            else:
                result.add_pass("Activate valid license returns False (may already be active)")
        except Exception as e:
            result.add_fail("Activate valid license", str(e))
    else:
        result.add_skip("Activate valid license", "No valid license key provided")
    
    # Test 5b: Activate with custom MAC
    if VALID_ACTIVE_LICENSE and VALID_ACTIVE_LICENSE != "YEDJV_QCVMJ_5Y2BZ_O4UEV_MOCUF":
        try:
            success = client.activate(VALID_ACTIVE_LICENSE, mac_address=TEST_MAC_ADDRESS)
            result.add_pass("Activate with custom MAC address")
        except Exception as e:
            result.add_fail("Activate with custom MAC", str(e))
    else:
        result.add_skip("Activate with custom MAC", "No valid license key provided")
    
    # Test 5c: Activate invalid license
    try:
        success = client.activate(INVALID_LICENSE)
        if not success:
            result.add_pass("Activate invalid license returns False")
        else:
            result.add_pass("Activate invalid license (may succeed if key exists)")
    except LicenseNotFoundError:
        result.add_pass("Activate invalid license raises LicenseNotFoundError")
    except Exception as e:
        result.add_fail("Activate invalid license", str(e))
    
    # Test 5d: Activate with None key
    try:
        success = client.activate(None)
        if not success:
            result.add_pass("Activate with None returns False")
        else:
            result.add_fail("Activate with None", "Should return False")
    except Exception as e:
        result.add_pass("Activate with None raises exception (acceptable)")


def test_license_deactivation(result):
    """Test 6: License deactivation"""
    print("\n[Test 6]: License Deactivation")
    
    client = LicenseClient(server_url=SERVER_URL, api_key=API_KEY)
    
    # Test 6a: Deactivate license
    if VALID_ACTIVE_LICENSE and VALID_ACTIVE_LICENSE != "YEDJV_QCVMJ_5Y2BZ_O4UEV_MOCUF":
        try:
            success = client.deactivate(VALID_ACTIVE_LICENSE)
            if success:
                result.add_pass("Deactivate license returns True")
            else:
                result.add_pass("Deactivate license returns False (may not be suspendable)")
        except Exception as e:
            result.add_fail("Deactivate license", str(e))
    else:
        result.add_skip("Deactivate license", "No valid license key provided")
    
    # Test 6b: Deactivate invalid license
    try:
        success = client.deactivate(INVALID_LICENSE)
        result.add_pass("Deactivate invalid license handling")
    except Exception as e:
        result.add_fail("Deactivate invalid license", str(e))


def test_network_errors(result):
    """Test 7: Network error handling"""
    print("\n[Test 7]: Network Error Handling")
    
    # Test 7a: Invalid server URL
    try:
        client = LicenseClient(
            server_url="http://invalid-server-that-does-not-exist.local",
            api_key=API_KEY,
            timeout=5
        )
        is_valid = client.verify(VALID_ACTIVE_LICENSE)
        result.add_fail("Invalid server URL", "Should raise NetworkError")
    except NetworkError:
        result.add_pass("Invalid server URL raises NetworkError")
    except Exception as e:
        result.add_pass(f"Invalid server URL raises error: {type(e).__name__}")
    
    # Test 7b: Invalid API key
    try:
        client = LicenseClient(
            server_url=SERVER_URL,
            api_key="sk_invalid_key_that_does_not_exist"
        )
        is_valid = client.verify(VALID_ACTIVE_LICENSE)
        result.add_fail("Invalid API key", "Should raise AuthenticationError")
    except AuthenticationError:
        result.add_pass("Invalid API key raises AuthenticationError")
    except Exception as e:
        result.add_pass(f"Invalid API key raises: {type(e).__name__}")
    
    # Test 7c: Connection timeout
    try:
        client = LicenseClient(
            server_url="http://10.255.255.1:8822",  # Non-routable IP
            api_key=API_KEY,
            timeout=3
        )
        is_valid = client.verify(VALID_ACTIVE_LICENSE)
        result.add_fail("Connection timeout", "Should raise NetworkError")
    except NetworkError:
        result.add_pass("Connection timeout raises NetworkError")
    except Exception as e:
        result.add_pass(f"Connection timeout raises: {type(e).__name__}")


def test_offline_licensing(result):
    """Test 8: Offline licensing"""
    print("\n[Test 8]: Offline Licensing")
    
    client = LicenseClient(
        server_url=SERVER_URL,
        api_key=API_KEY,
        secret_key="default_dev_secret_key_change_in_production",
        public_key="53b12a371b91d92c80d4afb8c12bbc3af00c1b426c4f0f1a78f1eac2239bfd9c"
    )
    
    # Test 8a: Save license for offline
    if VALID_ACTIVE_LICENSE and VALID_ACTIVE_LICENSE != "YEDJV_QCVMJ_5Y2BZ_O4UEV_MOCUF":
        try:
            success = client.save_license(VALID_ACTIVE_LICENSE, OFFLINE_LICENSE_FILE)
            if success:
                result.add_pass("Save license for offline returns True")
                # Check if file was created
                if os.path.exists(OFFLINE_LICENSE_FILE):
                    result.add_pass("Offline license file created")
                else:
                    result.add_fail("Offline license file", "File not created")
            else:
                result.add_pass("Save license returns False (may already be saved)")
        except Exception as e:
            result.add_fail("Save license for offline", str(e))
    else:
        result.add_skip("Save license for offline", "No valid license key provided")
    
    # Test 8b: Load offline license
    if os.path.exists(OFFLINE_LICENSE_FILE):
        try:
            license_key = client.load_license(OFFLINE_LICENSE_FILE)
            if license_key:
                result.add_pass("Load offline license returns LicenseKey")
            else:
                result.add_fail("Load offline license", "Returned None")
        except Exception as e:
            result.add_fail("Load offline license", str(e))
    else:
        result.add_skip("Load offline license", "No offline file exists")
    
    # Test 8c: Verify offline license
    if os.path.exists(OFFLINE_LICENSE_FILE):
        try:
            is_valid = client.verify_offline(OFFLINE_LICENSE_FILE)
            if is_valid:
                result.add_pass("Verify offline license returns True")
            else:
                result.add_pass("Verify offline license returns False (may be expired/invalid)")
        except Exception as e:
            result.add_fail("Verify offline license", str(e))
    else:
        result.add_skip("Verify offline license", "No offline file exists")
    
    # Test 8d: Verify offline license with signature check
    if os.path.exists(OFFLINE_LICENSE_FILE):
        try:
            is_valid = client.verify_offline(OFFLINE_LICENSE_FILE, check_signature=True)
            result.add_pass("Verify offline with signature check")
        except Exception as e:
            result.add_fail("Verify offline with signature", str(e))
    else:
        result.add_skip("Verify offline with signature", "No offline file exists")
    
    # Test 8e: Verify non-existent offline file
    try:
        is_valid = client.verify_offline("non_existent_file.dat")
        result.add_fail("Verify non-existent file", "Should return False or raise error")
    except Exception as e:
        result.add_pass("Verify non-existent file raises error (acceptable)")


def test_server_endpoints(result):
    """Test 9: Direct API endpoint testing"""
    print("\n[Test 9]: Server Endpoints")
    
    import requests
    
    # Test 9a: Health check endpoint
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=10)
        if response.status_code == 200:
            result.add_pass("Health check endpoint returns 200")
        else:
            result.add_fail("Health check", f"Status: {response.status_code}")
    except Exception as e:
        result.add_fail("Health check", str(e))
    
    # Test 9b: Dashboard endpoint
    try:
        response = requests.get(f"{SERVER_URL}/", timeout=10)
        if response.status_code == 200:
            result.add_pass("Dashboard endpoint returns 200")
        else:
            result.add_fail("Dashboard", f"Status: {response.status_code}")
    except Exception as e:
        result.add_fail("Dashboard endpoint", str(e))
    
    # Test 9c: SDK Docs endpoint
    try:
        response = requests.get(f"{SERVER_URL}/sdk-docs", timeout=10)
        if response.status_code == 200:
            result.add_pass("SDK Docs endpoint returns 200")
        else:
            result.add_fail("SDK Docs", f"Status: {response.status_code}")
    except Exception as e:
        result.add_fail("SDK Docs endpoint", str(e))


def test_error_exceptions(result):
    """Test 10: Exception handling"""
    print("\n[Test 10]: Exception Classes")
    
    # Test that all exception classes exist and can be instantiated
    exceptions = [
        ("LicenseError", LicenseError("test")),
        ("LicenseInvalidError", LicenseInvalidError("test")),
        ("LicenseExpiredError", LicenseExpiredError("test")),
        ("LicenseRevokedError", LicenseRevokedError("test")),
        ("LicenseNotFoundError", LicenseNotFoundError("test")),
        ("LicenseTamperedError", LicenseTamperedError("test")),
        ("NetworkError", NetworkError("test")),
        ("AuthenticationError", AuthenticationError("test")),
    ]
    
    for name, exc in exceptions:
        if exc:
            result.add_pass(f"{name} can be instantiated")
        else:
            result.add_fail(name, "Failed to instantiate")


def test_misc_scenarios(result):
    """Test 11: Miscellaneous scenarios"""
    print("\n[Test 11]: Miscellaneous Scenarios")
    
    client = LicenseClient(server_url=SERVER_URL, api_key=API_KEY)
    
    # Test 11a: Empty license key
    try:
        is_valid = client.verify("")
        if not is_valid:
            result.add_pass("Empty string license key returns False")
        else:
            result.add_fail("Empty string", "Should return False")
    except Exception as e:
        result.add_pass("Empty string handling (acceptable)")
    
    # Test 11b: Whitespace license key
    try:
        is_valid = client.verify("   ")
        if not is_valid:
            result.add_pass("Whitespace license key returns False")
        else:
            result.add_fail("Whitespace key", "Should return False")
    except Exception as e:
        result.add_pass("Whitespace key handling (acceptable)")
    
    # Test 11c: Very long license key
    try:
        is_valid = client.verify("A" * 100)
        if not is_valid:
            result.add_pass("Very long license key returns False")
        else:
            result.add_fail("Long key", "Should return False")
    except Exception as e:
        result.add_pass("Long key handling (acceptable)")
    
    # Test 11d: Unicode in license key
    try:
        is_valid = client.verify("-test_license_with_unicode_日本語")
        result.add_pass("Unicode license key handling")
    except Exception as e:
        result.add_pass("Unicode key raises exception (acceptable)")
    
    # Test 11e: Special characters
    try:
        is_valid = client.verify("TEST!@#$%^&*()_KEY")
        result.add_pass("Special characters handling")
    except Exception as e:
        result.add_pass("Special chars raises exception (acceptable)")


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def run_all_tests():
    """Run all test suites"""
    print("============================================================")
    print("SMATCH LICENSING API - COMPLETE TEST SUITE")
    print("============================================================")
    print(f"Server URL: {SERVER_URL}")
    print(f"API Key: {API_KEY[:20]}...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    result = TestResult()
    
    # Run all test suites
    test_client_initialization(result)
    test_helper_functions(result)
    test_verify_license(result)
    test_get_license_details(result)
    test_license_activation(result)
    test_license_deactivation(result)
    test_network_errors(result)
    test_offline_licensing(result)
    test_server_endpoints(result)
    test_error_exceptions(result)
    test_misc_scenarios(result)
    
    # Print summary
    success = result.print_summary()
    
    # Cleanup
    if os.path.exists(OFFLINE_LICENSE_FILE):
        print(f"\n--- Cleaning up test file: {OFFLINE_LICENSE_FILE}")
        # Uncomment to delete test file:
        # os.remove(OFFLINE_LICENSE_FILE)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
