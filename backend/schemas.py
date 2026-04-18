from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    fullname: str
    email: EmailStr
    phone: str
    password: str
    role: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class OtpVerify(BaseModel):
    email: EmailStr
    otp: str

class EmailRequest(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    email: EmailStr
    new_password: str

class JobCreate(BaseModel):
    title: str
    description: str
    company: str

class PostCreate(BaseModel):
    content: str

# =========================
# ✅ ADDED FOR OTP FLOW (LOGIN SUPPORT)
# =========================

class LoginOtpRequest(BaseModel):
    email: EmailStr
    password: str

class LoginOtpVerify(BaseModel):
    email: EmailStr
    otp: str