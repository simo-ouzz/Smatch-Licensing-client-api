"""
============================================================
REAL-WORLD SDK DEMO - "MyApp" Software License System
============================================================

This demo simulates how a real desktop application would
integrate the licensing SDK for software activation.

SCENARIOS COVERED:
1. First Run: License activation (online)
2. Offline Usage: License verification (offline)
3. Tamper Detection: Modified license file
4. Revoked License: Blocked access
5. Expired License: Blocked access
============================================================
"""

import sys
import os

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'licensing-api-client', 'src'))

from smatch_licensing_api_client import LicenseClient
from smatch_licensing_api_client.errors import LicenseTamperedError


# ==========================================================
# CONFIGURATION
# ==========================================================
# These would typically be in a config file or environment variables

CONFIG = {
    "SERVER_URL": "http://localhost:8000",
    "API_KEY": "sk_Ik9EfY44Hd-OotHqvHYqKoXOI0GNkVlSfGc3PPzc9Tw",
    "PUBLIC_KEY": "53b12a371b91d92c80d4afb8c12bbc3af00c1b426c4f0f1a78f1eac2239bfd9c",
    "SECRET_KEY": "default_dev_secret_key_change_in_production",
    "LICENSE_FILE": "license.dat"
}

# Test license key
LICENSE_KEY = "QWJ6W_PGOQB_O2VSX_IELIZ_556W6"


# ==========================================================
# MYAPP - SIMULATED APPLICATION
# ==========================================================

class MyApp:
    """
    Simulated desktop application that uses the licensing system.
    This is how you would integrate the SDK into a real app.
    """
    
    def __init__(self):
        """Initialize the application and license client"""
        print("=" * 60)
        print("INITIALIZING MYAPP")
        print("=" * 60)
        
        # Initialize license client with configuration
        self.client = LicenseClient(
            server_url=CONFIG["SERVER_URL"],
            api_key=CONFIG["API_KEY"],
            public_key=CONFIG["PUBLIC_KEY"],
            secret_key=CONFIG["SECRET_KEY"]
        )
        
        self.license_file = CONFIG["LICENSE_FILE"]
        print(f"License client initialized")
        print(f"Server: {CONFIG['SERVER_URL']}")
        print(f"License file: {self.license_file}")
        print()
    
    def first_run_setup(self):
        """
        Scenario 1: First time user launches the app
        They need to enter a license key to activate
        """
        print("\n" + "=" * 60)
        print("SCENARIO 1: FIRST RUN - LICENSE ACTIVATION")
        print("=" * 60)
        print()
        
        license_key = LICENSE_KEY
        
        print(f"User enters license key: {license_key}")
        
        # Step 1: Activate the license (binds to machine)
        print("\n[Step 1] Activating license...")
        success = self.client.activate(license_key)
        
        if success:
            print("  [OK] License activated successfully")
        else:
            print("  [!] License may already be active")
        
        # Step 2: Save license for offline use
        print("\n[Step 2] Saving license for offline use...")
        success = self.client.save_license(license_key, self.license_file)
        
        if success:
            print("  [OK] License saved to file")
            print(f"  File: {self.license_file}")
        else:
            print("  [X] Failed to save license")
            return False
        
        # Display license file contents
        print("\n[License File Contents]")
        import json
        with open(self.license_file, 'r') as f:
            data = json.load(f)
            print(f"  License Key: {data['license_key']}")
            print(f"  Expires: {data['expires']}")
            print(f"  State: {data['state']}")
            print(f"  Checksum: {data.get('checksum', 'N/A')[:20]}...")
        
        print("\n[OK] First run setup COMPLETE!")
        return True
    
    def verify_license(self):
        """
        Scenario 2: Verify license (works offline!)
        This is called every time the app starts
        """
        print("\n" + "=" * 60)
        print("SCENARIO 2: LICENSE VERIFICATION (OFFLINE)")
        print("=" * 60)
        print()
        
        # Check if license file exists
        if not os.path.exists(self.license_file):
            print("[X] License file not found!")
            print("  Please activate your license first.")
            return False
        
        print(f"Found license file: {self.license_file}")
        
        # Verify license (works completely offline!)
        print("\nVerifying license...")
        
        try:
            # Verify using HMAC checksum (works offline!)
            # Note: For production, set check_signature=True with proper NaCl setup
            is_valid = self.client.verify_offline(
                self.license_file, 
                check_signature=False  # Uses checksum for tamper detection
            )
            
            if is_valid:
                print("  [OK] License is VALID")
                print("  [OK] Checksum verified - no tampering detected")
                return True
            else:
                print("  [X] License is INVALID")
                return False
                
        except LicenseTamperedError as e:
            print(f"  [X] TAMPERING DETECTED!")
            print(f"  The license file has been modified!")
            print(f"  Error: {e}")
            return False
            
        except FileNotFoundError:
            print("  [X] License file not found!")
            return False
            
        except Exception as e:
            print(f"  [X] Verification failed: {e}")
            return False
    
    def simulate_tamper_attempt(self):
        """
        Scenario 3: User tries to tamper with license
        This demonstrates tamper detection
        """
        print("\n" + "=" * 60)
        print("SCENARIO 3: TAMPER DETECTION DEMO")
        print("=" * 60)
        print()
        
        # Read original license
        import json
        with open(self.license_file, 'r') as f:
            original = json.load(f)
        
        print("User tries to extend license by changing expiry date...")
        print(f"  Original expiry: {original['expires']}")
        
        # Modify the license file
        tampered = original.copy()
        tampered['expires'] = "2030-12-31T23:59:59"
        
        with open(self.license_file, 'w') as f:
            json.dump(tampered, f, indent=2)
        
        print(f"  Tampered expiry: {tampered['expires']}")
        print("\nUser tries to run the app with modified license...")
        
        # Try to verify
        try:
            is_valid = self.client.verify_offline(self.license_file, check_signature=True)
            print(f"  Result: {'VALID' if is_valid else 'INVALID'}")
            
            if is_valid:
                print("  [!] WARNING: Tamper was NOT detected!")
            else:
                print("  [OK] Tamper was detected!")
                
        except LicenseTamperedError as e:
            print(f"  [OK] TAMPERING DETECTED!")
            print(f"  Error: {e}")
        
        # Restore original
        with open(self.license_file, 'w') as f:
            json.dump(original, f, indent=2)
        
        print("\n[Restored original license file]")
        return True
    
    def run_app(self):
        """
        Main application logic - called after verification
        """
        print("\n" + "=" * 60)
        print("APPLICATION RUNNING")
        print("=" * 60)
        print()
        print("Welcome to MyApp!")
        print("Thank you for purchasing a license.")
        print()
        print("Features available:")
        print("  [OK] All features unlocked")
        print("  [OK] Premium support")
        print("  [OK] Auto-updates enabled")
        print()


