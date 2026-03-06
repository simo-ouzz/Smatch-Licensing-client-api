"""
Data models for the licensing API client.
"""
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional

from smatch_licensing_api_client.errors import LicenseTamperedError


class LicenseResponse:
    """
    Response object containing license verification results.
    
    Attributes:
        is_valid: Whether the license is valid
        license_key: The license key string
        expires: Expiration datetime
        remaining_days: Days until expiration
        state: License state (active, suspended, etc.)
        reason: If invalid, the reason (expired, revoked, etc.)
        raw_response: Raw response from server
    """
    
    def __init__(
        self,
        is_valid: bool,
        license_key: str = "",
        expires: Optional[datetime] = None,
        remaining_days: int = 0,
        state: str = "",
        reason: Optional[str] = None,
        raw_response: Optional[dict] = None
    ):
        self.is_valid = is_valid
        self.license_key = license_key
        self.expires = expires
        self.remaining_days = remaining_days
        self.state = state
        self.reason = reason
        self.raw_response = raw_response or {}
    
    def __bool__(self) -> bool:
        return self.is_valid
    
    def __repr__(self) -> str:
        return f"LicenseResponse(is_valid={self.is_valid}, expires={self.expires})"
    
    @classmethod
    def from_dict(cls, data: dict) -> "LicenseResponse":
        """Create LicenseResponse from dictionary."""
        expires = data.get("expires_at")
        if isinstance(expires, str):
            try:
                expires = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            except ValueError:
                expires = None
        
        remaining_days = 0
        if expires:
            delta = expires - datetime.now(expires.tzinfo) if expires.tzinfo else expires - datetime.now()
            remaining_days = max(0, delta.days)
        
        return cls(
            is_valid=data.get("valid", False),
            license_key=data.get("license_key", ""),
            expires=expires,
            remaining_days=remaining_days,
            state=data.get("state", ""),
            reason=data.get("reason"),
            raw_response=data
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "license_key": self.license_key,
            "expires": self.expires.isoformat() if self.expires else None,
            "remaining_days": self.remaining_days,
            "state": self.state,
            "reason": self.reason,
        }


