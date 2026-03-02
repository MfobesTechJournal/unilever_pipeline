#!/usr/bin/env python3
"""
Streamlit Analytics Dashboard for Unilever Data Pipeline
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import os
from dotenv import load_dotenv

# ==================== LOAD ENV ====================

load_dotenv()

# Use defaults if env vars not set
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5433"))
DB_NAME = os.getenv("DB_NAME", "unilever_warehouse")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")

# ==================== PAGE CONFIG ====================

st.set_page_config(
    page_title="Unilever Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== DATABASE ====================

@st.cache_resource
def get_db_connection():
    """Get a persistent database connection."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        # Set autocommit to avoid connection issues
        conn.autocommit = True
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


def execute_query(query):
    """Execute a database query and return results as DataFrame."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Query failed: {e}")
        return None

# ==================== HOME ====================

def page_home():
    st.title("Unilever Data Pipeline Analytics")

    col1, col2, col3, col4 = st.columns(4)

    revenue = execute_query("SELECT SUM(revenue) AS total FROM fact_sales")
    transactions = execute_query("SELECT COUNT(*) AS total FROM fact_sales")
    customers = execute_query("SELECT COUNT(DISTINCT customer_key) AS total FROM fact_sales")
    products = execute_query("SELECT COUNT(DISTINCT product_key) AS total FROM fact_sales")

    if all(df is not None and not df.empty for df in [revenue, transactions, customers, products]):
        col1.metric("Total Revenue", f"${revenue.iloc[0]['total'] or 0:,.2f}")
        col2.metric("Transactions", f"{transactions.iloc[0]['total']:,}")
        col3.metric("Customers", f"{customers.iloc[0]['total']:,}")
        col4.metric("Products", f"{products.iloc[0]['total']:,}")
    else:
        st.warning("Unable to load summary metrics.")

# ==================== SALES ====================

def page_sales():
    st.header("Sales Analytics")

    # Revenue by category
    query_category = """
    SELECT dp.category,
           SUM(fs.revenue) AS revenue,
           COUNT(*) AS transactions,
           ROUND(AVG(fs.revenue), 2) AS avg_transaction
    FROM fact_sales fs
    JOIN dim_product dp ON fs.product_key = dp.product_key
    GROUP BY dp.category
    ORDER BY revenue DESC
    """

    df_category = execute_query(query_category)

    if df_category is not None and not df_category.empty:
        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(df_category, x="category", y="revenue", title="Revenue by Category")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.pie(df_category, values="revenue", names="category", title="Revenue Distribution")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Category Details")
        st.dataframe(df_category, use_container_width=True)
    else:
        st.warning("No sales data available.")

# ==================== CUSTOMER ====================

def page_customers():
    st.header("Customer Insights")

    query = """
    SELECT dc.province,
           COUNT(DISTINCT dc.customer_key) AS customers,
           SUM(fs.revenue) AS revenue,
           COUNT(*) AS transactions
    FROM fact_sales fs
    JOIN dim_customer dc ON fs.customer_key = dc.customer_key
    WHERE dc.is_current = true
    GROUP BY dc.province
    ORDER BY revenue DESC
    """

    df = execute_query(query)

    if df is not None and not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(df, x="province", y="revenue", title="Revenue by Province")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(df, values="revenue", names="province", title="Revenue Distribution by Province")
            st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No customer data available.")

# ==================== PRODUCT ====================

def page_products():
    st.header("Product Performance")

    query = """
    SELECT dp.product_name,
           dp.category,
           SUM(fs.quantity) AS units_sold,
           SUM(fs.revenue) AS revenue,
           ROUND(AVG(fs.revenue), 2) AS avg_sale
    FROM fact_sales fs
    JOIN dim_product dp ON fs.product_key = dp.product_key
    GROUP BY dp.product_key, dp.product_name, dp.category
    ORDER BY revenue DESC
    LIMIT 30
    """

    df = execute_query(query)

    if df is not None and not df.empty:
        col1, col2 = st.columns(2)

        with col1:
            top_revenue = df.head(10).sort_values("revenue", ascending=True)
            fig = px.bar(
                top_revenue,
                x="revenue",
                y="product_name",
                orientation="h",
                title="Top 10 Products by Revenue",
                color="revenue"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            top_units = df.nlargest(10, "units_sold")[['product_name', 'units_sold']].sort_values("units_sold", ascending=True)
            fig = px.bar(
                top_units,
                x="units_sold",
                y="product_name",
                orientation="h",
                title="Top 10 Products by Units Sold",
                color="units_sold"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Product Details")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No product data available.")

# ==================== SYSTEM ====================

def page_system():
    st.header("System Health")

    services = {
        "PostgreSQL": DB_PORT
    }

    import socket

    for name, port in services.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex((DB_HOST, port))
        s.close()
        status = "Running" if result == 0 else "Down"
        st.metric(name, status)

# ==================== MAIN ====================

def main():
    st.sidebar.title("Navigation")

    page = st.sidebar.radio(
        "Select Page",
        ["Home", "Sales", "Customers", "Products", "System"]
    )

    if page == "Home":
        page_home()
    elif page == "Sales":
        page_sales()
    elif page == "Customers":
        page_customers()
    elif page == "Products":
        page_products()
    elif page == "System":
        page_system()

if __name__ == "__main__":
    main()
