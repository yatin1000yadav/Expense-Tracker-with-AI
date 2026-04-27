# main.py ── GUARANTEED CLEAN BOOT
# ─────────────────────────────────────────────────────────────────────────────
# HOW THIS FIXES THE CSS-LEAK BUG PERMANENTLY:
#
# Streamlit requires set_page_config() to be the very first st.* call.
# If ANY import triggers a st.* call before it, the page config is never set
# and ALL subsequent st.markdown() calls render as raw visible text.
#
# The fix: set_page_config() is called on line 1 after the import.
# Every other import and all logic lives inside _boot(), which runs AFTER.
# This means even if utils/gsheet_utils.py or any other util calls
# st.cache_data, st.secrets, etc. at module level — it doesn't matter,
# because set_page_config() has already been called first.
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💸",
    layout="centered",
    initial_sidebar_state="auto",
)


def _boot():
    # ── All imports are inside _boot() ── intentional, do NOT move up ────────
    import json, bcrypt, os
    import utils.app as app

    # =========================================================================
    #  GLOBAL LUXURY THEME
    # =========================================================================
    st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500;600;700&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,300&display=swap" rel="stylesheet">
<style>
:root {
  --navy:#080d18; --navy-mid:#0f1626; --navy-card:#131c2e; --navy-lift:#1a2540;
  --gold:#c9a84c; --gold-lt:#e8c96a; --gold-pale:rgba(201,168,76,0.09);
  --gold-glow:rgba(201,168,76,0.22); --gold-bdr:rgba(201,168,76,0.22);
  --cream:#f5f0e8; --tx-h:#eef0f8; --tx-b:#9aa3b5; --tx-dim:#565e72;
  --green:#22c55e; --red:#f43f5e; --blue:#60a5fa;
  --r:14px; --r-sm:8px;
  --shadow:0 10px 36px rgba(0,0,0,0.6);
  --shadow-gold:0 0 32px rgba(201,168,76,0.20);
}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;color:var(--tx-b)!important;}
.stApp{
  background:var(--navy)!important;
  background-image:
    radial-gradient(ellipse 75% 55% at 12% 0%,rgba(201,168,76,0.09) 0%,transparent 58%),
    radial-gradient(ellipse 55% 45% at 88% 100%,rgba(96,165,250,0.07) 0%,transparent 52%),
    radial-gradient(ellipse 60% 70% at 50% 50%,rgba(8,13,24,0.98) 0%,transparent 100%)!important;
  min-height:100vh;
}
.stApp::before{content:'';position:fixed;width:600px;height:600px;background:radial-gradient(circle,rgba(201,168,76,0.065) 0%,transparent 68%);border-radius:50%;top:-200px;left:-160px;animation:orb1 20s ease-in-out infinite alternate;pointer-events:none;z-index:0;}
.stApp::after{content:'';position:fixed;width:460px;height:460px;background:radial-gradient(circle,rgba(96,165,250,0.055) 0%,transparent 68%);border-radius:50%;bottom:-150px;right:-100px;animation:orb2 26s ease-in-out infinite alternate-reverse;pointer-events:none;z-index:0;}
@keyframes orb1{0%{transform:translate(0,0) scale(1);}40%{transform:translate(40px,25px) scale(1.07);}100%{transform:translate(-25px,45px) scale(0.94);}}
@keyframes orb2{0%{transform:translate(0,0) scale(1);}50%{transform:translate(-30px,-20px) scale(1.08);}100%{transform:translate(20px,30px) scale(0.95);}}
@keyframes fadeUp{from{opacity:0;transform:translateY(20px);}to{opacity:1;transform:translateY(0);}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes shimmer{0%{background-position:-700px 0;}100%{background-position:700px 0;}}
@keyframes pulseGold{0%,100%{box-shadow:0 0 0 0 rgba(201,168,76,0);}50%{box-shadow:0 0 0 7px rgba(201,168,76,0.12);}}
@keyframes float{0%,100%{transform:translateY(0px);}50%{transform:translateY(-6px);}}
section.main>div{animation:fadeIn 0.5s ease both;}
h1,h2,h3,h4,.stMarkdown h1,.stMarkdown h2,.stMarkdown h3{font-family:'Cormorant Garamond',serif!important;color:var(--tx-h)!important;letter-spacing:0.025em;}
h1{font-size:2.7rem!important;font-weight:600!important;}
h2{font-size:2rem!important;font-weight:500!important;}
h3{font-size:1.5rem!important;font-weight:500!important;}
[data-testid="stSubheader"] p,.stSubheader{font-family:'Cormorant Garamond',serif!important;color:var(--gold-lt)!important;font-size:1.4rem!important;letter-spacing:0.05em;text-transform:uppercase;}
hr{border:none!important;height:1px!important;background:linear-gradient(90deg,transparent,var(--gold-bdr),transparent)!important;margin:1.8rem 0!important;}
[data-testid="stSidebar"]{background:linear-gradient(185deg,#0c1020 0%,#080d18 100%)!important;border-right:1px solid var(--gold-bdr)!important;}
[data-testid="stSidebar"]>div{animation:fadeIn 0.6s ease both;}
.stButton>button{font-family:'DM Sans',sans-serif!important;font-weight:500!important;font-size:0.77rem!important;letter-spacing:0.08em!important;text-transform:uppercase!important;padding:0.65rem 1.7rem!important;border-radius:var(--r-sm)!important;border:1px solid var(--gold-bdr)!important;background:linear-gradient(135deg,rgba(201,168,76,0.13) 0%,rgba(201,168,76,0.05) 100%)!important;color:var(--gold-lt)!important;transition:all 0.28s cubic-bezier(0.4,0,0.2,1)!important;position:relative;overflow:hidden;}
.stButton>button:hover{background:linear-gradient(135deg,var(--gold) 0%,var(--gold-lt) 100%)!important;color:var(--navy)!important;border-color:var(--gold)!important;transform:translateY(-2px)!important;box-shadow:0 8px 28px rgba(201,168,76,0.35)!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,var(--gold) 0%,var(--gold-lt) 100%)!important;color:var(--navy)!important;border:none!important;font-weight:600!important;animation:pulseGold 3.2s ease infinite;}
.stButton>button[kind="primary"]:hover{transform:translateY(-3px)!important;box-shadow:0 12px 40px rgba(201,168,76,0.42)!important;}
.stTextInput>div>div>input,.stNumberInput>div>div>input,.stTextArea>div>div>textarea{background:var(--navy-card)!important;border:1px solid rgba(201,168,76,0.18)!important;border-radius:var(--r-sm)!important;color:var(--tx-h)!important;font-family:'DM Sans',sans-serif!important;transition:border-color 0.25s,box-shadow 0.25s!important;}
.stTextInput>div>div>input:focus,.stNumberInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{border-color:var(--gold)!important;box-shadow:0 0 0 3px var(--gold-pale),0 0 22px var(--gold-glow)!important;}
.stTextInput label,.stNumberInput label,.stSelectbox label,.stTextArea label,.stRadio label{font-size:0.75rem!important;font-weight:500!important;letter-spacing:0.07em!important;text-transform:uppercase!important;color:var(--tx-dim)!important;}
.stSelectbox>div>div{background:var(--navy-card)!important;border:1px solid rgba(201,168,76,0.18)!important;border-radius:var(--r-sm)!important;color:var(--tx-h)!important;}
.stTabs [data-baseweb="tab-list"]{background:var(--navy-card)!important;border-radius:var(--r)!important;border:1px solid var(--gold-bdr)!important;padding:4px!important;gap:4px!important;}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:var(--tx-dim)!important;border-radius:var(--r-sm)!important;font-size:0.78rem!important;font-weight:500!important;letter-spacing:0.05em!important;text-transform:uppercase!important;padding:0.5rem 1.2rem!important;transition:all 0.22s ease!important;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,var(--gold) 0%,var(--gold-lt) 100%)!important;color:var(--navy)!important;font-weight:600!important;box-shadow:0 4px 14px rgba(201,168,76,0.3)!important;}
[data-testid="stDataFrame"]>div{background:var(--navy-card)!important;border:1px solid var(--gold-bdr)!important;border-radius:var(--r)!important;overflow:hidden;box-shadow:var(--shadow);}
[data-testid="metric-container"]{background:var(--navy-card)!important;border:1px solid var(--gold-bdr)!important;border-radius:var(--r)!important;padding:1.2rem 1.4rem!important;box-shadow:var(--shadow);animation:fadeUp 0.55s ease both;transition:transform 0.25s ease,box-shadow 0.25s ease;}
[data-testid="metric-container"]:hover{transform:translateY(-3px)!important;box-shadow:var(--shadow),var(--shadow-gold)!important;}
[data-testid="metric-container"] label{color:var(--tx-dim)!important;font-size:0.72rem!important;letter-spacing:0.09em!important;text-transform:uppercase!important;}
[data-testid="stMetricValue"]{color:var(--tx-h)!important;font-family:'Cormorant Garamond',serif!important;font-size:2rem!important;}
[data-testid="stMetricDelta"]{font-size:0.8rem!important;}
[data-testid="stVegaLiteChart"],[data-testid="stPlotlyChart"]{background:var(--navy-card)!important;border:1px solid var(--gold-bdr)!important;border-radius:var(--r)!important;padding:1rem!important;box-shadow:var(--shadow);animation:fadeUp 0.55s ease both;transition:box-shadow 0.28s ease;}
[data-testid="stVegaLiteChart"]:hover,[data-testid="stPlotlyChart"]:hover{box-shadow:var(--shadow),var(--shadow-gold)!important;}
[data-testid="stForm"]{background:var(--navy-card)!important;border:1px solid var(--gold-bdr)!important;border-radius:var(--r)!important;padding:2rem!important;box-shadow:var(--shadow),0 0 70px rgba(201,168,76,0.07)!important;position:relative;overflow:hidden;animation:fadeUp 0.6s ease both;}
[data-testid="stForm"]::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--gold),var(--gold-lt),var(--gold),transparent);background-size:700px 2px;animation:shimmer 2.8s linear infinite;}
[data-testid="stAlert"]{border-radius:var(--r-sm)!important;border-left-width:3px!important;animation:fadeUp 0.4s ease both;}
.stSuccess{background:rgba(34,197,94,0.08)!important;border-color:var(--green)!important;}
.stInfo{background:rgba(96,165,250,0.08)!important;border-color:var(--blue)!important;}
.stWarning{background:rgba(201,168,76,0.08)!important;border-color:var(--gold)!important;}
.stError{background:rgba(244,63,94,0.08)!important;border-color:var(--red)!important;}
[data-testid="stToast"]{background:var(--navy-lift)!important;border:1px solid var(--gold-bdr)!important;border-radius:var(--r)!important;color:var(--tx-h)!important;box-shadow:var(--shadow-gold)!important;}
[data-testid="stSpinner"] div{border-top-color:var(--gold)!important;}
.stRadio>div>label{background:var(--navy-card)!important;border:1px solid rgba(201,168,76,0.14)!important;border-radius:var(--r-sm)!important;padding:0.45rem 1rem!important;color:var(--tx-b)!important;transition:all 0.22s ease!important;}
.stRadio>div>label:hover{border-color:var(--gold)!important;color:var(--gold-lt)!important;background:var(--gold-pale)!important;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:var(--navy);}
::-webkit-scrollbar-thumb{background:linear-gradient(180deg,var(--gold) 0%,rgba(201,168,76,0.3) 100%);border-radius:999px;}
nav ul{background:var(--navy-card)!important;border:1px solid var(--gold-bdr)!important;border-radius:var(--r)!important;padding:0.3rem!important;box-shadow:var(--shadow)!important;}
nav ul li a{font-family:'DM Sans',sans-serif!important;font-size:0.74rem!important;font-weight:500!important;letter-spacing:0.04em!important;color:var(--tx-dim)!important;border-radius:var(--r-sm)!important;padding:0.48rem 0.6rem!important;transition:all 0.22s ease!important;}
nav ul li a:hover{background:var(--gold-pale)!important;color:var(--gold-lt)!important;}
nav ul li a.active{background:linear-gradient(135deg,var(--gold) 0%,var(--gold-lt) 100%)!important;color:var(--navy)!important;font-weight:600!important;box-shadow:0 4px 16px rgba(201,168,76,0.38)!important;}
[data-testid="column"]:nth-child(1){animation:fadeUp 0.5s 0.05s ease both;}
[data-testid="column"]:nth-child(2){animation:fadeUp 0.5s 0.12s ease both;}
[data-testid="column"]:nth-child(3){animation:fadeUp 0.5s 0.19s ease both;}
[data-testid="metric-container"]:nth-child(1){animation-delay:0.05s;}
[data-testid="metric-container"]:nth-child(2){animation-delay:0.12s;}
[data-testid="metric-container"]:nth-child(3){animation-delay:0.19s;}
[data-testid="metric-container"]:nth-child(4){animation-delay:0.26s;}
.stMarkdown p{color:var(--tx-b)!important;line-height:1.76!important;}
.stMarkdown strong{color:var(--tx-h)!important;font-weight:600!important;}
.stBalloons{z-index:9999!important;}
.auth-card{background:linear-gradient(145deg,#131c2e 0%,#0f1626 100%);border:1px solid rgba(201,168,76,0.25);border-radius:18px;padding:2.4rem 2.2rem 2rem;box-shadow:0 20px 60px rgba(0,0,0,0.7),0 0 80px rgba(201,168,76,0.07);position:relative;overflow:hidden;animation:fadeUp 0.65s cubic-bezier(0.4,0,0.2,1) both;max-width:480px;margin:0 auto;}
.auth-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--gold),var(--gold-lt),var(--gold),transparent);background-size:700px 2px;animation:shimmer 2.8s linear infinite;}
.auth-card::after{content:'';position:absolute;width:300px;height:300px;background:radial-gradient(circle,rgba(201,168,76,0.06) 0%,transparent 70%);border-radius:50%;top:-100px;right:-80px;pointer-events:none;animation:float 6s ease-in-out infinite;}
.auth-corner{position:absolute;width:18px;height:18px;pointer-events:none;}
.auth-corner.tl{top:8px;left:8px;border-top:2px solid rgba(201,168,76,0.5);border-left:2px solid rgba(201,168,76,0.5);border-radius:3px 0 0 0;}
.auth-corner.tr{top:8px;right:8px;border-top:2px solid rgba(201,168,76,0.5);border-right:2px solid rgba(201,168,76,0.5);border-radius:0 3px 0 0;}
.auth-corner.bl{bottom:8px;left:8px;border-bottom:2px solid rgba(201,168,76,0.5);border-left:2px solid rgba(201,168,76,0.5);border-radius:0 0 0 3px;}
.auth-corner.br{bottom:8px;right:8px;border-bottom:2px solid rgba(201,168,76,0.5);border-right:2px solid rgba(201,168,76,0.5);border-radius:0 0 3px 0;}
</style>
""", unsafe_allow_html=True)

    # =========================================================================
    #  AUTH UTILITIES
    # =========================================================================
    AUTH_PATH = "config/auth.json"
    SECURITY_QUESTIONS = [
        "What was the name of your first pet?",
        "What is your mother's maiden name?",
        "What city were you born in?",
        "What was the name of your first school?",
        "What is your favourite movie?",
    ]

    def _load_auth():
        os.makedirs("config", exist_ok=True)
        if os.path.exists(AUTH_PATH) and os.path.getsize(AUTH_PATH) > 0:
            try:
                with open(AUTH_PATH, "r") as f:
                    data = json.load(f)
                if "hashed_password" in data and "users" not in data:
                    data = {"users": {"admin": {"hash": data["hashed_password"],
                        "security_q": "What is your pet's name?",
                        "security_a": bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode()}}}
                    _save_auth(data)
                return data
            except Exception:
                pass
        return {"users": {}}

    def _save_auth(data):
        with open(AUTH_PATH, "w") as f:
            json.dump(data, f, indent=4)

    def _hash(text):
        return bcrypt.hashpw(text.encode(), bcrypt.gensalt()).decode()

    def _verify(text, hashed):
        try:
            return bcrypt.checkpw(text.encode(), hashed.encode())
        except Exception:
            return False

    def _user_exists(auth, username):
        return username.strip().lower() in {k.lower() for k in auth.get("users", {})}

    def _get_user(auth, username):
        for k, v in auth.get("users", {}).items():
            if k.lower() == username.strip().lower():
                return v, k
        return None, None

    # =========================================================================
    #  AUTH PAGES
    # =========================================================================
    def _render_hero():
        st.markdown("""
        <div style="text-align:center;padding:2rem 0 1.4rem;animation:fadeUp 0.7s ease both;">
          <span style="display:block;font-family:'DM Sans',sans-serif;font-size:0.63rem;font-weight:600;
                       letter-spacing:0.45em;text-transform:uppercase;color:#c9a84c;opacity:0.8;margin-bottom:0.55rem;">
            Portfolio · Analytics · Wealth
          </span>
          <svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg"
               style="width:90px;margin:0 auto 0.6rem;display:block;
                      animation:float 4s ease-in-out infinite;filter:drop-shadow(0 0 12px rgba(201,168,76,0.35));">
            <rect x="30" y="15" width="60" height="65" fill="#c9a84c" opacity="0.85"/>
            <rect x="42" y="7" width="36" height="11" fill="#e8c96a" opacity="0.9"/>
            <rect x="52" y="1" width="16" height="9" fill="#c9a84c"/>
            <rect x="36" y="24" width="8" height="8" fill="#080d18" opacity="0.7"/>
            <rect x="49" y="24" width="8" height="8" fill="#080d18" opacity="0.7"/>
            <rect x="62" y="24" width="8" height="8" fill="#080d18" opacity="0.3"/>
            <rect x="75" y="24" width="8" height="8" fill="#080d18" opacity="0.7"/>
            <rect x="36" y="37" width="8" height="8" fill="#080d18" opacity="0.7"/>
            <rect x="49" y="37" width="8" height="8" fill="#080d18" opacity="0.7"/>
            <rect x="62" y="37" width="8" height="8" fill="#080d18" opacity="0.7"/>
            <rect x="75" y="37" width="8" height="8" fill="#080d18" opacity="0.3"/>
            <rect x="36" y="50" width="8" height="8" fill="#080d18" opacity="0.3"/>
            <rect x="49" y="50" width="8" height="8" fill="#080d18" opacity="0.7"/>
            <rect x="62" y="50" width="8" height="8" fill="#080d18" opacity="0.7"/>
            <rect x="75" y="50" width="8" height="8" fill="#080d18" opacity="0.7"/>
            <rect x="49" y="64" width="22" height="16" fill="#080d18" opacity="0.5"/>
            <rect x="3" y="40" width="24" height="40" fill="#8a6e30" opacity="0.65"/>
            <rect x="93" y="45" width="24" height="35" fill="#8a6e30" opacity="0.65"/>
            <line x1="0" y1="80" x2="120" y2="80" stroke="#c9a84c" stroke-width="1" opacity="0.35"/>
          </svg>
          <span style="display:block;font-family:'Cormorant Garamond',serif;font-size:2.8rem;font-weight:700;
                       background:linear-gradient(135deg,#e8c96a 0%,#f5f0e8 45%,#c9a84c 100%);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                       background-clip:text;letter-spacing:0.06em;line-height:1.1;">
            💸 Expense Tracker
          </span>
          <div style="width:70px;height:1px;background:linear-gradient(90deg,transparent,#c9a84c,transparent);margin:0.85rem auto 0;"></div>
        </div>
        """, unsafe_allow_html=True)

    def _page_login(auth):
        st.markdown("""
        <div style="text-align:center;margin-bottom:1.6rem;animation:fadeUp 0.65s cubic-bezier(0.4,0,0.2,1) both;">
          <div style="font-size:2rem;margin-bottom:0.3rem;">🔐</div>
          <div style="font-family:'Cormorant Garamond',serif;font-size:1.55rem;font-weight:600;color:#eef0f8;letter-spacing:0.04em;">Secure Sign In</div>
          <div style="font-size:0.78rem;color:#565e72;margin-top:0.25rem;letter-spacing:0.06em;">Your financial command centre</div>
        </div>
        """, unsafe_allow_html=True)
        username = st.text_input("👤 Username", placeholder="Enter your username", key="li_user")
        password = st.text_input("🔑 Password", type="password", placeholder="Enter your password", key="li_pass")
        col_a, col_b = st.columns(2)
        with col_a:
            login_clicked = st.button("🚀 Login", type="primary", use_container_width=True)
        with col_b:
            forgot_clicked = st.button("🔓 Forgot Password", use_container_width=True)
        if login_clicked:
            if not username.strip() or not password.strip():
                st.error("Please enter both username and password.")
            else:
                user_data, real_key = _get_user(auth, username)
                if user_data is None:
                    st.error("❌ Account not found. Please register first.")
                    st.info("👇 Switch to **Register** tab to create a new account.")
                elif _verify(password, user_data["hash"]):
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"]  = real_key
                    st.success(f"✅ Welcome back, **{real_key}**!")
                    st.rerun()
                else:
                    st.error("❌ Incorrect password. Please try again.")
        if forgot_clicked:
            st.session_state["auth_page"] = "forgot"
            st.rerun()
        st.markdown("---")
        st.markdown("<div style='text-align:center;font-size:0.78rem;color:#565e72;'>No account yet? Switch to the <b style='color:#c9a84c;'>Register</b> tab above.</div>", unsafe_allow_html=True)

    def _page_register(auth):
        st.markdown("""
        <div style="text-align:center;margin-bottom:1.4rem;animation:fadeUp 0.5s ease both;">
          <div style="font-size:1.9rem;margin-bottom:0.3rem;">🏛️</div>
          <div style="font-family:'Cormorant Garamond',serif;font-size:1.5rem;font-weight:600;color:#eef0f8;letter-spacing:0.04em;">Create Account</div>
          <div style="font-size:0.77rem;color:#565e72;margin-top:0.2rem;">Set up your financial command centre</div>
        </div>
        """, unsafe_allow_html=True)
        new_user     = st.text_input("👤 Choose a Username", placeholder="e.g. john_doe", key="reg_user")
        new_pass     = st.text_input("🔑 Password", type="password", placeholder="Min 6 characters", key="reg_pass")
        confirm_pass = st.text_input("🔑 Confirm Password", type="password", placeholder="Re-enter your password", key="reg_confirm")
        sec_q        = st.selectbox("🛡️ Security Question", SECURITY_QUESTIONS, key="reg_secq")
        sec_a        = st.text_input("✏️ Your Answer", placeholder="Memorable answer", key="reg_seca")
        if st.button("✅ Create Account", type="primary", use_container_width=True):
            if not new_user.strip():
                st.error("Username cannot be empty.")
            elif len(new_user.strip()) < 3:
                st.error("Username must be at least 3 characters.")
            elif _user_exists(auth, new_user):
                st.error(f"❌ Username **{new_user}** is already taken.")
            elif len(new_pass) < 6:
                st.error("Password must be at least 6 characters.")
            elif new_pass != confirm_pass:
                st.error("❌ Passwords do not match.")
            elif not sec_a.strip():
                st.error("Please provide a security answer.")
            else:
                auth.setdefault("users", {})[new_user.strip()] = {
                    "hash": _hash(new_pass), "security_q": sec_q,
                    "security_a": _hash(sec_a.strip().lower()),
                }
                _save_auth(auth)
                st.success(f"🎉 Account **{new_user}** created! Switch to Login.")
                st.balloons()
        st.markdown("---")
        st.markdown("<div style='text-align:center;font-size:0.78rem;color:#565e72;'>Already have an account? Switch to the <b style='color:#c9a84c;'>Login</b> tab.</div>", unsafe_allow_html=True)

    def _page_forgot(auth):
        st.markdown("""
        <div style="text-align:center;margin-bottom:1.4rem;animation:fadeUp 0.5s ease both;">
          <div style="font-size:1.9rem;margin-bottom:0.3rem;">🔓</div>
          <div style="font-family:'Cormorant Garamond',serif;font-size:1.5rem;font-weight:600;color:#eef0f8;letter-spacing:0.04em;">Reset Password</div>
          <div style="font-size:0.77rem;color:#565e72;margin-top:0.2rem;">Verify your identity with your security answer</div>
        </div>
        """, unsafe_allow_html=True)
        step = st.session_state.get("reset_step", 1)
        if step == 1:
            username = st.text_input("👤 Enter your Username", key="fp_user")
            if st.button("🔍 Find Account", type="primary", use_container_width=True):
                if not username.strip():
                    st.error("Please enter your username.")
                else:
                    user_data, real_key = _get_user(auth, username)
                    if user_data is None:
                        st.error("❌ No account found with that username.")
                    else:
                        st.session_state["reset_user"] = real_key
                        st.session_state["reset_step"] = 2
                        st.rerun()
        elif step == 2:
            real_key  = st.session_state["reset_user"]
            user_data = auth["users"][real_key]
            st.info(f"**Account:** {real_key}")
            st.markdown(f"**Security Question:** _{user_data['security_q']}_")
            sec_a = st.text_input("✏️ Your Answer", key="fp_ans")
            if st.button("✅ Verify Answer", type="primary", use_container_width=True):
                if _verify(sec_a.strip().lower(), user_data["security_a"]):
                    st.session_state["reset_step"] = 3
                    st.rerun()
                else:
                    st.error("❌ Incorrect answer.")
        elif step == 3:
            real_key = st.session_state["reset_user"]
            st.success(f"✅ Identity verified for **{real_key}**")
            new_pass    = st.text_input("🔑 New Password", type="password", placeholder="Min 6 characters", key="fp_newpass")
            confirm_new = st.text_input("🔑 Confirm New Password", type="password", key="fp_confirm")
            if st.button("🔄 Reset Password", type="primary", use_container_width=True):
                if len(new_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                elif new_pass != confirm_new:
                    st.error("❌ Passwords do not match.")
                else:
                    auth["users"][real_key]["hash"] = _hash(new_pass)
                    _save_auth(auth)
                    st.success(f"✅ Password reset for **{real_key}**! Please log in.")
                    for k in ("reset_user", "reset_step"):
                        st.session_state.pop(k, None)
                    st.session_state["auth_page"] = "login"
                    st.rerun()
        st.markdown("---")
        if st.button("← Back to Login", use_container_width=True):
            for k in ("reset_user", "reset_step"):
                st.session_state.pop(k, None)
            st.session_state["auth_page"] = "login"
            st.rerun()

    # =========================================================================
    #  SESSION INIT
    # =========================================================================
    auth = _load_auth()
    
    # PERMANENT HARDCODED ACCOUNT (Survives Render Resets)
    # The server will automatically recreate this account if the drive gets wiped.
    if "admin" not in auth.setdefault("users", {}):
        auth["users"]["admin"] = {
            "hash": _hash("admin123"), 
            "security_q": SECURITY_QUESTIONS[0],
            "security_a": _hash("fluffy"),
        }
        _save_auth(auth)

    for key, default in [("authenticated", False), ("current_user", ""), ("auth_page", "login")]:
        if key not in st.session_state:
            st.session_state[key] = default

    # =========================================================================
    #  ROUTING
    # =========================================================================
    if not st.session_state["authenticated"]:
        _render_hero()
        if st.session_state["auth_page"] == "forgot":
            _page_forgot(auth)
        else:
            tab_login, tab_register = st.tabs(["🔐  Login", "🏛️  Register"])
            with tab_login:
                _page_login(auth)
            with tab_register:
                _page_register(auth)
        st.stop()

    # ── Authenticated header ──────────────────────────────────────────────────
    st.markdown("""
<div style="text-align:center;padding:2.2rem 0 1.2rem;animation:fadeUp 0.7s ease both;">
  <span style="display:block;font-family:'DM Sans',sans-serif;font-size:0.65rem;font-weight:600;
               letter-spacing:0.45em;text-transform:uppercase;color:#c9a84c;opacity:0.75;margin-bottom:0.55rem;">
    Portfolio · Analytics · Wealth
  </span>
  <span style="display:block;font-family:'Cormorant Garamond',serif;font-size:3.1rem;font-weight:700;
               background:linear-gradient(135deg,#e8c96a 0%,#f5f0e8 45%,#c9a84c 100%);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;
               background-clip:text;letter-spacing:0.06em;line-height:1.1;">
    💸 Expense Tracker
  </span>
  <div style="width:70px;height:1px;background:linear-gradient(90deg,transparent,#c9a84c,transparent);margin:0.9rem auto 0;"></div>
</div>
""", unsafe_allow_html=True)

    user = st.session_state.get("current_user", "Admin")
    st.sidebar.markdown(f"""
<div style="text-align:center;padding:1rem 0 0.5rem;">
  <div style="font-size:2rem;">👤</div>
  <div style="font-family:'Cormorant Garamond',serif;font-size:1.1rem;color:#e8c96a;font-weight:600;">{user}</div>
  <div style="font-size:0.68rem;color:#565e72;letter-spacing:0.07em;text-transform:uppercase;margin-top:0.2rem;">Authenticated</div>
</div>
""", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["current_user"]  = ""
        st.rerun()
    st.sidebar.markdown("---")
    with st.sidebar.expander("🔑 Change Password"):
        old_p  = st.text_input("Current Password", type="password", key="cp_old")
        new_p  = st.text_input("New Password",      type="password", key="cp_new")
        conf_p = st.text_input("Confirm New",        type="password", key="cp_conf")
        if st.button("Update Password", key="cp_btn"):
            user_data = auth["users"].get(user, {})
            if not old_p.strip():
                st.error("Please enter your current password.")
            elif not _verify(old_p, user_data.get("hash", "")):
                st.error("❌ Current password is wrong.")
            elif len(new_p) < 6:
                st.error("New password must be at least 6 characters.")
            elif new_p != conf_p:
                st.error("❌ Passwords do not match.")
            else:
                auth["users"][user]["hash"] = _hash(new_p)
                _save_auth(auth)
                st.success("✅ Password updated!")

    try:
        app.run()
    except Exception as e:
        import traceback
        st.error(f"Error in app: {e}")
        st.code(traceback.format_exc(), language="python")
        st.info("Make sure all files are present in the utils folder.")


# ── Entry point ───────────────────────────────────────────────────────────────
_boot()
