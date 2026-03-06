from smatch_licensing_api_client import LicenseClient

client = LicenseClient(
    server_url=" http://localhost:7777",
    api_key="sk_Ik9EfY44Hd-OotHqvHYqKoXOI0GNkVlSfGc3PPzc9Tw",
    secret_key="..."  # Get from /licenses/secret-key
)

# First time - user needs internet
license_key = "BGYE_M4UPF_FI3AH_GKU2G_2A6AE"
client.activate(license_key)

# Save for offline use
client.save_license(license_key, "license.dat")

# Later - offline verification
if client.verify_offline("license.dat"):
    print("License valid!")
else:
    print("License invalid or tampered!")