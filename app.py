import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import math

# Set page configuration
st.set_page_config(
    page_title="Retirement Planner Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .scenario-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2e8b57;
        margin-bottom: 1rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def convert_annual_to_monthly_rate(annual_rate):
    """Convert annual percentage rate to monthly rate"""
    return (1 + annual_rate / 100) ** (1/12) - 1

def format_currency(amount):
    """Format amount as currency in Indian Rupees"""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.2f} Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.2f} L"
    else:
        return f"₹{amount:,.0f}"

def corpus_to_monthly_withdrawal(starting_corpus, annual_return, annual_inflation, years):
    """
    Calculate sustainable monthly withdrawal from corpus (inflation-adjusted)
    Uses Present Value of Growing Annuity formula:
    PV = PMT * [(1 - ((1+g)/(1+r))^n) / (r - g)]
    Where: PV = Present Value (corpus), PMT = Payment, r = real return, g = inflation, n = periods
    """
    monthly_return = convert_annual_to_monthly_rate(annual_return)
    monthly_inflation = convert_annual_to_monthly_rate(annual_inflation)
    total_months = years * 12
    
    # Real return rate (adjusted for inflation)
    if monthly_return == monthly_inflation:
        # Special case when return equals inflation
        monthly_withdrawal = starting_corpus / total_months
    else:
        # Growing annuity formula for inflation-adjusted withdrawals
        denominator = monthly_return - monthly_inflation
        numerator = 1 - ((1 + monthly_inflation) / (1 + monthly_return)) ** total_months
        pv_factor = numerator / denominator
        monthly_withdrawal = starting_corpus / pv_factor
    
    # Generate month-by-month breakdown
    data = []
    current_corpus = starting_corpus
    current_withdrawal = monthly_withdrawal
    
    for month in range(1, total_months + 1):
        # Apply return to corpus
        current_corpus = current_corpus * (1 + monthly_return)
        
        # Subtract current month's withdrawal
        current_corpus -= current_withdrawal
        
        data.append({
            'Month': month,
            'Year': math.ceil(month / 12),
            'Starting Balance': current_corpus + current_withdrawal,
            'Monthly Return': (current_corpus + current_withdrawal) * monthly_return,
            'Withdrawal Amount': current_withdrawal,
            'Ending Balance': current_corpus
        })
        
        # Increase withdrawal for next month due to inflation
        current_withdrawal *= (1 + monthly_inflation)
    
    return pd.DataFrame(data), monthly_withdrawal

def withdrawal_to_corpus_duration(starting_corpus, monthly_withdrawal, annual_return, annual_inflation):
    """
    Calculate how long corpus will last with given monthly withdrawals
    Simulates month-by-month until corpus is depleted
    """
    monthly_return = convert_annual_to_monthly_rate(annual_return)
    monthly_inflation = convert_annual_to_monthly_rate(annual_inflation)
    
    data = []
    current_corpus = starting_corpus
    current_withdrawal = monthly_withdrawal
    month = 0
    
    while current_corpus > 0:
        month += 1
        
        # Apply return to corpus
        corpus_after_return = current_corpus * (1 + monthly_return)
        
        # Check if withdrawal exceeds remaining corpus
        actual_withdrawal = min(current_withdrawal, corpus_after_return)
        
        # Subtract withdrawal
        current_corpus = corpus_after_return - actual_withdrawal
        
        data.append({
            'Month': month,
            'Year': math.ceil(month / 12),
            'Starting Balance': corpus_after_return,
            'Monthly Return': current_corpus + actual_withdrawal - corpus_after_return + (corpus_after_return * monthly_return),
            'Withdrawal Amount': actual_withdrawal,
            'Ending Balance': max(0, current_corpus)
        })
        
        # If corpus is depleted, break
        if current_corpus <= 0:
            break
            
        # Increase withdrawal for next month due to inflation
        current_withdrawal *= (1 + monthly_inflation)
        
        # Safety check to prevent infinite loop
        if month > 1200:  # 100 years max
            break
    
    return pd.DataFrame(data), month

