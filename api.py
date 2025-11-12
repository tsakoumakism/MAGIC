import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import psycopg2
import bcrypt
from datetime import datetime, timedelta
import random, string
import yagmail

# -----------------------------
# Load config from environment
# -----------------------------
DB_URL = os.environ.get("DATABASE_URL")
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

app = FastAPI(title="Auth API")

# -----------------------------
# Database helper
# -----------------------------
def get_connection():
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB connection failed: {e}")

# -----------------------------
# Pydantic models
# -----------------------------
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class VerifyRequest(BaseModel):
    username: str
    code: str

# -----------------------------
# Email helper
# -----------------------------
def send_verification_email(recipient, code):
    yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASSWORD)
    subject = "Your Verification Code"
    contents = f"Your verification code is: {code}\nIt expires in 10 minutes."
    yag.send(recipient, subject, contents)

# -----------------------------
# Endpoints
# -----------------------------
@app.post("/register")
def register_user(req: RegisterRequest):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT username, email FROM users WHERE username = %s OR email = %s", (req.username, req.email))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Username or email already exists.")

    hashed = bcrypt.hashpw(req.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    code = ''.join(random.choices(string.digits, k=6))
    expiry = datetime.utcnow() + timedelta(minutes=10)

    cur.execute("""
        INSERT INTO users (username, email, password_hash, verified, verification_code, verification_expiry)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (req.username, req.email, hashed, False, code, expiry))

    print("error 1 -----")
    conn.commit()
    print("error 2 -----")
    cur.close()
    print("error 3 -----")
    conn.close()
    print("error 4 -----")
    send_verification_email(req.email, code)
    print("error 5 -----")
    return {"message": "User registered. Verification email sent."}


@app.post("/verify")
def verify_user(req: VerifyRequest):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT verification_code, verification_expiry FROM users WHERE username = %s", (req.username,))
    result = cur.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    stored_code, expiry = result
    if datetime.utcnow() > expiry:
        raise HTTPException(status_code=400, detail="Verification code expired")

    if stored_code == req.code:
        cur.execute("""
            UPDATE users
            SET verified = TRUE, verification_code = NULL, verification_expiry = NULL
            WHERE username = %s
        """, (req.username,))
        conn.commit()
        cur.close()
        conn.close()
        return {"message": "Email verified!"}
    else:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid verification code")


@app.post("/login")
def login_user(req: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash, verified FROM users WHERE username = %s", (req.username,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    stored_hash, verified = result
    if not verified:
        raise HTTPException(status_code=400, detail="Email not verified")

    if bcrypt.checkpw(req.password.encode("utf-8"), stored_hash.encode("utf-8")):
        return {"message": "Login successful!"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
