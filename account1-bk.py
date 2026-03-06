import streamlit as st
import pandas as pd
import os
from datetime import date

DATA_FILE = "transactions.csv"

st.set_page_config(page_title="Small Business Accounting", layout="wide")

# Load or create data
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["Date","Type","Category","Description","Amount"])

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard","Add Transaction","Transactions"])

# Dashboard
if page == "Dashboard":

    st.title("📊 Small Business Accounting Dashboard")

    if df.empty:
        st.warning("No transactions yet.")
    else:
        df["Amount"] = df["Amount"].astype(float)

        income = df[df["Type"]=="Income"]["Amount"].sum()
        expenses = df[df["Type"]=="Expense"]["Amount"].sum()
        profit = income - expenses

        col1,col2,col3 = st.columns(3)

        col1.metric("Total Income", f"${income:,.2f}")
        col2.metric("Total Expenses", f"${expenses:,.2f}")
        col3.metric("Net Profit", f"${profit:,.2f}")

        st.subheader("Recent Transactions")
        st.dataframe(df.tail(10), use_container_width=True)

        # Category summary
        st.subheader("Expenses by Category")
        exp = df[df["Type"]=="Expense"]

        if not exp.empty:
            summary = exp.groupby("Category")["Amount"].sum()
            st.bar_chart(summary)

# Add transaction
elif page == "Add Transaction":

    st.title("➕ Add Transaction")

    with st.form("transaction_form"):

        t_date = st.date_input("Date", date.today())

        t_type = st.selectbox("Type",["Income","Expense"])

        category = st.text_input("Category")

        description = st.text_input("Description")

        amount = st.number_input("Amount", min_value=0.0, format="%.2f")

        submitted = st.form_submit_button("Save")

        if submitted:

            new_data = {
                "Date":t_date,
                "Type":t_type,
                "Category":category,
                "Description":description,
                "Amount":amount
            }

            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)

            df.to_csv(DATA_FILE, index=False)

            st.success("Transaction saved!")

# Transactions table
elif page == "Transactions":

    st.title("📋 All Transactions")

    if df.empty:
        st.info("No transactions available.")
    else:
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False)

        st.download_button(
            "Download CSV",
            csv,
            "transactions.csv",
            "text/csv"
        )
