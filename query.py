import streamlit as st
from werkzeug.security import generate_password_hash, check_password_hash

# Import your RAG answer generation
from query import retrievecontext, generateanswer

if "users" not in st.session_state:
    st.session_state["users"] = {}
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "chats" not in st.session_state:
    st.session_state["chats"] = {}
if "rerun" not in st.session_state:
    st.session_state["rerun"] = False

def toggle_rerun():
    st.session_state["rerun"] = not st.session_state["rerun"]

# Login / Signup UI
if not st.session_state["authenticated"]:
    st.title("Welcome to Legal Chatbot")
    page = st.radio("Choose an option:", ["Login", "Sign Up"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if page == "Sign Up":
        if st.button("Sign Up"):
            if not username or not password:
                st.error("Please fill all fields")
            elif username in st.session_state["users"]:
                st.error("Username already exists")
            else:
                st.session_state["users"][username] = generate_password_hash(password)
                st.success("Account created! Please login.")
    else:
        if st.button("Login"):
            user_hash = st.session_state["users"].get(username)
            if user_hash and check_password_hash(user_hash, password):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                if username not in st.session_state["chats"]:
                    st.session_state["chats"][username] = []
                toggle_rerun()
            else:
                st.error("Invalid username or password")

    st.stop()

# Authenticated UI
st.sidebar.title(f"Hello, {st.session_state['username']}")

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    toggle_rerun()

user_chats = st.session_state["chats"][st.session_state["username"]]

# New chat
if st.sidebar.button("New Chat"):
    chat_id = len(user_chats) + 1
    user_chats.append({"name": f"Chat {chat_id}", "history": []})
    toggle_rerun()

# Select chat (handle no chats)
if user_chats:
    selected_idx = st.sidebar.radio(
        "Chats",
        options=range(len(user_chats)),
        format_func=lambda i: user_chats[i]["name"],
        key="selected_chat"
    )
else:
    st.sidebar.write("No chats yet.")
    selected_idx = None

# Delete chat
if user_chats and st.sidebar.button("Delete Chat"):
    user_chats.pop(selected_idx)
    toggle_rerun()

# Rename chat
if user_chats:
    new_name = st.sidebar.text_input(
        "Rename Chat",
        value=user_chats[selected_idx]["name"],
        key="rename_input"
    )
    if st.sidebar.button("Rename"):
        if new_name.strip():
            user_chats[selected_idx]["name"] = new_name.strip()
            toggle_rerun()

# Main chat window with REAL answer logic
if selected_idx is not None:
    chat = user_chats[selected_idx]
    st.title(chat["name"])

    for msg in chat["history"]:
        st.markdown(f"**You:** {msg['user']}")
        st.markdown(f"**Bot:** {msg['bot']}")

    user_input = st.text_input("Enter your message:", key="user_input_field")

    if st.button("Send"):
        if user_input.strip():
            # Retrieve context using your legal vector search
            context = retrievecontext(user_input.strip())
            # Generate answer using retrieved context and your RAG LLM backend
            bot_response = generateanswer(user_input.strip(), context)
            chat["history"].append({"user": user_input.strip(), "bot": bot_response})
            toggle_rerun()
else:
    st.write("Create or select a chat to start.")
