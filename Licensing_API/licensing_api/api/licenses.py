from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from licensing_api.core.security import (
    require_admin,
    rate_limiter_validate_license,
)
from licensing_api.models.license_models import (
    LicenseActivateResponse,
    LicenseBaseInfo,
    LicenseCreateRequest,
    LicenseCreateResponse,
    LicenseDetailsResponse,
    LicenseExtendRequest,
    LicenseListItem,
    LicenseRevokeRequest,
    LicenseRestoreResponse,
    LicenseStateChangeResponse,
    LicenseTypeUpdateRequest,
    LicenseValidationRequest,
    LicenseValidationResponse,
)
from licensing_api.services.license_service import (
    DatabaseError,
    LicenseNotFoundError,
    create_license_service,
    extend_license_service,
    get_license_details_service,
    list_licenses_service,
    revoke_license_service,
    restore_license_service,
    suspend_license_service,
    unsuspend_license_service,
    update_license_type_service,
    validate_license_service,
    activate_license_service,
)


router = APIRouter()


@router.post(
    "",
    response_model=LicenseCreateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_license(payload: LicenseCreateRequest) -> LicenseCreateResponse:
    try:
        generated = create_license_service(payload)
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create license.",
        ) from exc

    return LicenseCreateResponse(**generated)


@router.get(
    "/{license_key}",
    response_model=LicenseDetailsResponse,
    dependencies=[Depends(require_admin)],
)
def get_license(license_key: str) -> LicenseDetailsResponse:
    try:
        details = get_license_details_service(license_key)
    except LicenseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found.",
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch license details.",
        ) from exc

    return LicenseDetailsResponse(**details)


@router.get(
    "",
    response_model=List[LicenseListItem],
    dependencies=[Depends(require_admin)],
)
def list_licenses(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> List[LicenseListItem]:
    try:
        rows = list_licenses_service(limit=limit, offset=offset)
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list licenses.",
        ) from exc

    return [LicenseListItem(**row) for row in rows]


@router.post(
    "/{license_key}/activate",
    response_model=LicenseActivateResponse,
    dependencies=[Depends(require_admin)],
)
def activate_license(license_key: str) -> LicenseActivateResponse:
    try:
        activated = activate_license_service(license_key)
    except LicenseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found.",
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate license.",
        ) from exc

    return LicenseActivateResponse(status="activated") if activated else LicenseActivateResponse(
        status="already_active"
    )


@router.post(
    "/{license_key}/revoke",
    response_model=LicenseStateChangeResponse,
    dependencies=[Depends(require_admin)],
)
def revoke_license(
    license_key: str,
    payload: LicenseRevokeRequest,
) -> LicenseStateChangeResponse:
    try:
        revoke_license_service(license_key, payload.reason)
    except LicenseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found.",
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke license.",
        ) from exc

    return LicenseStateChangeResponse(status="revoked")


@router.post(
    "/{license_key}/restore",
    response_model=LicenseRestoreResponse,
    dependencies=[Depends(require_admin)],
)
def restore_license(license_key: str) -> LicenseRestoreResponse:
    try:
        restore_license_service(license_key)
    except LicenseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found.",
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore license.",
        ) from exc

    return LicenseRestoreResponse(status="restored")


@router.post(
    "/{license_key}/suspend",
    response_model=LicenseStateChangeResponse,
    dependencies=[Depends(require_admin)],
)
def suspend_license(license_key: str) -> LicenseStateChangeResponse:
    try:
        suspend_license_service(license_key)
    except LicenseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found.",
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend license.",
        ) from exc

    return LicenseStateChangeResponse(status="suspended")


@router.post(
    "/{license_key}/unsuspend",
    response_model=LicenseStateChangeResponse,
    dependencies=[Depends(require_admin)],
)
def unsuspend_license(license_key: str) -> LicenseStateChangeResponse:
    try:
        unsuspend_license_service(license_key)
    except LicenseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found.",
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unsuspend license.",
        ) from exc

    return LicenseStateChangeResponse(status="unsuspended")


@router.post(
    "/{license_key}/extend",
    response_model=LicenseStateChangeResponse,
    dependencies=[Depends(require_admin)],
)
def extend_license(
    license_key: str,
    payload: LicenseExtendRequest,
) -> LicenseStateChangeResponse:
    try:
        extended = extend_license_service(license_key, payload.extra_days)
    except LicenseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found.",
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extend license.",
        ) from exc

    if not extended:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License could not be extended.",
        )

    return LicenseStateChangeResponse(status="extended")


@router.patch(
    "/{license_key}/type",
    response_model=LicenseStateChangeResponse,
    dependencies=[Depends(require_admin)],
)
def update_license_type(
    license_key: str,
    payload: LicenseTypeUpdateRequest,
) -> LicenseStateChangeResponse:
    try:
        update_license_type_service(license_key, payload.license_type)
    except LicenseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found.",
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update license type.",
        ) from exc

    return LicenseStateChangeResponse(status="type_updated")


@router.post(
    "/validate",
    response_model=LicenseValidationResponse,
    status_code=status.HTTP_200_OK,
)
async def validate_license(
    payload: LicenseValidationRequest,
    request: Request,
    _: None = Depends(rate_limiter_validate_license),
) -> LicenseValidationResponse:
    try:
        result = validate_license_service(payload.license_key)
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate license.",
        ) from exc

    return LicenseValidationResponse(**result)

