"""Admin auth router: login and me endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import get_current_admin
from app.modules.admin.models import Admin
from app.modules.admin_api.auth.service import AdminAuthService
from app.modules.admin_api.auth.schemas import LoginResponse, AdminMeResponse

router = APIRouter(prefix="/auth", tags=["admin-auth"])


@router.post("/login", response_model=LoginResponse)
async def admin_login(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    email = body.get("email")
    password = body.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    service = AdminAuthService(db)
    token = await service.login(email, password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": token}


@router.get("/me", response_model=AdminMeResponse)
async def admin_me(admin: Admin = Depends(get_current_admin)):
    service = AdminAuthService(None)  # db not needed for me
    return await service.me(admin)