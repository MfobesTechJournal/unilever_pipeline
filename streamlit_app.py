import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from psycopg2.extras import RealDictCursor

st.set_page_config(
    page_title="Unilever Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_db_connection():
    try:
        url = st.secrets["database"]["url"]
        return psycopg2.connect(url, connect_timeout=30)
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


def execute_query(query):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        if conn.closed:
            st.cache_resource.clear()
            conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return pd.DataFrame(cur.fetchall())
    except Exception as e:
        st.error(f"Query failed: {e}")
        return None


# ── HOME ──
def page_home():
    st.title("Unilever Analytics Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    df = execute_query("SELECT COALESCE(SUM(revenue),0) as value FROM fact_sales")
    if df is not None:
        col1.metric("Total Revenue", f"R{df['value'].iloc[0]:,.2f}")

    df = execute_query("SELECT COUNT(*) as value FROM fact_sales")
    if df is not None:
        col2.metric("Transactions", f"{df['value'].iloc[0]:,}")

    df = execute_query("SELECT COUNT(DISTINCT customer_key) as value FROM fact_sales")
    if df is not None:
        col3.metric("Unique Customers", f"{df['value'].iloc[0]:,}")

    df = execute_query("SELECT COUNT(DISTINCT product_key) as value FROM fact_sales")
    if df is not None:
        col4.metric("Products Sold", f"{df['value'].iloc[0]:,}")

    st.divider()

    st.subheader("Monthly Revenue Trend")
    df = execute_query("""
        SELECT dd.year, dd.month, dd.month_name,
               ROUND(SUM(fs.revenue)::numeric, 2) as revenue
        FROM fact_sales fs
        JOIN dim_date dd ON fs.date_key = dd.date_key
        GROUP BY dd.year, dd.month, dd.month_name
        ORDER BY dd.year, dd.month
    """)
    if df is not None:
        df['period'] = df['month_name'] + ' ' + df['year'].astype(str)
        fig = px.line(df, x='period', y='revenue', markers=True,
                      labels={'period': 'Month', 'revenue': 'Revenue (R)'})
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)


# ── SALES ──
def page_sales_analytics():
    st.header("Sales Analytics")

    col1, col2 = st.columns(2)

    with col1:
        df = execute_query("""
            SELECT dp.category, ROUND(SUM(fs.revenue)::numeric, 2) as total_revenue
            FROM fact_sales fs
            JOIN dim_product dp ON fs.product_key = dp.product_key
            GROUP BY dp.category ORDER BY total_revenue DESC
        """)
        if df is not None:
            fig = px.bar(df, x='category', y='total_revenue',
                         color='total_revenue', color_continuous_scale='Blues',
                         title='Revenue by Category',
                         labels={'category': 'Category', 'total_revenue': 'Revenue (R)'})
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        df = execute_query("""
            SELECT dp.category, ROUND(SUM(fs.revenue)::numeric, 2) as total_revenue
            FROM fact_sales fs
            JOIN dim_product dp ON fs.product_key = dp.product_key
            GROUP BY dp.category
        """)
        if df is not None:
            fig = px.pie(df, values='total_revenue', names='category',
                         title='Revenue Distribution')
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Revenue by Province")
    df = execute_query("""
        SELECT dc.province, ROUND(SUM(fs.revenue)::numeric, 2) as revenue,
               COUNT(*) as transactions
        FROM fact_sales fs
        JOIN dim_customer dc ON fs.customer_key = dc.customer_key
        GROUP BY dc.province ORDER BY revenue DESC
    """)
    if df is not None:
        fig = px.bar(df, x='province', y='revenue',
                     color='revenue', color_continuous_scale='Greens',
                     labels={'province': 'Province', 'revenue': 'Revenue (R)'})
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)


