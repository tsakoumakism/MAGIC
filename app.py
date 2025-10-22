import streamlit as st
import psycopg2
import bcrypt
from main import generateOutput

# --- DB CONNECTION ---
def get_connection():
    return psycopg2.connect(
        host="127.0.0.1",      # change if remote
        dbname="airaDB",
        user="postgres",
        password="superduper",
        port="5432"
    )

def verify_user(username, password):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result:
            stored_hash = result[0]
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        return False
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

# --- LOGIN LOGIC ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

    if login_button:
        if verify_user(username, password):
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password.")
else:
    # --- MAIN CHAT APP ---
    st.set_page_config(page_title="Simple Chatbot", layout="centered")
    st.title("💬 Research Copilot")

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
        st.session_state.logged_in = False
        st.rerun()