from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.database import get_db, get_sync_db
from app.services.auth import AuthService
from app.models.user import User


security = HTTPBearer(auto_error=False)


async def get_current_user(
   credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
   db: AsyncSession = Depends(get_db)
) -> User:
   """Get current authenticated user."""
   if not credentials:
      raise HTTPException(
         status_code=status.HTTP_401_UNAUTHORIZED,
         detail="Not authenticated",
         headers={"WWW-Authenticate": "Bearer"},
      )

   token_data = AuthService.decode_token(credentials.credentials)
   if not token_data or not token_data.user_id:
      raise HTTPException(
         status_code=status.HTTP_401_UNAUTHORIZED,
         detail="Invalid token",
         headers={"WWW-Authenticate": "Bearer"},
      )

   auth_service = AuthService(db)
   user = await auth_service.get_user_by_id(token_data.user_id)
   if not user:
      raise HTTPException(
         status_code=status.HTTP_401_UNAUTHORIZED,
         detail="User not found",
         headers={"WWW-Authenticate": "Bearer"},
      )

   return user


async def get_optional_user(
   credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
   db: AsyncSession = Depends(get_db)
) -> Optional[User]:
   """Get current user if authenticated, None otherwise."""
   if not credentials:
      return None

   token_data = AuthService.decode_token(credentials.credentials)
   if not token_data or not token_data.user_id:
      return None

   auth_service = AuthService(db)
   return await auth_service.get_user_by_id(token_data.user_id)

