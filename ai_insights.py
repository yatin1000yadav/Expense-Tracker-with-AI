import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def generate_storytelling(df):
    st.markdown("## 🔮 Predictive Spending Analytics")

    if df.empty:
        st.info("No data available for insights.")
        return

    # Prepare data - exclude fixed/investment categories
    fixed_categories = ['sip', 'rent,maid & electricity bills', 'financial support to family']
    expense_df = df[~df['category'].str.lower().isin([cat.lower() for cat in fixed_categories])]
    
    if expense_df.empty:
        st.info("No discretionary expenses to analyze.")
        return
    
    # Calculate category percentages
    category_totals = expense_df.groupby('category')['debit'].sum().abs()
    total_discretionary = category_totals.sum()
    category_percentages = (category_totals / total_discretionary * 100).round(1)
    
    st.markdown("---")
    
    # 1. SPENDING PERSONALITY
    st.markdown("### 🧠 Spending Personality")
    
    # Daily vs Weekend vs Planned analysis
    daily_pct = category_percentages.get('Today\'s expense ', 0)
    weekend_pct = category_percentages.get('Weekend expense', 0)
    shopping_pct = category_percentages.get('Shopping', 0)
    trips_pct = category_percentages.get('Trips', 0) + category_percentages.get('Travelling expense', 0)
    
    spontaneous_pct = daily_pct + weekend_pct
    planned_pct = shopping_pct + trips_pct
    
    if spontaneous_pct > 50:
        st.markdown(f"• **Spontaneous Spender** ({spontaneous_pct:.1f}%): You prefer in-the-moment purchases over planned spending")
    elif planned_pct > 40:
        st.markdown(f"• **Strategic Planner** ({planned_pct:.1f}%): You favor planned purchases and experiences")
    else:
        st.markdown(f"• **Balanced Decision Maker**: {spontaneous_pct:.1f}% spontaneous vs {planned_pct:.1f}% planned spending")
    
    # 2. LIFESTYLE ANALYSIS
    st.markdown("### 🏠 Lifestyle Profile")
    
    # Get top spending category
    if len(category_percentages) > 0:
        top_category = category_percentages.idxmax()
        top_percentage = category_percentages.max()
        
        lifestyle_profiles = {
            "Today's expense ": f"**Daily Comfort Seeker** ({top_percentage:.1f}%): Your largest expense is daily pleasures and immediate needs",
            "Weekend expense": f"**Weekend Warrior** ({top_percentage:.1f}%): You invest most in weekend entertainment and relaxation",
            "Shopping": f"**Thoughtful Shopper** ({top_percentage:.1f}%): Deliberate shopping dominates your discretionary spending",
            "Petrol": f"**Mobile Lifestyle** ({top_percentage:.1f}%): Transportation is your biggest discretionary expense",
            "Self Care": f"**Wellness Focused** ({top_percentage:.1f}%): You prioritize health and self-care investments",
            "Veggies,Gas cylinder and Dmart": f"**Home Manager** ({top_percentage:.1f}%): Household essentials are your primary focus",
            "Trips": f"**Experience Collector** ({top_percentage:.1f}%): Travel and experiences are your main investment",
            "Travelling expense": f"**Journey Enthusiast** ({top_percentage:.1f}%): Transportation and travel logistics are your priority",
            "Pune & village expense": f"**Family Explorer** ({top_percentage:.1f}%): You balance leisure activities with family time across cities"

        }
        
        if top_category in lifestyle_profiles:
            st.markdown(f"• {lifestyle_profiles[top_category]}")
    
    # 3. SPENDING BALANCE
    st.markdown("### ⚖️ Spending Balance")
    
    # Essential vs Lifestyle balance
    essential_categories = ['Veggies,Gas cylinder and Dmart', 'Petrol', 'Recharge']
    lifestyle_categories = ['Shopping', 'Self Care', 'Trips', 'Weekend expense', 'Travelling expense','Pune & village expense']
    
    essential_pct = sum([category_percentages.get(cat, 0) for cat in essential_categories])
    lifestyle_pct = sum([category_percentages.get(cat, 0) for cat in lifestyle_categories])
    
    if essential_pct > lifestyle_pct:
        st.markdown(f"• **Practical Prioritizer**: {essential_pct:.1f}% essentials vs {lifestyle_pct:.1f}% lifestyle - You focus on needs first")
    elif lifestyle_pct > essential_pct * 1.5:
        st.markdown(f"• **Lifestyle Investor**: {lifestyle_pct:.1f}% lifestyle vs {essential_pct:.1f}% essentials - You invest in experiences")
    else:
        st.markdown(f"• **Balanced Living**: {essential_pct:.1f}% essentials vs {lifestyle_pct:.1f}% lifestyle - Well-balanced approach")
    
    # 4. FINANCIAL BEHAVIOR
    st.markdown("### 📊 Financial Behavior")
    
    # Transaction pattern analysis
    avg_transaction = abs(expense_df['debit'].mean())
    transaction_count = len(expense_df)
    
    if avg_transaction < 200 and transaction_count > 20:
        st.markdown(f"• **Frequent Small Spender**: {transaction_count} transactions averaging ₹{avg_transaction:.0f} - You prefer many small purchases")
    elif avg_transaction > 1000 and transaction_count < 15:
        st.markdown(f"• **Bulk Decision Maker**: {transaction_count} transactions averaging ₹{avg_transaction:.0f} - You make fewer, larger purchases")
    else:
        st.markdown(f"• **Moderate Spender**: {transaction_count} transactions averaging ₹{avg_transaction:.0f} - Balanced transaction pattern")
    
    # 5. KEY RECOMMENDATION
    st.markdown("### 🎯 Smart Focus")
    
    # Focus on top spending area
    if len(category_percentages) > 0:
        top_category = category_percentages.idxmax()
        top_percentage = category_percentages.max()
        
        if top_percentage > 40:
            st.markdown(f"• **High Concentration Alert**: {top_percentage:.1f}% of spending is in '{top_category}' - Consider diversifying or optimizing this category")
        elif top_percentage < 15:
            st.markdown(f"• **Well-Distributed Spending**: Your largest category '{top_category}' is only {top_percentage:.1f}% - Good spending diversity")
        else:
            st.markdown(f"• **Optimization Opportunity**: Focus on '{top_category}' ({top_percentage:.1f}% of spending) for maximum savings impact")
    
    st.markdown("---")


