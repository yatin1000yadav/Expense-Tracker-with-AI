import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

def generate_weekly_insights(df):
    st.subheader("📆 Weekly Credit vs Debit")

    # Exclude SIP and convert date
    df = df[df['category'].str.lower() != 'sip'].copy()
    df['date'] = pd.to_datetime(df['date'], dayfirst=True)

    # Filter current month
    today = datetime.today()
    df = df[(df['date'].dt.month == today.month) & (df['date'].dt.year == today.year)]

    # Week and year info
    df['week'] = df['date'].dt.isocalendar().week
    df['year'] = df['date'].dt.year

    # Helper function for week label
    def get_week_label(week):
        return f"Week {int(week)}"

    # ---- Weekly Summary Chart ----
    weekly_summary = df.groupby(['year', 'week']).agg({
        'debit': lambda x: x[x < 0].sum(),
        'credit': lambda x: x[x > 0].sum()
    }).reset_index()
    weekly_summary['debit'] = weekly_summary['debit'].abs()
    weekly_summary['savings'] = weekly_summary['credit'] - weekly_summary['debit']
    weekly_summary['week_label'] = weekly_summary['week'].apply(get_week_label)

    melted = weekly_summary.melt(id_vars='week_label', value_vars=['debit', 'credit'],
                                  var_name='Type', value_name='Amount')

    bar_chart = alt.Chart(melted).mark_bar(size=20).encode(
        y=alt.Y('week_label:N', title='Week', sort='ascending'),
        x=alt.X('Amount:Q', title='Amount (₹)'),
        color=alt.Color('Type:N', title='Type', scale=alt.Scale(scheme='category10')),
        tooltip=['week_label', 'Type', alt.Tooltip('Amount:Q', format='.0f')]
    ).properties(height=220)
    st.altair_chart(bar_chart, use_container_width=True)
    st.dataframe(
        weekly_summary[['week_label', 'credit', 'debit', 'savings']].rename(columns={
            'week_label': 'Week', 'credit': 'Credit (₹)', 'debit': 'Debit (₹)', 'savings': 'Savings (₹)'
        }).style.format({
            'Credit (₹)': '₹{:.0f}', 'Debit (₹)': '₹{:.0f}', 'Savings (₹)': '₹{:.0f}'
        }),
        use_container_width=True
    )
    st.markdown("---")

    # ---- Average Daily Spend per Week ----
    st.markdown("## 📈 Average Daily Spend per Week")
    debit_df = df[df['debit'] < 0].copy()
    debit_df['debit'] = debit_df['debit'].abs()

    avg_spend = debit_df.groupby(['year', 'week'])['debit'].sum().reset_index()
    avg_spend['avg_daily_spend'] = avg_spend['debit'] / 7
    avg_spend['week_label'] = avg_spend['week'].apply(get_week_label)

    line_chart = alt.Chart(avg_spend).mark_line(point=True).encode(
        x=alt.X('week_label:N', title='Week'),
        y=alt.Y('avg_daily_spend:Q', title='Avg Daily Spend (₹)'),
        tooltip=[alt.Tooltip('week_label:N', title='Week'),
                 alt.Tooltip('avg_daily_spend:Q', title='₹', format='.0f')]
    )

    st.altair_chart(line_chart, use_container_width=True)
    st.dataframe(
        avg_spend[['week_label', 'avg_daily_spend']].rename(columns={
            'week_label': 'Week', 'avg_daily_spend': 'Avg Daily Spend (₹)'
        }).style.format({'Avg Daily Spend (₹)': '₹{:.0f}'}),
        use_container_width=True
    )
    st.markdown("---")

    # ---- Most Spent Day & Top Category ----
    st.markdown("## 💰 Most Spent Day per Week & Top Category")
    debit_df['date_only'] = debit_df['date'].dt.date

    daily_total = debit_df.groupby(['year', 'week', 'date_only'])['debit'].sum().reset_index()
    most_spent = daily_total.sort_values(['year', 'week', 'debit'], ascending=[True, True, False])
    most_spent = most_spent.groupby(['year', 'week']).first().reset_index()

    top_cat = debit_df.groupby(['year', 'week', 'date_only', 'category'])['debit'].sum().reset_index()
    top_cat = top_cat.sort_values(['year', 'week', 'date_only', 'debit'], ascending=[True, True, True, False])
    top_cat = top_cat.groupby(['year', 'week', 'date_only']).first().reset_index()

    final = pd.merge(most_spent, top_cat, on=['year', 'week', 'date_only'], how='left')
    final['week_label'] = final['week'].apply(get_week_label)

    display_df = final[['week_label', 'date_only', 'debit_x', 'category']].rename(columns={
        'week_label': 'Week', 'date_only': 'Most Spent Day', 'debit_x': 'Total Spent (₹)', 'category': 'Top Category'
    })

    bar_chart = alt.Chart(display_df).mark_bar().encode(
        y=alt.Y('Week:N'),
        x=alt.X('Total Spent (₹):Q'),
        color=alt.Color('Top Category:N'),
        tooltip=[
            alt.Tooltip('Week:N'),
            alt.Tooltip('Most Spent Day:T', title='Date', format='%d %b %Y'),
            alt.Tooltip('Total Spent (₹):Q', format='.0f'),
            alt.Tooltip('Top Category:N')
        ]
    )

    st.altair_chart(bar_chart, use_container_width=True)

    st.dataframe(
        display_df.style.format({
            'Total Spent (₹)': '₹{:.0f}',
            'Most Spent Day': lambda d: pd.to_datetime(d).strftime('%d %b %Y')
        }),
        use_container_width=True
    )
