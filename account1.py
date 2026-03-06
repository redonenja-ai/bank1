import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import calendar
from accounting_database import (
    init_db,
    get_dashboard_stats,
    add_transaction,
    get_transactions,
    add_invoice,
    get_invoices,
    mark_invoice_paid,
    delete_transaction,
    delete_invoice,
    INCOME_CATEGORIES,
    EXPENSE_CATEGORIES,
)

# Page config
st.set_page_config(
    page_title="Small Business Accounting",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4e8df5;
        color: white;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize database
init_db()

# Sidebar navigation
st.sidebar.title("📊 Accounting App")
page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Income", "Expenses", "Invoices", "Reports"],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Stats")
stats = get_dashboard_stats()
st.sidebar.metric("Monthly Profit", f"${stats['month_profit']:,.2f}")
st.sidebar.metric("Outstanding", f"${stats['outstanding_invoices']:,.2f}")

# DASHBOARD
if page == "Dashboard":
    st.title("📈 Dashboard")

    stats = get_dashboard_stats()

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Revenue",
            value=f"${stats['total_revenue']:,.2f}",
            delta=f"${stats['month_revenue']:,.2f} this month",
        )

    with col2:
        st.metric(
            label="Total Expenses",
            value=f"${stats['total_expenses']:,.2f}",
            delta=f"${stats['month_expenses']:,.2f} this month",
            delta_color="inverse",
        )

    with col3:
        st.metric(
            label="Net Profit",
            value=f"${stats['profit']:,.2f}",
            delta=f"${stats['month_profit']:,.2f} this month",
        )

    with col4:
        st.metric(
            label="Outstanding Invoices",
            value=f"${stats['outstanding_invoices']:,.2f}",
            delta=f"{stats['overdue_count']} overdue"
            if stats["overdue_count"] > 0
            else None,
            delta_color="off" if stats["overdue_count"] == 0 else "inverse",
        )

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Monthly Trend")
        transactions = get_transactions()
        if transactions:
            df = pd.DataFrame(
                [
                    {"date": t.date, "type": t.type, "amount": t.amount}
                    for t in transactions
                ]
            )
            df["date"] = pd.to_datetime(df["date"])
            df["month"] = df["date"].dt.to_period("M")

            monthly = df.groupby(["month", "type"])["amount"].sum().reset_index()
            monthly["month"] = monthly["month"].astype(str)

            fig = px.line(
                monthly,
                x="month",
                y="amount",
                color="type",
                labels={"amount": "Amount ($)", "month": "Month"},
                color_discrete_map={"income": "#10B981", "expense": "#EF4444"},
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add some transactions to see the trend!")

    with col2:
        st.subheader("Income vs Expenses")
        if stats["total_revenue"] > 0 or stats["total_expenses"] > 0:
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=["Income", "Expenses"],
                        values=[stats["total_revenue"], stats["total_expenses"]],
                        hole=0.4,
                        marker_colors=["#10B981", "#EF4444"],
                    )
                ]
            )
            fig.update_layout(height=350, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet!")

    # Recent transactions
    st.markdown("---")
    st.subheader("Recent Transactions")
    recent = get_transactions()[:10]
    if recent:
        df_recent = pd.DataFrame(
            [
                {
                    "Date": t.date,
                    "Type": t.type.title(),
                    "Category": t.category,
                    "Amount": f"${t.amount:,.2f}",
                    "Description": t.description,
                }
                for t in recent
            ]
        )
        st.dataframe(df_recent, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions yet. Add some from the Income or Expenses tabs!")

# INCOME
elif page == "Income":
    st.title("💰 Income Tracking")

    tab1, tab2 = st.tabs(["Add Income", "View Income"])

    with tab1:
        st.subheader("Record New Income")
        with st.form("income_form"):
            col1, col2 = st.columns(2)
            with col1:
                date_input = st.date_input("Date", date.today())
                category = st.selectbox("Category", INCOME_CATEGORIES)
            with col2:
                amount = st.number_input(
                    "Amount ($)", min_value=0.0, step=0.01, format="%.2f"
                )
            description = st.text_input("Description (optional)")

            submitted = st.form_submit_button(
                "💾 Save Income", use_container_width=True
            )

            if submitted:
                if amount > 0:
                    add_transaction(
                        date_input.isoformat(), "income", category, amount, description
                    )
                    st.success(f"✅ Income of ${amount:,.2f} recorded!")
                    st.rerun()
                else:
                    st.error("Please enter an amount greater than 0")

    with tab2:
        st.subheader("Income History")
        income = get_transactions(type_="income")
        if income:
            df = pd.DataFrame(
                [
                    {
                        "ID": t.id,
                        "Date": t.date,
                        "Category": t.category,
                        "Amount": t.amount,
                        "Description": t.description,
                    }
                    for t in income
                ]
            )

            edited_df = st.data_editor(
                df,
                column_config={
                    "Amount": st.column_config.NumberColumn(
                        "Amount ($)", format="$%.2f"
                    ),
                },
                disabled=["ID"],
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
            )

            # Category breakdown
            st.subheader("Income by Category")
            cat_sum = df.groupby("Category")["Amount"].sum().reset_index()
            fig = px.bar(
                cat_sum,
                x="Category",
                y="Amount",
                labels={"Amount": "Total ($)"},
                color="Category",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No income recorded yet!")

# EXPENSES
elif page == "Expenses":
    st.title("💸 Expense Tracking")

    tab1, tab2 = st.tabs(["Add Expense", "View Expenses"])

    with tab1:
        st.subheader("Record New Expense")
        with st.form("expense_form"):
            col1, col2 = st.columns(2)
            with col1:
                date_input = st.date_input("Date", date.today())
                category = st.selectbox("Category", EXPENSE_CATEGORIES)
            with col2:
                amount = st.number_input(
                    "Amount ($)", min_value=0.0, step=0.01, format="%.2f"
                )
            description = st.text_input("Description (optional)")

            submitted = st.form_submit_button(
                "💾 Save Expense", use_container_width=True
            )

            if submitted:
                if amount > 0:
                    add_transaction(
                        date_input.isoformat(), "expense", category, amount, description
                    )
                    st.success(f"✅ Expense of ${amount:,.2f} recorded!")
                    st.rerun()
                else:
                    st.error("Please enter an amount greater than 0")

    with tab2:
        st.subheader("Expense History")
        expenses = get_transactions(type_="expense")
        if expenses:
            df = pd.DataFrame(
                [
                    {
                        "ID": t.id,
                        "Date": t.date,
                        "Category": t.category,
                        "Amount": t.amount,
                        "Description": t.description,
                    }
                    for t in expenses
                ]
            )

            edited_df = st.data_editor(
                df,
                column_config={
                    "Amount": st.column_config.NumberColumn(
                        "Amount ($)", format="$%.2f"
                    ),
                },
                disabled=["ID"],
                use_container_width=True,
                hide_index=True,
            )

            # Category breakdown
            st.subheader("Expenses by Category")
            cat_sum = df.groupby("Category")["Amount"].sum().reset_index()
            fig = px.pie(cat_sum, values="Amount", names="Category", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expenses recorded yet!")

# INVOICES
elif page == "Invoices":
    st.title("📄 Invoice Management")

    tab1, tab2 = st.tabs(["Create Invoice", "View Invoices"])

    with tab1:
        st.subheader("Create New Invoice")
        with st.form("invoice_form"):
            col1, col2 = st.columns(2)
            with col1:
                invoice_num = st.text_input(
                    "Invoice Number",
                    value=f"INV-{datetime.now().strftime('%Y%m%d')}-001",
                )
                client_name = st.text_input("Client Name")
                amount = st.number_input(
                    "Amount ($)", min_value=0.0, step=0.01, format="%.2f"
                )
            with col2:
                issue_date = st.date_input("Issue Date", date.today())
                due_date = st.date_input("Due Date", date.today())
            description = st.text_area(
                "Description/Notes", placeholder="Services rendered..."
            )

            submitted = st.form_submit_button(
                "💾 Create Invoice", use_container_width=True
            )

            if submitted:
                if client_name and amount > 0:
                    try:
                        add_invoice(
                            invoice_num,
                            client_name,
                            amount,
                            issue_date.isoformat(),
                            due_date.isoformat(),
                            description,
                        )
                        st.success(
                            f"✅ Invoice {invoice_num} created for ${amount:,.2f}!"
                        )
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}. Make sure invoice number is unique.")
                else:
                    st.error("Please enter client name and amount")

    with tab2:
        st.subheader("All Invoices")
        invoices = get_invoices()

        if invoices:
            col1, col2 = st.columns([3, 1])
            with col1:
                filter_status = st.selectbox(
                    "Filter", ["All", "Paid", "Unpaid", "Overdue"]
                )

            df = pd.DataFrame(
                [
                    {
                        "ID": inv.id,
                        "Invoice #": inv.invoice_number,
                        "Client": inv.client_name,
                        "Amount": inv.amount,
                        "Issue Date": inv.issue_date,
                        "Due Date": inv.due_date,
                        "Status": "Paid" if inv.paid else "Unpaid",
                        "Paid Date": inv.paid_date or "-",
                    }
                    for inv in invoices
                ]
            )

            # Apply filters
            today = date.today().isoformat()
            if filter_status == "Paid":
                df = df[df["Status"] == "Paid"]
            elif filter_status == "Unpaid":
                df = df[df["Status"] == "Unpaid"]
            elif filter_status == "Overdue":
                df = df[(df["Status"] == "Unpaid") & (df["Due Date"] < today)]

            st.dataframe(df, use_container_width=True, hide_index=True)

            # Mark as paid section
            st.markdown("---")
            st.subheader("Mark Invoice as Paid")
            unpaid_invs = [inv for inv in invoices if not inv.paid]
            if unpaid_invs:
                col1, col2 = st.columns([3, 1])
                with col1:
                    inv_to_pay = st.selectbox(
                        "Select invoice",
                        options=unpaid_invs,
                        format_func=lambda x: (
                            f"{x.invoice_number} - {x.client_name} (${x.amount:,.2f})"
                        ),
                    )
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("✅ Mark Paid", use_container_width=True):
                        mark_invoice_paid(inv_to_pay.id)
                        st.success(
                            f"Invoice {inv_to_pay.invoice_number} marked as paid!"
                        )
                        st.rerun()
            else:
                st.info("All invoices are paid! 🎉")
        else:
            st.info("No invoices created yet!")

# REPORTS
elif page == "Reports":
    st.title("📊 Reports & Analytics")

    report_type = st.selectbox(
        "Select Report",
        ["Profit & Loss Summary", "Category Breakdown", "Invoice Aging"],
    )

    if report_type == "Profit & Loss Summary":
        st.subheader("Profit & Loss Statement")
        transactions = get_transactions()
        if transactions:
            df = pd.DataFrame(
                [
                    {"date": t.date, "type": t.type, "amount": t.amount}
                    for t in transactions
                ]
            )
            df["date"] = pd.to_datetime(df["date"])
            df["month"] = df["date"].dt.to_period("M")

            summary = df.pivot_table(
                values="amount",
                index="month",
                columns="type",
                aggfunc="sum",
                fill_value=0,
            ).reset_index()
            summary["month"] = summary["month"].astype(str)
            if "income" not in summary.columns:
                summary["income"] = 0
            if "expense" not in summary.columns:
                summary["expense"] = 0
            summary["profit"] = summary["income"] - summary["expense"]

            st.dataframe(
                summary.rename(
                    columns={
                        "month": "Month",
                        "income": "Revenue",
                        "expense": "Expenses",
                        "profit": "Net Profit",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=summary["month"],
                    y=summary["income"],
                    name="Revenue",
                    marker_color="#10B981",
                )
            )
            fig.add_trace(
                go.Bar(
                    x=summary["month"],
                    y=summary["expense"],
                    name="Expenses",
                    marker_color="#EF4444",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=summary["month"],
                    y=summary["profit"],
                    name="Profit",
                    line=dict(color="#3B82F6", width=3),
                )
            )
            fig.update_layout(barmode="group", title="Monthly P&L", height=450)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data to report!")

    elif report_type == "Category Breakdown":
        st.subheader("Category Analysis")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Income by Category")
            income = get_transactions(type_="income")
            if income:
                df = pd.DataFrame(
                    [{"Category": t.category, "Amount": t.amount} for t in income]
                )
                cat_sum = df.groupby("Category")["Amount"].sum().reset_index()
                fig = px.bar(cat_sum, x="Category", y="Amount", color="Category")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No income data")

        with col2:
            st.markdown("#### Expenses by Category")
            expenses = get_transactions(type_="expense")
            if expenses:
                df = pd.DataFrame(
                    [{"Category": t.category, "Amount": t.amount} for t in expenses]
                )
                cat_sum = df.groupby("Category")["Amount"].sum().reset_index()
                fig = px.pie(cat_sum, values="Amount", names="Category", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No expense data")

    elif report_type == "Invoice Aging":
        st.subheader("Invoice Aging Report")
        invoices = get_invoices(paid=False)
        if invoices:
            today = date.today()
            aging_data = {
                "Current (0-30 days)": 0,
                "31-60 days": 0,
                "61-90 days": 0,
                "Over 90 days": 0,
            }

            for inv in invoices:
                due = datetime.strptime(inv.due_date, "%Y-%m-%d").date()
                days_overdue = (today - due).days

                if days_overdue <= 0:
                    aging_data["Current (0-30 days)"] += inv.amount
                elif days_overdue <= 30:
                    aging_data["Current (0-30 days)"] += inv.amount
                elif days_overdue <= 60:
                    aging_data["31-60 days"] += inv.amount
                elif days_overdue <= 90:
                    aging_data["61-90 days"] += inv.amount
                else:
                    aging_data["Over 90 days"] += inv.amount

            df_aging = pd.DataFrame(
                {
                    "Aging Bucket": list(aging_data.keys()),
                    "Amount": list(aging_data.values()),
                }
            )

            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(df_aging, use_container_width=True, hide_index=True)
            with col2:
                fig = px.bar(
                    df_aging,
                    x="Aging Bucket",
                    y="Amount",
                    color="Aging Bucket",
                    color_discrete_map={
                        "Current (0-30 days)": "#10B981",
                        "31-60 days": "#F59E0B",
                        "61-90 days": "#EF4444",
                        "Over 90 days": "#7C3AED",
                    },
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No outstanding invoices!")

st.sidebar.markdown("---")
st.sidebar.markdown("📅 " + date.today().strftime("%B %d, %Y"))
