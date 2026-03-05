from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from licensing_api.models.user_models import (
    UserResponse,
    UserUpdateRequest,
)
from licensing_api.services import auth_service
from licensing_api.core.security import get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=List[UserResponse],
    dependencies=[Depends(require_admin)],
)
def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    users = auth_service.list_users(limit=limit, offset=offset)
    return [UserResponse(**user) for user in users]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
)
def get_user(user_id: int):
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse(**user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
):
    try:
        user = auth_service.update_user(
            user_id=user_id,
            email=payload.email,
            role=payload.role.value if payload.role else None,
            is_active=payload.is_active,
        )
        return UserResponse(**user)
    except auth_service.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_user(user_id: int):
    current_user = auth_service.get_user_by_id(int(get_current_user()["sub"]))
    if current_user and current_user["user_id"] == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    auth_service.revoke_all_user_tokens(user_id)
    return None
