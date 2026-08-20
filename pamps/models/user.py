from sqlmodel import Field, SQLModel
from typing import Optional
from pamps.security import HashedPassword

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, nullable = False)
    username: str = Field(unique=True, nullable = False)
    avatar: Optional[str] = None
    bio: Optional[str] = None
    password: str = HashedPassword()