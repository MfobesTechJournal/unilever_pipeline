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

REQUIRED_ENV_VARS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]

missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing:
    raise EnvironmentError(f"Missing required environment variables: {missing}")

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
    try:
        conn = psycopg2.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            database=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


@st.cache_data(ttl=300)
def execute_query(query):
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Query failed: {e}")
        return None
    finally:
        conn.close()

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

    query = """
    SELECT dp.category,
           SUM(fs.revenue) AS revenue,
           COUNT(*) AS transactions
    FROM fact_sales fs
    JOIN dim_product dp ON fs.product_key = dp.product_key
    GROUP BY dp.category
    ORDER BY revenue DESC
    """

    df = execute_query(query)

    if df is not None and not df.empty:
        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(df, x="category", y="revenue", title="Revenue by Category")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.pie(df, values="revenue", names="category", title="Revenue Distribution")
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df)
    else:
        st.warning("No sales data available.")

# ==================== CUSTOMER ====================

def page_customers():
    st.header("Customer Insights")

    query = """
    SELECT dc.customer_type,
           COUNT(DISTINCT dc.customer_key) AS customers,
           SUM(fs.revenue) AS revenue
    FROM fact_sales fs
    JOIN dim_customer dc ON fs.customer_key = dc.customer_key
    WHERE dc.is_current = true
    GROUP BY dc.customer_type
    ORDER BY revenue DESC
    """

    df = execute_query(query)

    if df is not None and not df.empty:
        fig = px.bar(df, x="customer_type", y="revenue", title="Revenue by Segment")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df)
    else:
        st.warning("No customer data available.")

# ==================== PRODUCT ====================

def page_products():
    st.header("Product Performance")

    query = """
    SELECT dp.product_name,
           SUM(fs.quantity) AS units_sold,
           SUM(fs.revenue) AS revenue
    FROM fact_sales fs
    JOIN dim_product dp ON fs.product_key = dp.product_key
    GROUP BY dp.product_name
    ORDER BY revenue DESC
    LIMIT 20
    """

    df = execute_query(query)

    if df is not None and not df.empty:
        col1, col2 = st.columns(2)

        with col1:
            top_revenue = df.head(10).sort_values("revenue")
            fig = px.bar(
                top_revenue,
                x="revenue",
                y="product_name",
                orientation="h",
                title="Top 10 by Revenue"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            top_units = df.nlargest(10, "units_sold").sort_values("units_sold")
            fig = px.bar(
                top_units,
                x="units_sold",
                y="product_name",
                orientation="h",
                title="Top 10 by Units Sold"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df)
    else:
        st.warning("No product data available.")

# ==================== SYSTEM ====================

def page_system():
    st.header("System Health")

    services = {
        "PostgreSQL": int(os.environ["DB_PORT"])
    }

    import socket

    for name, port in services.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex((os.environ["DB_HOST"], port))
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
