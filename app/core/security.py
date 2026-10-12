from datetime import datetime, timedelta, timezone

import jwt
from app.core.config import settings
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_access_token(user_id: int) -> str:   

    ahora = datetime.now(timezone.utc)
    vence = ahora + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {"sub": str(user_id), "exp": vence}

    token = jwt.encode(payload, settings.secret_key, algorithm = settings.algorithm)

    return token


def get_current_user(token:str = Depends(oauth2_scheme)) -> int:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms = [settings.algorithm])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, 
                            detail="Token Invalido o Vencido",
                            headers={"WWW-Authenticate": "Bearer"}
                            )
    user_id = int(payload["sub"])    

    return user_id


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)
