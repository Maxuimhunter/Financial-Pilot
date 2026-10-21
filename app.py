import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import db_utils
from streamlit_option_menu import option_menu
import os
import warnings
from dotenv import load_dotenv
from openai import OpenAI

# Suppress FutureWarning for pandas concat
warnings.filterwarnings('ignore', category=FutureWarning)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Personal Budget Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
db_utils.init_db()

# Constants
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

CATEGORIES = [
    "Income", "Rent/Mortgage", "Utilities", "Groceries", "Dining Out",
    "Transportation", "Entertainment", "Shopping", "Healthcare", "Savings",
    "Investments", "Other"
]

BUDGET_COLOR = '#667eea'
ACTUAL_COLOR = '#f5576c'
SAVINGS_COLOR = '#43e97b'
WARNING_COLOR = '#fccb90'
DANGER_COLOR = '#ff9a9e'
COLOR_PALETTE = [BUDGET_COLOR, ACTUAL_COLOR, SAVINGS_COLOR, WARNING_COLOR, DANGER_COLOR]

# Helper functions
def get_month_id(month_name):
    """Get month ID from month name."""
    return MONTHS.index(month_name) + 1

def calculate_summary(df):
    """Calculate summary statistics for the budget."""
    if df.empty:
        return {
            'total_budgeted': 0.0,
            'total_actual': 0.0,
            'difference': 0.0,
            'savings_rate': 0.0
        }
    
    try:
        # Ensure we're working with numeric values
        df = df.copy()
        df['budgeted'] = pd.to_numeric(df['budgeted'], errors='coerce').fillna(0.0)
        df['actual'] = pd.to_numeric(df['actual'], errors='coerce').fillna(0.0)
        
        # Calculate totals
        total_budgeted = float(df['budgeted'].sum())
        total_actual = float(df['actual'].sum())
        difference = float(total_budgeted - total_actual)
        
        # Calculate savings rate (assuming income is the first category)
        income_df = df[df['category'] == 'Income']
        savings_df = df[df['category'] == 'Savings']
        
        income = float(income_df['budgeted'].sum()) if not income_df.empty else 0.0
        savings = float(savings_df['budgeted'].sum()) if not savings_df.empty else 0.0
        
        savings_rate = float((savings / income * 100) if income > 0 else 0)
        
        return {
            'total_budgeted': total_budgeted,
            'total_actual': total_actual,
            'difference': difference,
            'savings_rate': savings_rate
        }
    except Exception as e:
        st.error(f"Error calculating summary: {str(e)}")
        return {
            'total_budgeted': 0.0,
            'total_actual': 0.0,
            'difference': 0.0,
            'savings_rate': 0.0
        }