def monthly_savings_to_corpus(monthly_sip, annual_stepup, years_to_retirement, annual_return):
    """
    Calculate final corpus from monthly SIP with annual step-up
    Uses Future Value of Growing Annuity formula:
    FV = PMT * [((1+r)^n - (1+g)^n) / (r - g)]
    Where: PMT = Payment, r = return rate, g = growth rate, n = periods
    """
    monthly_return = convert_annual_to_monthly_rate(annual_return)
    monthly_stepup = convert_annual_to_monthly_rate(annual_stepup)
    total_months = years_to_retirement * 12
    
    data = []
    current_corpus = 0
    current_sip = monthly_sip
    
    for month in range(1, total_months + 1):
        # Add current month's SIP
        current_corpus += current_sip
        
        # Apply return to corpus
        current_corpus *= (1 + monthly_return)
        
        data.append({
            'Month': month,
            'Year': math.ceil(month / 12),
            'SIP Amount': current_sip,
            'Corpus Before Return': current_corpus - (current_corpus * monthly_return / (1 + monthly_return)),
            'Monthly Return': current_corpus * monthly_return / (1 + monthly_return),
            'Corpus After Return': current_corpus
        })
        
        # Increase SIP annually (every 12 months)
        if month % 12 == 0:
            current_sip *= (1 + annual_stepup / 100)
    
    return pd.DataFrame(data), current_corpus

def custom_cashflow_calculation(cashflow_df, annual_return):
    """
    Calculate PV/FV for custom monthly cashflow schedule
    Positive values are inflows, negative values are outflows
    """
    monthly_return = convert_annual_to_monthly_rate(annual_return)
    
    data = []
    current_corpus = 0
    
    for index, row in cashflow_df.iterrows():
        month = index + 1
        cashflow = row['Cashflow']
        
        # Apply return to existing corpus
        current_corpus *= (1 + monthly_return)
        
        # Add/subtract cashflow
        current_corpus += cashflow
        
        data.append({
            'Month': month,
            'Year': math.ceil(month / 12),
            'Cashflow': cashflow,
            'Corpus Before Cashflow': current_corpus - cashflow,
            'Monthly Return': (current_corpus - cashflow) * monthly_return,
            'Corpus After Cashflow': current_corpus
        })
    
    return pd.DataFrame(data), current_corpus

