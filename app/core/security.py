from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings
from app.schemas import Token

password_hash = PasswordHash.recommended()

def create_access_token(user_id: int) -> Token:

    ahora = datetime.now(timezone.utc)
    vence = ahora + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {"sub": str(user_id), "exp": vence}

    token = jwt.encode(payload, settings.secret_key, algorithm = settings.algorithm)

    return token

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)
