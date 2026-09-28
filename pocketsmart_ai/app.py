"""
PocketSmart AI: Your Smart Budget & Recommendation Assistant
Main FastAPI Application: Routing, Authentication, Session Control, and AI Integration.
"""

import os
import json
import re
import base64
import shutil
import urllib.parse
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union

from fastapi import (
    FastAPI, HTTPException, Depends, File, UploadFile,
    Form, Request, status, Cookie
)
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# Import Gemini Recommendation Engine
from gemini_utils import (
    get_home_recommendations_ai,
    get_party_recommendations_ai,
    get_jewelry_recommendations_ai
)

load_dotenv()

# =============================================================
# App Initialization & Security Setup
# =============================================================
app = FastAPI(title="PocketSmart: AI Budget Planner", version="1.0.0")

SECRET_KEY = os.getenv("SECRET_KEY", "pocketsmart_ai_super_secret_jwt_key_2026")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash safely."""
    try:
        return pwd_context.verify(plain_password[:72], hashed_password)
    except Exception:
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password: str) -> str:
    """Generate secure hash for password."""
    try:
        return pwd_context.hash(password[:72])
    except Exception:
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories & Static Files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

templates = Jinja2Templates(directory=TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# =============================================================
# Pydantic Schemas
# =============================================================
class RegisterUser(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    password: str

class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    disabled: Optional[bool] = False

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class HomeBudgetInput(BaseModel):
    total_budget: float
    num_lights: int = 1
    num_fans: int = 0
    num_furniture: int = 0
    num_dining_tables: int = 0
    has_living_room: bool = False
    has_kitchen: bool = False
    has_bedroom: bool = False
    additional_requirements: Optional[str] = None

class PartyBudgetInput(BaseModel):
    total_budget: float
    num_guests: int = 10
    party_type: str = "Birthday"
    venue_type: Optional[str] = "Home"
    needs_catering: bool = True
    needs_decoration: bool = True
    needs_entertainment: bool = False
    additional_requirements: Optional[str] = None

class JewelryBudgetInput(BaseModel):
    total_budget: float
    occasion: str = "Wedding"
    preferences: Optional[str] = None


# =============================================================
# Data Persistence & In-Memory State
# =============================================================
USERS_FILE = os.path.join(DATA_DIR, "users.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

def load_json_file(filepath: str, default: Any) -> Any:
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json_file(filepath: str, data: Any):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        print(f"Error saving to {filepath}: {e}")

# Preload or initialize users
raw_users = load_json_file(USERS_FILE, {})
users_db: Dict[str, UserInDB] = {}

if raw_users:
    for u_name, u_dict in raw_users.items():
        users_db[u_name] = UserInDB(**u_dict)
else:
    # Seed default user for immediate test & viva demo
    default_user = UserInDB(
        username="demo",
        email="demo@pocketsmart.ai",
        full_name="Sai Kumar",
        hashed_password=get_password_hash("password123"),
        disabled=False
    )
    users_db["demo"] = default_user
    save_json_file(USERS_FILE, {u: users_db[u].model_dump() for u in users_db})

# Active sessions and token tracking
active_sessions: Dict[str, Dict[str, Any]] = {}
blacklisted_tokens = set()

# Recommendation History
user_recommendations: Dict[str, List[Dict[str, Any]]] = load_json_file(HISTORY_FILE, {})


# =============================================================
# Authentication Utilities
# =============================================================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_token_from_request(request: Request) -> Optional[str]:
    """Extract JWT token from authorization header or browser cookie."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1].strip()
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        if cookie_token.startswith("Bearer "):
            return cookie_token.split(" ")[1].strip()
        return cookie_token.strip()
    return None

async def get_current_user_optional(request: Request) -> Optional[UserInDB]:
    """Return user if logged in, None otherwise (does not raise 401)."""
    token = await get_token_from_request(request)
    if not token or token in blacklisted_tokens:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = users_db.get(username)
        return user
    except JWTError:
        return None

async def get_current_active_user(request: Request) -> UserInDB:
    """Enforce authentication, raising 401 or redirecting to /login."""
    user = await get_current_user_optional(request)
    if not user:
        # If web browser request for HTML, redirect to login
        if "text/html" in request.headers.get("accept", ""):
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": "/login"}
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user


