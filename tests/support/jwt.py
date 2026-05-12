from app.auth.dtos.user import AuthUserJWTData
from app.auth.models.user import User

_DEFAULT_DEVICE = "Chrome/100.0"


def jwt_from_user(user: User, *, device_id: str | None = None) -> AuthUserJWTData:
    """JWT payload DTO for a persisted user (same defaults as auth integration fixtures)."""
    return AuthUserJWTData.create_from_user(user, device_id=device_id or _DEFAULT_DEVICE)
