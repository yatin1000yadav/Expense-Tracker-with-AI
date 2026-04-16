import streamlit as st
import pandas as pd
import altair as alt


# ------------------ DATA PREP ------------------

def prepare_data(data):
    data = data[data['category'].str.lower() != 'sip'].copy()

    data['date'] = pd.to_datetime(data['date'], dayfirst=True, errors='coerce')
    data['display_date'] = data['date'].dt.date

    # IMPORTANT: Keep month_year strictly as Period[M]
    data['month_year'] = data['date'].dt.to_period('M')

    return data


# ------------------ MONTHLY SUMMARY ------------------

def get_monthly_summary(data):
    summary = (
        data.groupby('month_year')
        .agg(
            debit=('debit', lambda x: x[x < 0].sum()),
            credit=('credit', lambda x: x[x > 0].sum())
        )
        .reset_index()
    )

    summary['debit'] = summary['debit'].abs()
    summary['savings'] = summary['credit'] - summary['debit']

    summary['Spend change(%)'] = summary['debit'].pct_change().fillna(0) * 100
    summary['Income change(%)'] = summary['credit'].pct_change().fillna(0) * 100
    summary['Savings change(%)'] = summary['savings'].pct_change().fillna(0) * 100

    summary['month'] = summary['month_year'].astype(str)

    return summary


# ------------------ CHARTS ------------------

def plot_bar_chart(df):
    melted = df.melt(
        id_vars='month',
        value_vars=['debit', 'credit'],
        var_name='Type',
        value_name='Amount'
    )

    return alt.Chart(melted).mark_bar().encode(
        x='month:O',
        y='Amount:Q',
        color='Type:N',
        tooltip=['month', 'Type', 'Amount']
    )


def plot_line_chart(df, y_col, color='steelblue'):
    return alt.Chart(df).mark_line(point=True, color=color).encode(
        x='month:O',
        y=f'{y_col}:Q',
        tooltip=['month', y_col]
    )


# ------------------ MAX EXPENSE ------------------

def get_max_expenses(data):
    return (
        data[data['debit'] < 0]
        .copy()
        .assign(abs_debit=lambda df: df['debit'].abs())
        .sort_values(['month_year', 'abs_debit'], ascending=[True, False])
        .groupby('month_year', as_index=False)
        .first()
        [['month_year', 'display_date', 'category', 'debit', 'debit_details']]
        .assign(debit=lambda df: df['debit'].abs())
    )


# ------------------ ✅ FIXED AVG DAILY SPEND ------------------

def get_avg_daily_spend(data):
    monthly = (
        data[data['debit'] < 0]
        .groupby('month_year', as_index=False)
        .agg(total_debit=('debit', lambda x: x.sum()))
    )

    monthly['total_debit'] = monthly['total_debit'].abs()

    # ✅ CRITICAL FIX:
    # Convert Period[M] → number of days (INT)
    monthly['days_in_month'] = monthly['month_year'].dt.days_in_month

    # ✅ Safe numeric division (NO PeriodArray involved)
    monthly['avg_daily_spend'] = (
        monthly['total_debit'] / monthly['days_in_month']
    )

    monthly['month'] = monthly['month_year'].astype(str)

    return monthly


# ------------------ MAIN INSIGHTS ------------------

def generate_monthly_insights(data):
    st.markdown("## ⚖️ Monthly Spending vs Income")

    data = prepare_data(data)
    summary = get_monthly_summary(data)

    st.altair_chart(plot_bar_chart(summary), use_container_width=True)

    st.dataframe(
        summary.style.format({
            'debit': '₹{:.0f}',
            'credit': '₹{:.0f}',
            'savings': '₹{:.0f}',
            'Spend change(%)': '{:.1f}%',
            'Income change(%)': '{:.1f}%',
            'Savings change(%)': '{:.1f}%'
        }),
        use_container_width=True
    )

    st.markdown("## 🐖 Monthly Savings Trend")
    st.altair_chart(
        plot_line_chart(summary, 'savings'),
        use_container_width=True
    )

    st.markdown("## 💸 Biggest Expense per Month")
    max_txn = get_max_expenses(data)

    st.dataframe(
        max_txn.rename(columns={
            'month_year': 'Month',
            'display_date': 'Date',
            'category': 'Category',
            'debit': 'Amount',
            'debit_details': 'Details'
        }).style.format({'Amount': '₹{:.0f}'}),
        use_container_width=True
    )

    st.markdown("## 📊 Average Daily Spend per Month")
    avg_spend = get_avg_daily_spend(data)

    st.altair_chart(
        plot_line_chart(avg_spend, 'avg_daily_spend', color='orange'),
        use_container_width=True
    )

    st.dataframe(
        avg_spend[['month_year', 'avg_daily_spend']]
        .rename(columns={
            'month_year': 'Month',
            'avg_daily_spend': 'Average Daily Spend'
        })
        .style.format({'Average Daily Spend': '₹{:.0f}'}),
        use_container_width=True
    )
