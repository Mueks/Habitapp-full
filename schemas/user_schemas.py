from sqlmodel import SQLModel, Field


class UserUpdate(SQLModel):
    full_name: str | None = Field(default=None, min_length=3)
    timezone: str | None = Field(default=None, min_length=3)


class TokenRefreshResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
