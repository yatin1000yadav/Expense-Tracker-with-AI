# utils/ocr_utils.py – Fixed Version
import streamlit as st
import pytesseract
from PIL import Image
import re
import pandas as pd
import os
from datetime import datetime
import platform


# ============================================================
# CATEGORY AUTO-DETECTION FROM RECEIPT TEXT
# ============================================================

DEBIT_CATEGORY_KEYWORDS = {
    "Today's expense ": [
        'cafe', 'coffee', 'tea', 'snack', 'juice', 'chai', 'bakery',
        'daily', 'canteen', 'lunch', 'dinner', 'breakfast', 'meal',
        'swiggy', 'zomato', 'blinkit', 'zepto', 'instamart',
    ],
    "Weekend expense": [
        'bar', 'pub', 'club', 'lounge', 'weekend', 'party', 'movie',
        'pvr', 'inox', 'bookmyshow', 'bowling', 'arcade', 'amusement',
    ],
    "Shopping": [
        'amazon', 'flipkart', 'myntra', 'ajio', 'meesho', 'nykaa',
        'shopping', 'mall', 'store', 'mart', 'retail', 'cloth', 'fashion',
        'shoes', 'apparel', 'garment', 'boutique',
    ],
    "Petrol": [
        'petrol', 'diesel', 'fuel', 'hp pump', 'ioc', 'bpcl', 'hpcl',
        'indian oil', 'bharat petroleum', 'reliance petro', 'filling station',
    ],
    "Self Care": [
        'gym', 'fitness', 'salon', 'spa', 'haircut', 'parlour', 'parlor',
        'doctor', 'hospital', 'clinic', 'pharmacy', 'medicine', 'chemist',
        'health', 'wellness', 'medical',
    ],
    "Recharge": [
        'recharge', 'jio', 'airtel', 'vi ', 'vodafone', 'bsnl', 'dth',
        'broadband', 'internet', 'wifi', 'tata sky', 'dish tv', 'sun direct',
    ],
    "Veggies,Gas cylinder and Dmart": [
        'vegetable', 'veggies', 'sabzi', 'grocer', 'grocery', 'dmart',
        'big bazaar', 'reliance fresh', 'more supermarket', 'gas', 'cylinder',
        'lpg', 'indane', 'hp gas', 'bharat gas', 'fruits', 'supermarket',
    ],
    "Rent,Maid & Electricity bills": [
        'rent', 'electricity', 'mseb', 'bijli', 'maid', 'bai', 'house',
        'maintenance', 'society', 'water bill', 'property tax', 'flat',
        'housing', 'accommodation', 'pg ',
    ],
    "Trips": [
        'hotel', 'resort', 'oyo', 'makemytrip', 'goibibo', 'cleartrip',
        'yatra', 'booking.com', 'airbnb', 'trip', 'tour', 'holiday',
        'vacation', 'travel package', 'tourism',
    ],
    "Travelling expense": [
        'uber', 'ola', 'rapido', 'auto', 'rickshaw', 'taxi', 'cab',
        'train', 'irctc', 'railway', 'bus', 'redbus', 'flight', 'airline',
        'indigo', 'spicejet', 'air india', 'metro', 'toll', 'parking',
    ],
    "Pune & village expense": [
        'pune', 'village', 'gaon', 'native', 'hometown',
    ],
    "Financial Support to Family": [
        'family', 'parents', 'mother', 'father', 'sister', 'brother',
        'home transfer', 'send money', 'support',
    ],
    "SIP": [
        'sip', 'mutual fund', 'zerodha', 'groww', 'coin', 'investment',
        'mf ', 'direct plan', 'nfo',
    ],
}

CREDIT_CATEGORY_KEYWORDS = {
    "Salary": [
        'salary', 'payroll', 'wages', 'ctc', 'stipend', 'employer',
        'company', 'pvt ltd', 'ltd', 'technologies', 'solutions', 'services',
        'corp', 'inc', 'llp',
    ],
    "Side Income": [
        'freelance', 'client', 'project', 'consulting', 'service charge',
        'work', 'contract',
    ],
    "Udemy Income":     ['udemy', 'course', 'instructor', 'teaching', 'online course'],
    "Youtube Earning":  ['youtube', 'google adsense', 'adsense', 'content', 'creator', 'monetization'],
}


