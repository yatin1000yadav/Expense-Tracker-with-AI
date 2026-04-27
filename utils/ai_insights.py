import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def generate_storytelling(df):
    st.markdown("## 🔮 Predictive Spending Analytics")

    if df.empty:
        st.info("No data available for insights.")
        return

    df = df.copy()
    df['credit'] = pd.to_numeric(df['credit'], errors='coerce').fillna(0)
    df['debit']  = pd.to_numeric(df['debit'],  errors='coerce').fillna(0)

    fixed_categories = ['sip', 'rent,maid & electricity bills', 'financial support to family']
    expense_df = df[~df['category'].str.lower().isin([cat.lower() for cat in fixed_categories])]

    if expense_df.empty:
        st.info("No discretionary expenses to analyze.")
        return

    category_totals = expense_df.groupby('category')['debit'].sum().abs()
    total_discretionary = category_totals.sum()
    category_percentages = (category_totals / total_discretionary * 100).round(1)

    st.markdown("---")

    st.markdown("### 🧠 Spending Personality")
    daily_pct   = category_percentages.get("Today's expense ", 0)
    weekend_pct = category_percentages.get('Weekend expense', 0)
    shopping_pct = category_percentages.get('Shopping', 0)
    trips_pct = (category_percentages.get('Trips', 0)
                 + category_percentages.get('Travelling expense', 0))
    spontaneous_pct = daily_pct + weekend_pct
    planned_pct     = shopping_pct + trips_pct

    if spontaneous_pct > 50:
        st.markdown(f"• **Spontaneous Spender** ({spontaneous_pct:.1f}%): You prefer in-the-moment purchases over planned spending")
    elif planned_pct > 40:
        st.markdown(f"• **Strategic Planner** ({planned_pct:.1f}%): You favor planned purchases and experiences")
    else:
        st.markdown(f"• **Balanced Decision Maker**: {spontaneous_pct:.1f}% spontaneous vs {planned_pct:.1f}% planned spending")

    st.markdown("### 🏠 Lifestyle Profile")
    if len(category_percentages) > 0:
        top_category  = category_percentages.idxmax()
        top_percentage = category_percentages.max()
        lifestyle_profiles = {
            "Today's expense ": f"**Daily Comfort Seeker** ({top_percentage:.1f}%): Your largest expense is daily pleasures and immediate needs",
            "Weekend expense":  f"**Weekend Warrior** ({top_percentage:.1f}%): You invest most in weekend entertainment and relaxation",
            "Shopping":         f"**Thoughtful Shopper** ({top_percentage:.1f}%): Deliberate shopping dominates your discretionary spending",
            "Petrol":           f"**Mobile Lifestyle** ({top_percentage:.1f}%): Transportation is your biggest discretionary expense",
            "Self Care":        f"**Wellness Focused** ({top_percentage:.1f}%): You prioritize health and self-care investments",
            "Veggies,Gas cylinder and Dmart": f"**Home Manager** ({top_percentage:.1f}%): Household essentials are your primary focus",
            "Trips":            f"**Experience Collector** ({top_percentage:.1f}%): Travel and experiences are your main investment",
            "Travelling expense": f"**Journey Enthusiast** ({top_percentage:.1f}%): Transportation and travel logistics are your priority",
            "Pune & village expense": f"**Family Explorer** ({top_percentage:.1f}%): You balance leisure activities with family time across cities",
        }
        if top_category in lifestyle_profiles:
            st.markdown(f"• {lifestyle_profiles[top_category]}")

    st.markdown("### ⚖️ Spending Balance")
    essential_categories = ['Veggies,Gas cylinder and Dmart', 'Petrol', 'Recharge']
    lifestyle_categories = ['Shopping', 'Self Care', 'Trips', 'Weekend expense',
                            'Travelling expense', 'Pune & village expense']
    essential_pct = sum(category_percentages.get(cat, 0) for cat in essential_categories)
    lifestyle_pct = sum(category_percentages.get(cat, 0) for cat in lifestyle_categories)

    if essential_pct > lifestyle_pct:
        st.markdown(f"• **Practical Prioritizer**: {essential_pct:.1f}% essentials vs {lifestyle_pct:.1f}% lifestyle")
    elif lifestyle_pct > essential_pct * 1.5:
        st.markdown(f"• **Lifestyle Investor**: {lifestyle_pct:.1f}% lifestyle vs {essential_pct:.1f}% essentials")
    else:
        st.markdown(f"• **Balanced Living**: {essential_pct:.1f}% essentials vs {lifestyle_pct:.1f}% lifestyle")

    st.markdown("### 📊 Financial Behavior")
    avg_transaction  = abs(expense_df['debit'].mean())
    transaction_count = len(expense_df)
    if avg_transaction < 200 and transaction_count > 20:
        st.markdown(f"• **Frequent Small Spender**: {transaction_count} transactions averaging ₹{avg_transaction:.0f}")
    elif avg_transaction > 1000 and transaction_count < 15:
        st.markdown(f"• **Bulk Decision Maker**: {transaction_count} transactions averaging ₹{avg_transaction:.0f}")
    else:
        st.markdown(f"• **Moderate Spender**: {transaction_count} transactions averaging ₹{avg_transaction:.0f}")

    st.markdown("### 🎯 Smart Focus")
    if len(category_percentages) > 0:
        top_category  = category_percentages.idxmax()
        top_percentage = category_percentages.max()
        if top_percentage > 40:
            st.markdown(f"• **High Concentration Alert**: {top_percentage:.1f}% of spending is in '{top_category}'")
        elif top_percentage < 15:
            st.markdown(f"• **Well-Distributed Spending**: Largest category '{top_category}' is only {top_percentage:.1f}%")
        else:
            st.markdown(f"• **Optimization Opportunity**: Focus on '{top_category}' ({top_percentage:.1f}%) for maximum savings impact")

    st.markdown("---")


