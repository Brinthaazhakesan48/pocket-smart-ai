from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..db import get_db
from ..security import decode_access_token


templates = Jinja2Templates(directory="app/templates")

router = APIRouter(tags=["pages"])


def ctx(request: Request):
    user = None
    token = request.cookies.get("access_token")

    if token:
        try:
            uid = decode_access_token(token)

            with get_db() as db:
                row = db.execute(
                    "SELECT id, name, email FROM users WHERE id=?",
                    (uid,)
                ).fetchone()

                if row:
                    user = dict(row)

        except Exception:
            user = None

    return {
        "request": request,
        "user": user
    }


@router.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse("index.html", ctx(request))


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", ctx(request))


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", ctx(request))


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", ctx(request))


@router.get("/home-planner", response_class=HTMLResponse)
def home_planner(request: Request):
    return templates.TemplateResponse("home_planner.html", ctx(request))


@router.get("/party-planner", response_class=HTMLResponse)
def party_planner(request: Request):
    return templates.TemplateResponse("party_planner.html", ctx(request))


@router.get("/jewelry-planner", response_class=HTMLResponse)
def jewelry_planner(request: Request):
    return templates.TemplateResponse("jewelry_planner.html", ctx(request))


@router.get("/history", response_class=HTMLResponse)
def history(request: Request):
    return templates.TemplateResponse("history.html", ctx(request))


@router.get("/testimonials", response_class=HTMLResponse)
def testimonials(request: Request):
    return templates.TemplateResponse("testimonials.html", ctx(request))