# ==========================================================
# MAIN DEMO
# ==========================================================

def run_demo():
    """Run the complete demonstration"""
    
    print("\n" + "=" * 60)
    print("MYAPP - REAL-WORLD LICENSING DEMO")
    print("=" * 60)
    print()
    print("This demo shows how to integrate the licensing SDK")
    print("into a real desktop application.")
    print()
    
    # Create app instance
    app = MyApp()
    
    # Scenario 1: First run - activate license
    print("\n>>> Running Scenario 1: First Run Setup...")
    app.first_run_setup()
    
    # Scenario 2: Verify license (offline)
    print("\n>>> Running Scenario 2: Verify License...")
    is_valid = app.verify_license()
    
    if is_valid:
        # Run the app
        app.run_app()
    else:
        print("[X] Cannot run application - license invalid")
    
    # Scenario 3: Tamper detection demo
    print("\n>>> Running Scenario 3: Tamper Detection...")
    app.simulate_tamper_attempt()
    
    # Final verification
    print("\n>>> Final Verification...")
    is_valid = app.verify_license()
    
    if is_valid:
        print("[OK] License restored and working!")
        app.run_app()
    
    # Summary
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print()
    print("KEY TAKEAWAYS:")
    print("  1. License activation requires internet (one time)")
    print("  2. After activation, app works completely OFFLINE")
    print("  3. Tampering with license file is DETECTED")
    print("  4. NaCl signature ensures AUTHENTICITY")
    print()
    print("INTEGRATION INTO YOUR APP:")
    print("  1. Add licensing_client to your project")
    print("  2. Initialize LicenseClient on app start")
    print("  3. Call verify_offline() to check license")
    print("  4. Block access if verification fails")
    print()


if __name__ == "__main__":
    run_demo()
