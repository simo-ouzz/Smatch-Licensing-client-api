from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from licensing_api.core.security import (
    require_admin,
    require_admin_or_api_key,
    rate_limiter_validate_license,
)
from licensing_api.models.license_models import (
    LicenseActivateResponse,
    LicenseActivateRequest,
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
    MachineBindRequest,
    MachineInfo,
    MachineBindResponse,
    MaxMachinesUpdateRequest,
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
    bind_machine_service,
    unbind_machine_service,
    reset_machines_service,
    list_machines_service,
    update_max_machines_service,
    log_audit_event_service,
    get_license_audit_logs_service,
    get_all_audit_logs_service,
    get_audit_stats_service,
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
    "/secret-key",
    response_model=dict,
)
def get_offline_secret_key(
    _: None = Depends(require_admin_or_api_key),
) -> dict:
    """
    Get the secret key for offline license HMAC checksum.
    This key is required by the SDK to create tamper-proof offline license files.
    """
    from Cryptographyyy import OFFLINE_SECRET_KEY
    return {"secret_key": OFFLINE_SECRET_KEY}


@router.get(
    "/{license_key}",
    response_model=LicenseDetailsResponse,
    dependencies=[Depends(require_admin_or_api_key)],
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
)
def activate_license(
    license_key: str,
    payload: Optional[LicenseActivateRequest] = None,
) -> LicenseActivateResponse:
    mac_address = payload.mac_address if payload else None
    
    try:
        activated = activate_license_service(license_key)
        
        if mac_address:
            bind_result = bind_machine_service(license_key, mac_address)
            if not bind_result.get("success"):
                if bind_result.get("reason") == "mac_bound_to_other_license":
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"MAC address already bound to license: {bind_result.get('other_license')}",
                    )
                elif bind_result.get("reason") == "max_machines_reached":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Maximum machines ({bind_result.get('max')}) reached for this license.",
                    )
                    
    except LicenseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found.",
        )
    except HTTPException:
        raise
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
        
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", None)
        
        log_audit_event_service(
            license_key=payload.license_key,
            event_type="license_validation",
            ip_address=client_ip,
            user_agent=user_agent,
            success=result.get("is_valid", False),
            details={
                "is_valid": result.get("is_valid"),
                "state": result.get("state"),
                "product_id": result.get("product_id"),
            },
            is_offline=False
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate license.",
        ) from exc

    return LicenseValidationResponse(**result)


@router.post(
    "/offline-check",
    status_code=status.HTTP_200_OK,
)
async def log_offline_check(
    payload: dict,
    request: Request,
) -> dict:
    """Log an offline license check from the SDK."""
    license_key = payload.get("license_key")
    is_valid = payload.get("is_valid", False)
    machine_id = payload.get("machine_id")
    
    if not license_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="license_key is required.",
        )
    
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", None)
    
    log_audit_event_service(
        license_key=license_key,
        event_type="offline_license_check",
        mac_address=machine_id,
        ip_address=client_ip,
        user_agent=user_agent,
        success=is_valid,
        details={
            "is_valid": is_valid,
            "machine_id": machine_id,
            "offline_check": True,
        },
        is_offline=True
    )
    
    return {"success": True, "message": "Offline check logged."}


@router.get(
    "/{license_key}/machines",
    response_model=List[MachineInfo],
    dependencies=[Depends(require_admin_or_api_key)],
)
def list_machines(license_key: str) -> List[MachineInfo]:
    try:
        machines = list_machines_service(license_key)
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list machines.",
        ) from exc
    
    return [MachineInfo(**machine) for machine in machines]


@router.post(
    "/{license_key}/machines",
    response_model=MachineBindResponse,
    dependencies=[Depends(require_admin_or_api_key)],
)
def bind_machine(
    license_key: str,
    payload: MachineBindRequest,
) -> MachineBindResponse:
    try:
        result = bind_machine_service(license_key, payload.mac_address, payload.machine_name)
    except LicenseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found.",
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bind machine.",
        ) from exc
    
    if not result.get("success"):
        if result.get("reason") == "mac_bound_to_other_license":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"MAC address already bound to another license in the same product: {result.get('other_license')}",
            )
        elif result.get("reason") == "max_machines_reached":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Maximum machines ({result.get('max')}) reached for this license.",
            )
    
    return MachineBindResponse(
        success=True,
        action=result.get("action"),
    )


@router.delete(
    "/{license_key}/machines/{mac_address}",
    response_model=LicenseStateChangeResponse,
    dependencies=[Depends(require_admin_or_api_key)],
)
def unbind_machine(
    license_key: str,
    mac_address: str,
) -> LicenseStateChangeResponse:
    try:
        success = unbind_machine_service(license_key, mac_address)
    except LicenseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License or machine not found.",
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unbind machine.",
        ) from exc
    
    return LicenseStateChangeResponse(status="unbound")


@router.delete(
    "/{license_key}/machines",
    response_model=LicenseStateChangeResponse,
    dependencies=[Depends(require_admin_or_api_key)],
)
def reset_machines(
    license_key: str,
) -> LicenseStateChangeResponse:
    try:
        reset_machines_service(license_key)
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset machines.",
        ) from exc
    
    return LicenseStateChangeResponse(status="reset")


@router.put(
    "/{license_key}/max-machines",
    response_model=LicenseStateChangeResponse,
    dependencies=[Depends(require_admin_or_api_key)],
)
def update_max_machines(
    license_key: str,
    payload: MaxMachinesUpdateRequest,
) -> LicenseStateChangeResponse:
    try:
        success = update_max_machines_service(license_key, payload.max_machines)
    except LicenseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found.",
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update max machines.",
        ) from exc
    
    return LicenseStateChangeResponse(status="updated")


# Audit Log Endpoints

@router.get(
    "/audit/logs",
    response_model=List[dict],
    dependencies=[Depends(require_admin_or_api_key)],
)
def get_all_audit_logs(
    search: Optional[str] = None,
    event_type: Optional[str] = None,
    license_key: Optional[str] = None,
    is_offline: Optional[bool] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[dict]:
    """Get all audit logs with filters."""
    try:
        logs = get_all_audit_logs_service(
            search=search,
            event_type=event_type,
            license_key=license_key,
            is_offline=is_offline,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit logs.",
        ) from exc
    
    return logs


@router.get(
    "/audit/stats",
    response_model=dict,
    dependencies=[Depends(require_admin_or_api_key)],
)
def get_audit_stats(license_key: Optional[str] = None) -> dict:
    """Get audit statistics."""
    try:
        stats = get_audit_stats_service(license_key)
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit stats.",
        ) from exc
    
    return stats


@router.get(
    "/{license_key}/audit/logs",
    response_model=List[dict],
    dependencies=[Depends(require_admin_or_api_key)],
)
def get_license_audit_logs(
    license_key: str,
    limit: int = 100,
    offset: int = 0,
) -> List[dict]:
    """Get audit logs for a specific license."""
    try:
        logs = get_license_audit_logs_service(license_key, limit, offset)
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit logs.",
        ) from exc
    
    return logs