def main():
    # Main header
    st.markdown('<h1 class="main-header">💰 Retirement Planner Tracker</h1>', unsafe_allow_html=True)
    
    # Sidebar for scenario selection and inputs
    st.sidebar.title("📊 Planning Scenarios")
    
    scenario = st.sidebar.selectbox(
        "Choose a scenario:",
        [
            "Corpus to Monthly Withdrawal",
            "Withdrawal to Corpus Duration", 
            "Monthly Savings to Corpus",
            "Custom Cashflow Analysis"
        ]
    )
    
    st.sidebar.markdown("---")
    
    # Scenario-specific inputs and calculations
    if scenario == "Corpus to Monthly Withdrawal":
        st.markdown('<h2 class="scenario-header">📈 Corpus to Monthly Withdrawal Calculator</h2>', unsafe_allow_html=True)
        st.write("Calculate sustainable monthly withdrawal amount from your retirement corpus (inflation-adjusted).")
        
        # Input fields
        col1, col2 = st.sidebar.columns(2)
        with col1:
            starting_corpus = st.number_input("Starting Corpus (₹)", value=10000000, step=100000, format="%d")
            annual_return = st.number_input("Annual Return (%)", value=8.0, step=0.1, format="%.1f")
        with col2:
            annual_inflation = st.number_input("Annual Inflation (%)", value=6.0, step=0.1, format="%.1f")
            years = st.number_input("Number of Years", value=25, step=1, format="%d")
        
        if st.sidebar.button("Calculate", type="primary"):
            df, monthly_withdrawal = corpus_to_monthly_withdrawal(starting_corpus, annual_return, annual_inflation, years)
            
            # Results summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Initial Monthly Withdrawal", format_currency(monthly_withdrawal))
            with col2:
                final_withdrawal = monthly_withdrawal * ((1 + convert_annual_to_monthly_rate(annual_inflation)) ** (years * 12))
                st.metric("Final Monthly Withdrawal", format_currency(final_withdrawal))
            with col3:
                total_withdrawn = df['Withdrawal Amount'].sum()
                st.metric("Total Amount Withdrawn", format_currency(total_withdrawn))
            
            # Chart
            fig = px.line(df, x='Month', y='Ending Balance', 
                         title='Corpus Depletion Over Time',
                         labels={'Ending Balance': 'Corpus Balance (₹)', 'Month': 'Month'})
            fig.update_layout(yaxis_tickformat='₹,.0f')
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table and download
            st.subheader("Month-by-Month Breakdown")
            
            # Format currency columns for display
            display_df = df.copy()
            currency_cols = ['Starting Balance', 'Monthly Return', 'Withdrawal Amount', 'Ending Balance']
            for col in currency_cols:
                display_df[col] = display_df[col].apply(lambda x: f"₹{x:,.0f}")
            
            st.dataframe(display_df, use_container_width=True)
            
            # CSV download
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"corpus_withdrawal_plan_{years}years.csv",
                mime="text/csv"
            )
    
    elif scenario == "Withdrawal to Corpus Duration":
        st.markdown('<h2 class="scenario-header">⏰ Withdrawal to Corpus Duration Calculator</h2>', unsafe_allow_html=True)
        st.write("Calculate how long your corpus will last with a given monthly withdrawal amount.")
        
        # Input fields
        col1, col2 = st.sidebar.columns(2)
        with col1:
            starting_corpus = st.number_input("Starting Corpus (₹)", value=10000000, step=100000, format="%d")
            monthly_withdrawal = st.number_input("Monthly Withdrawal (₹)", value=80000, step=1000, format="%d")
        with col2:
            annual_return = st.number_input("Annual Return (%)", value=8.0, step=0.1, format="%.1f")
            annual_inflation = st.number_input("Annual Inflation (%)", value=6.0, step=0.1, format="%.1f")
        
        if st.sidebar.button("Calculate", type="primary"):
            df, total_months = withdrawal_to_corpus_duration(starting_corpus, monthly_withdrawal, annual_return, annual_inflation)
            
            # Results summary
            years_duration = total_months / 12
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Duration (Years)", f"{years_duration:.1f}")
            with col2:
                st.metric("Duration (Months)", f"{total_months}")
            with col3:
                total_withdrawn = df['Withdrawal Amount'].sum()
                st.metric("Total Amount Withdrawn", format_currency(total_withdrawn))
            
            # Chart
            fig = px.line(df, x='Month', y='Ending Balance', 
                         title='Corpus Depletion Over Time',
                         labels={'Ending Balance': 'Corpus Balance (₹)', 'Month': 'Month'})
            fig.update_layout(yaxis_tickformat='₹,.0f')
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table and download
            st.subheader("Month-by-Month Breakdown")
            
            # Format currency columns for display
            display_df = df.copy()
            currency_cols = ['Starting Balance', 'Monthly Return', 'Withdrawal Amount', 'Ending Balance']
            for col in currency_cols:
                display_df[col] = display_df[col].apply(lambda x: f"₹{x:,.0f}")
            
            st.dataframe(display_df, use_container_width=True)
            
            # CSV download
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"withdrawal_duration_plan.csv",
                mime="text/csv"
            )
    
    elif scenario == "Monthly Savings to Corpus":
        st.markdown('<h2 class="scenario-header">💪 Monthly Savings to Corpus Calculator</h2>', unsafe_allow_html=True)
        st.write("Calculate final retirement corpus from monthly SIP with annual step-up.")
        
        # Input fields
        col1, col2 = st.sidebar.columns(2)
        with col1:
            monthly_sip = st.number_input("Monthly SIP Amount (₹)", value=50000, step=1000, format="%d")
            annual_stepup = st.number_input("Annual Step-up (%)", value=10.0, step=0.1, format="%.1f")
        with col2:
            years_to_retirement = st.number_input("Years to Retirement", value=20, step=1, format="%d")
            annual_return = st.number_input("Annual Return (%)", value=12.0, step=0.1, format="%.1f")
        
        if st.sidebar.button("Calculate", type="primary"):
            df, final_corpus = monthly_savings_to_corpus(monthly_sip, annual_stepup, years_to_retirement, annual_return)
            
            # Results summary
            total_invested = df['SIP Amount'].sum()
            returns_earned = final_corpus - total_invested
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Final Corpus", format_currency(final_corpus))
            with col2:
                st.metric("Total Invested", format_currency(total_invested))
            with col3:
                st.metric("Returns Earned", format_currency(returns_earned))
            
            # Chart
            fig = px.line(df, x='Month', y='Corpus After Return', 
                         title='Corpus Growth Over Time',
                         labels={'Corpus After Return': 'Corpus Value (₹)', 'Month': 'Month'})
            fig.update_layout(yaxis_tickformat='₹,.0f')
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table and download
            st.subheader("Month-by-Month Breakdown")
            
            # Format currency columns for display
            display_df = df.copy()
            currency_cols = ['SIP Amount', 'Corpus Before Return', 'Monthly Return', 'Corpus After Return']
            for col in currency_cols:
                display_df[col] = display_df[col].apply(lambda x: f"₹{x:,.0f}")
            
            st.dataframe(display_df, use_container_width=True)
            
            # CSV download
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"sip_corpus_plan_{years_to_retirement}years.csv",
                mime="text/csv"
            )
    
    elif scenario == "Custom Cashflow Analysis":
        st.markdown('<h2 class="scenario-header">📋 Custom Cashflow Analysis</h2>', unsafe_allow_html=True)
        st.write("Upload a custom monthly cashflow schedule and calculate PV/FV. Positive values are inflows, negative values are outflows.")
        
        # Input fields
        annual_return = st.sidebar.number_input("Annual Return (%)", value=8.0, step=0.1, format="%.1f")
        
        # File upload
        uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=['csv'])
        
        # Sample CSV format
        st.sidebar.markdown("### CSV Format:")
        st.sidebar.code("Cashflow\n50000\n-30000\n25000\n...")
        
        if uploaded_file is not None:
            try:
                # Read uploaded CSV
                cashflow_df = pd.read_csv(uploaded_file)
                
                if 'Cashflow' not in cashflow_df.columns:
                    st.error("CSV must have a 'Cashflow' column")
                else:
                    if st.sidebar.button("Calculate", type="primary"):
                        df, final_value = custom_cashflow_calculation(cashflow_df, annual_return)
                        
                        # Results summary
                        total_inflows = cashflow_df[cashflow_df['Cashflow'] > 0]['Cashflow'].sum()
                        total_outflows = abs(cashflow_df[cashflow_df['Cashflow'] < 0]['Cashflow'].sum())
                        net_cashflow = total_inflows - total_outflows
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Final Value", format_currency(final_value))
                        with col2:
                            st.metric("Total Inflows", format_currency(total_inflows))
                        with col3:
                            st.metric("Total Outflows", format_currency(total_outflows))
                        with col4:
                            st.metric("Net Cashflow", format_currency(net_cashflow))
                        
                        # Chart
                        fig = px.line(df, x='Month', y='Corpus After Cashflow', 
                                     title='Corpus Value Over Time',
                                     labels={'Corpus After Cashflow': 'Corpus Value (₹)', 'Month': 'Month'})
                        fig.update_layout(yaxis_tickformat='₹,.0f')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Data table and download
                        st.subheader("Month-by-Month Breakdown")
                        
                        # Format currency columns for display
                        display_df = df.copy()
                        currency_cols = ['Cashflow', 'Corpus Before Cashflow', 'Monthly Return', 'Corpus After Cashflow']
                        for col in currency_cols:
                            display_df[col] = display_df[col].apply(lambda x: f"₹{x:,.0f}")
                        
                        st.dataframe(display_df, use_container_width=True)
                        
                        # CSV download
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name="custom_cashflow_analysis.csv",
                            mime="text/csv"
                        )
            
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
        
        else:
            # Show sample data option
            if st.sidebar.button("Use Sample Data"):
                sample_data = pd.DataFrame({
                    'Cashflow': [50000, 52000, 54000, -30000, -31000, 60000, 62000, -35000, 65000, 67000, -40000, 70000]
                })
                
                df, final_value = custom_cashflow_calculation(sample_data, annual_return)
                
                # Results summary
                total_inflows = sample_data[sample_data['Cashflow'] > 0]['Cashflow'].sum()
                total_outflows = abs(sample_data[sample_data['Cashflow'] < 0]['Cashflow'].sum())
                net_cashflow = total_inflows - total_outflows
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Final Value", format_currency(final_value))
                with col2:
                    st.metric("Total Inflows", format_currency(total_inflows))
                with col3:
                    st.metric("Total Outflows", format_currency(total_outflows))
                with col4:
                    st.metric("Net Cashflow", format_currency(net_cashflow))
                
                # Chart
                fig = px.line(df, x='Month', y='Corpus After Cashflow', 
                             title='Corpus Value Over Time (Sample Data)',
                             labels={'Corpus After Cashflow': 'Corpus Value (₹)', 'Month': 'Month'})
                fig.update_layout(yaxis_tickformat='₹,.0f')
                st.plotly_chart(fig, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    **📝 Notes:**
    - All calculations convert annual rates to monthly rates internally
    - Inflation-adjusted withdrawals use growing annuity formulas
    - Step-up SIP calculations compound monthly returns with annual SIP increases
    - Custom cashflow analysis supports both positive (inflows) and negative (outflows) values
    """)

if __name__ == "__main__":
    main()
