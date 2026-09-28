from fastapi import APIRouter, Depends, HTTPException, Request, Response
from ..db import get_db
from ..models.schemas import RegisterRequest, LoginRequest, TokenResponse
from ..security import hash_password, verify_password, create_access_token
from ..dependencies import current_user

router=APIRouter(prefix="", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
def register(data:RegisterRequest, response:Response):
    with get_db() as db:
        if db.execute("SELECT id FROM users WHERE email=?",(data.email.lower(),)).fetchone(): raise HTTPException(409,"Email already registered")
        cur=db.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",(data.name.strip(),data.email.lower(),hash_password(data.password)))
        token=create_access_token(cur.lastrowid)
    response.set_cookie("access_token",token,httponly=True,samesite="lax",max_age=7200)
    return {"access_token":token,"token_type":"bearer"}

@router.post("/login", response_model=TokenResponse)
def login(data:LoginRequest,response:Response):
    with get_db() as db: row=db.execute("SELECT * FROM users WHERE email=?",(data.email.lower(),)).fetchone()
    if not row or not verify_password(data.password,row["password_hash"]): raise HTTPException(401,"Invalid email or password")
    token=create_access_token(row["id"]); response.set_cookie("access_token",token,httponly=True,samesite="lax",max_age=7200)
    return {"access_token":token,"token_type":"bearer"}

@router.post("/logout")
def logout(response:Response):
    response.delete_cookie("access_token"); return {"message":"Logged out"}

@router.get("/session-info")
def session_info(user=Depends(current_user)): return {"authenticated":True,"user":user}

@router.get("/session-data")
def session_data(user=Depends(current_user)):
    with get_db() as db:
        count=db.execute("SELECT COUNT(*) c FROM recommendations WHERE user_id=?",(user["id"],)).fetchone()["c"]
    return {"user":user,"recommendation_count":count}
