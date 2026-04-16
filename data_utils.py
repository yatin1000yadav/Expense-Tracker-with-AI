from datetime import datetime
import pandas as pd

def get_current_date_month():
    """Returns current date as (DD-MM-YYYY, MonthName)."""
    now = datetime.today()
    return now.strftime('%d-%m-%Y'), now.strftime('%B')

def filter_old_records(df, threshold=350):
    """Filter out records older than `threshold` days."""
    today = pd.to_datetime(datetime.today(), dayfirst=True)

    def is_recent(row):
        try:
            row_date = pd.to_datetime(row['date'], dayfirst=True)
            return (today - row_date).days <= threshold
        except Exception:
            return True  # Skip malformed rows

    return df[df.apply(is_recent, axis=1)].reset_index(drop=True)

def _format_transaction_df(df, type_col, details_col):
    """Formats credit or debit dataframe with consistent structure."""
    temp = df[[ 'date', 'month', type_col, details_col, 'category']].copy()
    temp.columns = ['date', 'month', 'amount', 'details', 'category']
    return temp

def build_summary_df(df):
    """Builds a unified credit/debit summary DataFrame."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "month", "amount", "details", "category"])

    credit_df = _format_transaction_df(df[df['credit'] > 0], 'credit', 'credit_details')
    debit_df = _format_transaction_df(df[df['debit'] != 0], 'debit', 'debit_details')

    summary_df = pd.concat([credit_df, debit_df], ignore_index=True)
    summary_df['amount'] = summary_df['amount'].astype(int)
    return summary_df
