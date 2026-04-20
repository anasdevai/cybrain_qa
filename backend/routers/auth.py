"""Authentication routing endpoints for user registration, login, and profile."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime, timezone

from database.config import get_db
from database.models import User
from schemas.auth import UserCreate, UserResponse, UserLogin, TokenResponse
from auth.security import (
    hash_password, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    decode_token,
    get_current_user,
    JWT_REFRESH_SECRET_KEY
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)) -> Any:
    """Create a new user."""
    # Check if user already exists
    result = await db.execute(
        select(User).where(
            or_(User.email == user_in.email, User.username == user_in.username)
        )
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        if existing_user.email == user_in.email:
            raise HTTPException(
                status_code=400,
                detail="A user with this email already exists."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="A user with this username already exists."
            )
            
    # Create new user
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        is_active=True,
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=TokenResponse)
async def login(user_login: UserLogin, db: AsyncSession = Depends(get_db)) -> Any:
    """TEMPORARY BYPASS: returns a dummy token."""
    return {
        "access_token": "dummy_access_token",
        "refresh_token": "dummy_refresh_token",
        "token_type": "bearer",
        "expires_in": 3600
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str = Body(..., embed=True), db: AsyncSession = Depends(get_db)) -> Any:
    """TEMPORARY BYPASS: returns dummy refresh tokens."""
    return {
        "access_token": "dummy_access_token",
        "refresh_token": "dummy_refresh_token",
        "token_type": "bearer",
        "expires_in": 3600
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: User = Depends(get_current_user)) -> Any:
    """Logout the user (client should discard the token locally)."""
    # For full strictness, token blacklisting in Redis would be implemented here.
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)) -> Any:
    """Get the profile of the currently logged in user."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    update_data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Update the currently logged in user's username and/or password."""
     
    new_username = update_data.get("username", "").strip()
    current_password = update_data.get("current_password", "")
    new_password = update_data.get("new_password", "")

    # Update username if provided
    if new_username and new_username != current_user.username:
        # Check uniqueness
        result = await db.execute(select(User).where(User.username == new_username))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken by another user.")
        current_user.username = new_username

    # Update password if provided
    if new_password:
        if not current_password:
            raise HTTPException(status_code=400, detail="Current password is required to set a new password.")
        if not verify_password(current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect.")
        if len(new_password) < 8:
            raise HTTPException(status_code=400, detail="New password must be at least 8 characters.")
        current_user.hashed_password = hash_password(new_password)

    await db.commit()
    await db.refresh(current_user)
    return current_user
