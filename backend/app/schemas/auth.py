from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: dict


def serialize_user(user) -> dict:
    from app.schemas.common import iso

    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "daily_scan_quota": user.daily_scan_quota,
        "quota_used": user.quota_used,
        "quota_used_date": iso(user.quota_used_date),
        "created_at": iso(user.created_at),
    }
