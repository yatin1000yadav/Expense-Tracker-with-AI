
# main.py - FIXED VERSION
import streamlit as st
import json
import bcrypt
import os
import utils.app as app
from datetime import datetime
import pandas as pd

st.set_page_config(
    page_title="Expense Tracker",
    layout="centered"
)

st.title("💸 Expense Tracker")

# -------------------------------
# Auth Setup
# -------------------------------
AUTH_PATH = "config/auth.json"
os.makedirs("config", exist_ok=True)

# Load auth data
if os.path.exists(AUTH_PATH) and os.path.getsize(AUTH_PATH) > 0:
    with open(AUTH_PATH, "r") as f:
        auth_data = json.load(f)
else:
    auth_data = {}

# First-time setup
if "hashed_password" not in auth_data:
    default_password = "admin123"
    hashed_password = bcrypt.hashpw(default_password.encode(), bcrypt.gensalt()).decode()
    auth_data["hashed_password"] = hashed_password
    with open(AUTH_PATH, "w") as f:
        json.dump(auth_data, f, indent=4)

# Session state
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# ============================================
# LOGIN PAGE - Sirf login form
# ============================================
if not st.session_state["authenticated"]:
    st.markdown("## 🔐 Admin Login")
    password = st.text_input("Enter Password", type="password")
    
    if st.button("Login"):
        if bcrypt.checkpw(password.encode(), auth_data["hashed_password"].encode()):
            st.session_state["authenticated"] = True
            st.success("✅ Login successful")
            st.rerun()
        else:
            st.error("❌ Incorrect password")
    
    # IMPORTANT: Yahan pe STOP - login page ke baad kuch nahi dikhana
    st.stop()

# ============================================
# LOGIN KE BAAD WALA CONTENT
# ============================================
if st.session_state["authenticated"]:
    st.sidebar.success("✅ Logged in")
    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.rerun()
    
    # Ab run karo app
    try:
        app.run()
    except Exception as e:
        st.error(f"App error: {e}")
        # Fallback UI agar app.run() fail ho jaye
        st.header("📸 Scan Receipt")
        uploaded_file = st.file_uploader("Upload Receipt", type=['png','jpg','jpeg'])
        if uploaded_file:
            st.image(uploaded_file, width=300)
            with st.form("expense_form"):
                amount = st.number_input("Amount", min_value=0.0)
                date = st.date_input("Date", datetime.now())
                category = st.selectbox("Category", ["Today's expense", "Shopping", "Food"])
                details = st.text_input("Details")
                if st.form_submit_button("Add Expense"):
                    st.success("Added!")
