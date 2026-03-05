from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from licensing_api.models.user_models import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreateRequest,
    UserResponse,
)
from licensing_api.services import auth_service
from licensing_api.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: UserCreateRequest):
    try:
        user = auth_service.register_user(
            email=payload.email,
            password=payload.password,
            role=payload.role.value,
        )
        return UserResponse(**user)
    except auth_service.UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        tokens = auth_service.login(
            email=form_data.username,
            password=form_data.password,
        )
        return TokenResponse(**tokens)
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_token(payload: RefreshTokenRequest):
    try:
        tokens = auth_service.refresh_access_token(payload.refresh_token)
        return TokenResponse(**tokens)
    except auth_service.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(current_user: dict = Depends(get_current_user)):
    auth_service.revoke_all_user_tokens(int(current_user["sub"]))
    return None


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(current_user: dict = Depends(get_current_user)):
    user = auth_service.get_user_by_id(int(current_user["sub"]))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse(**user)
