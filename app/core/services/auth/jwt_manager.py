from dataclasses import dataclass
from typing import Any

import jwt

from app.core.services.auth.dto import JwtTokenType, Token
from app.core.services.auth.exceptions import ExpiredTokenError, InvalidTokenError


@dataclass
class JWTManager:
    jwt_secret: str
    jwt_algorithm: str

    def encode(self, payload: dict[str, Any]) -> str:
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def decode(self, token: str) -> dict[str, Any]:
        try:
            data = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
        except jwt.ExpiredSignatureError as err:
            raise ExpiredTokenError(token=token) from err
        except jwt.PyJWTError as err:
            raise InvalidTokenError(token=token) from err
        return data

    async def validate_token(self, token: str, token_type: JwtTokenType=JwtTokenType.ACCESS) -> Token:
        payload = self.decode(token)
        token_data = Token(**payload)

        if token_data.type != token_type:
            raise InvalidTokenError(token=token)

        return token_data

