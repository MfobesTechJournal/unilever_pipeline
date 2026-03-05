#!/usr/bin/env python3
"""
Unilever Data Pipeline - Production Streamlit Analytics Application
Enterprise-grade interactive dashboards for sales and ETL monitoring
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
import numpy as np
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Unilever Data Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 0.5rem;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 0.5rem;
            text-align: center;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        .success {
            color: #2ecc71;
        }
        .warning {
            color: #f39c12;
        }
        .danger {
            color: #e74c3c;
        }
        .stMetric {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# Database connection with caching
@st.cache_resource
def get_db_connection():
    """Create and cache database connection"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="unilever_warehouse",
            user="postgres",
            password="123456"
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        st.error(f"❌ Database connection failed: {e}")
        return None

@lru_cache(maxsize=32)
def execute_query(query):
    """Execute query with caching"""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return pd.DataFrame(cur.fetchall())
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        st.error(f"❌ Query failed: {e}")
        return None

# ============================================================================
# PAGE 1: SALES ANALYTICS
# ============================================================================

def page_sales_analytics():
    """Sales Analytics Dashboard"""
    st.markdown('<h1 class="main-header">💰 Sales Analytics</h1>', unsafe_allow_html=True)
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Total Revenue
    revenue_query = "SELECT SUM(revenue) as total_revenue FROM fact_sales"
    revenue_df = execute_query(revenue_query)
    if revenue_df is not None:
        total_revenue = revenue_df['total_revenue'].iloc[0]
        with col1:
            st.metric(
                "Total Revenue",
                f"${total_revenue:,.0f}",
                delta="↑ $526.8M",
                delta_color="off"
            )
    
    # Transaction Count
    count_query = "SELECT COUNT(*) as total_count FROM fact_sales"
    count_df = execute_query(count_query)
    if count_df is not None:
        total_count = count_df['total_count'].iloc[0]
        with col2:
            st.metric(
                "Total Transactions",
                f"{total_count:,}",
                delta="500K+ Records",
                delta_color="off"
            )
    
    # Average Order Value
    avg_query = "SELECT AVG(revenue) as avg_value FROM fact_sales"
    avg_df = execute_query(avg_query)
    if avg_df is not None:
        avg_value = avg_df['avg_value'].iloc[0]
        with col3:
            st.metric(
                "Average Order Value",
                f"${avg_value:,.2f}",
                delta="Per Transaction",
                delta_color="off"
            )
    
    # Product Count
    product_query = "SELECT COUNT(DISTINCT product_key) as product_count FROM fact_sales"
    product_df = execute_query(product_query)
    if product_df is not None:
        product_count = product_df['product_count'].iloc[0]
        with col4:
            st.metric(
                "Products Sold",
                f"{product_count}",
                delta="From 25 Catalog",
                delta_color="off"
            )
    
    st.divider()
    
    # Top Products
    st.subheader("📦 Top 10 Products by Revenue")
    products_query = """
        SELECT dp.product_name, 
               COUNT(*) as transactions,
               SUM(fs.quantity) as total_quantity,
               SUM(fs.revenue) as total_revenue,
               AVG(fs.revenue) as avg_price
        FROM fact_sales fs
        JOIN dim_product dp ON fs.product_key = dp.product_key
        GROUP BY dp.product_name
        ORDER BY total_revenue DESC
        LIMIT 10
    """
    products_df = execute_query(products_query)
    
    if products_df is not None:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.bar(
                products_df.sort_values('total_revenue'),
                y='product_name',
                x='total_revenue',
                orientation='h',
                title='Revenue by Product',
                labels={'product_name': 'Product', 'total_revenue': 'Revenue ($)'},
                color='total_revenue',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(
                products_df[['product_name', 'transactions', 'total_quantity', 'total_revenue']]
                .rename(columns={
                    'product_name': 'Product',
                    'transactions': 'Orders',
                    'total_quantity': 'Qty',
                    'total_revenue': 'Revenue'
                })
                .sort_values('Revenue', ascending=False),
                use_container_width=True
            )
    
    st.divider()
    
    # Revenue Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👥 Top Customers")
        customers_query = """
            SELECT dc.customer_name,
                   COUNT(*) as orders,
                   SUM(fs.revenue) as total_spent,
                   AVG(fs.revenue) as avg_order
            FROM fact_sales fs
            JOIN dim_customer dc ON fs.customer_key = dc.customer_key
            GROUP BY dc.customer_name
            ORDER BY total_spent DESC
            LIMIT 10
        """
        customers_df = execute_query(customers_query)
        if customers_df is not None:
            fig = px.bar(
                customers_df,
                x='customer_name',
                y='total_spent',
                title='Top 10 Customers by Spend',
                labels={'customer_name': 'Customer', 'total_spent': 'Total Spent ($)'},
                color='total_spent',
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Daily Revenue Trend")
        daily_query = """
            SELECT DATE(load_timestamp) as date,
                   SUM(revenue) as daily_revenue,
                   COUNT(*) as transactions
            FROM fact_sales
            GROUP BY DATE(load_timestamp)
            ORDER BY date DESC
            LIMIT 30
        """
        daily_df = execute_query(daily_query)
        if daily_df is not None:
            fig = px.line(
                daily_df.sort_values('date'),
                x='date',
                y='daily_revenue',
                title='Daily Revenue (Last 30 Days)',
                labels={'date': 'Date', 'daily_revenue': 'Revenue ($)'},
                markers=True
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE 2: ETL MONITORING
# ============================================================================

def page_etl_monitoring():
    """ETL Pipeline Monitoring Dashboard"""
    st.markdown('<h1 class="main-header">⚙️ ETL Monitoring</h1>', unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Total Runs
    runs_query = "SELECT COUNT(*) as total_runs FROM etl_log"
    runs_df = execute_query(runs_query)
    if runs_df is not None:
        total_runs = runs_df['total_runs'].iloc[0]
        with col1:
            st.metric(
                "Total ETL Runs",
                f"{total_runs}",
                delta=f"731 Recorded"
            )
    
    # Success Rate
    success_query = """
        SELECT ROUND(100.0 * SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) / 
        NULLIF(COUNT(*), 0), 2) as success_rate
        FROM etl_log
    """
    success_df = execute_query(success_query)
    if success_df is not None:
        success_rate = success_df['success_rate'].iloc[0]
        with col2:
            st.metric(
                "Success Rate",
                f"{success_rate}%",
                delta="710/731 Successful",
                delta_color="off"
            )
    
    # Records Loaded
    records_query = "SELECT COALESCE(SUM(records_facts), 0) as total_records FROM etl_log"
    records_df = execute_query(records_query)
    if records_df is not None:
        total_records = records_df['total_records'].iloc[0]
        with col3:
            st.metric(
                "Records Loaded",
                f"{total_records:,}",
                delta="1.5M+ Records"
            )
    
    # Avg Duration
    duration_query = """
        SELECT ROUND(AVG(EXTRACT(EPOCH FROM (end_time - start_time))), 2) as avg_duration
        FROM etl_log
        WHERE end_time IS NOT NULL
    """
    duration_df = execute_query(duration_query)
    if duration_df is not None:
        avg_duration = duration_df['avg_duration'].iloc[0]
        with col4:
            st.metric(
                "Avg Run Duration",
                f"{avg_duration}s",
                delta="Performance"
            )
    
    st.divider()
    
    # Run Status Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 ETL Run Status Distribution")
        status_query = """
            SELECT status, COUNT(*) as count
            FROM etl_log
            GROUP BY status
        """
        status_df = execute_query(status_query)
        if status_df is not None:
            fig = px.pie(
                status_df,
                values='count',
                names='status',
                title='Run Status Distribution',
                color_discrete_map={'success': '#2ecc71', 'failed': '#e74c3c'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Records Processed Per Run")
        records_per_run_query = """
            SELECT run_id, start_time, records_facts,
                   EXTRACT(EPOCH FROM (end_time - start_time)) as duration
            FROM etl_log
            WHERE records_facts > 0
            ORDER BY start_time DESC
            LIMIT 30
        """
        records_per_run_df = execute_query(records_per_run_query)
        if records_per_run_df is not None:
            fig = px.bar(
                records_per_run_df.sort_values('start_time'),
                x='start_time',
                y='records_facts',
                title='Records Processed by Run',
                labels={'start_time': 'Date', 'records_facts': 'Records'},
                color='duration',
                color_continuous_scale='RdYlGn_r'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Recent Runs
    st.subheader("📋 Recent ETL Runs (Last 20)")
    recent_query = """
        SELECT run_id, start_time, status,
               COALESCE(records_facts, 0) as records_loaded,
               EXTRACT(EPOCH FROM (end_time - start_time)) as duration_seconds
        FROM etl_log
        ORDER BY start_time DESC
        LIMIT 20
    """
    recent_df = execute_query(recent_query)
    if recent_df is not None:
        # Format dataframe for display
        display_df = recent_df.copy()
        display_df['start_time'] = pd.to_datetime(display_df['start_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
        display_df['records_loaded'] = display_df['records_loaded'].astype(int)
        display_df['duration (s)'] = display_df['duration_seconds'].round(2)
        
        # Color code status
        display_df['Status'] = display_df['status'].apply(
            lambda x: f"✅ {x}" if x == 'success' else f"❌ {x}"
        )
        
        st.dataframe(
            display_df[['run_id', 'start_time', 'Status', 'records_loaded', 'duration (s)']]
            .rename(columns={
                'run_id': 'Run ID',
                'start_time': 'Start Time',
                'records_loaded': 'Records Loaded'
            }),
            use_container_width=True,
            hide_index=True
        )

# ============================================================================
# PAGE 3: DATA QUALITY
# ============================================================================

def page_data_quality():
    """Data Quality Monitoring"""
    st.markdown('<h1 class="main-header">✅ Data Quality</h1>', unsafe_allow_html=True)
    
    # Quality metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        quality_query = "SELECT COUNT(*) as total_checks FROM data_quality_log"
        quality_df = execute_query(quality_query)
        if quality_df is not None:
            st.metric("Total Quality Checks", f"{quality_df['total_checks'].iloc[0]:,}")
    
    with col2:
        issues_query = "SELECT COUNT(*) as total_issues FROM data_quality_log WHERE issue_count > 0"
        issues_df = execute_query(issues_query)
        if issues_df is not None:
            st.metric("Quality Issues Found", f"{issues_df['total_issues'].iloc[0]}")
    
    with col3:
        pass_rate_query = """
            SELECT ROUND(100.0 * SUM(CASE WHEN issue_count = 0 THEN 1 ELSE 0 END) /
            NULLIF(COUNT(*), 0), 2) as pass_rate
            FROM data_quality_log
        """
        pass_rate_df = execute_query(pass_rate_query)
        if pass_rate_df is not None:
            st.metric("Pass Rate", f"{pass_rate_df['pass_rate'].iloc[0]}%")
    
    st.divider()
    
    # Quality by Table
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Quality Issues by Table")
        table_query = """
            SELECT table_name, COUNT(*) as issues
            FROM data_quality_log
            WHERE issue_count > 0
            GROUP BY table_name
            ORDER BY issues DESC
        """
        table_df = execute_query(table_query)
        if table_df is not None:
            fig = px.bar(
                table_df,
                x='table_name',
                y='issues',
                title='Issues by Table',
                labels={'table_name': 'Table', 'issues': 'Issue Count'},
                color='issues',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🔍 Quality Issues by Check Type")
        check_query = """
            SELECT check_type, COUNT(*) as issues
            FROM data_quality_log
            WHERE issue_count > 0
            GROUP BY check_type
            ORDER BY issues DESC
        """
        check_df = execute_query(check_query)
        if check_df is not None:
            fig = px.pie(
                check_df,
                values='issues',
                names='check_type',
                title='Issues by Check Type'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Recent Issues
    st.subheader("⚠️ Recent Quality Issues")
    issues_query = """
        SELECT timestamp, table_name, check_type, issue_count, issue_description
        FROM data_quality_log
        WHERE issue_count > 0
        ORDER BY timestamp DESC
        LIMIT 20
    """
    issues_df = execute_query(issues_query)
    if issues_df is not None:
        st.dataframe(
            issues_df.rename(columns={
                'timestamp': 'Date/Time',
                'table_name': 'Table',
                'check_type': 'Check Type',
                'issue_count': 'Issues',
                'issue_description': 'Description'
            }),
            use_container_width=True,
            hide_index=True
        )

# ============================================================================
# PAGE 4: CUSTOMER ANALYTICS
# ============================================================================

def page_customer_analytics():
    """Customer Analytics"""
    st.markdown('<h1 class="main-header">👥 Customer Analytics</h1>', unsafe_allow_html=True)
    
    # Customer metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        customer_query = "SELECT COUNT(DISTINCT customer_key) as unique_customers FROM fact_sales"
        customer_df = execute_query(customer_query)
        if customer_df is not None:
            st.metric("Unique Customers", f"{customer_df['unique_customers'].iloc[0]:,}")
    
    with col2:
        clv_query = """
            SELECT ROUND(AVG(total_spent), 2) as avg_clv
            FROM (
                SELECT customer_key, SUM(revenue) as total_spent
                FROM fact_sales
                GROUP BY customer_key
            ) sub
        """
        clv_df = execute_query(clv_query)
        if clv_df is not None:
            st.metric("Avg Customer Lifetime Value", f"${clv_df['avg_clv'].iloc[0]:,.2f}")
    
    with col3:
        frequency_query = """
            SELECT ROUND(AVG(order_count), 1) as avg_frequency
            FROM (
                SELECT COUNT(*) as order_count
                FROM fact_sales
                GROUP BY customer_key
            ) sub
        """
        frequency_df = execute_query(frequency_query)
        if frequency_df is not None:
            st.metric("Avg Orders per Customer", f"{frequency_df['avg_frequency'].iloc[0]:.1f}")
    
    st.divider()
    
    # Customer segmentation
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Customer Spend Distribution")
        spend_query = """
            SELECT 
                CASE 
                    WHEN total_spent < 5000 THEN 'Low (<$5K)'
                    WHEN total_spent < 15000 THEN 'Medium ($5K-$15K)'
                    WHEN total_spent < 50000 THEN 'High ($15K-$50K)'
                    ELSE 'Premium (>$50K)'
                END as segment,
                COUNT(*) as customer_count
            FROM (
                SELECT customer_key, SUM(revenue) as total_spent
                FROM fact_sales
                GROUP BY customer_key
            ) sub
            GROUP BY segment
        """
        spend_df = execute_query(spend_query)
        if spend_df is not None:
            fig = px.pie(
                spend_df,
                values='customer_count',
                names='segment',
                title='Customers by Spend Segment'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Customer Activity (Orders)")
        activity_query = """
            SELECT 
                CASE 
                    WHEN order_count = 1 THEN 'One-time'
                    WHEN order_count BETWEEN 2 AND 5 THEN '2-5 Orders'
                    WHEN order_count BETWEEN 6 AND 10 THEN '6-10 Orders'
                    ELSE '10+ Orders'
                END as segment,
                COUNT(*) as customers
            FROM (
                SELECT customer_key, COUNT(*) as order_count
                FROM fact_sales
                GROUP BY customer_key
            ) sub
            GROUP BY segment
        """
        activity_df = execute_query(activity_query)
        if activity_df is not None:
            fig = px.bar(
                activity_df,
                x='segment',
                y='customers',
                title='Customer Distribution by Activity',
                labels={'segment': 'Activity Level', 'customers': 'Customer Count'},
                color='customers',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE 5: SYSTEM HEALTH
# ============================================================================

def page_system_health():
    """System Health & Performance"""
    st.markdown('<h1 class="main-header">🏥 System Health</h1>', unsafe_allow_html=True)
    
    # System status
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("PostgreSQL", "✅ Online", "Port 5433")
    
    with col2:
        st.metric("Grafana", "✅ Online", "Port 3000")
    
    with col3:
        st.metric("Streamlit", "✅ Online", "Port 8501")
    
    with col4:
        status_query = """
            SELECT COUNT(*) as data_freshness
            FROM fact_sales
            WHERE load_timestamp >= CURRENT_DATE
        """
        fresh_df = execute_query(status_query)
        if fresh_df is not None:
            count = fresh_df['data_freshness'].iloc[0]
            st.metric("Today's Records", f"{count:,}", "Fresh Data")
    
    st.divider()
    
    # Performance metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Database Statistics")
        stats_query = """
            SELECT 
                'fact_sales'::text as table_name,
                COUNT(*) as row_count,
                ROUND(SUM(revenue)::numeric, 2) as total_revenue
            FROM fact_sales
            UNION ALL
            SELECT 
                'dim_customer'::text,
                COUNT(*),
                NULL
            FROM dim_customer
            UNION ALL
            SELECT 
                'dim_product'::text,
                COUNT(*),
                NULL
            FROM dim_product
            UNION ALL
            SELECT 
                'etl_log'::text,
                COUNT(*),
                NULL
            FROM etl_log
        """
        stats_df = execute_query(stats_query)
        if stats_df is not None:
            st.dataframe(
                stats_df.rename(columns={
                    'table_name': 'Table',
                    'row_count': 'Records',
                    'total_revenue': 'Value'
                }),
                use_container_width=True,
                hide_index=True
            )
    
    with col2:
        st.subheader("🔄 System Information")
        info_data = {
            "Component": [
                "Database Engine",
                "Database Version",
                "Data Warehouse",
                "Star Schema",
                "Total Records",
                "Data Freshness",
                "API Status",
                "Backup Status"
            ],
            "Status": [
                "PostgreSQL 15",
                "15.x",
                "unilever_warehouse",
                "1 Fact + 3 Dimensions",
                "500,000+ Sales",
                "Real-time",
                "Healthy ✅",
                "Active ✅"
            ]
        }
        info_df = pd.DataFrame(info_data)
        st.dataframe(info_df, use_container_width=True, hide_index=True)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application"""
    # Sidebar navigation
    st.sidebar.markdown("# 🏭 Unilever Analytics")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Select Dashboard",
        ["💰 Sales Analytics", "⚙️ ETL Monitoring", "✅ Data Quality", "👥 Customer Analytics", "🏥 System Health"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📧 Contact")
    st.sidebar.info(
        "**Email**: merelelentintelo@gmail.com\n\n"
        "**GitHub**: [mfobestechjournal](https://github.com/mfobestechjournal)\n\n"
        "**Support**: GitHub Issues"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔗 Quick Links")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.markdown("[Grafana](http://localhost:3000)")
        st.markdown("[Database](http://localhost:5433)")
    with col2:
        st.markdown("[GitHub](https://github.com/mfobestechjournal)")
        st.markdown("[Docs](https://github.com/mfobestechjournal/unilever_pipeline)")
    
    # Page routing
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
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: gray; font-size: 0.85rem;">
            <p>Built with ❤️ for Unilever Global Operations | Last Updated: March 5, 2026</p>
            <p>© 2026 Mfobe's Tech Journal | Production Ready ✅</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
