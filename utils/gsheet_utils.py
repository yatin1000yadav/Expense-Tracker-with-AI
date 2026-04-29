from datetime import datetime
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import streamlit as st

# 🌐 Constants
GSHEET_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
CREDENTIALS_PATH = "config/your-service-account.json"
SPREADSHEET_NAME = "birthday"
SAMPLE_DATA_PATH = "sample_data/expense_dummy_data.xlsx"


class MockSheet:
    def __init__(self, df, title=None):
        self.df = df
        self.title = title or f"test-{datetime.now().year}"

    def get_all_records(self):
        return self.df.to_dict(orient='records')

    def clear(self):
        pass

    def update(self, range_name, data):
        """Save updated data both in-memory and to Excel file."""
        try:
            if len(data) > 0:
                headers = data[0]
                values  = data[1:]
                self.df = pd.DataFrame(values, columns=headers)

                # ✅ FIX: create sample_data directory if it doesn't exist
                os.makedirs(os.path.dirname(SAMPLE_DATA_PATH), exist_ok=True)
                self.df.to_excel(SAMPLE_DATA_PATH, index=False)

                # ✅ FIX: also keep session_state in sync so Summary page is live
                st.session_state['live_df'] = self.df.copy()
                st.toast("💾 Data saved to local Excel file", icon="💾")
        except Exception as e:
            st.error(f"Failed to save local data: {e}")

    def append_row(self, row):
        pass


class MockSpreadsheet:
    def __init__(self, df):
        self.sheet = MockSheet(df)

    def worksheet(self, title):
        return self.sheet

    def worksheets(self):
        return [self.sheet]

    def add_worksheet(self, title, rows, cols):
        return self.sheet

    def open(self, name):
        return self


import json

# ✅ Authentication & client initialization
def get_gspread_client():
    # Priority: Read from Render Environment Variable securely
    if "GOOGLE_CREDENTIALS_JSON" in os.environ:
        try:
            creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, GSHEET_SCOPE)
            return gspread.authorize(creds)
        except Exception as e:
            st.error(f"Error parsing GOOGLE_CREDENTIALS_JSON: {e}")
            raise e
    
    # Fallback: Read from local JSON file
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, GSHEET_SCOPE)
    return gspread.authorize(creds)


# 🧾 Check if current year sheet exists
def is_new_year_sheet_needed(spreadsheet):
    current_year = datetime.now().year
    return f"test-{current_year}" not in [s.title for s in spreadsheet.worksheets()]


# 🆕 Create sheet for new year with header
def create_new_year_sheet(spreadsheet, sheet_title):
    sheet = spreadsheet.add_worksheet(title=sheet_title, rows="1000", cols="26")
    sheet.append_row(["date", "month", "credit", "credit_details", "debit", "debit_details", "category"])
    return sheet


# 📥 Load current year's data
def load_data_from_gsheet():
    # ✅ FIX: If an entry was just added (OCR/Voice), use the live df from session_state
    #         instead of re-reading the Excel file (which may not have flushed yet)
    if "live_df" in st.session_state and st.session_state["live_df"] is not None:
        df = st.session_state["live_df"].copy()
        spreadsheet = MockSpreadsheet(df)
        return df, spreadsheet.sheet, spreadsheet

    # If credentials missing → use sample data (offline mode)
    if not os.path.exists(CREDENTIALS_PATH) and "GOOGLE_CREDENTIALS_JSON" not in os.environ:
        if "sample_data_loaded" not in st.session_state:
            st.toast("⚠️ Using Local Sample Data (Offline Mode)", icon="📂")
            st.session_state["sample_data_loaded"] = True

        if os.path.exists(SAMPLE_DATA_PATH):
            try:
                df = pd.read_excel(SAMPLE_DATA_PATH)
                df = df.fillna("")
                expected_cols = ["date", "month", "credit", "credit_details",
                                 "debit", "debit_details", "category"]
                for col in expected_cols:
                    if col not in df.columns:
                        df[col] = ""
                spreadsheet = MockSpreadsheet(df)
                worksheet   = spreadsheet.sheet
                return df, worksheet, spreadsheet
            except Exception as e:
                st.error(f"❌ Error loading sample data: {e}")
                return pd.DataFrame(columns=["date", "month", "credit", "credit_details", "debit", "debit_details", "category"]), None, None
        else:
            st.warning("⚠️ No database connected. Using temporary empty storage.")
            empty_df = pd.DataFrame(columns=["date", "month", "credit", "credit_details", "debit", "debit_details", "category"])
            spreadsheet = MockSpreadsheet(empty_df)
            return empty_df, spreadsheet.sheet, spreadsheet

    try:
        client       = get_gspread_client()
        spreadsheet  = client.open(SPREADSHEET_NAME)
        sheet_title  = f"test-{datetime.now().year}"

        if is_new_year_sheet_needed(spreadsheet):
            worksheet = create_new_year_sheet(spreadsheet, sheet_title)
        else:
            worksheet = spreadsheet.worksheet(sheet_title)

        df = pd.DataFrame(worksheet.get_all_records())
        return df, worksheet, spreadsheet
    except Exception as e:
        st.error(f"Connection Error: {e}. Switching to offline mode.")
        if os.path.exists(SAMPLE_DATA_PATH):
            df          = pd.read_excel(SAMPLE_DATA_PATH).fillna("")
            spreadsheet = MockSpreadsheet(df)
            return df, spreadsheet.sheet, spreadsheet
        return pd.DataFrame(), None, None


# 🔄 Push updated DataFrame to Google Sheet / MockSheet
def update_data_to_gsheet(sheet, df):
    sheet.clear()
    data = [df.columns.tolist()] + df.values.tolist()
    sheet.update('A1', data)


# 📊 Load all yearly data from "test-" sheets
def load_yearly_data(spreadsheet):
    yearly_data = {}

    if isinstance(spreadsheet, MockSpreadsheet):
        # ✅ FIX: always prefer live_df from session_state so OCR/Voice entries
        #         are reflected immediately in AI Insights (and all other views).
        #         spreadsheet.sheet.df may be stale if MockSheet.update() wrote
        #         to live_df but a new MockSpreadsheet was constructed from the
        #         old df reference.
        if "live_df" in st.session_state and st.session_state["live_df"] is not None:
            df = st.session_state["live_df"].copy()
        else:
            df = spreadsheet.sheet.df.copy()
        # Also sync the sheet's internal df so downstream callers stay consistent
        spreadsheet.sheet.df = df
        df['credit'] = pd.to_numeric(df['credit'] if 'credit' in df.columns else 0, errors='coerce').fillna(0)
        df['debit']  = pd.to_numeric(df['debit']  if 'debit'  in df.columns else 0, errors='coerce').fillna(0)
        if 'year' not in df.columns:
            df['year'] = str(datetime.now().year)
        yearly_data[spreadsheet.sheet.title] = df
        return yearly_data

    for sheet in spreadsheet.worksheets():
        if sheet.title.lower().startswith("test-"):
            df = pd.DataFrame(sheet.get_all_records())
            if not df.empty:
                df['year']   = sheet.title.split('-')[-1]
                df['credit'] = pd.to_numeric(df['credit'] if 'credit' in df.columns else 0, errors='coerce').fillna(0)
                df['debit']  = pd.to_numeric(df['debit']  if 'debit'  in df.columns else 0, errors='coerce').fillna(0)
                yearly_data[sheet.title] = df
    return yearly_data
