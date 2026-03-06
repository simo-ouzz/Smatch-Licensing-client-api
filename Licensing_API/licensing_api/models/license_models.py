from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LicenseTypeEnum(str, Enum):
    LA = "L.A"
    LO = "L.O"
    LM = "L.M"
    LT = "L.T"


class LicenseBaseInfo(BaseModel):
    license_key: str = Field(..., description="Human-readable license key.")


class LicenseCreateRequest(BaseModel):
    company_name: str = Field(..., max_length=255)
    email: EmailStr
    product_id: int = Field(..., ge=1)
    license_type: LicenseTypeEnum
    period_days: int = Field(..., ge=1)
    grace_period_days: int = Field(0, ge=0)


class LicenseCreateResponse(LicenseBaseInfo):
    license_id_hex: str
    signature_hex: str


class LicenseDetailsResponse(BaseModel):
    license_key: str
    company_name: str
    email: EmailStr
    license_type: str
    state: str
    is_revoked: bool
    revoked_reason: Optional[str]
    creation_date: str
    activation_date: Optional[str]
    activation_mac: Optional[str] = None
    expiry_date: str
    remaining_seconds: int
    remaining_days: int
    grace_period_days: int
    product_id: int
    license_id_hex: Optional[str] = None
    signature_hex: Optional[str] = None
    max_machines: int = 1


class LicenseListItem(BaseModel):
    license_key: str
    company_name: str
    state: str
    expiry_date: str


class LicenseRevokeRequest(BaseModel):
    reason: str = Field(..., max_length=512)


class LicenseExtendRequest(BaseModel):
    extra_days: int = Field(..., ge=1)


class LicenseTypeUpdateRequest(BaseModel):
    license_type: LicenseTypeEnum


class LicenseStateChangeResponse(BaseModel):
    status: str


class LicenseActivateResponse(BaseModel):
    status: str


class LicenseRestoreResponse(BaseModel):
    status: str


class LicenseValidationRequest(BaseModel):
    license_key: str
    mac_address: Optional[str] = None


class LicenseValidationResponse(BaseModel):
    valid: bool
    reason: Optional[str] = None
    state: Optional[str] = None
    expires_at: Optional[str] = None


class LicenseActivateRequest(BaseModel):
    mac_address: Optional[str] = None


class MachineBindRequest(BaseModel):
    mac_address: str = Field(..., pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
    machine_name: Optional[str] = None


class MachineInfo(BaseModel):
    id: int
    mac_address: str
    machine_name: Optional[str]
    bound_at: str
    last_seen_at: Optional[str]
    is_active: bool


class MachineBindResponse(BaseModel):
    success: bool
    action: Optional[str] = None
    reason: Optional[str] = None


class MaxMachinesUpdateRequest(BaseModel):
    max_machines: int = Field(..., ge=0)