def detect_category(text, trans_type):
    text_lower   = text.lower()
    keyword_map  = CREDIT_CATEGORY_KEYWORDS if trans_type == 'credit' else DEBIT_CATEGORY_KEYWORDS
    for category, keywords in keyword_map.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return "Salary" if trans_type == 'credit' else "Other"


# ============================================================
# TRANSACTION TYPE DETECTION
# ============================================================
def detect_transaction_type(text):
    text_lower = text.lower()
    credit_kws = [
        'salary', 'credited', 'credit', 'received', 'payment from',
        'deposited', 'income', 'bonus', 'refund', 'reimbursement',
        'money received', 'amount received', 'transferred to you',
    ]
    debit_kws = [
        'paid to', 'debited', 'debit', 'transaction successful',
        'amount paid', 'payment done', 'purchase', 'expense',
        'total', 'bill', 'amount due', 'store', 'restaurant',
        'shopping', 'petrol', 'dmart', 'grocery',
        'swiggy', 'zomato', 'amazon', 'flipkart',
        'debited from', 'sent to',
    ]
    credit_score = sum(1 for kw in credit_kws if kw in text_lower)
    debit_score  = sum(1 for kw in debit_kws  if kw in text_lower)
    return 'credit' if credit_score > debit_score else 'debit'


# ============================================================
# TESSERACT PATH AUTO-DETECT (lazy — only when OCR is used)
# ============================================================
def get_tesseract_path():
    system = platform.system()
    if system == "Windows":
        for path in [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]:
            if os.path.exists(path):
                return path
    elif system == "Darwin":
        for p in ['/usr/local/bin/tesseract', '/opt/homebrew/bin/tesseract']:
            if os.path.exists(p):
                return p
    else:
        for p in ['/usr/bin/tesseract', '/usr/local/bin/tesseract']:
            if os.path.exists(p):
                return p
        import shutil
        found = shutil.which('tesseract')
        if found:
            return found
    return None


def _init_tesseract():
    path = get_tesseract_path()
    if path:
        pytesseract.pytesseract.tesseract_cmd = path
        return path, True
    return None, False


# ============================================================
# OCR IMAGE → TEXT
# BUG FIX ✅: Added contrast enhancement before OCR for better
# accuracy on low-quality / phone camera receipt photos.
# ============================================================
@st.cache_data
def extract_text_from_image(uploaded_file):
    tess_path, ok = _init_tesseract()
    if not ok:
        st.error(
            "❌ Tesseract OCR is not installed or not found.\n\n"
            "**Install:**\n"
            "- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`\n"
            "- macOS: `brew install tesseract`\n"
            "- Windows: https://github.com/UB-Mannheim/tesseract/wiki"
        )
        return ""
    try:
        image = Image.open(uploaded_file)
        from PIL import ImageOps, ImageEnhance
        # Convert to greyscale
        image = ImageOps.grayscale(image)
        # Boost contrast — helps with faded or low-contrast receipts
        image = ImageEnhance.Contrast(image).enhance(2.0)
        # Sharpen slightly
        image = ImageEnhance.Sharpness(image).enhance(1.5)
        return pytesseract.image_to_string(image, config='--psm 6')
    except Exception as e:
        st.error(f"OCR Error: {e}")
        return ""


# ============================================================
# SMART AMOUNT PARSER
# ============================================================
def _normalize_ocr_text(text: str) -> str:
    text = re.sub(r'[\|\`]\s*', '₹', text)
    text = re.sub(r'\b[zZ]\s*(?=\d)', '₹', text)
    text = re.sub(r'€\s*(?=\d)', '₹', text)
    text = re.sub(
        r'(?<=[ \t])2([0-9]{1,3}(?:,[0-9]{2,3})+(?:\.[0-9]{1,2})?)',
        r'₹\1', text,
    )
    text = re.sub(r'\bR\s+([A-Z])', r'Rs \1', text)
    text = re.sub(r'\bR\s*s\b', 'Rs', text)
    text = re.sub(r'\bRs[\s.:]*', 'Rs.', text, flags=re.IGNORECASE)
    text = re.sub(r'\bIN\s*R\b', 'INR', text, flags=re.IGNORECASE)
    text = re.sub(r'\bINR[\s:]*', 'INR ', text, flags=re.IGNORECASE)
    text = text.replace('₹ ', '₹')
    text = re.sub(r'₹\s+', '₹', text)
    return text


