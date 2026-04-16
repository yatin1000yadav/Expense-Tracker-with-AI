# utils/voice_utils.py - Cloud Fixed Version (One-Go)

import streamlit as st
import whisper
import re
import pandas as pd
from datetime import datetime
import tempfile
import os
from io import BytesIO

# Safe Import for Streamlit Cloud
try:
    from audiorecorder import audiorecorder
except ImportError:
    try:
        from streamlit_audiorecorder import audiorecorder
    except ImportError:
        st.error("❌ streamlit-audiorecorder is not installed. Add it to requirements.txt")
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
# Convert AudioSegment to WAV bytes
# ============================================
def audio_segment_to_wav_bytes(audio_segment):
    buffer = BytesIO()
    audio_segment.export(buffer, format="wav")
    buffer.seek(0)
    return buffer.read()

# ============================================
# Transcribe Audio
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
            initial_prompt="Expense tracker examples: spent 500 on food, paid 1200 for electricity, received salary 50000, uncle gave me 500 rupees, salary mila, petrol 300.",
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
# Parser with Strong Credit Detection
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

    # Strong Credit Detection
    if any(phrase in text_lower for phrase in ['gave me', 'uncle gave', 'aunty gave', 'received', 'salary', 'income', 'credited', 'credit amount', 'mila', 'got paid']):
        trans_type = "credit"
    elif any(kw in text_lower for kw in ['salary', 'income', 'credited', 'received', 'mila', 'got']) and not any(kw in text_lower for kw in ['spent', 'paid', 'bill', 'kharcha', 'gaya', 'petrol', 'food']):
        trans_type = "credit"
    elif any(kw in text_lower for kw in ['spent', 'paid', 'bill', 'kharcha', 'gaya', 'purchase', 'bought', 'expense', 'petrol', 'food']):
        trans_type = "debit"
    else:
        trans_type = "debit"

    # Category
    categories = {
        "Food": ["food", "khana", "lunch", "dinner"],
        "Petrol": ["petrol", "fuel"],
        "Bills": ["bill", "electricity"],
        "Shopping": ["shopping", "purchase"],
        "Salary": ["salary", "income"],
        "Gift": ["uncle", "aunty", "gave me"],
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

    st.info("**How to use:** Click mic button → Speak → Stop → Click Transcribe Audio")

    audio_segment = audiorecorder("🎙️ Click to Start Recording", "⏹️ Click to Stop Recording")

    if audio_segment is not None and audio_segment.duration_seconds > 0.5:
        st.success("✅ Audio recorded! Click **Transcribe Audio**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔍 Transcribe Audio", type="primary", use_container_width=True):
            if audio_segment is None or audio_segment.duration_seconds < 0.5:
                st.error("❌ Please record first.")
            else:
                with st.spinner("Transcribing..."):
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

    # Confirm & Save
    if st.session_state.parsed_data is not None:
        st.markdown("---")
        parsed = st.session_state.parsed_data

        st.info(f"📝 **You said:** {st.session_state.transcribed_text}")
        color = "green" if parsed['type'] == "credit" else "red"
        st.markdown(f"**Type:** <span style='color:{color}; font-weight:bold;'>{parsed['type'].upper()}</span>", unsafe_allow_html=True)
        st.json(parsed)

        override = st.radio("Correct type:", ["credit", "debit"], 
                            index=0 if parsed['type']=="credit" else 1, horizontal=True)
        st.session_state.parsed_data['type'] = override

        if st.button("✅ Confirm Entry & Save to Sheet", type="primary"):
            date = datetime.now().strftime('%d-%m-%Y')
            month = datetime.now().strftime('%B')

            if parsed['type'] == 'credit':
                new_row = {'date': date, 'month': month, 'credit': parsed['amount'], 'credit_details': parsed['details'],
                           'debit': 0, 'debit_details': 'NA', 'category': parsed['category']}
            else:
                new_row = {'date': date, 'month': month, 'credit': 0, 'credit_details': 'NA',
                           'debit': -parsed['amount'] if parsed['amount'] else 0, 'debit_details': parsed['details'],
                           'category': parsed['category']}

            from utils.gsheet_utils import update_data_to_gsheet
            new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            update_data_to_gsheet(sheet, new_df)

            st.success("✅ Saved successfully!")
            st.balloons()

            st.session_state.parsed_data = None
            st.session_state.transcribed_text = None
            st.rerun()

    st.markdown("---")
    st.subheader("✍️ Manual Entry")
    manual = st.text_input("Type here (e.g. uncle gave me 500 or spent 300 on food)")
    if st.button("Process Manual Text"):
        if manual.strip():
            result = parse_natural_command(manual)
            st.session_state.transcribed_text = manual
            st.session_state.parsed_data = result
            st.rerun()