# ── CUSTOMER ──
def page_customer_insights():
    st.header("Customer Insights")

    col1, col2, col3 = st.columns(3)

    df = execute_query("SELECT COUNT(DISTINCT customer_key) as v FROM fact_sales")
    if df is not None:
        col1.metric("Active Customers", f"{df['v'].iloc[0]:,}")

    df = execute_query("""
        SELECT ROUND(AVG(total_spent)::numeric, 2) as v FROM (
            SELECT customer_key, SUM(revenue) as total_spent
            FROM fact_sales GROUP BY customer_key) sub
    """)
    if df is not None:
        col2.metric("Avg Customer Value", f"R{df['v'].iloc[0]:,.2f}")

    df = execute_query("""
        SELECT ROUND(AVG(order_count)::numeric, 1) as v FROM (
            SELECT customer_key, COUNT(*) as order_count
            FROM fact_sales GROUP BY customer_key) sub
    """)
    if df is not None:
        col3.metric("Avg Orders per Customer", f"{df['v'].iloc[0]:.1f}")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Customers")
        df = execute_query("""
            SELECT dc.customer_name,
                   COUNT(*) as orders,
                   ROUND(SUM(fs.revenue)::numeric, 2) as total_spent
            FROM fact_sales fs
            JOIN dim_customer dc ON fs.customer_key = dc.customer_key
            GROUP BY dc.customer_name
            ORDER BY total_spent DESC LIMIT 10
        """)
        if df is not None:
            fig = px.bar(df, x='customer_name', y='total_spent',
                         color='total_spent', color_continuous_scale='Blues',
                         labels={'customer_name': 'Customer', 'total_spent': 'Revenue (R)'})
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Customers by Province")
        df = execute_query("""
            SELECT dc.province, COUNT(DISTINCT fs.customer_key) as customers
            FROM fact_sales fs
            JOIN dim_customer dc ON fs.customer_key = dc.customer_key
            GROUP BY dc.province ORDER BY customers DESC
        """)
        if df is not None:
            fig = px.bar(df, x='province', y='customers',
                         color='customers', color_continuous_scale='Purples',
                         labels={'province': 'Province', 'customers': 'Customers'})
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)


# ── PRODUCT ──
def page_product_performance():
    st.header("Product Performance")

    df = execute_query("""
        SELECT dp.product_name, dp.category,
               SUM(fs.quantity) as units_sold,
               ROUND(SUM(fs.revenue)::numeric, 2) as total_revenue
        FROM fact_sales fs
        JOIN dim_product dp ON fs.product_key = dp.product_key
        GROUP BY dp.product_name, dp.category
        ORDER BY total_revenue DESC LIMIT 20
    """)

    if df is None or df.empty:
        st.warning("No product data available.")
        return

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            df.head(10).sort_values('total_revenue'),
            x='total_revenue', y='product_name', orientation='h',
            title='Top 10 Products by Revenue',
            color='total_revenue', color_continuous_scale='Viridis',
            labels={'total_revenue': 'Revenue (R)', 'product_name': 'Product'}
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            df.nlargest(10, 'units_sold').sort_values('units_sold'),
            x='units_sold', y='product_name', orientation='h',
            title='Top 10 Products by Units Sold',
            color='units_sold', color_continuous_scale='Oranges',
            labels={'units_sold': 'Units Sold', 'product_name': 'Product'}
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("All Products")
    st.dataframe(df, use_container_width=True, hide_index=True)


