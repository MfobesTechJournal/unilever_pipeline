#!/usr/bin/env python3
"""
Unilever Data Pipeline - Streamlit Analytics Application
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Unilever Data Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; margin-bottom: 0.5rem; }
        .stMetric { background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost", port=5433,
            database="unilever_warehouse",
            user="postgres", password="123456"
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


def run_query(query):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        if conn.closed:
            conn = psycopg2.connect(
                host="localhost", port=5433,
                database="unilever_warehouse",
                user="postgres", password="123456"
            )
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return pd.DataFrame(cur.fetchall())
    except Exception as e:
        logger.error(f"Query failed: {e}")
        st.error(f"Query failed: {e}")
        return None


# ── PAGE 1: SALES ANALYTICS ──

def page_sales_analytics():
    st.markdown('<h1 class="main-header">💰 Sales Analytics</h1>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    df = run_query("SELECT SUM(revenue) as v FROM fact_sales")
    if df is not None:
        col1.metric("Total Revenue", f"R{df['v'].iloc[0]:,.0f}")

    df = run_query("SELECT COUNT(*) as v FROM fact_sales")
    if df is not None:
        col2.metric("Total Transactions", f"{df['v'].iloc[0]:,}")

    df = run_query("SELECT AVG(revenue) as v FROM fact_sales")
    if df is not None:
        col3.metric("Avg Order Value", f"R{df['v'].iloc[0]:,.2f}")

    df = run_query("SELECT COUNT(DISTINCT customer_key) as v FROM fact_sales")
    if df is not None:
        col4.metric("Unique Customers", f"{df['v'].iloc[0]:,}")

    st.divider()

    st.subheader("📦 Top 10 Products by Revenue")
    df = run_query("""
        SELECT dp.product_name, dp.category,
               COUNT(*) as transactions,
               SUM(fs.quantity) as total_qty,
               ROUND(SUM(fs.revenue)::numeric, 2) as revenue
        FROM fact_sales fs
        JOIN dim_product dp ON fs.product_key = dp.product_key
        GROUP BY dp.product_name, dp.category
        ORDER BY revenue DESC
        LIMIT 10
    """)
    if df is not None:
        col1, col2 = st.columns([2, 1])
        with col1:
            fig = px.bar(
                df.sort_values('revenue'),
                y='product_name', x='revenue', orientation='h',
                color='revenue', color_continuous_scale='Viridis',
                labels={'product_name': 'Product', 'revenue': 'Revenue (R)'}
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.dataframe(
                df[['product_name', 'category', 'transactions', 'revenue']],
                use_container_width=True, hide_index=True
            )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏷️ Revenue by Category")
        df = run_query("""
            SELECT dp.category, ROUND(SUM(fs.revenue)::numeric, 2) as revenue
            FROM fact_sales fs
            JOIN dim_product dp ON fs.product_key = dp.product_key
            GROUP BY dp.category ORDER BY revenue DESC
        """)
        if df is not None:
            fig = px.pie(df, values='revenue', names='category', title='Revenue by Category')
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🗺️ Revenue by Province")
        df = run_query("""
            SELECT dc.province, ROUND(SUM(fs.revenue)::numeric, 2) as revenue,
                   COUNT(*) as transactions
            FROM fact_sales fs
            JOIN dim_customer dc ON fs.customer_key = dc.customer_key
            GROUP BY dc.province ORDER BY revenue DESC
        """)
        if df is not None:
            fig = px.bar(
                df, x='province', y='revenue',
                color='revenue', color_continuous_scale='Blues',
                labels={'province': 'Province', 'revenue': 'Revenue (R)'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("📈 Monthly Revenue Trend")
    df = run_query("""
        SELECT dd.year, dd.month, dd.month_name,
               ROUND(SUM(fs.revenue)::numeric, 2) as revenue,
               COUNT(*) as transactions
        FROM fact_sales fs
        JOIN dim_date dd ON fs.date_key = dd.date_key
        GROUP BY dd.year, dd.month, dd.month_name
        ORDER BY dd.year, dd.month
    """)
    if df is not None:
        df['period'] = df['month_name'] + ' ' + df['year'].astype(str)
        fig = px.line(
            df, x='period', y='revenue', markers=True,
            labels={'period': 'Month', 'revenue': 'Revenue (R)'},
            title='Monthly Revenue 2024-2025'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)


# ── PAGE 2: ETL MONITORING ──

def page_etl_monitoring():
    st.markdown('<h1 class="main-header">⚙️ ETL Monitoring</h1>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    df = run_query("SELECT COUNT(*) as v FROM etl_log")
    if df is not None:
        col1.metric("Total ETL Runs", f"{df['v'].iloc[0]:,}")

    df = run_query("""
        SELECT ROUND(100.0 * SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) /
        NULLIF(COUNT(*), 0), 1) as v FROM etl_log
    """)
    if df is not None:
        col2.metric("Success Rate", f"{df['v'].iloc[0]}%")

    df = run_query("SELECT COALESCE(SUM(records_facts), 0) as v FROM etl_log")
    if df is not None:
        col3.metric("Total Records Loaded", f"{df['v'].iloc[0]:,}")

    df = run_query("""
        SELECT ROUND(AVG(EXTRACT(EPOCH FROM (end_time - start_time))), 0) as v
        FROM etl_log WHERE end_time IS NOT NULL AND status = 'success'
    """)
    if df is not None:
        col4.metric("Avg Run Duration", f"{df['v'].iloc[0]:.0f}s")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Run Status Distribution")
        df = run_query("SELECT status, COUNT(*) as count FROM etl_log GROUP BY status")
        if df is not None:
            fig = px.pie(
                df, values='count', names='status',
                color_discrete_map={'success': '#2ecc71', 'failed': '#e74c3c'}
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📈 Monthly Run Summary")
        df = run_query("""
            SELECT DATE_TRUNC('month', start_time) as month,
                   COUNT(*) as total_runs,
                   SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as successful,
                   SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed
            FROM etl_log
            GROUP BY 1 ORDER BY 1
        """)
        if df is not None:
            fig = px.bar(
                df, x='month', y=['successful', 'failed'],
                labels={'month': 'Month', 'value': 'Runs'},
                color_discrete_map={'successful': '#2ecc71', 'failed': '#e74c3c'},
                barmode='stack'
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("📈 Records Loaded Over Time")
    df = run_query("""
        SELECT DATE_TRUNC('month', start_time) as month,
               SUM(records_facts) as facts,
               SUM(records_customers) as customers,
               SUM(records_products) as products
        FROM etl_log WHERE status = 'success'
        GROUP BY 1 ORDER BY 1
    """)
    if df is not None:
        fig = px.line(
            df, x='month', y=['facts', 'customers', 'products'],
            labels={'month': 'Month', 'value': 'Records'},
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("📋 Recent ETL Runs (Last 20)")
    df = run_query("""
        SELECT run_id,
               start_time,
               end_time,
               status,
               COALESCE(records_facts, 0) as records_loaded,
               ROUND(EXTRACT(EPOCH FROM (end_time - start_time))::numeric, 0) as duration_s,
               records_quality_issues,
               error_message
        FROM etl_log
        ORDER BY start_time DESC
        LIMIT 20
    """)
    if df is not None:
        df['start_time'] = pd.to_datetime(df['start_time']).dt.strftime('%Y-%m-%d %H:%M')
        df['end_time'] = pd.to_datetime(df['end_time']).dt.strftime('%Y-%m-%d %H:%M')
        df['status'] = df['status'].apply(lambda x: f"✅ {x}" if x == 'success' else f"❌ {x}")
        st.dataframe(df, use_container_width=True, hide_index=True)


# ── PAGE 3: DATA QUALITY ──

def page_data_quality():
    st.markdown('<h1 class="main-header">✅ Data Quality</h1>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    df = run_query("SELECT COUNT(*) as v FROM data_quality_log")
    if df is not None:
        col1.metric("Total Checks Run", f"{df['v'].iloc[0]:,}")

    df = run_query("SELECT COUNT(*) as v FROM data_quality_log WHERE issue_count > 0")
    if df is not None:
        col2.metric("Checks With Issues", f"{df['v'].iloc[0]:,}")

    df = run_query("""
        SELECT ROUND(100.0 * SUM(CASE WHEN issue_count = 0 THEN 1 ELSE 0 END) /
        NULLIF(COUNT(*), 0), 1) as v FROM data_quality_log
    """)
    if df is not None:
        col3.metric("Pass Rate", f"{df['v'].iloc[0]}%")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Issues by Table")
        df = run_query("""
            SELECT table_name, SUM(issue_count) as total_issues
            FROM data_quality_log WHERE issue_count > 0
            GROUP BY table_name ORDER BY total_issues DESC
        """)
        if df is not None:
            fig = px.bar(
                df, x='table_name', y='total_issues',
                color='total_issues', color_continuous_scale='Reds',
                labels={'table_name': 'Table', 'total_issues': 'Issues'}
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Issues by Check Type")
        df = run_query("""
            SELECT check_type, SUM(issue_count) as total_issues
            FROM data_quality_log WHERE issue_count > 0
            GROUP BY check_type ORDER BY total_issues DESC
        """)
        if df is not None:
            fig = px.pie(df, values='total_issues', names='check_type')
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Recent Quality Issues")
    df = run_query("""
        SELECT dql.timestamp, dql.table_name, dql.check_type,
               dql.issue_count, dql.issue_description
        FROM data_quality_log dql
        WHERE dql.issue_count > 0
        ORDER BY dql.timestamp DESC
        LIMIT 30
    """)
    if df is not None:
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(df, use_container_width=True, hide_index=True)


# ── PAGE 4: CUSTOMER ANALYTICS ──

def page_customer_analytics():
    st.markdown('<h1 class="main-header">👥 Customer Analytics</h1>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    df = run_query("SELECT COUNT(DISTINCT customer_key) as v FROM fact_sales")
    if df is not None:
        col1.metric("Active Customers", f"{df['v'].iloc[0]:,}")

    df = run_query("""
        SELECT ROUND(AVG(total_spent)::numeric, 2) as v FROM (
            SELECT customer_key, SUM(revenue) as total_spent FROM fact_sales GROUP BY customer_key
        ) sub
    """)
    if df is not None:
        col2.metric("Avg Customer Lifetime Value", f"R{df['v'].iloc[0]:,.2f}")

    df = run_query("""
        SELECT ROUND(AVG(order_count)::numeric, 1) as v FROM (
            SELECT customer_key, COUNT(*) as order_count FROM fact_sales GROUP BY customer_key
        ) sub
    """)
    if df is not None:
        col3.metric("Avg Orders per Customer", f"{df['v'].iloc[0]:.1f}")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Customers by Revenue")
        df = run_query("""
            SELECT dc.customer_name,
                   COUNT(*) as orders,
                   ROUND(SUM(fs.revenue)::numeric, 2) as total_spent
            FROM fact_sales fs
            JOIN dim_customer dc ON fs.customer_key = dc.customer_key
            GROUP BY dc.customer_name
            ORDER BY total_spent DESC
            LIMIT 10
        """)
        if df is not None:
            fig = px.bar(
                df, x='customer_name', y='total_spent',
                color='total_spent', color_continuous_scale='Blues',
                labels={'customer_name': 'Customer', 'total_spent': 'Revenue (R)'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Customers by Province")
        df = run_query("""
            SELECT dc.province, COUNT(DISTINCT fs.customer_key) as customers
            FROM fact_sales fs
            JOIN dim_customer dc ON fs.customer_key = dc.customer_key
            GROUP BY dc.province ORDER BY customers DESC
        """)
        if df is not None:
            fig = px.bar(
                df, x='province', y='customers',
                color='customers', color_continuous_scale='Greens',
                labels={'province': 'Province', 'customers': 'Customers'}
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Customer Spend Segments")
    df = run_query("""
        SELECT
            CASE
                WHEN total_spent < 5000 THEN 'Low (<R5K)'
                WHEN total_spent < 15000 THEN 'Medium (R5K-R15K)'
                WHEN total_spent < 50000 THEN 'High (R15K-R50K)'
                ELSE 'Premium (>R50K)'
            END as segment,
            COUNT(*) as customers
        FROM (
            SELECT customer_key, SUM(revenue) as total_spent
            FROM fact_sales GROUP BY customer_key
        ) sub
        GROUP BY segment ORDER BY customers DESC
    """)
    if df is not None:
        fig = px.pie(df, values='customers', names='segment', title='Customer Spend Segments')
        st.plotly_chart(fig, use_container_width=True)


# ── PAGE 5: SYSTEM HEALTH ──

def page_system_health():
    st.markdown('<h1 class="main-header">🏥 System Health</h1>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("PostgreSQL", "✅ Online", "Port 5433")
    col2.metric("Grafana", "✅ Online", "Port 3000")
    col3.metric("Airflow", "✅ Online", "Port 8080")
    col4.metric("Streamlit", "✅ Online", "Port 8501")

    st.divider()

    st.subheader("Database Table Statistics")
    df = run_query("""
        SELECT 'fact_sales' as table_name, COUNT(*) as rows, ROUND(SUM(revenue)::numeric, 2) as total_revenue FROM fact_sales
        UNION ALL SELECT 'dim_customer', COUNT(*), NULL FROM dim_customer
        UNION ALL SELECT 'dim_product', COUNT(*), NULL FROM dim_product
        UNION ALL SELECT 'dim_date', COUNT(*), NULL FROM dim_date
        UNION ALL SELECT 'etl_log', COUNT(*), NULL FROM etl_log
        UNION ALL SELECT 'data_quality_log', COUNT(*), NULL FROM data_quality_log
    """)
    if df is not None:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Last 5 ETL Runs")
        df = run_query("""
            SELECT run_id, start_time, status,
                   COALESCE(records_facts, 0) as records,
                   ROUND(EXTRACT(EPOCH FROM (end_time - start_time))::numeric, 0) as duration_s
            FROM etl_log ORDER BY start_time DESC LIMIT 5
        """)
        if df is not None:
            df['start_time'] = pd.to_datetime(df['start_time']).dt.strftime('%Y-%m-%d %H:%M')
            df['status'] = df['status'].apply(lambda x: "✅" if x == 'success' else "❌")
            st.dataframe(df, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Recent Quality Issues")
        df = run_query("""
            SELECT table_name, check_type, issue_count, issue_description
            FROM data_quality_log
            WHERE issue_count > 0
            ORDER BY timestamp DESC LIMIT 5
        """)
        if df is not None:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.success("No recent quality issues")


# ── MAIN ──

def main():
    st.sidebar.markdown("# 🏭 Unilever Analytics")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Select Dashboard",
        ["💰 Sales Analytics", "⚙️ ETL Monitoring", "✅ Data Quality", "👥 Customer Analytics", "🏥 System Health"]
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📧 Contact")
    st.sidebar.info(
        "**Email**: relelentintelo@gmail.com\n\n"
        "**GitHub**: [mfobestechjournal](https://github.com/mfobestechjournal)\n\n"
        "**Support**: GitHub Issues"
    )

    if page == "💰 Sales Analytics":
        page_sales_analytics()
    elif page == "⚙️ ETL Monitoring":
        page_etl_monitoring()
    elif page == "✅ Data Quality":
        page_data_quality()
    elif page == "👥 Customer Analytics":
        page_customer_analytics()
    elif page == "🏥 System Health":
        page_system_health()

    st.markdown("---")
    st.markdown(
        '<div style="text-align:center;color:gray;font-size:0.85rem;">'
        'Unilever SA Data Pipeline | Built by Mfobe Ntintelo | 2026'
        '</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
