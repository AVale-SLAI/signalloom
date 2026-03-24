"""
API Key authentication middleware.

Validates Bearer token on every request via webhooks.api_keys.verify().
Whitelisted paths: /health, /v1/info, /docs, /redoc, /openapi.json, /signup, /terms, /privacy
"""
from __future__ import annotations

from starlette.authentication import AuthenticationBackend, AuthenticationError, SimpleUser
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# Paths that don't require authentication (exact match)
PUBLIC_PATHS = {
    "/health",
    "/v1/info",
    "/v1/keys",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/signup",
    "/terms",
    "/privacy",
}

# URL prefixes that don't require auth
PUBLIC_PREFIXES = (
    "/docs",
    "/redoc",
    "/openapi",
)


class RateLimitExceeded(Exception):
    """Raised when an API key exceeds its rate limit quota."""
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after


class BearerAuthBackend(AuthenticationBackend):
    """
    Bearer-token authentication that verifies keys against the ApiKeyManager.

    Sets request.state.api_key to the full raw key on success.
    Sets request.state.api_key_obj to the ApiKey object on success.
    """

    def __init__(self):
        pass

    async def authenticate(self, request: Request):
        path = request.url.path

        # Whitelist check
        if path in PUBLIC_PATHS:
            return None
        for prefix in PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return None

        # Extract token
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise AuthenticationError("Missing or invalid Authorization header")

        token = auth_header[7:]  # strip "Bearer "
        if not token or len(token) < 8:
            raise AuthenticationError("Invalid API key format")

        # Verify against the ApiKeyManager
        # verify() returns (is_valid: bool, api_key: Optional[ApiKey], error_msg: str)
        from webhooks.api_keys import api_keys
        is_valid, api_key_obj, error_msg = api_keys.verify(token)
        if not is_valid:
            # Differentiate rate-limit errors from auth errors
            if error_msg and "Rate limit" in error_msg:
                raise RateLimitExceeded(error_msg)
            raise AuthenticationError(error_msg or "Invalid or revoked API key")

        # Attach to request state for downstream use
        request.state.api_key = token
        request.state.api_key_obj = api_key_obj  # the ApiKey object

        return SimpleUser(api_key_obj.key_id), token


def auth_on_error(conn, exc):
    """Handle authentication errors. Called by AuthenticationMiddleware."""
    from starlette.responses import JSONResponse
    if isinstance(exc, RateLimitExceeded):
        return JSONResponse(
            {
                "error": "rate_limit_exceeded",
                "detail": exc.message,
            },
            status_code=429,
            headers={
                "Retry-After": str(exc.retry_after),
                "WWW-Authenticate": "Bearer",
            },
        )
    # Standard authentication error
    return JSONResponse(
        {"detail": str(exc)},
        status_code=401,
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_auth_middleware() -> AuthenticationMiddleware:
    return AuthenticationMiddleware(BearerAuthBackend(), on_error=auth_on_error)


async def auth_error(message: str, status: int = 401):
    return JSONResponse(
        {"detail": message},
        status_code=status,
        headers={"WWW-Authenticate": "Bearer"},
    )