# ── ETL MONITORING ──
def page_etl_monitoring():
    st.header("ETL Monitoring")

    col1, col2, col3, col4 = st.columns(4)

    df = execute_query("SELECT COUNT(*) as v FROM etl_log")
    if df is not None:
        col1.metric("Total Runs", f"{df['v'].iloc[0]:,}")

    df = execute_query("""
        SELECT ROUND(100.0 * SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) /
        NULLIF(COUNT(*), 0), 1) as v FROM etl_log
    """)
    if df is not None:
        col2.metric("Success Rate", f"{df['v'].iloc[0]}%")

    df = execute_query("SELECT COALESCE(SUM(records_facts), 0) as v FROM etl_log")
    if df is not None:
        col3.metric("Total Records Loaded", f"{df['v'].iloc[0]:,}")

    df = execute_query("""
        SELECT ROUND(AVG(EXTRACT(EPOCH FROM (end_time - start_time)))::numeric, 0) as v
        FROM etl_log WHERE status = 'success'
    """)
    if df is not None:
        col4.metric("Avg Duration", f"{df['v'].iloc[0]:.0f}s")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        df = execute_query("SELECT status, COUNT(*) as count FROM etl_log GROUP BY status")
        if df is not None:
            fig = px.pie(df, values='count', names='status',
                         title='Run Status Distribution',
                         color_discrete_map={'success': '#2ecc71', 'failed': '#e74c3c'})
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        df = execute_query("""
            SELECT DATE_TRUNC('month', start_time) as month,
                   SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as successful,
                   SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed
            FROM etl_log GROUP BY 1 ORDER BY 1
        """)
        if df is not None:
            fig = px.bar(df, x='month', y=['successful', 'failed'],
                         title='Monthly Run Summary', barmode='stack',
                         color_discrete_map={'successful': '#2ecc71', 'failed': '#e74c3c'})
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent ETL Runs")
    df = execute_query("""
        SELECT run_id, start_time, end_time, status,
               COALESCE(records_facts, 0) as records_loaded,
               ROUND(EXTRACT(EPOCH FROM (end_time - start_time))::numeric, 0) as duration_s,
               error_message
        FROM etl_log ORDER BY start_time DESC LIMIT 20
    """)
    if df is not None:
        df['start_time'] = pd.to_datetime(df['start_time']).dt.strftime('%Y-%m-%d %H:%M')
        df['end_time'] = pd.to_datetime(df['end_time']).dt.strftime('%Y-%m-%d %H:%M')
        df['status'] = df['status'].apply(lambda x: "✅ success" if x == 'success' else "❌ failed")
        st.dataframe(df, use_container_width=True, hide_index=True)


# ── SYSTEM HEALTH ──
def page_system_health():
    st.header("System Health")

    df = execute_query("SELECT 1 as status")
    if df is not None:
        st.success("Database connection healthy")
    else:
        st.error("Database not reachable")

    st.subheader("Table Row Counts")
    df = execute_query("""
        SELECT 'fact_sales' as table_name, COUNT(*) as rows FROM fact_sales
        UNION ALL SELECT 'dim_customer', COUNT(*) FROM dim_customer
        UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
        UNION ALL SELECT 'dim_date', COUNT(*) FROM dim_date
        UNION ALL SELECT 'etl_log', COUNT(*) FROM etl_log
        UNION ALL SELECT 'data_quality_log', COUNT(*) FROM data_quality_log
    """)
    if df is not None:
        st.dataframe(df, use_container_width=True, hide_index=True)


# ── MAIN ──
def main():
    st.sidebar.title("Unilever Analytics")
    st.sidebar.markdown("---")

    page = st.sidebar.radio("Navigation", [
        "Home",
        "Sales Analytics",
        "Customer Insights",
        "Product Performance",
        "ETL Monitoring",
        "System Health"
    ])

    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Email**: merelelentintelo@gmail.com\n\n"
        "**GitHub**: [mfobestechjournal](https://github.com/mfobestechjournal)"
    )

    if page == "Home":
        page_home()
    elif page == "Sales Analytics":
        page_sales_analytics()
    elif page == "Customer Insights":
        page_customer_insights()
    elif page == "Product Performance":
        page_product_performance()
    elif page == "ETL Monitoring":
        page_etl_monitoring()
    elif page == "System Health":
        page_system_health()

    st.markdown("---")
    st.markdown(
        '<div style="text-align:center;color:gray;font-size:0.85rem;">'
        'Unilever SA Data Pipeline | Mfobe Ntintelo | 2026'
        '</div>', unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
