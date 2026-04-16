# utils/voice_utils.py - Final Cloud-Compatible Version

import streamlit as st
import whisper
import re
import pandas as pd
from datetime import datetime
import tempfile
import os
from io import BytesIO

# Safe import for Streamlit Cloud
try:
    from audiorecorder import audiorecorder
except ImportError:
    try:
        from streamlit_audiorecorder import audiorecorder
    except ImportError:
        st.error("❌ 'streamlit-audiorecorder' package is missing. Please check requirements.txt")
        st.stop()

from pydub import AudioSegment

# ============================================
# Load Whisper Model
# ============================================
@st.cache_resource
def load_whisper_model():
    try:
        model = whisper.load_model("base", device="cpu")
        return model, None
    except Exception as e:
        return None, str(e)

# ============================================
# AudioSegment to WAV bytes
# ============================================
def audio_segment_to_wav_bytes(audio_segment: AudioSegment) -> bytes:
    buffer = BytesIO()
    audio_segment.export(buffer, format="wav")
    buffer.seek(0)
    return buffer.read()

# ============================================
# Transcribe
# ============================================
def transcribe_audio(audio_segment, model):
    if audio_segment is None or audio_segment.duration_seconds < 0.5:
        return None
    try:
        wav_bytes = audio_segment_to_wav_bytes(audio_segment)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with open(tmp.name, "wb") as f:
            f.write(wav_bytes)
        
        result = model.transcribe(
            tmp.name,
            initial_prompt=(
                "This is an expense tracker. "
                "Examples: spent 500 on food, paid 1200 electricity bill, "
                "received salary 50000, uncle gave me 500 rupees added to credit, "
                "salary mila, petrol kharcha 300."
            ),
            temperature=0,
            language=None
        )
        return result["text"].strip()
    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
        return None
    finally:
        if 'tmp' in locals() and os.path.exists(tmp.name):
            try:
                os.remove(tmp.name)
            except:
                pass

# ============================================
# Parser (Improved Credit Detection)
# ============================================
WORD_TO_NUM = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "twenty": "20", "thirty": "30", "forty": "40", "fifty": "50",
    "hundred": "100", "thousand": "1000", "lakh": "100000", "lac": "100000",
}

def normalize_spoken_numbers(text: str) -> str:
    text = re.sub(r'\b(rupees?|rs\.?|inr|₹)\b', '', text, flags=re.IGNORECASE)
    for word, digit in WORD_TO_NUM.items():
        text = re.sub(rf'\b{word}\b', digit, text, flags=re.IGNORECASE)
    text = re.sub(r'\b(\d+)\s+(100|1000|100000)\b', lambda m: str(int(m.group(1)) * int(m.group(2))), text)
    return text

def parse_natural_command(text: str) -> dict:
    text_lower = text.lower().strip()
    normalized = normalize_spoken_numbers(text_lower)

    amounts = re.findall(r'\b(\d+(?:,\d{3})*(?:\.\d{1,2})?)\b', normalized)
    amount = max([float(a.replace(',', '')) for a in amounts]) if amounts else None

    strong_credit_phrases = [
        'gave me', 'uncle gave', 'aunty gave', 'received', 'salary', 'income', 
        'credited', 'credit amount', 'added to credit', 'add to my credit', 
        'mila', 'mil gaya', 'aa gaya', 'got', 'got paid'
    ]

    credit_keywords = ['salary', 'income', 'credited', 'received', 'refund', 'bonus', 'deposit', 'credit', 'mila', 'got']
    debit_keywords = ['spent', 'paid', 'bill', 'kharcha', 'gaya', 'purchase', 'bought', 'expense', 'petrol', 'food', 'diya']

    if any(phrase in text_lower for phrase in strong_credit_phrases):
        trans_type = "credit"
    elif any(kw in text_lower for kw in credit_keywords) and not any(kw in text_lower for kw in debit_keywords):
        trans_type = "credit"
    elif any(kw in text_lower for kw in debit_keywords):
        trans_type = "debit"
    else:
        trans_type = "debit"

    categories = {
        "Food": ["food", "khana", "lunch", "dinner", "snack"],
        "Petrol": ["petrol", "fuel"],
        "Bills": ["bill", "electricity", "recharge"],
        "Shopping": ["shopping", "purchase"],
        "Salary": ["salary", "income"],
        "Gift": ["uncle", "aunty", "gave me", "gift"],
        "Other": []
    }

    detected_category = "Other"
    for cat, kws in categories.items():
        if any(kw in text_lower for kw in kws):
            detected_category = cat
            break

    return {
        'amount': amount,
        'type': trans_type,
        'category': detected_category,
        'details': text_lower
    }

# ============================================
# Main Voice Interface
# ============================================
def show_voice_interface(df, sheet):
    st.markdown("# 🎤 Smart Voice Assistant")
    st.markdown("---")

    model, error = load_whisper_model()
    if error:
        st.error(f"❌ Whisper load failed: {error}")
        return

    for key in ['parsed_data', 'transcribed_text']:
        if key not in st.session_state:
            st.session_state[key] = None

    st.info("**How to use:** Click the mic button → Speak clearly → Click Stop → Click **Transcribe Audio**")

    audio_segment = audiorecorder("🎙️ Click to Start Recording", "⏹️ Click to Stop Recording")

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
                    st.session_state.parsed_data = parsed
                else:
                    st.warning("Could not understand speech. Try again.")

    with col2:
        if st.button("🗑️ Clear & Reset", use_container_width=True):
            st.session_state.parsed_data = None
            st.session_state.transcribed_text = None
            st.rerun()

    if st.session_state.parsed_data is not None:
        st.markdown("---")
        parsed = st.session_state.parsed_data

        st.info(f"📝 **You said:** {st.session_state.transcribed_text}")
        color = "green" if parsed['type'] == "credit" else "red"
        st.markdown(f"**Type:** <span style='color:{color}; font-weight:bold;'>{parsed['type'].upper()}</span>", unsafe_allow_html=True)
        st.json(parsed)

        override_type = st.radio("Correct the type if needed:", ["credit", "debit"], 
                                 index=0 if parsed['type'] == "credit" else 1, horizontal=True)
        st.session_state.parsed_data['type'] = override_type

        if st.button("✅ Confirm Entry & Save to Sheet", type="primary"):
            date = datetime.now().strftime('%d-%m-%Y')
            month = datetime.now().strftime('%B')

            if parsed['type'] == 'credit':
                new_row = {'date': date, 'month': month, 'credit': parsed['amount'], 
                           'credit_details': parsed['details'], 'debit': 0, 'debit_details': 'NA',
                           'category': parsed['category']}
            else:
                new_row = {'date': date, 'month': month, 'credit': 0, 'credit_details': 'NA',
                           'debit': -parsed['amount'] if parsed['amount'] else 0, 
                           'debit_details': parsed['details'], 'category': parsed['category']}

            from utils.gsheet_utils import update_data_to_gsheet
            new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            update_data_to_gsheet(sheet, new_df)

            st.success("✅ Transaction saved successfully!")
            st.balloons()

            st.session_state.parsed_data = None
            st.session_state.transcribed_text = None
            st.rerun()

    st.markdown("---")
    st.subheader("✍️ Manual Entry")
    manual_text = st.text_input("Example: spent 500 on food or uncle gave me 500")
    if st.button("Process Manual Text"):
        if manual_text.strip():
            result = parse_natural_command(manual_text)
            st.session_state.transcribed_text = manual_text
            st.session_state.parsed_data = result
            st.rerun()
