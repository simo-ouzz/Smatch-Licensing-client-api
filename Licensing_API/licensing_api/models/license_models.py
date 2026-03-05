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
    expiry_date: str
    remaining_seconds: int
    remaining_days: int
    grace_period_days: int
    product_id: int


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


class LicenseValidationResponse(BaseModel):
    valid: bool
    reason: Optional[str] = None
    state: Optional[str] = None
    expires_at: Optional[str] = None

