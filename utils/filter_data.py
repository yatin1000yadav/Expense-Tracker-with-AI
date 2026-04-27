import streamlit as st
import pandas as pd


def display_filtered_data(all_data_dict):
    st.markdown("### 🔍 View Debits by Category")

    full_df = pd.concat(all_data_dict.values(), ignore_index=True)

    # BUG FIX ✅: Coerce debit to numeric first — OCR/Voice may store strings.
    full_df['debit'] = pd.to_numeric(full_df['debit'], errors='coerce').fillna(0)

    # BUG FIX ✅: Include BOTH negative debits (normal entry) AND positive debits
    # (OCR / Voice path). Original filter was debit < 0 which missed positive ones.
    debit_mask = full_df['debit'] != 0
    category_list = (
        full_df[debit_mask]['category']
        .dropna()
        .unique()
        .tolist()
    )
    # Exclude pure income categories from the filter list
    income_categories = ['salary', 'side income', 'udemy income', 'youtube earning']
    category_list = [
        c for c in category_list
        if c.lower() not in income_categories
    ]
    category_list.sort()

    if not category_list:
        st.info("No expense categories found.")
        return

    selected_category = st.selectbox("Select a Category:", category_list)
    st.markdown("---")

    for sheet_name in sorted(all_data_dict.keys(), reverse=True):
        year = sheet_name.split("-")[-1]
        df   = all_data_dict[sheet_name].copy()

        # BUG FIX ✅: Coerce per-sheet too
        df['debit'] = pd.to_numeric(df['debit'], errors='coerce').fillna(0)

        # BUG FIX ✅: Catch both negative AND positive debits for this category
        filtered_df = df[
            (df['debit'] != 0) & (df['category'] == selected_category)
        ].copy()

        if filtered_df.empty:
            continue

        # Normalise debit to absolute value for display
        filtered_df['debit'] = filtered_df['debit'].abs()

        # BUG FIX ✅: Drop NaT rows from bad dates before sorting so they
        # don't appear randomly at the top or bottom of the table.
        filtered_df['date'] = pd.to_datetime(
            filtered_df['date'], dayfirst=True, errors='coerce'
        )
        filtered_df = filtered_df.dropna(subset=['date'])
        filtered_df = filtered_df.sort_values(by='date', ascending=True)
        filtered_df['date'] = filtered_df['date'].dt.strftime('%d-%m-%Y')

        st.markdown(f"#### 📅 Year: {year}")
        st.dataframe(
            filtered_df[['date', 'month', 'debit', 'debit_details']].rename(columns={
                'date':         'Date',
                'month':        'Month',
                'debit':        'Amount (₹)',
                'debit_details':'Details',
            }),
            use_container_width=True,
        )
        st.markdown("---")


def filter_data(all_data_dict):
    display_filtered_data(all_data_dict)