def get_ai_financial_advice(budget_data, month, year):
    """Get AI-powered financial advice using ChatGPT."""
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        return "OpenAI API key not found. Please add OPENAI_API_KEY to your .env file."

    try:
        client = OpenAI(api_key=api_key)

        # Format budget data for the prompt
        budget_summary = f"""
Budget for {month} {year}:
- Total Budgeted: ${budget_data.get('total_budgeted', 0):,.2f}
- Total Spent: ${budget_data.get('total_actual', 0):,.2f}
- Difference: ${budget_data.get('difference', 0):,.2f}
- Savings Rate: {budget_data.get('savings_rate', 0):.1f}%
"""

        prompt = f"""
You are a financial advisor. Based on the following budget data, provide 3-5 concise, actionable financial tips.

{budget_summary}

Focus on:
1. Spending patterns
2. Savings recommendations
3. Areas for improvement
4. Practical advice

Keep your response under 200 words and use bullet points.
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful financial advisor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error getting AI advice: {str(e)}"

# Sidebar
with st.sidebar:
    st.title("💰 Budget Tracker")

    # Get available years and also show a range of years
    available_years = db_utils.get_available_years()
    year_range = db_utils.get_years_range(2020, 2030)

    # Combine available years with the range, remove duplicates, sort descending
    all_years = sorted(list(set(available_years + year_range)), reverse=True)

    # Year selector
    selected_year = st.selectbox(
        "Select Year",
        all_years,
        index=0,
        key="sidebar_year_select"
    )

    # Navigation
    menu = option_menu(
        menu_title=None,
        options=["Monthly Budget", "Annual Overview", "AI Advisor", "Settings"],
        icons=["calendar-month", "graph-up", "robot", "gear"],
        default_index=0
    )

    # Month selector
    selected_month = st.selectbox(
        "Select Month",
        MONTHS,
        index=datetime.now().month - 1,
        key="sidebar_month_select"
    )
    
    st.markdown("---")
    st.markdown("### Quick Actions")

    if st.button("Export to Excel", key="sidebar_export_excel"):
        # Export functionality will be implemented
        st.success("Export feature coming soon!")

    if st.button("Reset Current Month", key="sidebar_reset_month"):
        # Reset functionality will be implemented
        st.warning("Reset feature coming soon!")

# Helper functions
def display_expense_form(category):
    """Display a form to add a new expense."""
    with st.expander(f"Add New Expense - {category}", expanded=False):
        with st.form(key=f'expense_form_{category}'):
            col1, col2 = st.columns(2)
            with col1:
                description = st.text_input("Description", key=f"desc_{category}")
                amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f", key=f"amount_{category}")
            with col2:
                expense_date = st.date_input("Date", key=f"date_{category}")
                
            if st.form_submit_button("Add Expense"):
                if description and amount > 0:
                    success = db_utils.add_expense(
                        month_id=month_id,
                        category=category,
                        description=description,
                        amount=amount,
                        expense_date=expense_date,
                        year=selected_year
                    )
                    if success:
                        st.success("Expense added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add expense. Please try again.")
                else:
                    st.warning("Please fill in all required fields.")

def display_expenses(month_id, category, year):
    """Display expenses for a specific category, month, and year."""
    expenses = db_utils.get_expenses(month_id, category, year)
    if not expenses:
        st.info("No expenses recorded yet.")
        return 0.0
    
    total = 0.0
    for expense in expenses:
        col1, col2, col3, col4 = st.columns([4, 2, 1, 1])
        with col1:
            st.write(expense['description'])
            st.caption(expense['expense_date'].strftime('%b %d, %Y') if expense['expense_date'] else 'N/A')
        with col2:
            st.write(f"${float(expense['amount']):.2f}")
        with col3:
            if st.button("✏️", key=f"edit_{expense['id']}_{selected_year}"):
                st.session_state.editing_expense = expense['id']
        with col4:
            if st.button("🗑️", key=f"delete_{expense['id']}_{selected_year}"):
                if db_utils.delete_expense(expense['id']):
                    st.rerun()
        
        total += float(expense['amount'])
    
    return total

# Main content
if menu == "Monthly Budget":
    st.title(f"{selected_month} {selected_year} Budget")
    
    # Get month ID
    month_id = get_month_id(selected_month)
    
    # Get existing budget data
    budget_data = db_utils.get_month_budget(month_id, selected_year)
    
    # Convert to DataFrame
    if budget_data:
        df = pd.DataFrame(budget_data)
    else:
        df = pd.DataFrame(columns=['category', 'budgeted', 'actual'])
    
    # Ensure all categories are present
    for category in CATEGORIES:
        if category not in df['category'].values:
            new_row = pd.DataFrame([{
                'category': category,
                'budgeted': 0.00,
                'actual': 0.00
            }])
            df = pd.concat([df, new_row], ignore_index=True, copy=False)
    
    # Budget section with two columns
    budget_col1, budget_col2 = st.columns([3, 1])
    
    with budget_col1:
        st.subheader("Budget vs Actual")
        
        # Ensure numeric types for the entire dataframe
        df['budgeted'] = pd.to_numeric(df['budgeted'], errors='coerce').fillna(0.0)
        df['actual'] = pd.to_numeric(df['actual'], errors='coerce').fillna(0.0)
        
        # Create a copy of the dataframe for editing, excluding Income from the editable section
        editable_df = df[df['category'] != 'Income'].copy()
        
        # Create editable budget table
        edited_values = {}
        
        # Display income with edit capability
        income_row = df[df['category'] == 'Income'].iloc[0] if not df[df['category'] == 'Income'].empty else None
        if income_row is not None:
            st.markdown("### Income")

            # Use year-specific session state key for income editing
            income_edit_key = f'editing_income_{selected_year}_{month_id}'

            # Initialize session state for edit mode
            if income_edit_key not in st.session_state:
                st.session_state[income_edit_key] = False

            cols = st.columns([3, 2, 1])
            with cols[0]:
                st.markdown(f"**Income**")

            if st.session_state[income_edit_key]:
                with cols[1]:
                    new_income = st.number_input(
                        "New Income Amount",
                        min_value=0.0,
                        step=100.0,
                        value=float(income_row['actual']),
                        key=f"new_income_input_{selected_year}_{month_id}"
                    )
                with cols[2]:
                    if st.button("💾 Save", key=f"save_income_{selected_year}_{month_id}"):
                        # Update both budgeted and actual income amounts
                        if db_utils.update_budget(
                            month_id=month_id,
                            category='Income',
                            budgeted=new_income,
                            is_income=True,
                            year=selected_year
                        ):
                            st.session_state[income_edit_key] = False
                            st.rerun()
                    if st.button("❌ Cancel", key=f"cancel_income_{selected_year}_{month_id}"):
                        st.session_state[income_edit_key] = False
                        st.rerun()
            else:
                with cols[1]:
                    # Always show the actual amount, not the budgeted amount
                    st.markdown(f"**${float(income_row['actual']):,.2f}**")
                with cols[2]:
                    if st.button("✏️ Edit", key=f"edit_income_btn_{selected_year}_{month_id}"):
                        st.session_state[income_edit_key] = True
                        st.rerun()
            
            st.markdown("---")
        
        # Display budget expenses section
        st.markdown("### Budget Expenses")

        # Use year-specific session state key
        budget_state_key = f'edited_budget_values_{selected_year}_{month_id}'

        # Initialize edited values if not exists for this year/month
        if budget_state_key not in st.session_state:
            st.session_state[budget_state_key] = {}

        # Calculate totals for reference
        total_budgeted = 0.0
        total_actual = 0.0

        # Create a form for all budget entries
        with st.form("budget_form"):
            for _, row in editable_df.iterrows():
                category = row['category']
                # Initialize session state for this category if not exists
                if category not in st.session_state[budget_state_key]:
                    st.session_state[budget_state_key][category] = float(row['budgeted'])

                cols = st.columns([3, 1, 1])
                with cols[0]:
                    st.markdown(f"**{category}**")
                with cols[1]:
                    # Make budgeted amount editable
                    st.session_state[budget_state_key][category] = st.number_input(
                        label=f"Budget for {category}",
                        min_value=0.0,
                        step=1.0,
                        value=st.session_state[budget_state_key][category],
                        key=f"budget_edit_{category}_{selected_year}_{month_id}",
                        label_visibility="collapsed"
                    )
                    total_budgeted += st.session_state[budget_state_key][category]
                with cols[2]:
                    # Display actual spending with color coding
                    actual = float(row['actual'])
                    total_actual += actual
                    budgeted = st.session_state[budget_state_key][category]
                    diff = actual - budgeted

                    if diff > 0:
                        st.markdown(f"<span style='color:red'>${actual:,.2f} (${diff:,.2f} over)</span>", unsafe_allow_html=True)
                    elif diff < 0:
                        st.markdown(f"<span style='color:green'>${actual:,.2f} (${abs(diff):,.2f} under)</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"${actual:,.2f} (on budget)")

            # Add save button at the bottom of the form
            submitted = st.form_submit_button("💾 Save Budget Expenses", use_container_width=True)
            if submitted:
                success = True
                for category, budgeted in st.session_state[budget_state_key].items():
                    if not db_utils.update_budget(
                        month_id=month_id,
                        category=category,
                        budgeted=budgeted,
                        year=selected_year
                    ):
                        st.error(f"Failed to update {category} budget.")
                        success = False

                if success:
                    st.success("Budget expenses updated successfully!")
                    # Clear the edited values from session state for this year/month
                    del st.session_state[budget_state_key]
                    st.rerun()
            
            # Add a small divider between categories
            st.markdown("---")
        
        # Display budget vs actual summary
        st.markdown("### Budget vs Actual Summary")
        
        # Calculate differences
        total_diff = total_actual - total_budgeted
        remaining_budget = total_budgeted - total_actual
        
        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Budgeted", f"${total_budgeted:,.2f}")
        
        with col2:
            st.metric("Actual", f"${total_actual:,.2f}")
        
        with col3:
            if total_diff > 0:
                st.metric("Difference", 
                        f"${abs(total_diff):,.2f} Over", 
                        delta=f"Over by ${abs(total_diff):,.2f}",
                        delta_color="inverse")
            elif total_diff < 0:
                st.metric("Difference", 
                        f"${abs(total_diff):,.2f} Under", 
                        delta=f"Under by ${abs(total_diff):,.2f}",
                        delta_color="normal")
            else:
                st.metric("Difference", "On Budget", delta="0.00")
        
        # Display remaining budget
        st.markdown("---")
        st.markdown("### Remaining Budget")
        if remaining_budget >= 0:
            st.success(f"**${remaining_budget:,.2f}** remaining in your budget")
        else:
            st.error(f"**${abs(remaining_budget):,.2f}** over budget")
    
    with budget_col2:
        # Financial Overview
        st.markdown("### Financial Overview")
        
        # Get all expenses from the database
        expenses = db_utils.get_expenses(month_id, year=selected_year)
        # Calculate total spent by summing all expense amounts
        total_spent = sum(float(expense['amount']) for expense in expenses) if expenses else 0.0
        
        # Get budgeted amounts (excluding income)
        expenses_df = df[df['category'] != 'Income']
        total_budgeted = float(expenses_df['budgeted'].sum())
        
        # Display metrics
        st.markdown("#### Total Budgeted")
        st.markdown(f"**${total_budgeted:,.2f}")
        
        st.markdown("#### Total Spent")
        st.markdown(f"**${total_spent:,.2f}")
        
        # Calculate and display difference
        difference = total_budgeted - total_spent
        st.markdown("#### Remaining Budget")
        if difference >= 0:
            st.markdown(f"<span style='color:green'>**${difference:,.2f}**</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:red'>**-${abs(difference):,.2f}**</span>", unsafe_allow_html=True)
        
        # Visual indicator for budget status
        if total_budgeted > 0:
            budget_used = (total_spent / total_budgeted) * 100
            if budget_used > 100:
                st.error("Over budget!")
            elif budget_used > 90:
                st.warning("Approaching budget limit")
            else:
                st.success("Within budget")
        
        # Add a refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    # Expense Details Section
    st.subheader("Expense Details")
    
    # Only show expense categories (exclude Income)
    expense_categories = [cat for cat in CATEGORIES if cat != 'Income']
    
    for category in expense_categories:
        category_sum = float(df[df['category'] == category]['actual'].sum()) if not df[df['category'] == category].empty else 0.0
        with st.expander(f"{category} - ${category_sum:.2f}", expanded=False):
            # Add new expense form
            with st.form(key=f"expense_form_{category}"):
                cols = st.columns([2, 1, 1, 1])
                with cols[0]:
                    description = st.text_input("Description", key=f"desc_{category}")
                with cols[1]:
                    amount = st.number_input("Amount", min_value=0.01, step=0.01, key=f"amt_{category}")
                with cols[2]:
                    expense_date = st.date_input("Date", value=datetime.now().date(), key=f"date_{category}")
                with cols[3]:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("Add Expense"):
                        if description and amount > 0:
                            success = db_utils.add_expense(
                                month_id=month_id,
                                category=category,
                                description=description,
                                amount=amount,
                                expense_date=expense_date,
                                year=selected_year
                            )
                            if success:
                                st.success("Expense added!")
                                st.rerun()
            
            # Display existing expenses
            st.write("### Recent Expenses")
            total_spent = display_expenses(month_id, category, selected_year)
                
            # Update the actual amount in the UI
            if not df[df['category'] == category].empty:
                df.loc[df['category'] == category, 'actual'] = float(total_spent) if total_spent else 0.0
    
    # Summary Section
    st.markdown("---")
    st.subheader("Financial Overview")
    
    # Calculate summary using the main df which has both budgeted and actual
    if not df.empty and 'actual' in df.columns and 'budgeted' in df.columns:
        # Ensure numeric types
        df['actual'] = pd.to_numeric(df['actual'], errors='coerce').fillna(0.0)
        df['budgeted'] = pd.to_numeric(df['budgeted'], errors='coerce').fillna(0.0)
        
        # Calculate totals
        total_budgeted = float(df['budgeted'].sum())
        total_actual = float(df['actual'].sum())
        remaining = total_budgeted - total_actual
        
        # Calculate savings rate (excluding income from the calculation)
        income = float(df[df['category'] == 'Income']['actual'].sum())
        if income > 0:
            savings_rate = ((income - float(df[df['category'] != 'Income']['actual'].sum())) / income) * 100
        else:
            savings_rate = 0.0
        
        # Display summary metrics
        cols = st.columns(4)
        
        with cols[0]:
            st.metric("Total Budgeted", f"${total_budgeted:,.2f}")
        with cols[1]:
            st.metric("Total Spent", f"${total_actual:,.2f}")
        with cols[2]:
            st.metric("Remaining", f"${remaining:,.2f}", 
                     delta_color="normal" if remaining >= 0 else "inverse")
        with cols[3]:
            st.metric("Savings Rate", f"{savings_rate:.1f}%")
            
        # Add some space before visualizations
        st.markdown("---")
        
        # Visualizations
        st.subheader("Spending Breakdown")
        
        # Prepare data for visualizations
        plot_df = df[df['category'] != 'Income'].copy()
        plot_df = plot_df[plot_df['actual'] > 0]
        
        if not plot_df.empty:
            # Pie chart
            fig = px.pie(
                plot_df,
                values='actual',
                names='category',
                title=f"{selected_month} Spending by Category",
                hole=0.3
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Bar chart comparing budgeted vs actual
            bar_df = df[df['category'] != 'Income'].copy()
            bar_df = bar_df.melt(
                id_vars=['category'],
                value_vars=['budgeted', 'actual'],
                var_name='type',
                value_name='amount'
            )
            
            fig = px.bar(
                bar_df,
                x='category',
                y='amount',
                color='type',
                barmode='group',
                title="Budgeted vs Actual Spending",
                labels={'amount': 'Amount ($)', 'category': 'Category'},
                color_discrete_map={'budgeted': BUDGET_COLOR, 'actual': ACTUAL_COLOR}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No spending data available for visualizations. Add some expenses to see the charts.")
    else:
        st.warning("No budget data available. Please set up your budget first.")
        
        # Add quick expense button
        with st.popover("➕ Quick Add Expense"):
            category = st.selectbox("Category", CATEGORIES)
            description = st.text_input("Description")
            amount = st.number_input("Amount", min_value=0.01, step=0.01)
            if st.button("Add", key="quick_add_expense"):
                if description and amount > 0:
                    success = db_utils.add_expense(
                        month_id=month_id,
                        category=category,
                        description=description,
                        amount=amount,
                        expense_date=datetime.now().date(),
                        year=selected_year
                    )
                    if success:
                        st.success("Expense added!")
                        st.rerun()
    
    # Visualizations
    st.subheader("Spending Breakdown")
    
    # Visualization section
    st.subheader("Spending Breakdown")
    
    # Use the main df which has both budgeted and actual columns
    if not df.empty and 'actual' in df.columns:
        # Filter out zero values and income for better visualization
        plot_df = df[(df['actual'] > 0) & (df['category'] != 'Income')].copy()
        
        if not plot_df.empty:
            # Ensure we're working with numeric values
            plot_df['actual'] = pd.to_numeric(plot_df['actual'], errors='coerce').fillna(0)

            # Create pie chart
            fig = px.pie(
                plot_df,
                values='actual',
                names='category',
                title=f"{selected_month} Spending by Category",
                color_discrete_sequence=COLOR_PALETTE
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Create bar chart comparing budgeted vs actual
            st.subheader("Budget vs Actual Spending")
            
            # Prepare data for bar chart
            bar_df = df[df['category'] != 'Income'].copy()
            bar_df['budgeted'] = pd.to_numeric(bar_df['budgeted'], errors='coerce').fillna(0)
            bar_df['actual'] = pd.to_numeric(bar_df['actual'], errors='coerce').fillna(0)
            
            # Melt the dataframe for easier plotting
            bar_df = bar_df.melt(
                id_vars=['category'], 
                value_vars=['budgeted', 'actual'],
                var_name='type',
                value_name='amount'
            )
            
            # Create bar chart
            fig = px.bar(
                bar_df,
                x='category',
                y='amount',
                color='type',
                barmode='group',
                title="Budgeted vs Actual Spending by Category",
                labels={'amount': 'Amount ($)', 'category': 'Category', 'type': 'Type'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No spending data available for visualization.")
    else:
        st.info("No data available for visualization. Add some expenses to see the charts.")

elif menu == "Annual Overview":
    st.title(f"Annual Overview - {selected_year}")
    
    # Get annual budget data
    annual_data = db_utils.get_annual_budget(selected_year)
    
    if not annual_data:
        st.info("No budget data available yet. Start by adding budgets for individual months.")
    else:
        # Convert to DataFrame
        df = pd.DataFrame(annual_data)
        
        # Ensure numeric types
        df['budgeted'] = pd.to_numeric(df['budgeted'], errors='coerce').fillna(0.0)
        df['actual'] = pd.to_numeric(df['actual'], errors='coerce').fillna(0.0)
        
        # Calculate annual summary
        income_df = df[df['category'] == 'Income']
        total_income = float(income_df['actual'].sum()) if not income_df.empty else 0.0
        
        expenses_df = df[df['category'] != 'Income']
        total_budgeted = float(expenses_df['budgeted'].sum())
        total_spent = float(expenses_df['actual'].sum())
        total_savings = total_income - total_spent
        savings_rate = (total_savings / total_income * 100) if total_income > 0 else 0.0
        
        # Display annual summary metrics
        st.subheader("Annual Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Income", f"${total_income:,.2f}")
        
        with col2:
            st.metric("Total Budgeted", f"${total_budgeted:,.2f}")
        
        with col3:
            st.metric("Total Spent", f"${total_spent:,.2f}")
        
        with col4:
            st.metric("Total Savings", f"${total_savings:,.2f}", 
                     delta=f"{savings_rate:.1f}% of income")
        
        st.markdown("---")

        # Multi-year comparison
        st.subheader("Multi-Year Comparison")
        st.write("Compare spending across different years")

        # Get years to compare (exclude current selected year for comparison)
        compare_years = [y for y in all_years if y != selected_year]

        if len(compare_years) > 0:
            # Allow user to select years to compare
            years_to_compare = st.multiselect(
                "Select years to compare",
                compare_years,
                default=[y for y in compare_years[:2] if y in compare_years]  # Default to first 2 available years
            )

            if years_to_compare:
                comparison_years = [selected_year] + years_to_compare

                # Get data for all selected years
                comparison_data = []
                for year in comparison_years:
                    year_data = db_utils.get_annual_budget(year)
                    if year_data:
                        year_df = pd.DataFrame(year_data)
                        year_df['year'] = year
                        comparison_data.append(year_df)

                if comparison_data:
                    comparison_df = pd.concat(comparison_data, ignore_index=True)

                    # Calculate total spending by year
                    yearly_spending = comparison_df[comparison_df['category'] != 'Income'].groupby('year')['actual'].sum().reset_index()
                    yearly_spending = yearly_spending.sort_values('year')

                    if not yearly_spending.empty:
                        # Yearly spending comparison chart
                        fig = px.bar(
                            yearly_spending,
                            x='year',
                            y='actual',
                            title='Total Spending by Year',
                            labels={'actual': 'Amount Spent ($)', 'year': 'Year'},
                            color_discrete_sequence=[BUDGET_COLOR]
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)

                        # Monthly spending comparison across years
                        monthly_comparison = comparison_df[comparison_df['category'] != 'Income'].groupby(['year', 'month_name'])['actual'].sum().reset_index()
                        monthly_comparison['month_number'] = monthly_comparison['month_name'].apply(lambda x: MONTHS.index(x) + 1)
                        monthly_comparison = monthly_comparison.sort_values(['month_number', 'year'])

                        if not monthly_comparison.empty:
                            fig = px.line(
                                monthly_comparison,
                                x='month_name',
                                y='actual',
                                color='year',
                                title='Monthly Spending Comparison Across Years',
                                markers=True,
                                labels={'actual': 'Amount Spent ($)', 'month_name': 'Month', 'year': 'Year'},
                                color_discrete_sequence=COLOR_PALETTE
                            )
                            fig.update_layout(height=500)
                            st.plotly_chart(fig, use_container_width=True)

                        # Category comparison across years
                        category_comparison = comparison_df[comparison_df['category'] != 'Income'].groupby(['year', 'category'])['actual'].sum().reset_index()

                        if not category_comparison.empty:
                            fig = px.bar(
                                category_comparison,
                                x='category',
                                y='actual',
                                color='year',
                                title='Spending by Category Across Years',
                                labels={'actual': 'Amount ($)', 'category': 'Category', 'year': 'Year'},
                                barmode='group',
                                color_discrete_sequence=COLOR_PALETTE
                            )
                            fig.update_layout(height=500)
                            st.plotly_chart(fig, use_container_width=True)

                        # Year-over-year comparison table
                        st.subheader("Year-over-Year Summary")
                        yearly_summary = comparison_df[comparison_df['category'] != 'Income'].groupby('year').agg({
                            'budgeted': 'sum',
                            'actual': 'sum'
                        }).reset_index()
                        yearly_summary['difference'] = yearly_summary['budgeted'] - yearly_summary['actual']
                        yearly_summary = yearly_summary.sort_values('year', ascending=False)
                        yearly_summary.columns = ['Year', 'Budgeted', 'Actual', 'Difference']

                        st.dataframe(
                            yearly_summary,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Budgeted": st.column_config.NumberColumn("Budgeted ($)", format="%.2f"),
                                "Actual": st.column_config.NumberColumn("Actual ($)", format="%.2f"),
                                "Difference": st.column_config.NumberColumn("Difference ($)", format="%.2f")
                            }
                        )
            else:
                st.info("Select years to compare to see multi-year analysis.")
        else:
            st.info("No other years available for comparison yet.")

        st.markdown("---")

        # Monthly spending trend
        st.subheader("Monthly Spending Trend")
        monthly_spending = df[df['category'] != 'Income'].groupby('month_name')['actual'].sum().reset_index()
        monthly_spending['month_number'] = monthly_spending['month_name'].apply(lambda x: MONTHS.index(x) + 1)
        monthly_spending = monthly_spending.sort_values('month_number')
        
        if not monthly_spending.empty and monthly_spending['actual'].sum() > 0:
            fig = px.line(
                monthly_spending,
                x='month_name',
                y='actual',
                title='Monthly Spending Throughout the Year',
                markers=True,
                labels={'actual': 'Amount Spent ($)', 'month_name': 'Month'},
                color_discrete_sequence=[BUDGET_COLOR]
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No spending data available for the trend chart.")
        
        st.markdown("---")
        
        # Two columns for additional charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.subheader("Annual Spending by Category")
            category_spending = df[df['category'] != 'Income'].groupby('category')['actual'].sum().reset_index()
            category_spending = category_spending[category_spending['actual'] > 0].sort_values('actual', ascending=True)
            
            if not category_spending.empty:
                fig = px.bar(
                    category_spending,
                    x='actual',
                    y='category',
                    orientation='h',
                    title='Total Spending by Category',
                    labels={'actual': 'Amount ($)', 'category': 'Category'},
                    color='category',
                    color_discrete_sequence=COLOR_PALETTE
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No spending data available by category.")
        
        with chart_col2:
            st.subheader("Budget vs Actual by Month")
            monthly_comparison = df[df['category'] != 'Income'].groupby('month_name').agg({
                'budgeted': 'sum',
                'actual': 'sum'
            }).reset_index()
            monthly_comparison['month_number'] = monthly_comparison['month_name'].apply(lambda x: MONTHS.index(x) + 1)
            monthly_comparison = monthly_comparison.sort_values('month_number')
            
            if not monthly_comparison.empty and (monthly_comparison['budgeted'].sum() > 0 or monthly_comparison['actual'].sum() > 0):
                monthly_comparison = monthly_comparison.melt(
                    id_vars=['month_name'],
                    value_vars=['budgeted', 'actual'],
                    var_name='type',
                    value_name='amount'
                )
                
                fig = px.bar(
                    monthly_comparison,
                    x='month_name',
                    y='amount',
                    color='type',
                    title='Monthly Budget vs Actual Spending',
                    labels={'amount': 'Amount ($)', 'month_name': 'Month', 'type': 'Type'},
                    barmode='group',
                    color_discrete_map={'budgeted': BUDGET_COLOR, 'actual': ACTUAL_COLOR}
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No budget or spending data available for comparison.")
        
        st.markdown("---")
        
        # Savings rate over time
        st.subheader("Savings Rate Trend")
        monthly_savings = []
        
        for month_name in MONTHS:
            month_data = df[df['month_name'] == month_name]
            month_income = float(month_data[month_data['category'] == 'Income']['actual'].sum()) if not month_data[month_data['category'] == 'Income'].empty else 0.0
            month_spent = float(month_data[month_data['category'] != 'Income']['actual'].sum())
            month_savings_rate = ((month_income - month_spent) / month_income * 100) if month_income > 0 else 0.0
            
            monthly_savings.append({
                'month_name': month_name,
                'month_number': MONTHS.index(month_name) + 1,
                'savings_rate': month_savings_rate
            })
        
        savings_df = pd.DataFrame(monthly_savings)
        
        if savings_df['savings_rate'].sum() > 0 or any(sr < 0 for sr in savings_df['savings_rate']):
            fig = px.line(
                savings_df,
                x='month_name',
                y='savings_rate',
                title='Monthly Savings Rate (%)',
                markers=True,
                labels={'savings_rate': 'Savings Rate (%)', 'month_name': 'Month'},
                color_discrete_sequence=[SAVINGS_COLOR]
            )
            fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break-even")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No savings rate data available.")
        
        st.markdown("---")
        
        # Top spending categories
        st.subheader("Top Spending Categories")
        if not category_spending.empty:
            top_categories = category_spending.tail(5)  # Top 5
            for _, row in top_categories.iterrows():
                percentage = (row['actual'] / total_spent * 100) if total_spent > 0 else 0
                st.metric(
                    row['category'],
                    f"${row['actual']:,.2f}",
                    f"{percentage:.1f}% of total spending"
                )
        else:
            st.info("No spending data available.")
        
        st.markdown("---")
        
        # Detailed monthly breakdown table
        st.subheader("Monthly Breakdown")
        monthly_summary = df.groupby('month_name').agg({
            'budgeted': 'sum',
            'actual': 'sum'
        }).reset_index()
        monthly_summary['month_number'] = monthly_summary['month_name'].apply(lambda x: MONTHS.index(x) + 1)
        monthly_summary = monthly_summary.sort_values('month_number')
        monthly_summary['difference'] = monthly_summary['budgeted'] - monthly_summary['actual']
        monthly_summary = monthly_summary[['month_name', 'budgeted', 'actual', 'difference']]
        monthly_summary.columns = ['Month', 'Budgeted', 'Actual', 'Difference']
        
        st.dataframe(
            monthly_summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Budgeted": st.column_config.NumberColumn("Budgeted ($)", format="%.2f"),
                "Actual": st.column_config.NumberColumn("Actual ($)", format="%.2f"),
                "Difference": st.column_config.NumberColumn("Difference ($)", format="%.2f")
            }
        )

elif menu == "AI Advisor":
    st.title("🤖 AI Financial Advisor")
    st.markdown("Get personalized financial advice based on your budget data.")

    # Select month for advice
    advice_month = st.selectbox("Select Month", MONTHS, index=datetime.now().month - 1, key="ai_advisor_month_select")

    # Get budget data for the selected month and year
    month_id = get_month_id(advice_month)
    df = db_utils.get_month_budget(month_id, selected_year)

    if not df.empty:
        # Calculate summary
        summary = calculate_summary(df)

        # Display current budget summary
        st.subheader(f"Budget Summary for {advice_month} {selected_year}")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Budgeted", f"${summary['total_budgeted']:,.2f}")
        col2.metric("Total Spent", f"${summary['total_actual']:,.2f}")
        col3.metric("Difference", f"${summary['difference']:,.2f}")
        col4.metric("Savings Rate", f"{summary['savings_rate']:.1f}%")

        st.markdown("---")

        # Get AI advice button
        if st.button("💡 Get AI Financial Advice", key="get_ai_advice"):
            with st.spinner("Analyzing your budget..."):
                advice = get_ai_financial_advice(summary, advice_month, selected_year)
                st.success("Here's your personalized advice:")

                # Display advice in a nice format
                formatted_advice = advice.replace('\n', '<br>')
                st.markdown(f"""
                <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #667eea;'>
                    {formatted_advice}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning(f"No budget data found for {advice_month} {selected_year}. Please add budget data first to get AI advice.")

elif menu == "Settings":
    st.title("Settings")
    
    st.subheader("Database Configuration")
    st.code("""
    DB_HOST=localhost
    DB_USER=root
    DB_PASSWORD=yourpassword
    DB_NAME=budget_tracker
    """, language="ini")
    
    st.info("Update the .env file in the project directory to change database settings.")
    
    st.subheader("Export Data")
    st.button("Export to CSV", key="export_csv")
    st.button("Export to Excel", key="export_excel")
    
    st.subheader("Import Data")
    st.file_uploader("Upload Budget Data", type=["csv", "xlsx"])

# Add some custom CSS
st.markdown("""
<style>
    .stDataFrame {
        max-height: 600px;
        overflow-y: auto;
    }
    .stMetric {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    h1 {
        color: #667eea;
    }
    h2, h3 {
        color: #764ba2;
    }
</style>
""", unsafe_allow_html=True)
