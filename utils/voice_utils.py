# utils/voice_utils.py - Fixed & Improved Version

import streamlit as st
import re
import pandas as pd
from datetime import datetime
import tempfile
import os
from io import BytesIO

# Safe import for whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Safe import for audiorecorder
try:
    from audiorecorder import audiorecorder
    AUDIO_AVAILABLE = True
except ImportError:
    try:
        from streamlit_audiorecorder import audiorecorder
        AUDIO_AVAILABLE = True
    except ImportError:
        AUDIO_AVAILABLE = False

# Safe import for pydub
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


# ============================================================
# Load Whisper Model (cached so it only loads once)
# ============================================================
@st.cache_resource
def load_whisper_model():
    if not WHISPER_AVAILABLE:
        return None, "Whisper not installed"
    try:
        model = whisper.load_model("base", device="cpu")
        return model, None
    except Exception as e:
        return None, str(e)


# ============================================================
# AudioSegment → WAV bytes
# ============================================================
def audio_segment_to_wav_bytes(audio_segment) -> bytes:
    buffer = BytesIO()
    audio_segment.export(buffer, format="wav")
    buffer.seek(0)
    return buffer.read()


# ============================================================
# Transcribe with Whisper
# ============================================================
def transcribe_audio(audio_segment, model):
    if model is None:
        return None
    if audio_segment is None or audio_segment.duration_seconds < 0.5:
        return None
    tmp_path = None
    try:
        wav_bytes = audio_segment_to_wav_bytes(audio_segment)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(wav_bytes)
            tmp_path = tmp.name

        result = model.transcribe(
            tmp_path,
            initial_prompt=(
                "This is an expense tracker. "
                "Examples: spent 500 on food, paid 1200 electricity bill, "
                "received salary 50000, uncle gave me 500 rupees added to credit, "
                "salary mila, petrol kharcha 300, won 20 crores in KBC, "
                "received 5 lakh salary, paid 2 lakh 50 thousand for rent."
            ),
            temperature=0,
            language=None,
        )
        return result["text"].strip()
    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


# ============================================================
# Indian number unit parser
# ============================================================

WORD_TO_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}

INDIAN_UNITS = [
    (r'\barab s?\b',    1_000_000_000),
    (r'\bcrores?\b',    10_000_000),
    (r'\bcr\b',         10_000_000),
    (r'\blakhs?\b',     100_000),
    (r'\blacs?\b',      100_000),
    (r'\bthousands?\b', 1_000),
    (r'\bhundreds?\b',  100),
]


def _words_to_base_number(text: str) -> str:
    for word, val in sorted(WORD_TO_NUM.items(), key=lambda x: -len(x[0])):
        text = re.sub(rf'\b{word}\b', str(val), text, flags=re.IGNORECASE)
    return text


def _collapse_indian_units(text: str) -> str:
    for pattern, multiplier in INDIAN_UNITS:
        new_text = ""
        last_end = 0
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            before = text[:m.start()].rstrip()
            num_match = re.search(r'(\d+(?:\.\d+)?)\s*$', before)
            if num_match:
                num_pos = before.rfind(num_match.group(1))
                val = int(float(num_match.group(1)) * multiplier)
                new_text += text[last_end:num_pos] + str(val)
                last_end = m.end()
            else:
                new_text += text[last_end:m.end()]
                last_end = m.end()
        new_text += text[last_end:]
        text = new_text

    for _ in range(3):
        text = re.sub(
            r'\b(\d{3,})\s+(\d{3,})\b',
            lambda m: str(int(m.group(1)) + int(m.group(2))),
            text,
        )
    return text


def normalize_spoken_numbers(text: str) -> str:
    text = re.sub(r'\b(rupees?|rs\.?|inr|₹)\b', '', text, flags=re.IGNORECASE)
    text = _words_to_base_number(text)
    text = _collapse_indian_units(text)
    return text


