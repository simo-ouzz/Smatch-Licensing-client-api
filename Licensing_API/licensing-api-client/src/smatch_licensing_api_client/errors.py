"""
Custom exceptions for the licensing API client.
"""


class LicenseError(Exception):
    """Base exception for all license-related errors."""
    pass


class LicenseServerError(LicenseError):
    """Raised when the license server returns an error."""
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class LicenseInvalidError(LicenseError):
    """Raised when the license key is invalid."""
    pass


class LicenseExpiredError(LicenseError):
    """Raised when the license has expired."""
    pass


class LicenseRevokedError(LicenseError):
    """Raised when the license has been revoked."""
    pass


class LicenseNotFoundError(LicenseError):
    """Raised when the license key is not found."""
    pass


class LicenseTamperedError(LicenseError):
    """Raised when the license data has been tampered with."""
    pass


class NetworkError(LicenseError):
    """Raised when there's a network connectivity issue."""
    pass


class AuthenticationError(LicenseError):
    """Raised when API key is invalid or missing."""
    pass


class OfflineLicenseError(LicenseError):
    """Raised when offline license verification fails."""
    pass
