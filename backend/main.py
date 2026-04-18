from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
import shutil
import os
import random

import models
import schemas
from database import engine, SessionLocal
from auth import hash_password, verify_password
from jwt_handler import create_access_token, get_current_user
from email_utils import send_otp_email
import posts

app = FastAPI()
app.include_router(posts.router)
# ================= CONFIG =================

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ================= CORS =================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= DB =================

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def admin_required(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
# ================= OTP STORAGE =================
otp_store = {}

# ================= REGISTER =================

@app.post("/register")
def register(user: schemas.UserRegister):

    email = user.email.strip().lower()

    db = SessionLocal()
    existing = db.query(models.User).filter(models.User.email == email).first()
    db.close()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    otp = str(random.randint(100000, 999999))

    otp_store[email] = {
        "otp": otp,
        "type": "register",
        "data": user.dict()
    }

    send_otp_email(email, otp)

    return {"message": "OTP sent for registration", "email": email}


# ================= LOGIN =================

@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):

    email = user.email.strip().lower()

    db_user = db.query(models.User).filter(models.User.email == email).first()

    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")

    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    otp = str(random.randint(100000, 999999))

    otp_store[email] = {
        "otp": otp,
        "type": "login",
        "user_id": db_user.id
    }

    send_otp_email(email, otp)

    return {"message": "OTP sent for login", "email": email}

@app.post("/admin/login")
def admin_login(user: schemas.UserLogin, db: Session = Depends(get_db)):

    email = user.email.strip().lower()

    db_user = db.query(models.User).filter(
        models.User.email == email,
        models.User.role == "admin"
    ).first()

    if not db_user:
        raise HTTPException(status_code=403, detail="Not an admin")

    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    token = create_access_token({
        "user_id": db_user.id,
        "role": "admin"
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ================= VERIFY OTP =================

@app.post("/verify-otp")
def verify_otp(data: schemas.OtpVerify, db: Session = Depends(get_db)):

    email = data.email.strip().lower()
    otp = data.otp

    record = otp_store.get(email)

    if not record:
        raise HTTPException(status_code=400, detail="OTP expired or not found")

    if record["otp"] != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # remove OTP after verification
    otp_store.pop(email)

    # ================= REGISTER FLOW =================
    if record["type"] == "register":

        user_data = record["data"]

        new_user = models.User(
            fullname=user_data["fullname"],
            email=email,
            phone=user_data["phone"],
            password=hash_password(user_data["password"]),
            role=user_data["role"],
            is_verified=True
        )

        db.add(new_user)
        db.commit()

        return {"message": "Registration successful"}

    # ================= LOGIN FLOW =================
    db_user = db.query(models.User).filter(models.User.email == email).first()

    token = create_access_token({
    "email": email,
    "user_id": db_user.id,
    "role": db_user.role   # ✅ IMPORTANT
})

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer"
    }


# ================= PROFILE =================

@app.get("/me")
def get_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(
        models.User.id == current_user.get("user_id")
    ).first()

    if not user and current_user.get("email"):
        user = db.query(models.User).filter(
            models.User.email == current_user["email"]
        ).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ================= UPDATE PROFILE =================

@app.post("/update_profile")
def update_profile(
    fullname: str = Form(None),
    headline: str = Form(None),
    skills: str = Form(None),
    education: str = Form(None),
    linkedin: str = Form(None),
    location: str = Form(None),
    bio: str = Form(None),

    companyName: str = Form(None),
    industry: str = Form(None),
    companyWebsite: str = Form(None),
    aboutCompany: str = Form(None),

    photo: UploadFile = File(None),

    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(
        models.User.id == current_user["user_id"]
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if photo:
        filename = f"user_{user.id}_{photo.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)

        user.photo = file_path

    # update fields safely
    user.fullname = fullname or user.fullname
    user.headline = headline or user.headline
    user.skills = skills or user.skills
    user.education = education or user.education
    user.linkedin = linkedin or user.linkedin
    user.location = location or user.location
    user.bio = bio or user.bio

    user.company_name = companyName or user.company_name
    user.industry = industry or user.industry
    user.company_website = companyWebsite or user.company_website
    user.about_company = aboutCompany or user.about_company

    db.commit()

    return {"message": "Profile updated successfully"}


# ================= USERS =================

@app.get("/users")
def get_users(db: Session = Depends(get_db)):

    users = db.query(models.User).all()

    return [
        {
            "id": u.id,
            "fullname": u.fullname,
            "email": u.email,
            "role": u.role
        }
        for u in users
    ]


# ================= POSTS =================

@app.post("/posts")
def create_post(
    data: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    new_post = models.Post(
        content=data.content,
        user_id=current_user["user_id"],
        created_at=datetime.utcnow()
    )

    db.add(new_post)
    db.commit()

    return {"message": "Post created"}


@app.get("/posts")
def get_posts(db: Session = Depends(get_db)):

    posts = db.query(models.Post).order_by(models.Post.id.desc()).all()

    result = []

    for p in posts:
        user = db.query(models.User).filter(models.User.id == p.user_id).first()

        result.append({
            "id": p.id,
            "content": p.content,
            "created_at": p.created_at,
            "fullname": user.fullname if user else "Unknown",
            "photo": user.photo if user else None
        })

    return result


# ================= DASHBOARD =================

@app.get("/dashboard")
def dashboard(current_user: dict = Depends(get_current_user)):
    return {
        "message": "Welcome to Career Flow",
        "user": current_user
    }

# ================= ADMIN SECTION =================

def admin_required(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ================= GET ALL USERS =================
@app.get("/admin/users")
def get_all_users(
    db: Session = Depends(get_db),
    admin: dict = Depends(admin_required)
):
    users = db.query(models.User).all()

    return {
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "fullname": u.fullname,
                "email": u.email,
                "role": u.role,
                "created_at": str(u.created_at) if u.created_at else ""
            }
            for u in users
        ]
    }


# ================= SEARCH USERS =================
@app.get("/admin/search-users")
def search_users(
    query: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(admin_required)
):
    users = db.query(models.User).filter(
        or_(
            models.User.fullname.ilike(f"%{query}%"),
            models.User.email.ilike(f"%{query}%")
        )
    ).all()

    return {
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "fullname": u.fullname,
                "email": u.email,
                "role": u.role
            }
            for u in users
        ]
    }


# ================= DELETE USER =================
@app.delete("/admin/delete-user/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: dict = Depends(admin_required)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ❌ Prevent admin from deleting himself
    if user.id == admin["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}


# ================= ADMIN DASHBOARD =================
@app.get("/admin/dashboard")
def admin_dashboard(
    db: Session = Depends(get_db),
    admin: dict = Depends(admin_required)
):
    total_users = db.query(models.User).count()
    total_posts = db.query(models.Post).count()

    return {
        "total_users": total_users,
        "total_posts": total_posts
    }