# ============================================================
# Credit / Debit parser
# ============================================================
STRONG_CREDIT_PHRASES = [
    'gave me', 'give me', 'given me',
    'uncle gave', 'aunty gave', 'bhai ne diya', 'sister ne diya',
    'friend gave', 'ne diya', 'ne bheja',
    'received', 'received from',
    'salary', 'salary mila', 'salary aa gaya',
    'income', 'bonus',
    'credited', 'credit amount',
    'added to credit', 'add to my credit', 'add credit',
    'mila', 'mil gaya', 'aa gaya', 'aa gyi',
    'got paid', 'got money', 'got cash',
    'won', 'win', 'prize', 'award', 'reward',
    'cashback', 'refund', 'reimbursement',
    'deposited', 'deposit',
    'transferred to me', 'transfer received',
]

CREDIT_KEYWORDS = [
    'salary', 'income', 'credited', 'received', 'refund', 'bonus',
    'deposit', 'credit', 'mila', 'got', 'won', 'prize', 'award',
    'cashback', 'reimbursement',
]

DEBIT_KEYWORDS = [
    'spent', 'paid', 'bill', 'kharcha', 'gaya', 'purchase', 'bought',
    'expense', 'petrol', 'food', 'diya', 'diye', 'nikala', 'nikale',
    'transfer kiya', 'bheja', 'send kiya', 'payment',
]


def parse_natural_command(text: str) -> dict:
    text_lower = text.lower().strip()
    normalized = normalize_spoken_numbers(text_lower)

    amounts = re.findall(r'\b(\d+(?:,\d{3})*(?:\.\d{1,2})?)\b', normalized)
    amount  = max([float(a.replace(',', '')) for a in amounts]) if amounts else None

    if any(phrase in text_lower for phrase in STRONG_CREDIT_PHRASES):
        trans_type = "credit"
    elif any(kw in text_lower for kw in CREDIT_KEYWORDS) and \
            not any(kw in text_lower for kw in DEBIT_KEYWORDS):
        trans_type = "credit"
    elif any(kw in text_lower for kw in DEBIT_KEYWORDS):
        trans_type = "debit"
    else:
        trans_type = "debit"

    CATEGORIES = {
        "Food":        ["food", "khana", "lunch", "dinner", "snack", "breakfast",
                        "meal", "swiggy", "zomato", "blinkit"],
        "Petrol":      ["petrol", "fuel", "diesel"],
        "Bills":       ["bill", "electricity", "recharge", "broadband", "wifi"],
        "Shopping":    ["shopping", "purchase", "amazon", "flipkart", "myntra"],
        "Salary":      ["salary", "income", "payroll"],
        "Gift":        ["uncle", "aunty", "bhai", "didi", "friend", "gave me",
                        "gift", "ne diya"],
        "Prize":       ["won", "prize", "award", "kbc", "lottery", "reward"],
        "SIP":         ["sip", "mutual fund", "investment", "groww", "zerodha"],
        "Side Income": ["freelance", "client", "consulting", "project"],
        "Other":       [],
    }

    detected_category = "Other"
    for cat, kws in CATEGORIES.items():
        if any(kw in text_lower for kw in kws):
            detected_category = cat
            break

    return {
        'amount':   amount,
        'type':     trans_type,
        'category': detected_category,
        'details':  text_lower,
    }


# ============================================================
# Save voice entry helper
# ============================================================
def _save_voice_entry(df, sheet, parsed):
    from utils.gsheet_utils import update_data_to_gsheet

    date  = datetime.now().strftime('%d-%m-%Y')
    month = datetime.now().strftime('%B')
    amt   = parsed.get('amount') or 0

    if parsed['type'] == 'credit':
        new_row = {
            'date': date, 'month': month,
            'credit': amt,      'credit_details': parsed.get('details', 'Voice Entry'),
            'debit':  0,        'debit_details':  'NA',
            'category': parsed.get('category', 'Other'),
        }
    else:
        new_row = {
            'date': date, 'month': month,
            'credit': 0,        'credit_details': 'NA',
            'debit': -abs(amt), 'debit_details':  parsed.get('details', 'Voice Entry'),
            'category': parsed.get('category', 'Other'),
        }

    new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    st.session_state['live_df'] = new_df.copy()
    update_data_to_gsheet(sheet, new_df)
    return new_df


