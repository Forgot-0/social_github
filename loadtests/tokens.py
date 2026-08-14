"""Access token minting for load tests.

Reuses the application's own ``JWTManager`` and ``UserJWTData`` so the token
contract is not duplicated. ``JWTManager.validate_token`` performs no session
or DB lookup (see ``app/core/services/auth/depends.py`` and
``app/chats/routes/v1/ws.py``), so offline minting is sufficient for both REST
and websocket auth.
"""

from __future__ import annotations

import time
from uuid import uuid4

from app.core.services.auth.dto import JwtTokenType, UserJWTData
from app.core.services.auth.jwt_manager import JWTManager

from loadtests.config import config

_manager = JWTManager()

# Permissions granted to seeded users. Chat-level access comes from the
# chat_members role, so no global chat:* permission is handed out here: that
# would take the ChatAccessService global-admin shortcut and skip the code path
# real users hit.
_DEFAULT_PERMISSIONS: list[str] = []
_DEFAULT_ROLES: list[str] = ["user"]


def mint_access_token(
    user_id: int,
    username: str,
    *,
    device_id: str | None = None,
    ttl_seconds: int | None = None,
) -> str:
    now = int(time.time())
    ttl = ttl_seconds if ttl_seconds is not None else config.token_ttl_seconds

    user_data = UserJWTData(
        id=str(user_id),
        username=username,
        roles=list(_DEFAULT_ROLES),
        permissions=list(_DEFAULT_PERMISSIONS),
        security_level=1,
        device_id=device_id or f"lt-{uuid4().hex[:12]}",
    )

    payload = {
        **user_data.to_dict(),
        "type": JwtTokenType.ACCESS.value,
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + ttl,
    }
    return _manager.encode(payload)