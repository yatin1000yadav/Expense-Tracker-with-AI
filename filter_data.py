import streamlit as st
import pandas as pd

def display_filtered_data(all_data_dict):
    st.markdown("### 🔍 View Debits by Category")

    # Combine all data to get unique categories
    full_df = pd.concat(all_data_dict.values(), ignore_index=True)
    category_list = full_df[full_df['debit'] < 0]['category'].dropna().unique().tolist()
    category_list.sort()

    selected_category = st.selectbox("Select a Category:", category_list)

    st.markdown("---")

    # Loop over each year in descending order
    for sheet_name in sorted(all_data_dict.keys(), reverse=True):
        year = sheet_name.split("-")[-1]
        df = all_data_dict[sheet_name]

        # Filter only relevant category and debit entries
        filtered_df = df[(df['debit'] < 0) & (df['category'] == selected_category)].copy()
        if filtered_df.empty:
            continue

        # inside for-loop, just before sorting
        filtered_df['debit'] = filtered_df['debit'].abs()

        # 🔧 Convert 'date' column to datetime for proper sorting
        filtered_df['date'] = pd.to_datetime(filtered_df['date'], dayfirst=True, errors='coerce')

        # ✅ Now sort by proper datetime
        filtered_df = filtered_df.sort_values(by='date', ascending=True)

        # ✅ Format date for display
        filtered_df['date'] = filtered_df['date'].dt.strftime('%d-%m-%Y')
        
        st.markdown(f"#### 📅 Year: {year}")
        st.dataframe(
            filtered_df[['date', 'month', 'debit', 'debit_details']].rename(columns={
                'date': 'Date',
                'month': 'Month',
                'debit': 'Amount (₹)',
                'debit_details': 'Details'
            }),
            use_container_width=True
        )
        st.markdown("---")

def filter_data(all_data_dict):
    display_filtered_data(all_data_dict)
