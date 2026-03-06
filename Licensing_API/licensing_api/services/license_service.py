from __future__ import annotations

from typing import Any, Dict, List

import psycopg2

import Cryptographyyy as core
from licensing_api.models.license_models import LicenseCreateRequest, LicenseTypeEnum


class LicenseNotFoundError(Exception):
    """Raised when a license cannot be found in the database."""


class ProductNotFoundError(Exception):
    """Raised when a product cannot be found in the database."""


class ProductDeleteError(Exception):
    """Raised when a product cannot be safely deleted."""


class DatabaseError(Exception):
    """Wrapper around low-level database errors."""


def _wrap_db_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except psycopg2.Error as exc:  # type: ignore[attr-defined]
            raise DatabaseError(str(exc)) from exc

    return wrapper


@_wrap_db_errors
def create_license_service(payload: LicenseCreateRequest) -> Dict[str, Any]:
    generated = core.generate_license()

    core.insert_license(
        generated["license_key"],
        generated["license_id_hex"],
        generated["signature_hex"],
        payload.company_name,
        payload.email,
        payload.product_id,
        payload.license_type.value,
        payload.period_days,
        payload.grace_period_days,
    )

    return generated


@_wrap_db_errors
def get_license_details_service(license_key: str) -> Dict[str, Any]:
    details = core.get_license_details(license_key)
    if not details:
        raise LicenseNotFoundError()

    if hasattr(details["creation_date"], "isoformat"):
        details["creation_date"] = details["creation_date"].isoformat()
    if details.get("activation_date") and hasattr(details["activation_date"], "isoformat"):
        details["activation_date"] = details["activation_date"].isoformat()
    if hasattr(details["expiry_date"], "isoformat"):
        details["expiry_date"] = details["expiry_date"].isoformat()

    return details


@_wrap_db_errors
def list_licenses_service(limit: int, offset: int) -> List[Dict[str, Any]]:
    rows = core.list_licenses(limit=limit, offset=offset)
    result: List[Dict[str, Any]] = []
    for license_key, company_name, state, expiry_date in rows:
        result.append(
            {
                "license_key": license_key,
                "company_name": company_name,
                "state": state,
                "expiry_date": expiry_date.isoformat() if hasattr(expiry_date, "isoformat") else str(expiry_date),
            }
        )
    return result