def save_to_history(username: str, recommendation_type: str, input_data: dict, result: dict):
    """Save recommendation query and result to user history."""
    if username not in user_recommendations:
        user_recommendations[username] = []

    rec_id = f"rec_{uuid.uuid4().hex[:8]}"
    timestamp = datetime.now().strftime("%b %d, %Y, %I:%M %p")

    # Generate friendly summaries
    input_summary = ""
    if recommendation_type == "home":
        rooms = []
        if input_data.get("has_living_room"): rooms.append("Living Room")
        if input_data.get("has_kitchen"): rooms.append("Kitchen")
        if input_data.get("has_bedroom"): rooms.append("Bedroom")
        input_summary = f"Rooms: {', '.join(rooms) if rooms else 'General'} | Lights: {input_data.get('num_lights', 0)}, Fans: {input_data.get('num_fans', 0)}"
    elif recommendation_type == "party":
        input_summary = f"Party: {input_data.get('party_type', 'Event')} | Guests: {input_data.get('num_guests', 0)} | Venue: {input_data.get('venue_type', 'N/A')}"
    elif recommendation_type == "jewelry":
        input_summary = f"Occasion: {input_data.get('occasion', 'Event')} | Outfit Image: {'Yes' if input_data.get('image') else 'No'}"

    history_item = {
        "id": rec_id,
        "timestamp": timestamp,
        "type": recommendation_type,
        "recommendation_type": recommendation_type,
        "input_summary": input_summary,
        "input": input_summary,
        "input_data": input_data,
        "result_summary": f"Total Budget: ₹{result.get('total_budget', 0):.2f} | Remaining: ₹{result.get('remaining_budget', 0):.2f}",
        "summary": f"Total Budget: ₹{result.get('total_budget', 0):.2f} | Remaining: ₹{result.get('remaining_budget', 0):.2f}",
        "result": result,
        "full_result": result
    }

    user_recommendations[username].insert(0, history_item)
    save_json_file(HISTORY_FILE, user_recommendations)


def render_template(request: Request, name: str, context: Optional[dict] = None) -> HTMLResponse:
    """Helper to render Jinja2 templates safely across all Starlette versions."""
    ctx = context.copy() if context else {}
    ctx["request"] = request
    try:
        return templates.TemplateResponse(request=request, name=name, context=ctx)
    except TypeError:
        return templates.TemplateResponse(name, ctx)

