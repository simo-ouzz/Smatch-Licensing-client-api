from smatch_licensing_api_client import LicenseClient

client = LicenseClient(
    server_url="http://localhost:8000",
    api_key="sk_Ik9EfY44Hd-OotHqvHYqKoXOI0GNkVlSfGc3PPzc9Tw",
    public_key="53b12a371b91d92c80d4afb8c12bbc3af00c1b426c4f0f1a78f1eac2239bfd9c"
)

license_key = "QWJ6W_PGOQB_O2VSX_IELIZ_556W6"

# Verify license
if client.verify(license_key):
    print("[OK] License is valid")
    
    # Activate the license
    if client.activate(license_key):
        print("[OK] License activated successfully!")
    else:
        print("[X] Failed to activate license")
else:
    print("[X] License is invalid")

# Full details
result = client.verify(license_key, full_details=True)
print(f"Valid: {result.is_valid}")
print(f"State: {result.state}")
print(f"Expires: {result.expires}")
