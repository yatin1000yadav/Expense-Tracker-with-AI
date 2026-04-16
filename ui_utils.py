import streamlit as st
import pandas as pd
from utils.data_utils import get_current_date_month, build_summary_df
from utils.gsheet_utils import update_data_to_gsheet
from utils.yearly_overview import plot_category_chart, apply_custom_style_row

# 🔁 Unified form logic
def _append_and_update(df, sheet, new_row, success_msg):
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    update_data_to_gsheet(sheet, df)
    st.toast(success_msg, icon="✅")

# ➕ Credit Entry Form
def show_credit_form(df, sheet):
    category_options = ["Salary", "Side Income", "Udemy Income","Youtube Earning" ]

    with st.form("credit_form", clear_on_submit=True):
        amount = st.number_input("Enter credited amount:", min_value=0, key="credit_amount")
        category = st.selectbox("Income Type:", category_options)
        source = st.text_input("Source description:")
        if st.form_submit_button("Add Credit Details") and amount > 0:
            date, month = get_current_date_month()
            new_row = {
                'date': date,
                'month': month,
                'credit': amount,
                'credit_details': source or 'NA',
                'debit': 0,
                'debit_details': 'NA',
                'category': category
            }
            _append_and_update(df, sheet, new_row, "Credit details added successfully!")
            

# ➖ Debit Entry Form
def show_debit_form(df, sheet):
    category_options = [
        "Today's expense ", "Weekend expense", "Financial Support to Family",
        "Shopping", "Petrol", "Self Care", "Recharge", "SIP",
        "Veggies,Gas cylinder and Dmart", "Rent,Maid & Electricity bills",
        "Pune & village expense", "Travelling expense", "Trips", "Other"
    ]

    with st.form("debit_form", clear_on_submit=True):
        amount = st.number_input("Enter debited amount:", min_value=0, key="debit_amount")
        category = st.selectbox("Expense Type:", category_options)
        note = st.text_input("Details/Source:")
        if st.form_submit_button("Add Debit Details") and amount > 0:
            date, month = get_current_date_month()
            new_row = {
                'date': date,
                'month': month,
                'credit': 0,
                'credit_details': 'NA',
                'debit': -abs(amount),
                'debit_details': note or 'NA',
                'category': category
            }
            _append_and_update(df, sheet, new_row, "Debit details added successfully!")
            

# 📊 Monthly Summary + Visuals
def show_summary(yearly_data):
    # Extract available years from the keys
    years = []
    for key in yearly_data.keys():
        year = key.split('-')[-1]
        if year.isdigit():
            years.append(int(year))
    years = sorted(years, reverse=True)

    if not years:
        st.warning("No data available.")
        return

    # Select year dropdown (default latest year)
    selected_year = st.selectbox("Select Year:", years, index=0)
    sheet_key = f"test-{selected_year}"

    if sheet_key not in yearly_data:
        st.warning("Data for the selected year is not available.")
        return

    df = yearly_data[sheet_key]
    df = build_summary_df(df)  # Now passing the correct DataFrame

    df['month'] = pd.to_datetime(df['month'], format='%B', errors='coerce')
    df = df.dropna(subset=['month']).sort_values('month', ascending=False)

    final_saving = 0
    total_by_category = {}

    for month in df['month'].dt.strftime('%B').unique():
        st.subheader(f"📅 {month}")
        month_df = df[df['month'].dt.strftime('%B') == month]

        credit = month_df.query("amount > 0")['amount'].sum()
        debit = abs(month_df.query("amount < 0")['amount'].sum())
        savings = credit - debit
        final_saving += savings

        st.markdown(f"**Total Credited:** <span style='color:green; font-size:22px'>₹{credit}</span>", unsafe_allow_html=True)
        st.markdown(f"**Total Debited:** <span style='color:red; font-size:22px'>₹{debit}</span>", unsafe_allow_html=True)
        color = 'green' if savings >= 0 else 'red'
        st.markdown(f"**Savings:** <span style='color:{color}; font-size:22px'>₹{savings}</span>", unsafe_allow_html=True)

        for cat in month_df['category'].dropna().unique():
            amt = abs(month_df[month_df['category'] == cat]['amount'].sum())
            total_by_category[cat] = total_by_category.get(cat, 0) + amt

        display_df = month_df[['date', 'amount', 'details', 'category']].sort_values('date')
        st.dataframe(display_df.style.apply(apply_custom_style_row, axis=1), use_container_width=True)
        plot_category_chart(month_df, debit)

    color = 'green' if final_saving >= 0 else 'red'
    st.markdown("<h2 style='text-align:center;'>Total Savings in this Year:</h2>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center;color:{color};'>₹{final_saving}</h1>", unsafe_allow_html=True)

    st.markdown("<h3 style='text-align:center;'>Expenses by Category:</h3>", unsafe_allow_html=True)
    exp_df = pd.DataFrame(total_by_category.items(), columns=['Category', 'Amount'])
    exclude_categories = ['salary', 'udemy income', 'side income', 'youtube earning']
    exp_df = exp_df[~exp_df['Category'].str.lower().isin(exclude_categories)]
    st.table(exp_df.sort_values('Amount', ascending=False))
