from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status

from licensing_api.core.security import get_current_user, require_admin
from licensing_api.models.product_models import (
    ProductCreateRequest,
    ProductCreateResponse,
    ProductDeleteResponse,
    ProductDetailsResponse,
    ProductListItem,
    ProductUpdateRequest,
)
from licensing_api.services.license_service import (
    DatabaseError,
    ProductDeleteError,
    ProductNotFoundError,
    create_product_service,
    delete_product_service,
    get_product_service,
    list_products_service,
    update_product_service,
    get_licenses_by_product_service,
    list_licenses_service,
)


router = APIRouter()


@router.post(
    "",
    response_model=ProductCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(payload: ProductCreateRequest, _: dict = Depends(require_admin)) -> ProductCreateResponse:
    try:
        product = create_product_service(
            product_name=payload.product_name,
            product_code=payload.product_code,
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product.",
        ) from exc

    return ProductCreateResponse(**product)


@router.get("", response_model=List[ProductListItem])
def list_products(_: dict = Depends(require_admin)) -> List[ProductListItem]:
    try:
        rows = list_products_service()
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list products.",
        ) from exc

    return [ProductListItem(**row) for row in rows]


@router.get(
    "/{product_id}",
    response_model=ProductDetailsResponse,
)
def get_product(
    product_id: int = Path(..., ge=1),
    _: dict = Depends(require_admin),
) -> ProductDetailsResponse:
    try:
        product = get_product_service(product_id)
    except ProductNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch product.",
        ) from exc

    return ProductDetailsResponse(**product)


@router.get(
    "/{product_id}/licenses",
)
def get_product_licenses(
    product_id: int = Path(..., ge=1),
    _: dict = Depends(require_admin),
):
    try:
        get_product_service(product_id)
    except ProductNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch licenses.",
        ) from exc
    
    try:
        licenses = get_licenses_by_product_service(product_id)
        return licenses
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch licenses.",
        ) from exc


@router.patch(
    "/{product_id}",
    response_model=ProductDetailsResponse,
)
def update_product(
    payload: ProductUpdateRequest,
    product_id: int = Path(..., ge=1),
    _: dict = Depends(require_admin),
) -> ProductDetailsResponse:
    try:
        updated = update_product_service(product_id, payload.product_name)
    except ProductNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product.",
        ) from exc

    return ProductDetailsResponse(**updated)


@router.delete(
    "/{product_id}",
    response_model=ProductDeleteResponse,
)
def delete_product(
    product_id: int = Path(..., ge=1),
    _: dict = Depends(require_admin),
) -> ProductDeleteResponse:
    try:
        result = delete_product_service(product_id)
    except ProductNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    except ProductDeleteError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product.",
        ) from exc

    return ProductDeleteResponse(**result)

