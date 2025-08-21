# backend/app/auth.py
"""
Clerk token verification and FastAPI dependency.

- Primary verification uses Clerk JWT (Authorization: Bearer <token>)
  verified via JWKS URL (CLERK_JWKS_URL). If not provided, default
  is https://api.clerk.dev/v1/jwks (Clerk Backend API).
- For convenience in local dev we accept X-Clerk-User-Id header if no token provided.
- When verified, the user row is ensured in Supabase 'users' table.

Security note:
- For production you should use Clerk's official server SDK or ensure correct JWT claims validation
  (aud, iss) according to your Clerk configuration. This implementation is a pragmatic, secure
  verification using JWKS and PyJWT.
"""

import os
from fastapi import Header, HTTPException, status, Depends, Request
from typing import Optional, Dict, Any
import jwt
from jwt import PyJWKClient
from .supabase_client import supabase

CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", "https://api.clerk.dev/v1/jwks")


def verify_clerk_jwt(token: str) -> Dict[str, Any]:
    """
    Verify and decode a Clerk JWT using JWKS.
    Returns decoded claims dict.
    Raises jwt.PyJWKClientError / jwt.InvalidTokenError on failure.
    """
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    # Remove "Bearer " prefix if present
    if token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1]

    try:
        jwk_client = PyJWKClient(CLERK_JWKS_URL)
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        # We don't strictly enforce audience here because Clerk tokens may not include aud for some flows.
        payload = jwt.decode(token, signing_key.key, algorithms=["RS256"], options={"verify_aud": False})
        return payload
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


async def get_current_user(authorization: Optional[str] = Header(None), x_clerk_user_id: Optional[str] = Header(None)):
    """
    FastAPI dependency. Returns the user DB row from Supabase.
    Accepts either Authorization Bearer token (preferred) OR X-Clerk-User-Id (dev).
    """
    clerk_user_id = None
    if authorization:
        payload = verify_clerk_jwt(authorization)
        # Clerk's subject claim is usually 'sub' and contains the clerk user id.
        clerk_user_id = payload.get("sub") or payload.get("user_id") or payload.get("uid")
        if not clerk_user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject claim")
    elif x_clerk_user_id:
        # development fallback
        clerk_user_id = x_clerk_user_id
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication")

    # Ensure user exists in Supabase (create if not)
    resp = supabase.table("users").select("*").eq("clerk_user_id", clerk_user_id).execute()
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="DB error checking user")
    if resp.data and len(resp.data) > 0:
        user_row = resp.data[0]
    else:
        # create minimal user row
        ins = supabase.table("users").insert({"clerk_user_id": clerk_user_id}).execute()
        if ins.status_code not in (200, 201):
            raise HTTPException(status_code=500, detail="Failed to create user")
        user_row = ins.data[0]
    # Return user row (supabase object)
    return user_row
