from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
   email: EmailStr
   password: str


class UserResponse(BaseModel):
   id: UUID
   email: str
   created_at: datetime

   class Config:
      from_attributes = True


class Token(BaseModel):
   access_token: str
   token_type: str = "bearer"


class TokenData(BaseModel):
   user_id: Optional[UUID] = None

