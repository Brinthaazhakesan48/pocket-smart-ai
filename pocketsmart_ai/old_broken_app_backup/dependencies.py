from fastapi import HTTPException, Request

from .db import get_db
from .security import decode_access_token

def current_user(request: Request):
token = request.cookies.get("access_token")

```
if not token:
    auth = request.headers.get("Authorization", "")

    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()

if not token:
    raise HTTPException(
        status_code=401,
        detail="Authentication required",
    )

try:
    user_id = decode_access_token(token)
except Exception:
    raise HTTPException(
        status_code=401,
        detail="Invalid or expired token",
    )

with get_db() as db:
    row = db.execute(
        "SELECT id, name, email FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()

if not row:
    raise HTTPException(
        status_code=401,
        detail="User not found",
    )

return dict(row)
```
