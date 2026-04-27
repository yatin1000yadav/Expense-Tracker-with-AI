import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

def plot_category_chart(df, total_debit):
    exclude_categories = ['credit', 'sip', 'salary', 'udemy income', 'side income', 'youtube earning']
    chart_data = (
        df.copy()
        .assign(amount=lambda d: d['amount'].abs())
        .loc[~df['category'].str.lower().isin(exclude_categories)]
        .groupby('category', as_index=False)['amount'].sum()
        .sort_values('amount')
    )
    chart_data['percentage'] = (chart_data['amount'] / chart_data['amount'].sum()) * 100

    fig, ax = plt.subplots()
    bars = ax.barh(chart_data['category'], chart_data['amount'], color=plt.cm.Paired(np.arange(len(chart_data))))

    for bar, val, perc in zip(bars, chart_data['amount'], chart_data['percentage']):
        x_pos = bar.get_width() + 1 if val < 0.25 * total_debit else bar.get_width() - 5
        color = 'white' if val >= 0.25 * total_debit else 'black'
        ha = 'left' if val < 0.25 * total_debit else 'right'
        ax.text(x_pos, bar.get_y() + bar.get_height() / 2, f'{val:.0f} ({perc:.1f}%)', va='center', ha=ha, color=color)

    ax.set_title('Total Debit by Category')
    st.pyplot(fig)

def apply_custom_style_row(row):
    return [f"color: {'green' if row['amount'] >= 0 else 'red'}"] * len(row)

def show_savings_line_chart(summary_df):
    st.subheader("📈 Yearly Savings (Line Chart)")

    chart = alt.Chart(summary_df).mark_line(point=True).encode(
        y=alt.Y("Year:O", sort="ascending", title="Year"),
        x=alt.X("Savings:Q", title="Savings (₹)"),
        tooltip=["Year", "Savings"],
        color=alt.condition("datum.Savings >= 0", alt.value("green"), alt.value("red"))
    ).properties(height=300)

    st.altair_chart(chart, use_container_width=True)

def show_credit_vs_debit(summary_df):
    st.subheader("📊 Credit vs Spend")

    melted_df = summary_df.melt(
        id_vars="Year", value_vars=["Credit", "Spend"],
        var_name="Type", value_name="Amount"
    )
    melted_df["Total"] = melted_df.groupby("Year")["Amount"].transform("sum")
    melted_df["Percentage"] = (melted_df["Amount"] / melted_df["Total"]) * 100
    melted_df["Label"] = melted_df.apply(lambda row: f"{row['Type']} ({row['Percentage']:.0f}%)", axis=1)
    melted_df.sort_values(["Year", "Type"], inplace=True)
    melted_df["Normalized"] = melted_df["Percentage"] / 100
    melted_df["Cumulative"] = melted_df.groupby("Year")["Normalized"].cumsum()
    melted_df["Start"] = melted_df["Cumulative"] - melted_df["Normalized"]
    melted_df["Midpoint"] = melted_df["Start"] + melted_df["Normalized"] / 2

    bar = alt.Chart(melted_df).mark_bar().encode(
        y=alt.Y("Year:O", sort="ascending"),
        x=alt.X("Percentage:Q", stack="normalize", title=None, axis=None),
        color=alt.Color("Type:N", scale=alt.Scale(scheme="category10")),
        tooltip=["Year", "Type", alt.Tooltip("Amount:Q", format=",.0f"), alt.Tooltip("Percentage:Q", format=".1f")]
    ).properties(height=100)

    text = alt.Chart(melted_df).mark_text(
        align='center', baseline='middle', fontSize=12,
        color='black', fontWeight=700
    ).encode(
        y=alt.Y("Year:O", sort="ascending"),
        x=alt.X("Midpoint:Q"),
        text=alt.Text("Label:N")
    )

    st.altair_chart(bar + text, use_container_width=True)

def show_all_category_data(yearly_data_dict):
    all_data = pd.concat(yearly_data_dict.values(), ignore_index=True)
    all_data['category'] = all_data['category'].astype(str).str.lower()

    spend_data = all_data.query("category != 'credit' and category != 'other'").copy()
    spend_data['amount'] = spend_data['debit'].abs()
    total_debit = spend_data['amount'].sum()

    category_summary = (
        spend_data.groupby('category')['debit']
        .sum().abs().sort_values(ascending=False)
        .reset_index()
        .rename(columns={'category': 'Category', 'debit': 'Total Spend (₹)'})
    )

    st.markdown("### 🧾 Total Spend by Category (All Time)")
    plot_category_chart(spend_data, total_debit)
    st.dataframe(category_summary, use_container_width=True)

def show_yearly_credit_spends(summary_df):
    def color_savings(val):
        return f"color: {'green' if val >= 0 else 'red'}"

    styled_df = summary_df.style.map(color_savings, subset=["Savings"])
    st.subheader("📋 Yearly Summary Table")
    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    total_savings = summary_df["Savings"].sum()
    savings_color = "green" if total_savings >= 0 else "red"

    st.markdown("---")
    st.markdown(
        f"<h3>🟢 Total Savings Over All Years:</b>"
        f"<span style='color:{savings_color};'> ₹{total_savings:,.2f}</span></h3>",
        unsafe_allow_html=True
    )
    st.markdown("---")

def show_yearly_overview(yearly_data_dict):
    if not yearly_data_dict:
        st.info("No yearly data available.")
        return

    summary = [
        {
            "Year": int(sheet.split('-')[-1]),
            "Credit": df['credit'].sum(),
            "Spend": abs(df['debit'].sum()),
            "Savings": df['credit'].sum() - abs(df['debit'].sum())
        }
        for sheet, df in yearly_data_dict.items()
    ]

    summary_df = pd.DataFrame(summary).sort_values(by="Year")

    show_credit_vs_debit(summary_df)
    show_savings_line_chart(summary_df)
    show_yearly_credit_spends(summary_df)
    show_all_category_data(yearly_data_dict)