def generate_financial_health_score(df):
    st.markdown("## 💯 Financial Health Score")

    if df.empty:
        st.info("No data available for score calculation.")
        return

    # ── Ensure numeric types (OCR / Voice may send strings) ──────────────────
    df = df.copy()
    df['credit'] = pd.to_numeric(df['credit'], errors='coerce').fillna(0)
    df['debit']  = pd.to_numeric(df['debit'],  errors='coerce').fillna(0)

    # ── Income & expenses ─────────────────────────────────────────────────────
    total_income   = df[df['credit'] > 0]['credit'].sum()
    # BUG FIX ✅: debit column stores NEGATIVE values for expenses.
    # The original code did abs(df[df['debit'] < 0]['debit'].sum()) which is correct,
    # but if any rows have debit stored as positive (e.g. from voice/OCR),
    # they were ignored. We now handle BOTH signs defensively.
    debit_col      = df['debit']
    total_expenses = (
        abs(debit_col[debit_col < 0].sum())   # stored as negative  (normal path)
        + debit_col[debit_col > 0].sum()       # stored as positive  (OCR/voice path)
    )

    if total_income <= 0:
        st.warning("No income data found. Cannot calculate financial health score.")
        return

    # ── Savings rate ──────────────────────────────────────────────────────────
    net_savings  = total_income - total_expenses
    savings_rate = (net_savings / total_income) * 100   # can be negative if overspent

    # ── Base score  (capped 0-100) ────────────────────────────────────────────
    # 50% savings rate → 100 score; 0% → 0; negative → still 0
    base_score = max(0.0, min(100.0, savings_rate * 2))

    # ── Fixed / discretionary split ───────────────────────────────────────────
    fixed_categories = ['sip', 'rent,maid & electricity bills', 'financial support to family']
    fixed_mask = df['category'].str.lower().isin(fixed_categories)

    fixed_debit        = df.loc[fixed_mask, 'debit']
    fixed_expenses     = (
        abs(fixed_debit[fixed_debit < 0].sum())
        + fixed_debit[fixed_debit > 0].sum()
    )
    discretionary_expenses = max(0.0, total_expenses - fixed_expenses)

    # ── Adjustments ───────────────────────────────────────────────────────────
    adjustments = 0.0

    sip_mask  = df['category'].str.lower() == 'sip'
    sip_debit = df.loc[sip_mask, 'debit']
    sip_amount = (
        abs(sip_debit[sip_debit < 0].sum())
        + sip_debit[sip_debit > 0].sum()
    )
    if sip_amount > 0:
        sip_ratio   = (sip_amount / total_income) * 100
        adjustments += min(15.0, sip_ratio * 1.5)

    discretionary_ratio = (discretionary_expenses / total_income) * 100
    if discretionary_ratio > 60:
        adjustments -= 10.0
    elif discretionary_ratio < 30:
        adjustments += 10.0

    final_score = max(0.0, min(100.0, base_score + adjustments))

    # ── BUG FIX ✅: Gauge needle ──────────────────────────────────────────────
    # Previously the gauge bar color was "darkblue" which COVERED the coloured
    # arc and made the needle appear to point at the wrong place visually.
    # Fix: set bar color to a very thin transparent-looking indicator and rely
    # on the step colours + threshold line to communicate the score.
    # Also: delta reference changed to 50 (previous score baseline) so the
    # green ▲ / red ▼ arrow makes intuitive sense.
    fig = go.Figure(go.Indicator(
        mode   = "gauge+number+delta",
        value  = round(final_score, 1),
        domain = {'x': [0, 1], 'y': [0, 1]},
        title  = {
            'text': "Financial Health Score",
            'font': {'size': 22, 'color': 'darkblue'}
        },
        delta  = {
            'reference':  50,                          # compare against mid-point
            'increasing': {'color': '#2ecc71'},
            'decreasing': {'color': '#e74c3c'},
            'valueformat': '.1f',
        },
        number = {
            'font': {'size': 60, 'color': 'darkblue'},
            'valueformat': '.0f',
        },
        gauge  = {
            'axis': {
                'range':     [0, 100],
                'tickwidth': 1,
                'tickcolor': 'darkblue',
                'tickvals':  [0, 20, 40, 60, 75, 85, 100],
            },
            # BUG FIX ✅: Use a narrow, semi-transparent bar so the coloured
            # steps remain visible and the needle position is unambiguous.
            'bar': {
                'color':     'rgba(0,0,139,0.85)',   # semi-transparent dark-blue
                'thickness': 0.15,                   # thin needle-like bar
            },
            'bgcolor':     'white',
            'borderwidth': 2,
            'bordercolor': 'gray',
            'steps': [
                {'range': [0,  40],  'color': '#ff6b6b'},   # Red   – Poor
                {'range': [40, 60],  'color': '#ffa726'},   # Orange– Fair
                {'range': [60, 75],  'color': '#ffeb3b'},   # Yellow– Good
                {'range': [75, 85],  'color': '#66bb6a'},   # Lt Green – Very Good
                {'range': [85, 100], 'color': '#4caf50'},   # Green – Excellent
            ],
            # Threshold line at 90 (shows where "excellent" truly begins)
            'threshold': {
                'line':      {'color': 'red', 'width': 3},
                'thickness': 0.75,
                'value':     90,
            },
        },
    ))

    fig.update_layout(
        height         = 420,
        margin         = dict(t=80, b=20, l=20, r=20),
        font           = {'color': 'darkblue', 'family': 'Arial'},
        paper_bgcolor  = 'white',
        plot_bgcolor   = 'white',
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── Score breakdown metrics ───────────────────────────────────────────────
    st.markdown("### 📊 Score Breakdown")
    col1, col2, col3 = st.columns(3)
    sip_ratio_display = (sip_amount / total_income * 100) if total_income > 0 else 0.0

    with col1:
        color = "normal" if net_savings >= 0 else "inverse"
        st.metric(
            label="💰 Savings Rate",
            value=f"{savings_rate:.1f}%",
            delta=f"₹{net_savings:,.0f} saved" if net_savings >= 0 else f"₹{abs(net_savings):,.0f} deficit",
            delta_color=color,
        )
    with col2:
        st.metric(
            label="📈 Investment Rate",
            value=f"{sip_ratio_display:.1f}%",
            delta=f"₹{sip_amount:,.0f} in SIP" if sip_amount > 0 else "No SIP yet",
        )
    with col3:
        st.metric(
            label="🎯 Lifestyle Spending",
            value=f"{discretionary_ratio:.1f}%",
            delta=f"₹{discretionary_expenses:,.0f}",
        )

    # ── Profile & next steps ──────────────────────────────────────────────────
    st.markdown("### 🎯 Your Financial Profile & Next Steps")

    if final_score >= 85:
        st.success("**🌟 Financial Champion** – Excellent money management! Your disciplined approach puts you in the top tier.")
        st.markdown("• **Next Steps**: Explore advanced investments (index funds, NPS) and automate transfers to maximise growth.")
    elif final_score >= 75:
        st.success("**💪 Financial Achiever** – Very good financial health with a positive savings rate!")
        st.markdown(f"• **Next Steps**: {'Increase SIP investments' if sip_ratio_display < 15 else 'Optimise with tax-saving instruments (ELSS, PPF)'} to reach champion level.")
    elif final_score >= 60:
        st.warning("**⚖️ Financial Balancer** – Good foundation, room for improvement.")
        st.markdown("• **Next Steps**: Reduce discretionary spending by 5–10 % and boost SIP by ₹1,000–2,000 monthly.")
    elif final_score >= 40:
        st.warning("**⚠️ Financial Attention Needed** – Time to refocus priorities.")
        st.markdown("• **Next Steps**: Build an emergency fund first, then follow the 50/30/20 rule (50 % needs, 30 % wants, 20 % savings).")
    else:
        st.error("**🚨 Financial Emergency** – Immediate action required.")
        st.markdown("• You are spending more than you earn – this is unsustainable.")
        st.markdown("• Focus on essential expenses only and eliminate all unnecessary spending.")
        st.markdown("• **Next Steps**: Expense audit + income boost through side income or skill development.")

    # Show score details in expander for transparency
    with st.expander("🔍 Score Calculation Details"):
        st.write(f"**Total Income:** ₹{total_income:,.0f}")
        st.write(f"**Total Expenses:** ₹{total_expenses:,.0f}")
        st.write(f"**Net Savings:** ₹{net_savings:,.0f}")
        st.write(f"**Savings Rate:** {savings_rate:.1f}%")
        st.write(f"**Base Score** (savings rate × 2, capped 0–100): {base_score:.1f}")
        st.write(f"**Adjustments** (SIP bonus / discretionary penalty): {adjustments:+.1f}")
        st.write(f"**Final Score:** {final_score:.1f} / 100")

    st.markdown("---")


def show_ai_insights(yearly_data):
    # Always prefer live_df from session_state so OCR/Voice entries
    # are reflected immediately without a full page reload.
    if "live_df" in st.session_state and st.session_state["live_df"] is not None:
        all_data = st.session_state["live_df"].copy()
        for col in ('credit', 'debit'):
            if col not in all_data.columns:
                all_data[col] = 0
        all_data['credit'] = pd.to_numeric(all_data['credit'], errors='coerce').fillna(0)
        all_data['debit']  = pd.to_numeric(all_data['debit'],  errors='coerce').fillna(0)
    else:
        all_data = pd.concat(yearly_data.values(), ignore_index=True) if yearly_data else pd.DataFrame()

    generate_financial_health_score(all_data)
    generate_storytelling(all_data)