def generate_financial_health_score(df):
    st.markdown("## 💯 Financial Health Score")
    
    if df.empty:
        st.info("No data available for score calculation.")
        return
    
    # Calculate income and expenses
    total_income = df[df['credit'] > 0]['credit'].sum()
    total_expenses = abs(df[df['debit'] < 0]['debit'].sum())
    
    if total_income <= 0:
        st.warning("No income data found. Cannot calculate financial health score.")
        return
    
    # Calculate savings rate
    net_savings = total_income - total_expenses
    savings_rate = (net_savings / total_income) * 100
   
    # Calculate financial health score (0-100)
    # Base score from savings rate
    base_score = max(0, min(100, savings_rate * 2))  # 50% savings = 100 score

    # Adjust for spending behavior
    fixed_categories = ['sip', 'rent,maid & electricity bills', 'financial support to family']
    fixed_expenses = abs(df[df['category'].str.lower().isin(fixed_categories)]['debit'].sum())
    discretionary_expenses = total_expenses - fixed_expenses
    
    # Bonus/Penalty adjustments
    adjustments = 0
    
    # SIP Investment Bonus (up to +15 points)
    sip_amount = abs(df[df['category'].str.lower() == 'sip']['debit'].sum())
    if sip_amount > 0:
        sip_ratio = (sip_amount / total_income) * 100
        adjustments += min(15, sip_ratio * 1.5)  # Max 15 points for 10%+ SIP
    
    # Discretionary spending penalty/bonus
    discretionary_ratio = (discretionary_expenses / total_income) * 100
    if discretionary_ratio > 60:
        adjustments -= 10  # High discretionary spending penalty
    elif discretionary_ratio < 30:
        adjustments += 10  # Low discretionary spending bonus
    
    # Final score calculation
    final_score = max(0, min(100, base_score + adjustments))
  
    # Create gauge chart
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = final_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Financial Health Score", 'font': {'size': 24, 'weight': 700}},
        delta = {'reference': 50, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color':  "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#ff6b6b'},      # Red - Poor
                {'range': [40, 60], 'color': '#ffa726'},     # Orange - Fair  
                {'range': [60, 75], 'color': '#ffeb3b'},     # Yellow - Good
                {'range': [75, 85], 'color': '#66bb6a'},     # Light Green - Very Good
                {'range': [85, 100], 'color': '#4caf50'}     # Green - Excellent
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=400,
        font={'color': "darkblue", 'family': "Arial"},
        paper_bgcolor="white"
    )
    
    # Display the gauge
    st.plotly_chart(fig, use_container_width=True)
    
    # Score-based insights
    st.markdown("### 📊 Score Breakdown")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💰 Savings Rate", 
            value=f"{savings_rate:.1f}%",
            # delta=f"₹{net_savings:,.0f} saved" if net_savings > 0 else f"₹{abs(net_savings):,.0f} overspent"
        )
    
    with col2:
        sip_ratio = (sip_amount / total_income * 100) if total_income > 0 else 0
        st.metric(
            label="📈 Investment Rate", 
            value=f"{sip_ratio:.1f}%",
            # delta=f"₹{sip_amount:,.0f} invested"
        )
    
    with col3:
        discretionary_ratio = (discretionary_expenses / total_income * 100) if total_income > 0 else 0
        st.metric(
            label="🎯 Lifestyle Spending", 
            value=f"{discretionary_ratio:.1f}%",
            # delta=f"₹{discretionary_expenses:,.0f}"
        )
    
    st.markdown("### 🎯 Your Financial Profile & Next Steps")
    
    if final_score >= 85:
        st.success("**🌟 Financial Champion** - Excellent money management! Your disciplined approach puts you in the top tier.")
        st.markdown("• **Next Steps**: Explore advanced investments and automate transfers to maximize growth")
        
    elif final_score >= 75:
        st.success("**💪 Financial Achiever** - Very good financial health with positive savings rate!")
        st.markdown(f"• **Next Steps**: {'Increase SIP investments' if sip_ratio < 15 else 'Optimize with tax-saving investments'} for champion level")
        
    elif final_score >= 60:
        st.warning("**⚖️ Financial Balancer** - Good foundation, room for improvement")
        st.markdown(f"• **Next Steps**: Reduce discretionary spending by 5-10% and boost SIP by ₹1000-2000 monthly")
        
    elif final_score >= 40:
        st.warning("**⚠️ Financial Attention Needed** - Time to refocus priorities")
        st.markdown(f"• **Next Steps**: Build emergency fund first, then follow 50/30/20 rule (50% needs, 30% wants, 20% savings)")
        
    else:
        st.error("**🚨 Financial Emergency** - Immediate action required")
        st.markdown("• You're Very Close to spend more than you earn - this is unsustainable")
        st.markdown("• Focus on essential expenses only and eliminate all unnecessary spending")
        st.markdown("• Consider additional income sources or drastically reduce expenses")
        st.markdown("• **Next Steps**: Expense audit and income boost through side income or skill development")

    st.markdown("---")

def show_ai_insights(yearly_data):
    all_data = pd.concat(yearly_data.values(), ignore_index=True)
    generate_financial_health_score(all_data)
    generate_storytelling(all_data)
