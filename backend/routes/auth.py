"""
Authentication routes - Register, Login, JWT token management.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database import get_connection

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

SECRET_KEY = "code-analyzer-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "developer"


class LoginRequest(BaseModel):
    email: str
    password: str


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_admin(current_user: dict = Depends(get_current_user)):
    """Dependency that ensures the current user is an admin."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def require_role(allowed_roles: list):
    """Factory for role-based access control."""
    def checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Access denied. Required role: {', '.join(allowed_roles)}")
        return current_user
    return checker


@router.post("/register")
def register(req: RegisterRequest):
    # Block admin registration — admin is a permanent seeded account
    if req.role == "admin":
        raise HTTPException(status_code=403, detail="Admin accounts cannot be registered. Use the default admin login.")

    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (req.email,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = pwd_context.hash(req.password)
    cursor = conn.execute(
        "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
        (req.name, req.email, hashed, req.role)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    token = create_access_token({"user_id": user_id, "email": req.email, "role": req.role})
    return {"token": token, "user": {"id": user_id, "name": req.name, "email": req.email, "role": req.role}}


@router.post("/login")
def login(req: LoginRequest):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (req.email,)).fetchone()
    conn.close()

    if not user or not pwd_context.verify(req.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"user_id": user["id"], "email": user["email"], "role": user["role"]})
    return {"token": token, "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}}


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    user = conn.execute("SELECT id, name, email, role, created_at FROM users WHERE id = ?", (current_user["user_id"],)).fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)


class ProfileUpdate(BaseModel):
    name: str = None
    email: str = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


@router.put("/profile")
def update_profile(req: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Update user profile."""
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (current_user["user_id"],)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    name = req.name or user["name"]
    email = req.email or user["email"]

    if req.email and req.email != user["email"]:
        existing = conn.execute("SELECT id FROM users WHERE email = ? AND id != ?", (req.email, current_user["user_id"])).fetchone()
        if existing:
            conn.close()
            raise HTTPException(status_code=400, detail="Email already taken")

    conn.execute("UPDATE users SET name = ?, email = ? WHERE id = ?", (name, email, current_user["user_id"]))
    conn.commit()
    conn.close()
    return {"message": "Profile updated", "name": name, "email": email}


@router.put("/password")
def change_password(req: PasswordChange, current_user: dict = Depends(get_current_user)):
    """Change user password."""
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (current_user["user_id"],)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    if not pwd_context.verify(req.old_password, user["password"]):
        conn.close()
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    hashed = pwd_context.hash(req.new_password)
    conn.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, current_user["user_id"]))
    conn.commit()
    conn.close()
    return {"message": "Password changed successfully"}
