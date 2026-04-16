# main.py
import streamlit as st
import json
import bcrypt
import os
import utils.app as app

# -------------------------------
# Streamlit Page Config
# -------------------------------
st.set_page_config(
    page_title="Expense Tracker",
    layout="centered"
)

st.title("💸 Expense Tracker")

# -------------------------------
# Auth file path
# -------------------------------
AUTH_PATH = "config/auth.json"

# -------------------------------
# Ensure config directory exists
# -------------------------------
os.makedirs("config", exist_ok=True)

# -------------------------------
# Load auth data safely
# -------------------------------
if os.path.exists(AUTH_PATH) and os.path.getsize(AUTH_PATH) > 0:
    try:
        with open(AUTH_PATH, "r") as f:
            auth_data = json.load(f)
    except json.JSONDecodeError:
        auth_data = {}
else:
    auth_data = {}

# -------------------------------
# First-time setup
# -------------------------------
if "hashed_password" not in auth_data:
    default_password = "admin123"
    hashed_password = bcrypt.hashpw(
        default_password.encode(),
        bcrypt.gensalt()
    ).decode()

    auth_data["hashed_password"] = hashed_password

    with open(AUTH_PATH, "w") as f:
        json.dump(auth_data, f, indent=4)

    st.info("⚠ First-time setup complete. Default password: admin123")

stored_hash = auth_data["hashed_password"]

# -------------------------------
# Session state
# -------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# -------------------------------
# LOGIN PAGE - Sirf login form
# -------------------------------
if not st.session_state["authenticated"]:
    st.markdown("## 🔐 Admin Login")
    password = st.text_input("🔐 Enter Password", type="password")

    if st.button("Login"):
        try:
            if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                st.session_state["authenticated"] = True
                st.success("✅ Login successful")
                st.rerun()
            else:
                st.error("❌ Incorrect password")
        except Exception as e:
            st.error("Authentication error")
            st.exception(e)
    
    # Login page ke baad kuch nahi dikhana
    st.stop()

# -------------------------------
# MAIN APP - Sirf login ke baad
# -------------------------------
st.sidebar.success("✅ Logged in as Admin")
if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()

# Run the app
try:
    app.run()
except Exception as e:
    st.error(f"Error in app: {e}")
    st.info("Make sure all files are present in utils folder")
















