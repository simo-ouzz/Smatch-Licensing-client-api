from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from licensing_api.models.user_models import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyResponse,
)
from licensing_api.services import auth_service
from licensing_api.core.security import get_current_user

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post(
    "",
    response_model=APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_api_key(
    payload: APIKeyCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["sub"])
    result = auth_service.create_api_key(
        user_id=user_id,
        name=payload.name,
        expires_at=payload.expires_at,
    )
    return APIKeyCreateResponse(
        key_id=result["key_id"],
        api_key=result["api_key"],
        secret=result["secret"],
        name=result["name"],
        expires_at=result["expires_at"],
    )


@router.get(
    "",
    response_model=List[APIKeyResponse],
)
def list_api_keys(
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["sub"])
    keys = auth_service.list_api_keys(user_id)
    return [APIKeyResponse(**key) for key in keys]


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_api_key(
    key_id: int,
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["sub"])
    deleted = auth_service.delete_api_key(key_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    return None
