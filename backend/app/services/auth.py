from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, TokenData


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
   def __init__(self, db: AsyncSession):
      self.db = db

   def verify_password(self, plain_password: str, hashed_password: str) -> bool:
      return pwd_context.verify(plain_password, hashed_password)

   def get_password_hash(self, password: str) -> str:
      return pwd_context.hash(password)

   def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
      to_encode = data.copy()
      if expires_delta:
         expire = datetime.utcnow() + expires_delta
      else:
         expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
      to_encode.update({"exp": expire})
      encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
      return encoded_jwt

   @staticmethod
   def decode_token(token: str) -> Optional[TokenData]:
      try:
         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
         user_id: str = payload.get("sub")
         if user_id is None:
            return None
         return TokenData(user_id=UUID(user_id))
      except JWTError:
         return None

   async def get_user_by_email(self, email: str) -> Optional[User]:
      result = await self.db.execute(select(User).where(User.email == email))
      return result.scalar_one_or_none()

   async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
      result = await self.db.execute(select(User).where(User.id == user_id))
      return result.scalar_one_or_none()

   async def create_user(self, user_data: UserCreate) -> User:
      hashed_password = self.get_password_hash(user_data.password)
      user = User(
         email=user_data.email,
         hashed_password=hashed_password
      )
      self.db.add(user)
      await self.db.commit()
      await self.db.refresh(user)
      return user

   async def authenticate_user(self, email: str, password: str) -> Optional[User]:
      user = await self.get_user_by_email(email)
      if not user:
         return None
      if not self.verify_password(password, user.hashed_password):
         return None
      return user

