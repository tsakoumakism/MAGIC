import streamlit as st
import psycopg2
import bcrypt
import random
import string
import yagmail
import os
from datetime import datetime, timedelta
from main import generateOutput

TOKEN_FILE = ".auth_token"

# --- READ FROM STREAMLIT SECRETS
def get_connection():
    db = st.secrets["database"]
    email = st.secrets["email"]
    return psycopg2.connect(
        host=db["host"],
        dbname=db["dbname"],
        user=db["user"],
        password=db["password"],
        port=db["port"]
    )

# --- EMAIL SENDER ---
def send_verification_email(recipient, code):
    try:
        yag = yagmail.SMTP(st.secrets["email"]["user"], st.secrets["email"]["password"])
        subject = "Your Verification Code"
        contents = f"Welcome! Your verification code is: {code}\n\nIt expires in 10 minutes."
        yag.send(recipient, subject, contents)
        st.info(f"Verification code sent to {recipient}.")
    except Exception as e:
        st.error(f"Failed to send verification email: {e}")

# --- DB CONNECTION ---
def get_connection():
    return psycopg2.connect(

    )

# --- VERIFY USER ---
def verify_user(username, password):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT password_hash, verified FROM users WHERE username = %s", (username,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            stored_hash, verified = result
            if not verified:
                st.warning("Please verify your email before logging in.")
                return False
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        return False
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

# --- REGISTER USER ---
def register_user(username, email, password):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT username, email FROM users WHERE username = %s OR email = %s", (username, email))
        if cur.fetchone():
            st.warning("Username or email already exists.")
            cur.close()
            conn.close()
            return False

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        code = ''.join(random.choices(string.digits, k=6))
        expiry = datetime.utcnow() + timedelta(minutes=10)

        cur.execute("""
            INSERT INTO users (username, email, password_hash, verified, verification_code, verification_expiry)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (username, email, hashed, False, code, expiry))
        conn.commit()
        cur.close()
        conn.close()

        send_verification_email(email, code)
        st.session_state.pending_verification = username
        return True
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

# --- VERIFY EMAIL CODE ---
def verify_email_code(username, code):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT verification_code, verification_expiry FROM users WHERE username = %s", (username,))
        result = cur.fetchone()

        if not result:
            return False

        stored_code, expiry = result
        if datetime.utcnow() > expiry:
            st.error("Verification code has expired. Please register again.")
            cur.close()
            conn.close()
            return False

        if stored_code == code:
            cur.execute("""
                UPDATE users
                SET verified = TRUE, verification_code = NULL, verification_expiry = NULL
                WHERE username = %s
            """, (username,))
            conn.commit()
            cur.close()
            conn.close()
            return True
        else:
            cur.close()
            conn.close()
            return False
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

# --- REMEMBER ME HELPERS ---
def save_remember_token(username):
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET remember_token = %s WHERE username = %s", (token, username))
        conn.commit()
        cur.close()
        conn.close()
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
    except Exception as e:
        st.error(f"Error saving remember token: {e}")

def get_user_from_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r") as f:
            token = f.read().strip()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT username FROM users WHERE remember_token = %s", (token,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else None
    except Exception:
        return None

def clear_remember_token(username=None):
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
    if username:
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE users SET remember_token = NULL WHERE username = %s", (username,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception:
            pass

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "register_mode" not in st.session_state:
    st.session_state.register_mode = False
if "pending_verification" not in st.session_state:
    st.session_state.pending_verification = None
if "username" not in st.session_state:
    st.session_state.username = None

# --- AUTO LOGIN ---
if not st.session_state.logged_in:
    remembered_user = get_user_from_token()
    if remembered_user:
        st.session_state.logged_in = True
        st.session_state.username = remembered_user

# --- AUTH FLOW ---
if not st.session_state.logged_in:
    if st.session_state.pending_verification:
        st.title("📧 Verify Your Email")

        with st.form("verify_form"):
            code = st.text_input("Enter the 6-digit code sent to your email")
            verify_button = st.form_submit_button("Verify")

        if verify_button:
            if verify_email_code(st.session_state.pending_verification, code):
                st.success("Email verified! You can now log in.")
                st.session_state.pending_verification = None
                st.session_state.register_mode = False
                st.rerun()
            else:
                st.error("Invalid or expired verification code.")
    elif st.session_state.register_mode:
        st.title("🆕 Register")

        with st.form("register_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            register_button = st.form_submit_button("Register")

        if register_button:
            if password != confirm:
                st.error("Passwords do not match.")
            elif not username or not password or not email:
                st.error("All fields are required.")
            else:
                if register_user(username, email, password):
                    st.info("Check your email for the verification code.")
                    st.rerun()

        if st.button("Back to Login"):
            st.session_state.register_mode = False
            st.rerun()
    else:
        st.title("🔐 Login")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            remember_me = st.checkbox("Remember me")
            login_button = st.form_submit_button("Login")

        if login_button:
            if verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                if remember_me:
                    save_remember_token(username)
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.info("Don't have an account?")
        if st.button("Register here"):
            st.session_state.register_mode = True
            st.rerun()
# --- MAIN APP ---
else:
    st.set_page_config(page_title="Simple Chatbot", layout="centered")
    st.title(f"💬 Research Copilot — Welcome, {st.session_state.username}!")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("You:", key="input")
        submit_button = st.form_submit_button(label="Send")

    if submit_button and user_input:
        st.session_state.chat_history.append(("You", user_input))
        bot_response = generateOutput(user_input)
        st.session_state.chat_history.append(("Bot", bot_response))

    for sender, message in st.session_state.chat_history:
        if sender == "You":
            st.markdown(f"**{sender}:** {message}")
        else:
            st.markdown(f"<div style='color: gray'><b>{sender}:</b> {message}</div>", unsafe_allow_html=True)

    if st.button("Logout"):
        clear_remember_token(st.session_state.username)
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()
