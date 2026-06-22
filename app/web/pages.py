from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.web.auth import get_optional_user

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    return RedirectResponse("/recognize" if user else "/login")


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if user is not None:
        return RedirectResponse("/recognize")
    return templates.TemplateResponse(request, "login.html", {"user": None})


@router.get("/enroll")
def enroll_page(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if user is None:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "enroll.html", {"user": user})


@router.get("/recognize")
def recognize_page(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if user is None:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "recognize.html", {"user": user})


@router.get("/dashboard")
def dashboard_page(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if user is None:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "attendance_dashboard.html", {"user": user})


@router.get("/audit")
def audit_page(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if user is None:
        return RedirectResponse("/login")
    if user.role.value != "admin":
        return RedirectResponse("/recognize")
    return templates.TemplateResponse(request, "audit_log.html", {"user": user})


@router.get("/operators")
def operators_page(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if user is None:
        return RedirectResponse("/login")
    if user.role.value != "admin":
        return RedirectResponse("/recognize")
    return templates.TemplateResponse(request, "users.html", {"user": user})


@router.get("/kiosk")
def kiosk_page(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if user is None:
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "kiosk.html", {"user": user})
