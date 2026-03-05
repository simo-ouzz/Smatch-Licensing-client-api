"""
Main client for the licensing API.
"""
import os
import requests
from typing import Optional, Union
from urllib.parse import urljoin

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
)


class LicenseClient:
    """
    Main client for verifying licenses against the licensing API.
    
    Example:
        >>> from licensing_api_client import LicenseClient
        >>> 
        >>> client = LicenseClient(
        ...     server_url="http://localhost:8000",
        ...     api_key="sk_your_api_key"
        ... )
        >>> 
        >>> # Simple verification
        >>> if client.verify("XXXXX_XXXXX_XXXXX_XXXXX_XXXXX"):
        ...     print("License is valid!")
        ...
        >>> # Full details
        >>> result = client.verify("XXXXX_XXXXX_XXXXX_XXXXX_XXXXX", full_details=True)
        >>> print(f"Expires: {result.expires}")
    """
    
    DEFAULT_TIMEOUT = 30
    
    def __init__(
        self,
        server_url: str,
        api_key: Optional[str] = None,
        public_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        verify_ssl: bool = True
    ):
        """
        Initialize the license client.
        
        Args:
            server_url: Base URL of the licensing API (e.g., "http://localhost:8000")
            api_key: API key for authentication (can also set via LICENSING_API_KEY env var)
            public_key: Public key for offline signature verification (hex format).
                       Get this from your Cryptographyyy.py: PUBLIC_KEY_HEX
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key or os.environ.get("LICENSING_API_KEY")
        self.public_key = public_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._offline_manager = OfflineLicenseManager(public_key=public_key)
        
        if not self.api_key:
            raise AuthenticationError(
                "API key is required. Provide it as parameter or set LICENSING_API_KEY env variable."
            )
    
    def _get_headers(self) -> dict:
        """Get request headers with API key."""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "licensing-api-client/1.0.0"
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None
    ) -> dict:
        """Make an HTTP request to the API."""
        url = urljoin(self.server_url + "/", endpoint.lstrip("/"))
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=self._get_headers(),
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            
            if response.status_code == 404:
                raise LicenseNotFoundError("License not found")
            
            if response.status_code >= 500:
                raise LicenseServerError(
                    f"Server error: {response.text}",
                    status_code=response.status_code
                )
            
            if response.status_code >= 400:
                raise LicenseError(f"Request failed: {response.text}")
            
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection failed: {str(e)}")
        except requests.exceptions.Timeout as e:
            raise NetworkError(f"Request timed out: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request failed: {str(e)}")
    
    def verify(
        self,
        key: str,
        full_details: bool = False
    ) -> Union[bool, LicenseResponse]:
        """
        Verify a license key.
        
        Args:
            key: The license key to verify (format: XXXXX_XXXXX_XXXXX_XXXXX_XXXXX)
            full_details: If True, returns LicenseResponse with full details
                         If False, returns just True/False
        
        Returns:
            If full_details=False: bool (True if valid, False if invalid)
            If full_details=True: LicenseResponse object
        
        Example:
            >>> # Simple usage
            >>> if client.verify("XXXXX_XXXXX_XXXXX_XXXXX_XXXXX"):
            ...     print("Valid!")
            ...
            >>> # Full details
            >>> result = client.verify("XXXXX_XXXXX_XXXXX_XXXXX_XXXXX", full_details=True)
            >>> print(result.expires)
            >>> print(result.remaining_days)
        """
        if not key or not isinstance(key, str):
            return False if not full_details else LicenseResponse(
                is_valid=False,
                reason="invalid_key_format"
            )
        
        key = key.strip()
        
        try:
            response = self._make_request(
                method="POST",
                endpoint="/licenses/validate",
                data={"license_key": key}
            )
            
            result = LicenseResponse.from_dict(response)
            
            if full_details:
                return result
            return result.is_valid
            
        except (LicenseNotFoundError, AuthenticationError, NetworkError):
            return False if not full_details else LicenseResponse(
                is_valid=False,
                reason="verification_failed"
            )
        except LicenseServerError:
            return False if not full_details else LicenseResponse(
                is_valid=False,
                reason="server_error"
            )
    
    def activate(self, key: str) -> bool:
        """
        Activate a license key.
        
        Args:
            key: The license key to activate
            
        Returns:
            True if activation successful, False otherwise
        
        Example:
            >>> if client.activate("XXXXX_XXXXX_XXXXX_XXXXX_XXXXX"):
            ...     print("Activated!")
        """
        if not key:
            return False
        
        key = key.strip()
        
        try:
            response = self._make_request(
                method="POST",
                endpoint=f"/licenses/{key}/activate"
            )
            return response.get("status") in ["activated", "already_active"]
        except (LicenseNotFoundError, AuthenticationError, NetworkError, LicenseServerError):
            return False
    
    def deactivate(self, key: str) -> bool:
        """
        Deactivate a license key.
        
        Args:
            key: The license key to deactivate
            
        Returns:
            True if deactivation successful, False otherwise
        """
        if not key:
            return False
        
        key = key.strip()
        
        try:
            self._make_request(
                method="POST",
                endpoint=f"/licenses/{key}/unsuspend"
            )
            return True
        except (LicenseNotFoundError, AuthenticationError, NetworkError, LicenseServerError):
            return False
    
    def get_license_details(self, key: str) -> Optional[dict]:
        """
        Get full license details from the server.
        
        Args:
            key: The license key
            
        Returns:
            Dictionary with license details or None if not found
        
        Example:
            >>> details = client.get_license_details("XXXXX_XXXXX_XXXXX_XXXXX_XXXXX")
            >>> print(details["expires"])
            >>> print(details["state"])
        """
        if not key:
            return None
        
        key = key.strip()
        
        try:
            return self._make_request(
                method="GET",
                endpoint=f"/licenses/{key}"
            )
        except (LicenseNotFoundError, AuthenticationError, NetworkError, LicenseServerError):
            return None
    
    def save_license(self, key: str, filepath: str) -> bool:
        """
        Save a license to a file for offline verification.
        
        Args:
            key: The license key to save
            filepath: Path where to save the license file
            
        Returns:
            True if saved successfully, False otherwise
        
        Example:
            >>> client.save_license("XXXXX_XXXXX_XXXXX_XXXXX_XXXXX", "license.dat")
        """
        if not key:
            return False
        
        details = self.get_license_details(key.strip())
        if not details:
            return False
        
        try:
            license_key = LicenseKey(
                license_key=details.get("license_key", key),
                license_id=details.get("license_id_hex", ""),
                signature=details.get("signature_hex", ""),
                expires=details.get("expiry_date"),
                state=details.get("state", "active"),
                is_revoked=details.get("is_revoked", False)
            )
            
            self._offline_manager.save(license_key, filepath)
            return True
        except Exception:
            return False
    
    def verify_offline(self, filepath: str, check_signature: bool = True) -> bool:
        """
        Verify a license from a saved file (offline).
        
        Args:
            filepath: Path to the saved license file
            check_signature: If True, verify cryptographic signature (requires public_key)
            
        Returns:
            True if license is valid, False otherwise
        
        Example:
            >>> if client.verify_offline("license.dat"):
            ...     print("Offline license is valid!")
        """
        license_key = self._offline_manager.load(filepath)
        
        if not license_key:
            return False
        
        is_valid, reason = self._offline_manager.verify(license_key, check_signature=check_signature)
        return is_valid
    
    def load_license(self, filepath: str) -> Optional[LicenseKey]:
        """
        Load a license from file.
        
        Args:
            filepath: Path to the license file
            
        Returns:
            LicenseKey object if loaded successfully, None otherwise
        """
        return self._offline_manager.load(filepath)


class Helpers:
    """
    Helper utilities for license verification.
    """
    
    @staticmethod
    def is_valid_key_format(key: str) -> bool:
        """
        Check if the license key format is valid.
        
        Args:
            key: The license key to check
            
        Returns:
            True if format is valid, False otherwise
        
        Example:
            >>> Helpers.is_valid_key_format("XXXXX_XXXXX_XXXXX_XXXXX_XXXXX")
            True
            >>> Helpers.is_valid_key_format("invalid")
            False
        """
        if not key or not isinstance(key, str):
            return False
        
        key = key.strip()
        
        parts = key.split("_")
        if len(parts) != 5:
            return False
        
        for part in parts:
            if len(part) != 5:
                return False
        
        return True