def _parse_amount(raw: str):
    try:
        cleaned = raw.replace(',', '').replace(' ', '')
        val = float(cleaned)
        if 1 <= val <= 999999:
            return val
    except ValueError:
        pass
    return None


def parse_receipt_text(text):
    text = _normalize_ocr_text(text)

    def _clean_amount(raw: str):
        try:
            cleaned = raw.replace(',', '').replace(' ', '').strip()
            if not cleaned:
                return None
            val = float(cleaned)
            if 1900 <= val < 2100:   # reject years
                return None
            if 1 <= val <= 9_99_999:
                return val
        except (ValueError, AttributeError):
            pass
        return None

    def _is_id_line(line: str) -> bool:
        return bool(re.search(
            r'(transaction\s*id|txn\s*id|utr|ref(?:erence)?\s*(?:no|#|id)?'
            r'|receipt\s*no|order\s*(?:no|id)|[xX]{3,}|XX+'
            r'|account|a/c|phone|mobile)',
            line, re.IGNORECASE,
        ))

    lines         = [ln.strip() for ln in text.splitlines() if ln.strip()]
    amounts_found = []

    # Tier 1: currency-symbol anchored
    CURRENCY_RE = re.compile(
        r'(?:₹|Rs\.?|INR|[%£&#@*~^?€])\s{0,3}'
        r'([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?)',
        re.IGNORECASE,
    )
    for line in lines:
        for m in CURRENCY_RE.finditer(line):
            val = _clean_amount(m.group(1))
            if val:
                amounts_found.append(val)

    # Tier 2: keyword-anchored (only if Tier 1 empty)
    if not amounts_found:
        KW_RE = re.compile(
            r'(?:paid|debited|amount|total|bill|net\s+amount|grand\s+total'
            r'|credited|received)[:\s=₹]*'
            r'([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?)',
            re.IGNORECASE,
        )
        for line in lines:
            if _is_id_line(line):
                continue
            if re.search(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', line):
                continue
            for m in KW_RE.finditer(line):
                val = _clean_amount(m.group(1))
                if val:
                    amounts_found.append(val)

    # Tier 3: Indian comma-formatted numbers (only if Tiers 1 & 2 empty)
    if not amounts_found:
        INDIAN_NUM_RE = re.compile(
            r'(?<![0-9])([0-9]{1,3},[0-9]{2,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?)\b'
        )
        for line in lines:
            if _is_id_line(line):
                continue
            if re.search(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', line):
                continue
            for m in INDIAN_NUM_RE.finditer(line):
                val = _clean_amount(m.group(1))
                if val:
                    amounts_found.append(val)

    total = max(amounts_found) if amounts_found else 0.0

    # Date extraction
    date_found = None
    for pattern in [
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',
        r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{2,4})\b',
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            date_found = m.group(1)
            break

    # Merchant — first non-empty, non-ID, non-numeric line
    merchant = ""
    for line in lines:
        if (not re.match(r'^[\d\s,.:@₹+\-/]+$', line)
                and not _is_id_line(line)
                and not re.match(r'^(?:transaction|message|utr|ref)\b', line, re.IGNORECASE)):
            merchant = line
            break

    return {'total': total, 'date': date_found, 'merchant': merchant}


# ============================================================
# HELPER — save OCR entry to sheet + sync session state
# BUG FIX ✅: live_df is now set BEFORE update_data_to_gsheet
# so Financial Health Score and Summary pages see the new row
# instantly on the next render without needing a second rerun.
# ============================================================
def _save_ocr_entry(df, sheet, date_str, trans_type, amount, category, details):
    from utils.gsheet_utils import update_data_to_gsheet
    try:
        parsed_date = pd.to_datetime(date_str, dayfirst=True).strftime('%d-%m-%Y')
        month       = pd.to_datetime(parsed_date, dayfirst=True).strftime('%B')
    except Exception:
        parsed_date = datetime.now().strftime('%d-%m-%Y')
        month       = datetime.now().strftime('%B')

    if trans_type == 'credit':
        new_row = {
            'date': parsed_date, 'month': month,
            'credit': amount,    'credit_details': details,
            'debit':  0,         'debit_details':  'NA',
            'category': category,
        }
    else:
        new_row = {
            'date': parsed_date, 'month': month,
            'credit': 0,         'credit_details': 'NA',
            'debit': -amount,    'debit_details':  details,
            'category': category,
        }

    new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Sync live_df FIRST — guarantees all pages see the new row immediately
    st.session_state['live_df'] = new_df.copy()

    # Persist to sheet / Excel
    update_data_to_gsheet(sheet, new_df)

    # Clear OCR state
    for key in ['ocr_parsed', 'ocr_text', 'ocr_type', 'ocr_file_name']:
        st.session_state[key] = None

    label = "income" if trans_type == 'credit' else "expense"
    st.success(f"✅ ₹{amount:,.0f} {label} added under **{category}**!")
    st.balloons()


# ============================================================
# MAIN OCR PAGE
# ============================================================
def show_ocr_page(df, sheet):
    st.markdown("## 📷 Scan Receipt")

    tess_path, tess_ok = _init_tesseract()
    if not tess_ok:
        st.warning(
            "⚠️ **Tesseract OCR is not installed.** Receipt scanning requires Tesseract.\n\n"
            "**Install it:**\n"
            "- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`\n"
            "- macOS: `brew install tesseract`\n"
            "- Windows: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki)"
        )
        return
    else:
        st.sidebar.success("✅ Tesseract ready")

    # Init session state
    for key, default in [
        ('ocr_parsed', None), ('ocr_text', None),
        ('ocr_type', None),   ('ocr_file_name', None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    uploaded_file = st.file_uploader(
        "Upload a receipt image (JPG, PNG, JPEG)",
        type=["jpg", "jpeg", "png"],
    )

    # Reset state when a new file is uploaded
    if uploaded_file and uploaded_file.name != st.session_state['ocr_file_name']:
        st.session_state['ocr_file_name'] = uploaded_file.name
        st.session_state['ocr_parsed']    = None
        st.session_state['ocr_text']      = None
        st.session_state['ocr_type']      = None

    if not uploaded_file:
        return

    col1, col2 = st.columns([1, 1])

    with col1:
        st.image(uploaded_file, caption="Uploaded Receipt", use_container_width=True)

    with col2:
        if st.session_state['ocr_parsed'] is None:
            with st.spinner("🔍 Extracting text from receipt..."):
                extracted_text = extract_text_from_image(uploaded_file)

            if not extracted_text.strip():
                st.warning("⚠️ Could not extract text. Please upload a clearer image.")
                return

            detected_type = detect_transaction_type(extracted_text)
            parsed_data   = parse_receipt_text(extracted_text)
            auto_category = detect_category(extracted_text, detected_type)

            st.session_state['ocr_text']   = extracted_text
            st.session_state['ocr_type']   = detected_type
            st.session_state['ocr_parsed'] = {**parsed_data, 'auto_category': auto_category}

        parsed        = st.session_state['ocr_parsed']
        detected_type = st.session_state['ocr_type']

        with st.expander("🔎 View Extracted Text"):
            st.text(st.session_state['ocr_text'])

        with st.expander("🐛 Debug — Parsed Data"):
            st.write(f"Parsed amount:   {parsed['total']}")
            st.write(f"Parsed date:     {parsed['date']}")
            st.write(f"Parsed merchant: {parsed['merchant']}")

        badge_color = "green" if detected_type == 'credit' else "red"
        st.markdown(
            f"🤖 Detected: <span style='color:{badge_color}; font-weight:bold; font-size:15px;'>"
            f"{'💰 INCOME (Credit)' if detected_type == 'credit' else '💸 EXPENSE (Debit)'}</span>",
            unsafe_allow_html=True,
        )

        override_type = st.radio(
            "Correct type if wrong:",
            ["debit", "credit"],
            index=0 if detected_type == 'debit' else 1,
            horizontal=True,
            key="ocr_type_override",
        )

        if override_type != detected_type:
            parsed['auto_category']       = detect_category(st.session_state['ocr_text'], override_type)
            st.session_state['ocr_type']  = override_type

        try:
            default_amount = float(parsed['total'] or 0.0)
        except (ValueError, TypeError):
            default_amount = 0.0

        try:
            default_date_str = pd.to_datetime(
                parsed['date'] or datetime.now().strftime('%d-%m-%Y'), dayfirst=True
            ).strftime('%d-%m-%Y')
        except Exception:
            default_date_str = datetime.now().strftime('%d-%m-%Y')

        # BUG FIX ✅: Warn when no amount was auto-detected so user knows
        # they must fill it in manually rather than saving ₹0.
        if default_amount == 0.0:
            st.warning("⚠️ Amount not detected automatically — please enter it below.")

        st.markdown("---")
        st.markdown("### ✏️ Confirm & Edit Details")

        if override_type == 'debit':
            debit_categories = [
                "Today's expense ", "Weekend expense", "Financial Support to Family",
                "Shopping", "Petrol", "Self Care", "Recharge", "SIP",
                "Veggies,Gas cylinder and Dmart", "Rent,Maid & Electricity bills",
                "Pune & village expense", "Travelling expense", "Trips", "Other",
            ]
            auto_cat  = parsed.get('auto_category', 'Other')
            cat_index = (
                debit_categories.index(auto_cat)
                if auto_cat in debit_categories
                else len(debit_categories) - 1
            )

            merchant = st.text_input("🏪 Merchant / Store", parsed['merchant'] or "", key="ocr_merchant")
            date_val = st.text_input("📅 Date (DD-MM-YYYY)", default_date_str,   key="ocr_date_d")
            amount   = st.number_input("💰 Amount (₹)", min_value=0.0, value=default_amount,
                                       step=1.0, format="%.2f", key="ocr_amount_d")
            category = st.selectbox("📂 Category", debit_categories, index=cat_index, key="ocr_cat_d")
            notes    = st.text_input("📝 Additional Notes", "", key="ocr_notes")

            if st.button("➕ Add Expense", type="primary", use_container_width=True, key="ocr_add_debit"):
                if amount <= 0:
                    st.error("❌ Amount must be greater than 0.")
                else:
                    _save_ocr_entry(
                        df=df, sheet=sheet, date_str=date_val,
                        trans_type='debit', amount=amount, category=category,
                        details=f"{merchant} - {notes}" if notes else (merchant or 'OCR Scan'),
                    )

        else:
            credit_categories = ["Salary", "Side Income", "Udemy Income", "Youtube Earning"]
            auto_cat  = parsed.get('auto_category', 'Salary')
            cat_index = credit_categories.index(auto_cat) if auto_cat in credit_categories else 0

            source   = st.text_input("🏢 Source (Company / Person)", parsed['merchant'] or "", key="ocr_source")
            date_val = st.text_input("📅 Date (DD-MM-YYYY)", default_date_str,              key="ocr_date_c")
            amount   = st.number_input("💰 Amount (₹)", min_value=0.0, value=default_amount,
                                       step=1.0, format="%.2f", key="ocr_amount_c")
            category = st.selectbox("📂 Income Type", credit_categories, index=cat_index, key="ocr_cat_c")

            if st.button("➕ Add Income", type="primary", use_container_width=True, key="ocr_add_credit"):
                if amount <= 0:
                    st.error("❌ Amount must be greater than 0.")
                else:
                    _save_ocr_entry(
                        df=df, sheet=sheet, date_str=date_val,
                        trans_type='credit', amount=amount, category=category,
                        details=source or 'OCR Scan',
                    )
