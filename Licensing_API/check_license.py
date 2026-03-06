"""
Simple offline license check demo

This script simulates how your actual application would check the license.
It reads the local license.dat file and verifies it without any internet connection.
"""
import sys
import os

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'licensing-api-client', 'src'))

from smatch_licensing_api_client import LicenseClient
from smatch_licensing_api_client.errors import LicenseTamperedError


# Configuration - These would be hardcoded in your real app
SERVER_URL = "http://localhost:8000"  # Only used to fetch secret key ONCE
API_KEY = "sk_Ik9EfY44Hd-OotHqvHYqKoXOI0GNkVlSfGc3PPzc9Tw"
SECRET_KEY = "default_dev_secret_key_change_in_production"  # Or fetch from server

LICENSE_FILE = "license.dat"


def check_license_offline():
    """
    Main license check function.
    This is what your app would call to verify the license.
    Works completely OFFLINE after first setup!
    """
    print("=" * 50)
    print("OFFLINE LICENSE CHECK")
    print("=" * 50)
    print()
    
    # Step 1: Check if license file exists
    print("[1] Checking for license file...")
    if not os.path.exists(LICENSE_FILE):
        print("    ERROR: License file not found!")
        print("    Please enter a license key first.")
        return False
    
    print(f"    Found: {LICENSE_FILE}")
    
    # Step 2: Initialize client (doesn't need internet)
    print("[2] Initializing license client...")
    client = LicenseClient(
        server_url=SERVER_URL,
        api_key=API_KEY,
        secret_key=SECRET_KEY
    )
    print("    Client initialized")
    
    # Step 3: Verify license (OFFLINE - no internet needed!)
    print("[3] Verifying license (OFFLINE)...")
    try:
        is_valid = client.verify_offline(LICENSE_FILE, check_signature=False)
        
        if is_valid:
            print("    SUCCESS: License is VALID!")
            print()
            print("=" * 50)
            print("ACCESS GRANTED")
            print("=" * 50)
            print("You can use the application.")
            return True
        else:
            print("    ERROR: License is INVALID!")
            print()
            print("=" * 50)
            print("ACCESS DENIED")
            print("=" * 50)
            return False
            
    except LicenseTamperedError as e:
        print(f"    ERROR: License file has been TAMPERED!")
        print(f"    Details: {e}")
        print()
        print("=" * 50)
        print("ACCESS DENIED - TAMPERING DETECTED")
        print("=" * 50)
        return False
        
    except Exception as e:
        print(f"    ERROR: {e}")
        return False


def main():
    """Run the offline license check"""
    print()
    print("This demo simulates checking a local license file.")
    print("No internet connection is required after setup!")
    print()
    
    # Run the check
    success = check_license_offline()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