class LicenseKey:
    """
    Represents a license key for offline verification.
    
    Attributes:
        license_key: The license key string
        license_id: License ID in hex
        signature: Cryptographic signature
        expires: Expiration datetime
        state: License state
        is_revoked: Whether license is revoked
    """
    
    def __init__(
        self,
        license_key: str,
        license_id: str = "",
        signature: str = "",
        expires: Optional[datetime] = None,
        state: str = "active",
        is_revoked: bool = False,
        raw_data: Optional[dict] = None
    ):
        self.license_key = license_key
        self.license_id = license_id
        self.signature = signature
        self.expires = expires
        self.state = state
        self.is_revoked = is_revoked
        self.raw_data = raw_data or {}
    
    def __bool__(self) -> bool:
        return not self.is_revoked and self.has_not_expired()
    
    def __repr__(self) -> str:
        return f"LicenseKey(key={self.license_key}, expires={self.expires})"
    
    def has_not_expired(self, allow_same_day: bool = True) -> bool:
        """Check if the license has not expired."""
        if not self.expires:
            return True
        
        now = datetime.now(self.expires.tzinfo) if self.expires.tzinfo else datetime.now()
        
        if allow_same_day:
            return now <= self.expires
        else:
            return now < self.expires
    
    def is_active(self) -> bool:
        """Check if license is active (not revoked, not expired)."""
        return self.state == "active" and not self.is_revoked and self.has_not_expired()
    
    @classmethod
    def load_from_string(cls, data: str) -> Optional["LicenseKey"]:
        """Load license from a string (file content)."""
        try:
            parsed = json.loads(data)
            return cls.from_dict(parsed)
        except (json.JSONDecodeError, ValueError):
            return None
    
    def save_to_string(self) -> str:
        """Save license as a string."""
        data = {
            "license_key": self.license_key,
            "license_id": self.license_id,
            "signature": self.signature,
            "expires": self.expires.isoformat() if self.expires else None,
            "state": self.state,
            "is_revoked": self.is_revoked,
        }
        return json.dumps(data, indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> "LicenseKey":
        """Create LicenseKey from dictionary."""
        expires = data.get("expires")
        if isinstance(expires, str):
            try:
                expires = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            except ValueError:
                expires = None
        
        return cls(
            license_key=data.get("license_key", ""),
            license_id=data.get("license_id", ""),
            signature=data.get("signature", ""),
            expires=expires,
            state=data.get("state", "active"),
            is_revoked=data.get("is_revoked", False),
            raw_data=data
        )


class OfflineLicenseManager:
    """
    Manages offline license file verification.
    
    Provides cryptographic signature verification and HMAC checksum to prevent tampering.
    Requires a public key to verify the license file authenticity and secret key for HMAC.
    """
    
    def __init__(self, public_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Initialize the offline license manager.
        
        Args:
            public_key: Public key for signature verification (hex format).
                       Get this from your Cryptographyyy.py: PUBLIC_KEY_HEX
            secret_key: Secret key for HMAC checksum verification.
                       Get this from server via /licenses/secret-key endpoint.
        """
        self.public_key = public_key
        self.secret_key = secret_key
    
    def verify(self, license_key: LicenseKey, check_signature: bool = True) -> tuple[bool, str]:
        """
        Verify an offline license.
        
        Args:
            license_key: The loaded license key
            check_signature: If True, verify cryptographic signature (requires public_key)
        
        Returns:
            Tuple of (is_valid: bool, reason: str)
            Reason can be: "valid", "tampered", "expired", "revoked", "suspended", "no_signature"
        """
        # Check signature first (if enabled and public_key is set)
        if check_signature and self.public_key:
            if not license_key.signature:
                return False, "no_signature"
            
            if not self._verify_signature(license_key):
                return False, "tampered"
        
        # Check revocation status
        if license_key.is_revoked:
            return False, "revoked"
        
        # Check expiry
        if not license_key.has_not_expired():
            return False, "expired"
        
        # Check suspension
        if license_key.state == "suspended":
            return False, "suspended"
        
        return True, "valid"
    
    def _verify_signature(self, license_key: LicenseKey) -> bool:
        """
        Verify the cryptographic signature of a license.
        
        Args:
            license_key: The license to verify
        
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.public_key or not license_key.signature:
            return False
        
        try:
            from nacl.signing import VerifyKey
            from nacl.exceptions import BadSignatureError
            
            verify_key = VerifyKey(bytes.fromhex(self.public_key))
            message = f"{license_key.license_key}|{license_key.license_id}"
            verify_key.verify(message.encode(), bytes.fromhex(license_key.signature))
            return True
        except (ValueError, BadSignatureError, Exception):
            return False
    
    def verify_signature_only(self, license_key: LicenseKey) -> bool:
        """
        Verify only the signature without checking expiry/revocation.
        
        Args:
            license_key: The license to verify
        
        Returns:
            True if signature is valid
        """
        return self._verify_signature(license_key)
    
    def _calculate_checksum(self, data: dict, secret_key: str) -> str:
        """
        Calculate HMAC-SHA256 checksum of license data.
        
        Args:
            data: License data dictionary
            secret_key: Secret key for HMAC
            
        Returns:
            Hex-encoded HMAC-SHA256 checksum
        """
        import hmac
        import hashlib
        
        # Create a copy without the checksum field
        data_to_sign = {k: v for k, v in data.items() if k != "checksum"}
        
        # Sort keys for consistent ordering
        import json
        message = json.dumps(data_to_sign, sort_keys=True, default=str)
        
        # Calculate HMAC
        signature = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _verify_checksum(self, data: dict, secret_key: str) -> bool:
        """
        Verify HMAC-SHA256 checksum of license data.
        
        Args:
            data: License data dictionary with checksum
            secret_key: Secret key for HMAC
            
        Returns:
            True if checksum is valid
        """
        if not secret_key or "checksum" not in data:
            return True  # No checksum to verify
        
        expected_checksum = data.get("checksum", "")
        actual_checksum = self._calculate_checksum(data, secret_key)
        
        return hmac.compare_digest(expected_checksum, actual_checksum)
    
    def save(self, license_key: LicenseKey, filepath: str, secret_key: Optional[str] = None) -> None:
        """
        Save license to file with optional HMAC checksum.
        
        Args:
            license_key: The license to save
            filepath: Path to save to
            secret_key: Secret key for HMAC checksum (uses instance secret_key if not provided)
        """
        secret = secret_key or self.secret_key
        
        # Get the data from license key
        data = {
            "license_key": license_key.license_key,
            "license_id": license_key.license_id,
            "signature": license_key.signature,
            "expires": license_key.expires.isoformat() if license_key.expires else None,
            "state": license_key.state,
            "is_revoked": license_key.is_revoked,
        }
        
        # Add checksum if secret key is available
        if secret:
            data["checksum"] = self._calculate_checksum(data, secret)
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def load(self, filepath: str, secret_key: Optional[str] = None) -> Optional[LicenseKey]:
        """
        Load license from file and verify checksum.
        
        Args:
            filepath: Path to license file
            secret_key: Secret key for HMAC verification (uses instance secret_key if not provided)
            
        Returns:
            LicenseKey if valid, None if invalid or tampered
            
        Raises:
            LicenseTamperedError: If checksum verification fails
        """
        secret = secret_key or self.secret_key
        
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            
            # Verify checksum if secret key is provided
            if secret and "checksum" in data:
                if not self._verify_checksum(data, secret):
                    raise LicenseTamperedError("License file has been tampered with - checksum mismatch")
            
            return LicenseKey.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        except LicenseTamperedError:
            raise