# ============================================================
# Main Voice Interface
# ============================================================
def show_voice_interface(df, sheet):
    st.markdown("# 🎤 Smart Voice Assistant")
    st.markdown("---")

    # Show warning if voice features unavailable but don't crash
    if not WHISPER_AVAILABLE or not AUDIO_AVAILABLE or not PYDUB_AVAILABLE:
        st.warning("⚠️ Voice recording is not available in this environment. Use Manual Entry below.")
        model = None
    else:
        model, error = load_whisper_model()
        if error:
            st.warning(f"⚠️ Voice model unavailable: {error}. Use Manual Entry below.")
            model = None

    for key in ['parsed_data', 'transcribed_text']:
        if key not in st.session_state:
            st.session_state[key] = None

    if model is not None and AUDIO_AVAILABLE:
        st.info("**How to use:** Click the mic → Speak clearly → Click Stop → Click **Transcribe Audio**")

        audio_segment = audiorecorder(
            "🎙️ Click to Start Recording",
            "⏹️ Click to Stop Recording",
        )

        if audio_segment is not None and audio_segment.duration_seconds > 0.5:
            st.success("✅ Audio recorded! Now click **Transcribe Audio**")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔍 Transcribe Audio", type="primary", use_container_width=True):
                if audio_segment is None or audio_segment.duration_seconds < 0.5:
                    st.error("❌ Please record audio first.")
                else:
                    with st.spinner("🎙️ Transcribing..."):
                        text = transcribe_audio(audio_segment, model)

                    if text:
                        st.info(f"💬 **Heard:** {text}")
                        parsed = parse_natural_command(text)
                        st.session_state.transcribed_text = text
                        st.session_state.parsed_data      = parsed
                    else:
                        st.warning("Could not understand speech. Try again.")

        with col2:
            if st.button("🗑️ Clear & Reset", use_container_width=True):
                st.session_state.parsed_data      = None
                st.session_state.transcribed_text = None
                st.rerun()

    # ── Parsed result & confirmation UI ────────────────────────────────────
    if st.session_state.parsed_data is not None:
        st.markdown("---")
        parsed = st.session_state.parsed_data

        st.info(f"📝 **You said:** {st.session_state.transcribed_text}")
        color = "green" if parsed['type'] == "credit" else "red"
        st.markdown(
            f"**Detected Type:** "
            f"<span style='color:{color}; font-weight:bold;'>"
            f"{'💰 INCOME (Credit)' if parsed['type'] == 'credit' else '💸 EXPENSE (Debit)'}"
            f"</span>",
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Amount", f"₹{parsed['amount']:,.0f}" if parsed['amount'] else "Not detected")
        with col_b:
            st.metric("Category", parsed['category'])

        st.markdown("**Correct if needed:**")
        override_type = st.radio(
            "Transaction Type",
            ["credit", "debit"],
            index=0 if parsed['type'] == "credit" else 1,
            horizontal=True,
            key="voice_type_override",
        )
        st.session_state.parsed_data['type'] = override_type

        override_amount = st.number_input(
            "Amount (₹) — correct if wrong",
            min_value=0.0,
            value=float(parsed['amount']) if parsed['amount'] else 0.0,
            step=1.0,
            format="%.0f",
            key="voice_amount_override",
        )
        st.session_state.parsed_data['amount'] = override_amount

        if st.button("✅ Confirm Entry & Save", type="primary", use_container_width=True):
            if override_amount <= 0:
                st.error("❌ Amount must be greater than 0.")
            else:
                _save_voice_entry(df, sheet, st.session_state.parsed_data)
                st.success("✅ Transaction saved successfully!")
                st.balloons()
                st.session_state.parsed_data      = None
                st.session_state.transcribed_text = None
                st.rerun()

    # ── Manual text entry ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("✍️ Manual Entry")
    manual_text = st.text_input(
        "Example: spent 500 on food   OR   won 20 crores in KBC   OR   received 5 lakh salary",
        key="voice_manual_input",
    )
    if st.button("Process Manual Text", key="voice_process_manual"):
        if manual_text.strip():
            result = parse_natural_command(manual_text)
            st.session_state.transcribed_text = manual_text
            st.session_state.parsed_data      = result
            st.rerun()
        else:
            st.warning("Please enter some text first.")
