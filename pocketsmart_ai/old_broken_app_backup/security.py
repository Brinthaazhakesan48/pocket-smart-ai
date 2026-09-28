import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from .config import get_settings

ALGORITHM = "HS256"
PBKDF2_SCHEME = "pbkdf2_sha256"
PBKDF2_ROUNDS = 210_000
SALT_BYTES = 16

def hash_password(password: str) -> str:
salt = secrets.token_bytes(SALT_BYTES)

```
digest = hashlib.pbkdf2_hmac(
    "sha256",
    password.encode("utf-8"),
    salt,
    PBKDF2_ROUNDS,
)

return (
    f"{PBKDF2_SCHEME}"
    f"${PBKDF2_ROUNDS}"
    f"${salt.hex()}"
    f"${digest.hex()}"
)
```

def verify_password(password: str, stored: str) -> bool:
try:
scheme, rounds, salt_hex, digest_hex = stored.split("$", 3)

```
    if scheme != PBKDF2_SCHEME:
        return False

    salt = bytes.fromhex(salt_hex)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        int(rounds),
    )

    return hmac.compare_digest(
        digest.hex(),
        digest_hex,
    )

except (ValueError, TypeError):
    return False
```

def create_access_token(user_id: int) -> str:
settings = get_settings()

```
now = datetime.now(timezone.utc)

payload = {
    "sub": str(user_id),
    "iat": now,
    "exp": now + timedelta(
        minutes=settings.access_token_expire_minutes
    ),
}

return jwt.encode(
    payload,
    settings.secret_key,
    algorithm=ALGORITHM,
)
```

def decode_access_token(token: str) -> int:
settings = get_settings()

```
payload = jwt.decode(
    token,
    settings.secret_key,
    algorithms=[ALGORITHM],
)

return int(payload["sub"])
```
