import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import get_settings

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict[str, Any]:
    if credentials is None:
        settings = get_settings()
        if not settings.supabase_url and not settings.supabase_anon_key and not settings.supabase_jwt_secret:
            return {"sub": "anonymous"}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in to continue")
    settings = get_settings()
    if settings.supabase_url and settings.supabase_anon_key:
        try:
            request = Request(
                f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
                headers={
                    "apikey": settings.supabase_anon_key,
                    "Authorization": f"Bearer {credentials.credentials}",
                },
            )
            with urlopen(request, timeout=5) as response:
                return json.loads(response.read())
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Supabase session") from exc
    if not settings.supabase_jwt_secret:
        return {"sub": "anonymous"}
    try:
        return jwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Supabase session") from exc


def user_id(user: dict[str, Any]) -> str:
    return str(user["sub"])


def scope_id(user: dict[str, Any]) -> str | None:
    return None if user_id(user) == "anonymous" else user_id(user)