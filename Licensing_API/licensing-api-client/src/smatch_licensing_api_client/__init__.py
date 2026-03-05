"""
smatch-licensing-api-client

Python client SDK for licensing API.
"""
from smatch_licensing_api_client.client import LicenseClient, Helpers
from smatch_licensing_api_client.models import LicenseResponse, LicenseKey, OfflineLicenseManager
from smatch_licensing_api_client.errors import (
    LicenseError,
    LicenseServerError,
    LicenseInvalidError,
    LicenseExpiredError,
    LicenseRevokedError,
    LicenseNotFoundError,
    LicenseTamperedError,
    NetworkError,
    AuthenticationError,
    OfflineLicenseError,
)

__version__ = "1.0.0"
__author__ = "Your Company"

__all__ = [
    # Client
    "LicenseClient",
    "Helpers",
    # Models
    "LicenseResponse",
    "LicenseKey",
    "OfflineLicenseManager",
    # Errors
    "LicenseError",
    "LicenseServerError",
    "LicenseInvalidError",
    "LicenseExpiredError",
    "LicenseRevokedError",
    "LicenseNotFoundError",
    "LicenseTamperedError",
    "NetworkError",
    "AuthenticationError",
    "OfflineLicenseError",
]
