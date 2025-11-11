import streamlit as st
import requests
import strings as STR
from main import generateOutput

BASE_URL = "https://airaapi.onrender.com"

st.set_page_config(page_title=STR.TITLE_CHAT, layout="centered")

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "register_mode" not in st.session_state:
    st.session_state.register_mode = False
if "pending_verification" not in st.session_state:
    st.session_state.pending_verification = None
if "username" not in st.session_state:
    st.session_state.username = None

# --- REGISTER ---
def register_user(username, email, password):
    try:
        response = requests.post(f"{BASE_URL}/register", json={
            "username": username,
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            st.session_state.pending_verification = username
            return True
        else:
            st.error(response.json().get("detail", STR.REG_FAILED))
            return False
    except Exception as e:
        st.error(STR.API_CONNECTION_FAILED+f" {e}")
        return False

# --- VERIFY EMAIL ---
def verify_email_code(username, code):
    try:
        response = requests.post(f"{BASE_URL}/verify", json={
            "username": username,
            "code": code
        })
        return response.status_code == 200
    except Exception as e:
        st.error(STR.API_CONNECTION_FAILED+f" {e}")
        return False

# --- LOGIN ---
def verify_user(username, password):
    try:
        response = requests.post(f"{BASE_URL}/login", json={
            "username": username,
            "password": password
        })
        return response.status_code == 200
    except Exception as e:
        st.error(STR.API_CONNECTION_FAILED+f" {e}")
        return False

# --- CHATBOT ---
def get_chat_response(user_input):
    try:
        response = requests.post(f"{BASE_URL}/chat", json={"user_input": user_input})
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return STR.API_RESPONSE_FAILED
    except Exception as e:
        return STR.API_CONNECTION_FAILED+f" {e}"

# --- AUTH FLOW ---
if not st.session_state.logged_in:
    if st.session_state.pending_verification:
        st.title(STR.TITLE_VERIFY)

        with st.form("verify_form"):
            code = st.text_input(STR.VERIFICATION_ENTER_CODE)
            verify_button = st.form_submit_button(STR.BTN_VERIFY)

        if verify_button:
            if verify_email_code(st.session_state.pending_verification, code):
                st.success(STR.EMAIL_VERIFIED)
                st.session_state.pending_verification = None
                st.session_state.register_mode = False
                st.rerun()
            else:
                st.error(STR.VERIFICATION_INVALID)

    elif st.session_state.register_mode:
        st.title(STR.TITLE_REGISTER)

        with st.form("register_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            register_button = st.form_submit_button("Register")

        if register_button:
            if password != confirm:
                st.error(STR.PASSWORD_MISMATCH)
            elif not username or not password or not email:
                st.error(STR.FIELDS_REQUIRED)
            else:
                if register_user(username, email, password):
                    st.info(STR.VERIFICATION_SENT)
                    st.rerun()

        if st.button(STR.BTN_BACK):
            st.session_state.register_mode = False
            st.rerun()

    else:
        st.title(STR.TITLE_LOGIN)

        with st.form(STR.TITLE_LOGIN):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button(STR.BTN_LOGIN)

        if login_button:
            if verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(STR.LOGIN_SUCCESS)
                st.rerun()
            else:
                st.error(STR.LOGIN_FAILED)

        st.info(STR.INFO_ACCOUNT)
        if st.button(STR.BTN_REGISTER_HERE):
            st.session_state.register_mode = True
            st.rerun()

# --- MAIN APP ---
else:
    st.title(STR.TITLE_WELCOME+f", {st.session_state.username}!")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("You:", key="input")
        submit_button = st.form_submit_button(label="Send")

    if submit_button and user_input:
        st.session_state.chat_history.append((STR.CHAT_PLACEHOLDER, user_input))
        bot_response = get_chat_response(user_input)
        st.session_state.chat_history.append((STR.BOT_PREFIX, bot_response))

    for sender, message in st.session_state.chat_history:
        if sender == "You":
            st.markdown(f"**{sender}:** {message}")
        else:
            st.markdown(f"<div style='color: gray'><b>{sender}:</b> {message}</div>", unsafe_allow_html=True)

    if st.button(STR.BTN_LOGOUT):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()