# =============================================================
# Static & HTML Navigation Routes
# =============================================================
@app.get("/", response_class=HTMLResponse)
async def home_landing(request: Request):
    """Main landing page introducing PocketSmart AI."""
    user = await get_current_user_optional(request)
    return render_template(request, "index.html", {"user": user})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login page or redirect to dashboard if logged in."""
    user = await get_current_user_optional(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return render_template(request, "login.html")

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Serve the registration page."""
    user = await get_current_user_optional(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    return render_template(request, "register.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, current_user: UserInDB = Depends(get_current_active_user)):
    """User Dashboard displaying recent recommendations and planner entries."""
    recent_activity = user_recommendations.get(current_user.username, [])[:5]
    return render_template(request, "dashboard.html", {
        "user": current_user,
        "recent_activity": recent_activity
    })

@app.get("/home-planner", response_class=HTMLResponse)
async def home_planner(request: Request, current_user: UserInDB = Depends(get_current_active_user)):
    """Home budget planner page."""
    return render_template(request, "home_planner.html", {"user": current_user})

@app.get("/party-planner", response_class=HTMLResponse)
async def party_planner(request: Request, current_user: UserInDB = Depends(get_current_active_user)):
    """Party budget planner page."""
    return render_template(request, "party_planner.html", {"user": current_user})

@app.get("/jewelry-planner", response_class=HTMLResponse)
async def jewelry_planner(request: Request, current_user: UserInDB = Depends(get_current_active_user)):
    """Jewelry budget planner page."""
    return render_template(request, "jewelry_planner.html", {"user": current_user})

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, current_user: UserInDB = Depends(get_current_active_user)):
    """History page to review past budget recommendations."""
    history_items = user_recommendations.get(current_user.username, [])
    return render_template(request, "history.html", {
        "user": current_user,
        "history_items": history_items
    })


# =============================================================
# Auth Endpoints (Register, Login, Token, Logout, Sessions)
# =============================================================
@app.post("/register")
async def register_user(request: Request):
    """Handle new user registration via JSON or Form."""
    content_type = request.headers.get("content-type", "")
    username = ""
    email = ""
    full_name = ""
    password = ""

    if "application/json" in content_type:
        body = await request.json()
        username = body.get("username", "").strip()
        email = body.get("email", "").strip()
        full_name = body.get("full_name", "")
        password = body.get("password", "")
    else:
        form = await request.form()
        username = form.get("username", "").strip()
        email = form.get("email", "").strip()
        full_name = form.get("full_name", "")
        password = form.get("password", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    if username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = UserInDB(
        username=username,
        email=email or f"{username}@example.com",
        full_name=full_name or username.title(),
        hashed_password=get_password_hash(password),
        disabled=False
    )
    users_db[username] = new_user
    save_json_file(USERS_FILE, {u: users_db[u].model_dump() for u in users_db})

    # Auto authenticate & return token
    access_token = create_access_token(data={"sub": username})
    active_sessions[username] = {
        "username": username,
        "login_time": datetime.utcnow(),
        "last_activity": datetime.utcnow(),
        "token": access_token,
        "user_data": {}
    }

    response = JSONResponse(content={"message": "Registration successful", "access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return response

@app.post("/token", response_model=Token)
async def login_for_access_token(request: Request):
    """Authenticate credentials and issue JWT token with session cookie."""
    username = ""
    password = ""

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        username = body.get("username", "").strip()
        password = body.get("password", "")
    else:
        form = await request.form()
        username = form.get("username", "").strip()
        password = form.get("password", "")

    user = users_db.get(username)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})

    # Save active session
    active_sessions[user.username] = {
        "username": user.username,
        "login_time": datetime.utcnow(),
        "last_activity": datetime.utcnow(),
        "token": access_token,
        "user_data": active_sessions.get(user.username, {}).get("user_data", {})
    }

    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return response

@app.get("/logout")
@app.post("/logout")
async def logout(request: Request):
    """Logout user, blacklist token, and clear cookies."""
    token = await get_token_from_request(request)
    if token:
        blacklisted_tokens.add(token)
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            uname = payload.get("sub")
            if uname and uname in active_sessions:
                del active_sessions[uname]
        except JWTError:
            pass

    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response

@app.get("/session-info")
async def get_session_info(request: Request, current_user: UserInDB = Depends(get_current_active_user)):
    """Retrieve metadata about the current user session (PDF Page 20)."""
    if current_user.username in active_sessions:
        session = active_sessions[current_user.username]
        login_t = session.get("login_time", datetime.utcnow())
        duration = int((datetime.utcnow() - login_t).total_seconds() // 60)
        return {
            "username": session.get("username"),
            "login_time": session.get("login_time"),
            "last_activity": session.get("last_activity"),
            "session_duration_minutes": duration,
            "user_data": session.get("user_data", {})
        }
    raise HTTPException(status_code=404, detail="No active session found")

@app.post("/session-data")
async def update_session_data(data: Dict[str, Any], current_user: UserInDB = Depends(get_current_active_user)):
    """Update user session data for personalization (PDF Page 20)."""
    if current_user.username in active_sessions:
        active_sessions[current_user.username]["user_data"].update(data)
        active_sessions[current_user.username]["last_activity"] = datetime.utcnow()
        return {
            "message": "Session data updated",
            "data": active_sessions[current_user.username]["user_data"]
        }
    raise HTTPException(status_code=404, detail="No active session found")


# =============================================================
# AI Recommendation Endpoints
# =============================================================

# 1. Home Planner (/home-budget and /generate-home)
@app.post("/home-budget")
@app.post("/generate-home")
async def plan_home_budget(budget_input: HomeBudgetInput, current_user: UserInDB = Depends(get_current_active_user)):
    """Generate home interior recommendations (PDF Page 21)."""
    try:
        # Store in session
        if current_user.username in active_sessions:
            active_sessions[current_user.username]["user_data"]["last_home_budget"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "budget": budget_input.total_budget,
                "requirements": budget_input.model_dump()
            }
            active_sessions[current_user.username]["last_activity"] = datetime.utcnow()

        result = get_home_recommendations_ai(budget_input)

        # Save to user history
        save_to_history(
            username=current_user.username,
            recommendation_type="home",
            input_data=budget_input.model_dump(),
            result=result
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


# 2. Party Planner (/party-budget and /generate-party)
@app.post("/party-budget")
@app.post("/generate-party")
async def plan_party_budget(budget_input: PartyBudgetInput, current_user: UserInDB = Depends(get_current_active_user)):
    """Generate party planning recommendations (PDF Page 22)."""
    try:
        # Store in session
        if current_user.username in active_sessions:
            active_sessions[current_user.username]["user_data"]["last_party_budget"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "budget": budget_input.total_budget,
                "party_type": budget_input.party_type,
                "guests": budget_input.num_guests
            }
            active_sessions[current_user.username]["last_activity"] = datetime.utcnow()

        result = get_party_recommendations_ai(budget_input)

        # Save to user history
        save_to_history(
            username=current_user.username,
            recommendation_type="party",
            input_data=budget_input.model_dump(),
            result=result
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


# 3. Jewelry Planner (/jewelry-budget and /generate-jewelry)
@app.post("/jewelry-budget")
@app.post("/generate-jewelry")
async def plan_jewelry_budget(
    total_budget: float = Form(...),
    occasion: str = Form(...),
    preferences: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Generate jewelry budget recommendations with optional outfit image analysis (PDF Page 23)."""
    try:
        budget_input = JewelryBudgetInput(
            total_budget=total_budget,
            occasion=occasion,
            preferences=preferences
        )

        image_path = None
        image_filename = None
        if image and image.filename:
            safe_name = f"{int(datetime.utcnow().timestamp())}_{re.sub(r'[^a-zA-Z0-9_.-]', '_', image.filename)}"
            image_path = os.path.join(UPLOADS_DIR, safe_name)
            with open(image_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            image_filename = safe_name

        # Store in session
        if current_user.username in active_sessions:
            active_sessions[current_user.username]["user_data"]["last_jewelry_budget"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "budget": total_budget,
                "occasion": occasion,
                "has_image": image_filename is not None
            }
            active_sessions[current_user.username]["last_activity"] = datetime.utcnow()

        result = get_jewelry_recommendations_ai(budget_input, image_path)

        input_data = budget_input.model_dump()
        if image_filename:
            input_data["image"] = f"/static/uploads/{image_filename}"

        # Save to history
        save_to_history(
            username=current_user.username,
            recommendation_type="jewelry",
            input_data=input_data,
            result=result
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")


# 4. Recommendation History & Details
@app.get("/recommendation-history")
async def get_recommendation_history(current_user: UserInDB = Depends(get_current_active_user)):
    """Retrieve user's recommendation history (PDF Page 23-24)."""
    history = user_recommendations.get(current_user.username, [])
    return {"history": history}

@app.get("/recommendation-details/{recommendation_id}")
async def get_recommendation_details(recommendation_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Retrieve detailed item information for a specific saved recommendation (PDF Page 24)."""
    user_items = user_recommendations.get(current_user.username, [])
    for item in user_items:
        if item.get("id") == recommendation_id:
            return item
    raise HTTPException(status_code=404, detail="Recommendation not found")


# =============================================================
# Startup & Main Runner
# =============================================================
@app.on_event("startup")
async def setup_session_cleanup():
    """Background task to clean up expired sessions (PDF Page 25)."""
    async def cleanup_expired_sessions():
        while True:
            try:
                current_time = datetime.utcnow()
                expired = [
                    uname for uname, sess in list(active_sessions.items())
                    if (current_time - sess.get("last_activity", current_time)).total_seconds() > 1800
                ]
                for uname in expired:
                    print(f"[PocketSmart AI] Removing expired session for user: {uname}")
                    active_sessions.pop(uname, None)
            except Exception as e:
                print(f"[PocketSmart AI] Session cleanup error: {e}")
            await asyncio.sleep(300)

    asyncio.create_task(cleanup_expired_sessions())


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  PocketSmart AI: Your Smart Budget & Recommendation Assistant")
    print("  Starting FastAPI server on http://127.0.0.1:8000")
    print("="*60 + "\n")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