@_wrap_db_errors
def get_licenses_by_product_service(product_id: int) -> List[Dict[str, Any]]:
    import os
    
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        database=os.getenv("DB_NAME", "licenses_db"),
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "@@MOHAMMED12@@")
    )
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    license_key,
                    company_name,
                    license_type,
                    state,
                    is_revoked,
                    creation_date,
                    activation_date,
                    expiry_date,
                    grace_period_in_days,
                    product_id
                FROM public.licenses
                WHERE product_id = %s
                ORDER BY creation_date DESC
            """, (product_id,))
            rows = cur.fetchall()
    
    result = []
    for row in rows:
        result.append({
            "license_key": row[0],
            "company_name": row[1],
            "license_type": row[2],
            "state": row[3],
            "is_revoked": row[4],
            "creation_date": row[5].isoformat() if hasattr(row[5], "isoformat") else str(row[5]),
            "activation_date": row[6].isoformat() if row[6] and hasattr(row[6], "isoformat") else None,
            "expiry_date": row[7].isoformat() if hasattr(row[7], "isoformat") else str(row[7]),
            "grace_period_days": row[8],
            "product_id": row[9]
        })
    return result


@_wrap_db_errors
def activate_license_service(license_key: str) -> bool:
    success = core.activate_license(license_key)
    if not success:
        raise LicenseNotFoundError()
    return success


@_wrap_db_errors
def revoke_license_service(license_key: str, reason: str) -> None:
    success = core.revoke_license(license_key, reason)
    if not success:
        raise LicenseNotFoundError()


@_wrap_db_errors
def restore_license_service(license_key: str) -> None:
    success = core.restore_license(license_key)
    if not success:
        raise LicenseNotFoundError()


@_wrap_db_errors
def suspend_license_service(license_key: str) -> None:
    success = core.suspend_license(license_key)
    if not success:
        raise LicenseNotFoundError()


@_wrap_db_errors
def unsuspend_license_service(license_key: str) -> None:
    success = core.unsuspend_license(license_key)
    if not success:
        raise LicenseNotFoundError()


@_wrap_db_errors
def extend_license_service(license_key: str, extra_days: int) -> bool:
    success = core.extend_license(license_key, extra_days)
    if not success:
        raise LicenseNotFoundError()
    return success


@_wrap_db_errors
def update_license_type_service(license_key: str, license_type: LicenseTypeEnum) -> None:
    success = core.update_license_type(license_key, license_type.value)
    if not success:
        raise LicenseNotFoundError()


@_wrap_db_errors
def validate_license_service(license_key: str) -> Dict[str, Any]:
    result = core.validate_license_server_side(license_key)
    return result


@_wrap_db_errors
def create_product_service(product_name: str, product_code: str) -> Dict[str, Any]:
    product = core.create_product(product_name, product_code)
    return product


@_wrap_db_errors
def get_product_service(product_id: int) -> Dict[str, Any]:
    product = core.get_product(product_id)
    if not product:
        raise ProductNotFoundError()
    return product


@_wrap_db_errors
def list_products_service() -> List[Dict[str, Any]]:
    rows = core.list_products()
    result: List[Dict[str, Any]] = []
    for product_id, product_name, product_code, creation_date in rows:
        result.append(
            {
                "product_id": product_id,
                "product_name": product_name,
                "product_code": product_code,
                "creation_date": creation_date,
            }
        )
    return result


@_wrap_db_errors
def update_product_service(product_id: int, product_name: str) -> Dict[str, Any]:
    success = core.update_product(product_id, product_name)
    if not success:
        raise ProductNotFoundError()
    product = core.get_product(product_id)
    if not product:
        raise ProductNotFoundError()
    return product


@_wrap_db_errors
def delete_product_service(product_id: int) -> Dict[str, Any]:
    result = core.delete_product(product_id)

    if result.get("reason") == "Product not found":
        raise ProductNotFoundError()

    if not result.get("success"):
        raise ProductDeleteError(result.get("reason", "Unable to delete product."))

    return result


@_wrap_db_errors
def bind_machine_service(license_key: str, mac_address: str, machine_name: str = None) -> Dict[str, Any]:
    result = core.bind_machine_to_license(license_key, mac_address, machine_name)
    if not result.get("success"):
        if result.get("reason") == "license_not_found":
            raise LicenseNotFoundError()
    return result


@_wrap_db_errors
def unbind_machine_service(license_key: str, mac_address: str) -> bool:
    success = core.unbind_machine_from_license(license_key, mac_address)
    if not success:
        raise LicenseNotFoundError()
    return success


@_wrap_db_errors
def reset_machines_service(license_key: str) -> bool:
    return core.reset_all_machines(license_key)


@_wrap_db_errors
def list_machines_service(license_key: str) -> List[Dict[str, Any]]:
    return core.list_license_machines(license_key)


@_wrap_db_errors
def update_max_machines_service(license_key: str, max_machines: int) -> bool:
    success = core.update_max_machines(license_key, max_machines)
    if not success:
        raise LicenseNotFoundError()
    return success


@_wrap_db_errors
def check_machine_binding_service(license_key: str, mac_address: str) -> Dict[str, Any]:
    return core.check_machine_binding(license_key, mac_address)


@_wrap_db_errors
def get_machine_count_service(license_key: str) -> int:
    return core.get_machine_count(license_key)


# Audit Log Service Functions

@_wrap_db_errors
def log_audit_event_service(
    license_key: str,
    event_type: str,
    mac_address: str = None,
    ip_address: str = None,
    user_agent: str = None,
    success: bool = True,
    details: dict = None,
    is_offline: bool = False
):
    """Log an audit event."""
    core.log_audit_event(
        license_key=license_key,
        event_type=event_type,
        mac_address=mac_address,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        details=details,
        is_offline=is_offline
    )


@_wrap_db_errors
def get_license_audit_logs_service(license_key: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Get audit logs for a specific license."""
    return core.get_license_audit_logs(license_key, limit, offset)


@_wrap_db_errors
def get_all_audit_logs_service(
    search: str = None,
    event_type: str = None,
    license_key: str = None,
    is_offline: bool = None,
    from_date: str = None,
    to_date: str = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get all audit logs with filters."""
    return core.get_all_audit_logs(
        search=search,
        event_type=event_type,
        license_key=license_key,
        is_offline=is_offline,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset
    )


@_wrap_db_errors
def get_audit_stats_service(license_key: str = None) -> dict:
    """Get audit statistics."""
    return core.get_audit_stats(license_key)

