import streamlit as st
from main import generateOutput

# Set page config
st.set_page_config(page_title="Simple Chatbot", layout="centered")

st.title("💬 Research Copilot")

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Text input and send button
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", key="input")
    submit_button = st.form_submit_button(label="Send")

# When the user sends a message
if submit_button and user_input:
    # Add user input to chat history
    st.session_state.chat_history.append(("You", user_input))

    # Dummy bot response (replace with your logic later)
    bot_response = generateOutput(user_input)
    st.session_state.chat_history.append(("Bot", bot_response))

# Display the chat history
for sender, message in st.session_state.chat_history:
    if sender == "You":
        st.markdown(f"**{sender}:** {message}")
    else:
        st.markdown(f"<div style='color: gray'><b>{sender}:</b> {message}</div>", unsafe_allow_html=True)
