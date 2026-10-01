"""Small local-demo JWT/password implementation. Use managed OIDC in production."""
import base64
import hashlib
import hmac
import json
import time


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def password_hash(password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or hashlib.sha256(str(time.time_ns()).encode()).digest()[:16]
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return _b64(salt), _b64(derived)


def password_matches(password: str, salt: str, expected: str) -> bool:
    _, got = password_hash(password, base64.urlsafe_b64decode(salt + "=="))
    return hmac.compare_digest(got, expected)


def issue_token(subject: str, tenant: str, role: str, secret: str, ttl: int = 1800) -> str:
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub": subject, "tenant": tenant, "role": role,
                               "iat": int(time.time()), "exp": int(time.time()) + ttl},
                              separators=(",", ":")).encode())
    body = f"{header}.{payload}"
    signature = _b64(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{signature}"


def decode_token(token: str, secret: str) -> dict:
    try:
        header, payload, signature = token.split(".")
        body = f"{header}.{payload}"
        expected = _b64(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid signature")
        claims = json.loads(base64.urlsafe_b64decode(payload + "=="))
        if int(claims["exp"]) <= int(time.time()):
            raise ValueError("expired token")
        return claims
    except Exception as exc:
        raise ValueError("invalid token") from exc
