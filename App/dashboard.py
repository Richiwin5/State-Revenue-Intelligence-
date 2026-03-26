# dashboard.py - Complete Revenue Intelligence Dashboard

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from datetime import datetime
import io
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================
# DATABASE CONNECTION (FROM .env FILE)
# ============================================

def get_database_url():
    """Get database URL from environment variables"""
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")

    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    return f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


@st.cache_resource
def init_connection():
    """Initializing connection"""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        return engine
    except Exception as e:
        st.error(f"  connection failed: {str(e)}")
        st.stop()


engine = init_connection()


@st.cache_data(ttl=600)
def run_query(query):
    """please wait...."""
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Query failed: {str(e)}")
        return pd.DataFrame()


# ============================================
# HELPER FUNCTIONS
# ============================================

def format_number(value):
    """Format large numbers to Trillions, Billions, Millions, Thousands"""
    if pd.isna(value) or value is None:
        return "₦0"
    if value >= 1_000_000_000_000:
        return f"<span class='trillions'>₦{value / 1_000_000_000_000:.2f}T</span>"
    elif value >= 1_000_000_000:
        return f"<span class='billions'>₦{value / 1_000_000_000:.2f}B</span>"
    elif value >= 1_000_000:
        return f"<span class='millions'>₦{value / 1_000_000:.2f}M</span>"
    elif value >= 1_000:
        return f"<span class='thousands'>₦{value / 1_000:.2f}K</span>"
    else:
        return f"₦{value:,.2f}"


def load_css():
    """Load custom CSS from file or use default"""
    try:
        with open('styles.css', 'r') as f:
            css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.markdown("""
        <style>
        .metric-card { padding: 1rem; background: #f0f2f6; border-radius: 0.5rem; margin: 0.5rem 0; }
        .metric-value { font-size: 1.5rem; font-weight: bold; }
        .metric-label { font-size: 0.8rem; color: #666; text-transform: uppercase; letter-spacing: 1px; }
        .chart-container { background: white; border-radius: 1rem; padding: 1rem; margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .custom-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 1rem; margin-bottom: 2rem; color: white; }
        .custom-footer { background: #2c3e50; color: white; padding: 1.5rem; border-radius: 1rem; text-align: center; margin-top: 2rem; }
        .dark-mode { background-color: #1a1a2e; color: white; }
        .dark-mode .chart-container { background: #2d2d44; color: white; }
        .dark-mode .metric-card { background: #2d2d44; color: white; }
        .trillions { color: #e74c3c; font-weight: bold; }
        .billions { color: #f39c12; font-weight: bold; }
        .millions { color: #27ae60; font-weight: bold; }
        .thousands { color: #3498db; font-weight: bold; }
        </style>
        """, unsafe_allow_html=True)


# ============================================
# PAGE CONFIGURATION
# ============================================

st.set_page_config(
    page_title=" Revenue Intelligence System",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_css()

# Initialize session state
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_page" not in st.session_state:
    st.session_state.current_page = "📊 Overview Dashboard"

current_year = datetime.now().year

# Test database connection
try:
    test_df = run_query("SELECT COUNT(*) as count FROM ebs_master")
    if not test_df.empty and test_df['count'][0] > 0:
        record_count = test_df['count'][0]
        st.sidebar.success(f" {record_count:,} records")
    else:
        st.sidebar.warning(" data not loading....")
except Exception as e:
    st.sidebar.error(f" Connection Error")
    st.stop()

# Custom Header
st.markdown("""
<div class="custom-header">
    <div style="display: flex; align-items: center; gap: 20px;">
        <div style="font-size: 3rem;">🏛️</div>
        <div>
            <h1>Revenue Intelligence System</h1>
            <p>Data-driven insights for better revenue management | Live Analytics Dashboard</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <div style="font-size: 4rem;">🏛️</div>
        <p style="margin: 0; font-weight: bold;"> Revenue</p>
        <p style="margin: 0; font-size: 0.8rem;">Intelligence Platform</p>
        <p style="margin-top: 0.5rem; font-size: 0.7rem; color: #27ae60;">...</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Navigation Menu
    st.markdown("### 📊 NAVIGATION MENU")
    menu_items = ["📊 Overview Dashboard", "🏢 Sector Analysis", "🏠 Property Intelligence",
                  "💼 Business Insights", "🗺️ LGA Deep Dive", "🤖 AI Assistant"]

    for item in menu_items:
        if st.button(item, key=item, use_container_width=True):
            st.session_state.current_page = item
            st.rerun()

    st.markdown("---")

    # Dark Mode Toggle
    dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()

    st.markdown("---")

    # Export Section
    st.markdown("###  EXPORT DATA")
    lga_df = run_query("SELECT DISTINCT lga FROM ebs_master ORDER BY lga")
    lga_list = ["All"] + lga_df['lga'].tolist() if not lga_df.empty else ["All"]
    export_lga = st.selectbox("Select LGA for Export", lga_list, key="export_lga")


    def generate_export_data():
        if export_lga == "All":
            query = """
                SELECT lga, SUM(amount_paid) as total_revenue, 
                       COUNT(DISTINCT taxpayer_id) as taxpayers,
                       SUM(amount_due) as total_due,
                       COUNT(*) as assessments
                FROM ebs_master 
                GROUP BY lga 
                ORDER BY total_revenue DESC
            """
        else:
            query = f"""
                SELECT lga, SUM(amount_paid) as total_revenue, 
                       COUNT(DISTINCT taxpayer_id) as taxpayers,
                       SUM(amount_due) as total_due,
                       COUNT(*) as assessments
                FROM ebs_master 
                WHERE lga = '{export_lga}'
                GROUP BY lga
            """
        return run_query(query)


    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 CSV", use_container_width=True):
            export_data = generate_export_data()
            if not export_data.empty:
                csv_data = export_data.to_csv(index=False)
                st.download_button(
                    label="Download",
                    data=csv_data,
                    file_name=f"revenue_data_{export_lga}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    with col2:
        if st.button("📄 Excel", use_container_width=True):
            export_data = generate_export_data()
            if not export_data.empty:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    export_data.to_excel(writer, index=False, sheet_name='Revenue Data')
                excel_data = output.getvalue()
                st.download_button(
                    label="Download",
                    data=excel_data,
                    file_name=f"revenue_data_{export_lga}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    st.markdown("---")

    # About Section
    st.markdown("### ℹ️ ABOUT")
    year_df = run_query("""
        SELECT MIN(EXTRACT(YEAR FROM payment_date)) as min_year,
               MAX(EXTRACT(YEAR FROM payment_date)) as max_year
        FROM payments WHERE payment_date IS NOT NULL
    """)
    if not year_df.empty:
        min_year = int(year_df['min_year'][0]) if not pd.isna(year_df['min_year'][0]) else 2022
        max_year = int(year_df['max_year'][0]) if not pd.isna(year_df['max_year'][0]) else 2026
    else:
        min_year, max_year = 2022, 2026

    st.info(f"""
    **Data Coverage:** {min_year}-{max_year}  
    **Status:** 🟢   
    **Database:** PostgreSQL (Render)
    """)

# Apply dark mode
if st.session_state.dark_mode:
    st.markdown('<div class="dark-mode">', unsafe_allow_html=True)

# Get current page
page = st.session_state.current_page

# Global filters
st.sidebar.markdown("---")
st.sidebar.markdown("### Global Filters")
lga_options_df = run_query("SELECT DISTINCT lga FROM ebs_master ORDER BY lga")
lga_options = ["All"] + lga_options_df['lga'].tolist() if not lga_options_df.empty else ["All"]
selected_lga_global = st.sidebar.selectbox("Select LGA for Analysis", lga_options)


def get_filtered_data(lga_filter=None):
    if lga_filter and lga_filter != "All":
        return run_query(f"SELECT * FROM ebs_master WHERE lga = '{lga_filter}'")
    else:
        return run_query("SELECT * FROM ebs_master")


# ============================================
# 1. OVERVIEW DASHBOARD
# ============================================
if page == "📊 Overview Dashboard":
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.header("📊 Executive Overview Dashboard")

    df = get_filtered_data(selected_lga_global if selected_lga_global != "All" else None)

    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_revenue = df['amount_paid'].sum()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">💰 TOTAL REVENUE</div>
                <div class="metric-value">{format_number(total_revenue)}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            total_taxpayers = df['taxpayer_id'].nunique()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">👥 TOTAL TAXPAYERS</div>
                <div class="metric-value">{total_taxpayers:,}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            total_due = df['amount_due'].sum()
            collection_rate = (total_revenue / total_due * 100) if total_due > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label"> COLLECTION RATE</div>
                <div class="metric-value">{collection_rate:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            total_assessments = len(df)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label"> TOTAL ASSESSMENTS</div>
                <div class="metric-value">{total_assessments:,}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Revenue Charts
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader(" 📊Revenue by LGA")
            revenue_lga = df.groupby('lga')['amount_paid'].sum().reset_index()
            revenue_lga = revenue_lga.sort_values('amount_paid', ascending=True).tail(10)
            fig = px.bar(revenue_lga, x='amount_paid', y='lga', orientation='h',
                         title='Top 10 LGAs by Revenue', labels={'amount_paid': 'Revenue', 'lga': 'LGA'},
                         color='amount_paid', color_continuous_scale='Viridis')
            fig.update_layout(height=500, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader("📊 Revenue by Sector")
            revenue_sector = df.groupby('sector')['amount_paid'].sum().reset_index()
            fig = px.pie(revenue_sector, values='amount_paid', names='sector',
                         title='Revenue Distribution by Sector', hole=0.3)
            fig.update_layout(height=500, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Top Taxpayers
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader(" Top Performing Taxpayers")
        top_taxpayers = df.groupby(['taxpayer_id', 'full_name', 'lga', 'sector'])['amount_paid'].sum().reset_index()
        top_taxpayers = top_taxpayers.sort_values('amount_paid', ascending=False).head(10)
        st.dataframe(top_taxpayers, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No data available")

# ============================================
# 2. SECTOR ANALYSIS
# ============================================
elif page == "🏢 Sector Analysis":
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.header("🏢 Sector Performance Analysis")

    df = get_filtered_data(selected_lga_global if selected_lga_global != "All" else None)

    if not df.empty:
        sectors = df['sector'].unique()
        cols = st.columns(min(len(sectors), 4))

        for idx, sector in enumerate(sectors[:4]):
            with cols[idx]:
                sector_df = df[df['sector'] == sector]
                revenue = sector_df['amount_paid'].sum()
                collection = (revenue / sector_df['amount_due'].sum() * 100) if sector_df['amount_due'].sum() > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{sector}</div>
                    <div class="metric-value">{format_number(revenue)}</div>
                    <div class="metric-label">{collection:.1f}% collection</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Sector Revenue Chart
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader("💰 Revenue by Sector")
        sector_revenue = df.groupby('sector')['amount_paid'].sum().reset_index()
        fig = px.bar(sector_revenue, x='sector', y='amount_paid',
                     title='Total Revenue Collected by Sector',
                     color='amount_paid', color_continuous_scale='Viridis')
        fig.update_layout(height=500, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Detailed Sector Table
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.subheader(" Detailed Sector Performance")
        sector_detail = df.groupby('sector').agg({
            'taxpayer_id': 'nunique',
            'amount_due': 'sum',
            'amount_paid': 'sum',
        }).reset_index()
        sector_detail.columns = ['Sector', 'Taxpayers', 'Total Due', 'Total Paid']
        sector_detail['Collection Rate'] = (sector_detail['Total Paid'] / sector_detail['Total Due'] * 100).round(2)
        sector_detail['Outstanding'] = sector_detail['Total Due'] - sector_detail['Total Paid']
        st.dataframe(sector_detail, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No data available")

# ============================================
# 3. PROPERTY INTELLIGENCE
# ============================================
elif page == "🏠 Property Intelligence":
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.header("🏠 Property Tax Intelligence")

    try:
        properties_df = run_query("""
            SELECT p.id, p.owner_id, p.lga, p.ward, p.street, p.property_type, p.estimated_value,
                   t.full_name, t.sector
            FROM properties p
            JOIN taxpayers t ON p.owner_id = t.id
            LIMIT 1000
        """)

        if selected_lga_global != "All" and not properties_df.empty:
            properties_df = properties_df[properties_df['lga'] == selected_lga_global]

        if not properties_df.empty:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_properties = len(properties_df)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">🏘️ TOTAL PROPERTIES</div>
                    <div class="metric-value">{total_properties:,}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                total_value = properties_df['estimated_value'].sum() if len(properties_df) > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">💰 TOTAL PROPERTY VALUE</div>
                    <div class="metric-value">{format_number(total_value)}</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                avg_value = properties_df['estimated_value'].mean() if len(properties_df) > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label"> AVERAGE PROPERTY VALUE</div>
                    <div class="metric-value">{format_number(avg_value)}</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                commercial = len(properties_df[properties_df['property_type'] == 'Commercial']) if len(
                    properties_df) > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label"> COMMERCIAL PROPERTIES</div>
                    <div class="metric-value">{commercial:,}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                property_types = properties_df['property_type'].value_counts()
                if not property_types.empty:
                    fig = px.pie(values=property_types.values, names=property_types.index,
                                 title='Residential vs Commercial Properties')
                    fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                lga_value = properties_df.groupby('lga')['estimated_value'].sum().reset_index()
                if not lga_value.empty:
                    lga_value = lga_value.sort_values('estimated_value', ascending=True).tail(10)
                    fig = px.bar(lga_value, x='estimated_value', y='lga', orientation='h',
                                 title='Total Property Value by LGA')
                    fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader(" Top Property Owners")
            top_owners = properties_df.groupby(['owner_id', 'full_name', 'lga', 'sector']).agg({
                'estimated_value': 'sum',
                'property_type': 'count'
            }).reset_index()
            top_owners = top_owners.sort_values('estimated_value', ascending=False).head(10)
            top_owners.columns = ['Owner ID', 'Name', 'LGA', 'Sector', 'Total Property Value', 'Properties Count']
            st.dataframe(top_owners, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No property data available")
    except Exception as e:
        st.info(f"Property data not available")

# ============================================
# 4. BUSINESS INSIGHTS
# ============================================
elif page == "💼 Business Insights":
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.header("💼 Business Intelligence & Performance")

    try:
        businesses_df = run_query("SELECT * FROM businesses LIMIT 1000")

        if selected_lga_global != "All" and not businesses_df.empty:
            businesses_df = businesses_df[businesses_df['lga'] == selected_lga_global]

        if not businesses_df.empty:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_businesses = len(businesses_df)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label"> TOTAL BUSINESSES</div>
                    <div class="metric-value">{total_businesses:,}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                total_revenue = businesses_df['annual_revenue'].sum() if len(businesses_df) > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label"> TOTAL ANNUAL REVENUE</div>
                    <div class="metric-value">{format_number(total_revenue)}</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                total_employees = businesses_df['employee_count'].sum() if len(businesses_df) > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">👥 TOTAL EMPLOYEES</div>
                    <div class="metric-value">{total_employees:,}</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                registered = len(businesses_df[businesses_df['registered'] == True]) if len(businesses_df) > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label"> REGISTERED BUSINESSES</div>
                    <div class="metric-value">{registered:,}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.subheader(" Top Businesses by Revenue")
                top_revenue = businesses_df.nlargest(10, 'annual_revenue')[
                    ['business_name', 'sector', 'annual_revenue', 'employee_count']]
                st.dataframe(top_revenue, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.subheader(" Revenue by Sector")
                sector_revenue = businesses_df.groupby('sector')['annual_revenue'].sum().reset_index()
                if not sector_revenue.empty:
                    fig = px.pie(sector_revenue, values='annual_revenue', names='sector',
                                 title='Business Revenue Distribution by Sector')
                    fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.subheader(" Business Performance Metrics")
            sector_performance = businesses_df.groupby('sector').agg({
                'business_name': 'count',
                'annual_revenue': 'sum',
                'employee_count': 'sum',
                'registered': 'mean'
            }).reset_index()
            sector_performance.columns = ['Sector', 'Business Count', 'Total Revenue', 'Total Employees',
                                          'Registration Rate']
            sector_performance['Avg Revenue/Business'] = sector_performance['Total Revenue'] / sector_performance[
                'Business Count']
            st.dataframe(sector_performance, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No business data available")
    except Exception as e:
        st.info(f"Business data not available")

# ============================================
# 5. LGA DEEP DIVE (WITH WARDS & STREETS) - CLEAN DISPLAY
# ============================================
elif page == "🗺️ LGA Deep Dive":
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.header("🗺️ Local Government Area Intelligence")

    lga_df = run_query("SELECT DISTINCT lga FROM ebs_master ORDER BY lga")
    if not lga_df.empty:
        lga_list = lga_df['lga'].tolist()
        selected_lga = st.selectbox("Select LGA for Detailed Analysis", lga_list)

        if selected_lga:
            lga_data = run_query(f"SELECT * FROM ebs_master WHERE lga = '{selected_lga}'")

            if not lga_data.empty:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    total_revenue = lga_data['amount_paid'].sum()
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">💰 TOTAL REVENUE</div>
                        <div class="metric-value">{format_number(total_revenue)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    taxpayers = lga_data['taxpayer_id'].nunique()
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">👥 TAXPAYERS</div>
                        <div class="metric-value">{taxpayers:,}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    total_due = lga_data['amount_due'].sum()
                    collection_rate = (total_revenue / total_due * 100) if total_due > 0 else 0
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">📈 COLLECTION RATE</div>
                        <div class="metric-value">{collection_rate:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col4:
                    outstanding = lga_data['amount_due'].sum() - lga_data['amount_paid'].sum()
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">⚠️ OUTSTANDING</div>
                        <div class="metric-value">{format_number(outstanding)}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("---")

                # Tabs for different analyses
                tab1, tab2, tab3, tab4 = st.tabs(
                    ["📊 Revenue Analysis", "🏘️ Properties", "💼 Businesses", "📍 Wards & Streets"])

                with tab1:
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    st.subheader(f"Revenue Analysis for {selected_lga}")

                    col1, col2 = st.columns(2)
                    with col1:
                        sector_data = lga_data.groupby('sector')['amount_paid'].sum().reset_index()
                        if len(sector_data) > 0:
                            fig = px.pie(sector_data, values='amount_paid', names='sector',
                                         title=f'Sector Revenue Distribution - {selected_lga}')
                            st.plotly_chart(fig, use_container_width=True)

                    with col2:
                        status_data = lga_data['status'].value_counts()
                        if len(status_data) > 0:
                            fig = px.pie(values=status_data.values, names=status_data.index,
                                         title='Payment Status Distribution')
                            st.plotly_chart(fig, use_container_width=True)

                    st.subheader(f"Top Taxpayers in {selected_lga}")
                    top_taxpayers = lga_data.groupby(['full_name', 'sector'])['amount_paid'].sum().reset_index()
                    top_taxpayers = top_taxpayers.sort_values('amount_paid', ascending=False).head(10)
                    # Clean formatting without HTML tags
                    top_taxpayers['amount_paid'] = top_taxpayers['amount_paid'].apply(lambda x: f"₦{x:,.2f}")
                    st.dataframe(top_taxpayers, use_container_width=True)

                    # Outstanding taxpayers in this LGA
                    st.subheader(f"Taxpayers with Outstanding Balance in {selected_lga}")
                    outstanding_taxpayers = lga_data[lga_data['amount_paid'] < lga_data['amount_due']].groupby(
                        ['full_name', 'sector']).agg({
                        'amount_due': 'sum',
                        'amount_paid': 'sum'
                    }).reset_index()
                    if not outstanding_taxpayers.empty:
                        outstanding_taxpayers['outstanding'] = outstanding_taxpayers['amount_due'] - \
                                                               outstanding_taxpayers['amount_paid']
                        outstanding_taxpayers = outstanding_taxpayers.sort_values('outstanding', ascending=False).head(
                            10)
                        outstanding_taxpayers['outstanding'] = outstanding_taxpayers['outstanding'].apply(
                            lambda x: f"₦{x:,.2f}")
                        st.dataframe(outstanding_taxpayers[['full_name', 'sector', 'outstanding']],
                                     use_container_width=True)
                    else:
                        st.info("No outstanding balances in this LGA")

                    st.markdown('</div>', unsafe_allow_html=True)

                with tab2:
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    st.subheader(f"Property Information for {selected_lga}")
                    try:
                        properties_lga = run_query(f"""
                            SELECT p.property_type, p.estimated_value, p.ward, p.street, t.full_name
                            FROM properties p
                            JOIN taxpayers t ON p.owner_id = t.id
                            WHERE p.lga = '{selected_lga}'
                            LIMIT 100
                        """)
                        if not properties_lga.empty:
                            properties_lga['estimated_value'] = properties_lga['estimated_value'].apply(
                                lambda x: f"₦{x:,.2f}")
                            st.dataframe(properties_lga, use_container_width=True)
                        else:
                            st.info(f"No property data available for {selected_lga}")
                    except Exception as e:
                        st.info(f"Property data not available")
                    st.markdown('</div>', unsafe_allow_html=True)

                with tab3:
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    st.subheader(f"Business Information for {selected_lga}")
                    try:
                        businesses_lga = run_query(f"""
                            SELECT business_name, sector, annual_revenue, employee_count, registered, ward, street
                            FROM businesses 
                            WHERE lga = '{selected_lga}'
                            LIMIT 100
                        """)
                        if not businesses_lga.empty:
                            businesses_lga['annual_revenue'] = businesses_lga['annual_revenue'].apply(
                                lambda x: f"₦{x:,.2f}")
                            st.dataframe(businesses_lga, use_container_width=True)
                        else:
                            st.info(f"No business data available for {selected_lga}")
                    except Exception as e:
                        st.info(f"Business data not available")
                    st.markdown('</div>', unsafe_allow_html=True)

                with tab4:
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    st.subheader(f"📍 Geographic Breakdown - Wards & Streets in {selected_lga}")

                    # Get unique wards
                    wards_list = lga_data['ward'].unique()
                    st.write(f"**Total Wards:** {len(wards_list)}")

                    # Ward Summary
                    ward_summary = lga_data.groupby('ward').agg({
                        'amount_paid': 'sum',
                        'taxpayer_id': 'nunique'
                    }).reset_index()
                    ward_summary = ward_summary.sort_values('amount_paid', ascending=False)
                    ward_summary.columns = ['Ward', 'Total Revenue', 'Number of Taxpayers']

                    # Clean display for dataframe (no HTML spans)
                    ward_summary['Revenue Display'] = ward_summary['Total Revenue'].apply(lambda x: f"₦{x:,.2f}")

                    st.subheader("📊 Ward Performance Summary")
                    # Display clean version
                    display_ward = ward_summary[['Ward', 'Revenue Display', 'Number of Taxpayers']].copy()
                    display_ward.columns = ['Ward', 'Total Revenue', 'Number of Taxpayers']
                    st.dataframe(display_ward, use_container_width=True)

                    # Ward-wise chart using raw values
                    fig = px.bar(ward_summary.head(10), x='Ward', y='Total Revenue',
                                 title=f'Top 10 Wards by Revenue in {selected_lga}',
                                 color='Total Revenue', color_continuous_scale='Viridis')
                    fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)

                    # Street-level breakdown
                    st.subheader("🏘️ Street-Level Breakdown by Ward")
                    selected_ward = st.selectbox("Select Ward to View Street Details", wards_list)

                    if selected_ward:
                        # Filter data for selected ward
                        ward_data = lga_data[lga_data['ward'] == selected_ward]

                        # Street summary
                        street_data = ward_data.groupby('street').agg({
                            'amount_paid': 'sum',
                            'taxpayer_id': 'nunique'
                        }).reset_index()
                        street_data = street_data.sort_values('amount_paid', ascending=False)
                        street_data.columns = ['Street', 'Total Revenue', 'Number of Taxpayers']

                        # Clean display for dataframe (no HTML spans)
                        street_data['Revenue Display'] = street_data['Total Revenue'].apply(lambda x: f"₦{x:,.2f}")

                        st.write(f"**Streets in {selected_ward}:** {len(street_data)}")
                        # Display clean version
                        display_streets = street_data[['Street', 'Revenue Display', 'Number of Taxpayers']].copy()
                        display_streets.columns = ['Street', 'Total Revenue', 'Number of Taxpayers']
                        st.dataframe(display_streets, use_container_width=True)

                        # Top streets chart using raw values
                        if not street_data.empty:
                            top_streets = street_data.nlargest(10, 'Total Revenue')
                            fig = px.bar(top_streets, x='Street', y='Total Revenue',
                                         title=f'Top 10 Streets by Revenue in {selected_ward}',
                                         color='Total Revenue', color_continuous_scale='Viridis')
                            fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                            fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                            st.plotly_chart(fig, use_container_width=True)

                        # Also show top taxpayers in this ward
                        st.subheader(f"Top Taxpayers in {selected_ward}")
                        top_taxpayers_ward = ward_data.groupby(['full_name', 'sector'])[
                            'amount_paid'].sum().reset_index()
                        top_taxpayers_ward = top_taxpayers_ward.sort_values('amount_paid', ascending=False).head(10)
                        top_taxpayers_ward['amount_paid'] = top_taxpayers_ward['amount_paid'].apply(
                            lambda x: f"₦{x:,.2f}")
                        st.dataframe(top_taxpayers_ward, use_container_width=True)

                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No LGA data available")



# ============================================
# 6. AI ASSISTANT - COMPLETE CHATBOT
# ============================================
elif page == "🤖 AI Assistant":
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.header("🤖 Revenue Intelligence Assistant")
    st.markdown(f"Ask me anything about your tax revenue data!")


    def get_bot_response(user_input):
        user_input_lower = user_input.lower().strip()

        # ========== GREETINGS ==========
        greetings = {
            'hello': "Hello! 👋 Welcome to the State Revenue Intelligence Platform. How can I help you today?",
            'hi': "Hi there! 👋 What would you like to know about your revenue data?",
            'good morning': "Good morning! ☀️ Ready to analyze your revenue data!",
            'good afternoon': "Good afternoon! 🌤️ How can I assist you today?",
            'good evening': "Good evening! 🌙 I'm here to help with your revenue intelligence!",
            'how are you': "I'm doing great! 🤖 Ready to help with your data analysis!"
        }

        for greeting, response in greetings.items():
            if greeting in user_input_lower:
                return response

        # ========== LGA SPECIFIC QUERIES ==========
        lga_df = run_query("SELECT DISTINCT lga FROM ebs_master ORDER BY lga")
        lga_list = lga_df['lga'].tolist() if not lga_df.empty else []

        for lga in lga_list:
            if lga.lower() in user_input_lower:
                # Revenue queries
                if any(word in user_input_lower for word in ['revenue', 'money', 'generated', 'make', 'collected']):
                    data = run_query(f"""
                        SELECT 
                            SUM(amount_paid) as revenue,
                            COUNT(DISTINCT taxpayer_id) as taxpayers,
                            COUNT(*) as assessments,
                            ROUND((SUM(amount_paid) / NULLIF(SUM(amount_due), 0) * 100), 2) as collection_rate
                        FROM ebs_master WHERE lga = '{lga}'
                    """)
                    if not data.empty:
                        revenue = data['revenue'][0] if not pd.isna(data['revenue'][0]) else 0
                        taxpayers = data['taxpayers'][0] if not pd.isna(data['taxpayers'][0]) else 0
                        assessments = data['assessments'][0] if not pd.isna(data['assessments'][0]) else 0
                        rate = data['collection_rate'][0] if not pd.isna(data['collection_rate'][0]) else 0
                        return f"💰 **{lga}** has generated {format_number(revenue)} in revenue from {assessments:,} assessments by {taxpayers:,} taxpayers. Collection rate: {rate:.1f}%"

                # Outstanding/Debt queries
                elif any(word in user_input_lower for word in ['outstanding', 'debt', 'owe', 'owing']):
                    data = run_query(f"""
                        SELECT 
                            SUM(amount_due - amount_paid) as total_debt,
                            COUNT(DISTINCT CASE WHEN amount_paid < amount_due THEN taxpayer_id END) as debtors
                        FROM ebs_master WHERE lga = '{lga}'
                    """)
                    if not data.empty:
                        total_debt = data['total_debt'][0] if not pd.isna(data['total_debt'][0]) else 0
                        debtors = data['debtors'][0] if not pd.isna(data['debtors'][0]) else 0

                        top_debtors = run_query(f"""
                            SELECT full_name, ROUND(amount_due - amount_paid, 2) as debt
                            FROM ebs_master 
                            WHERE lga = '{lga}' AND amount_paid < amount_due
                            ORDER BY debt DESC LIMIT 5
                        """)

                        result = f"⚠️ **{lga}** has {format_number(total_debt)} in outstanding debt from {debtors} taxpayers.\n"
                        if not top_debtors.empty:
                            result += "\n**Top 5 debtors:**\n"
                            for _, row in top_debtors.iterrows():
                                result += f"• {row['full_name']}: {format_number(row['debt'])}\n"
                        return result

                # Compliance queries
                elif any(word in user_input_lower for word in ['compliance', 'compliant']):
                    data = run_query(f"""
                        SELECT 
                            COUNT(CASE WHEN status = 'Paid' THEN 1 END) as fully_paid,
                            COUNT(*) as total,
                            ROUND((COUNT(CASE WHEN status = 'Paid' THEN 1 END) * 100.0 / COUNT(*)), 2) as compliance_rate
                        FROM ebs_master WHERE lga = '{lga}'
                    """)
                    if not data.empty:
                        fully = data['fully_paid'][0]
                        total = data['total'][0]
                        rate = data['compliance_rate'][0]
                        return f"📊 **{lga} Compliance Report:**\n\n• Compliance Rate: {rate:.1f}%\n• Fully Paid: {fully:,} out of {total:,} assessments"

                # Wards queries
                elif 'ward' in user_input_lower:
                    wards = run_query(f"SELECT DISTINCT ward FROM ebs_master WHERE lga = '{lga}' LIMIT 10")
                    if not wards.empty:
                        ward_list = wards['ward'].tolist()
                        return f"📍 **{lga}** has {len(ward_list)} wards. Top wards: {', '.join(ward_list[:5])}"

        # ========== STATE-WIDE QUERIES ==========

        # Total Revenue
        if any(word in user_input_lower for word in ['total revenue', 'overall revenue', 'state revenue']):
            data = run_query("""
                SELECT 
                    SUM(amount_paid) as total_revenue,
                    COUNT(DISTINCT taxpayer_id) as total_taxpayers,
                    ROUND((SUM(amount_paid) / NULLIF(SUM(amount_due), 0) * 100), 2) as collection_rate
                FROM ebs_master
            """)
            if not data.empty:
                return f"💰 **State-wide Revenue:**\n\n• Total Revenue: {format_number(data['total_revenue'][0])}\n• Total Taxpayers: {data['total_taxpayers'][0]:,}\n• Collection Rate: {data['collection_rate'][0]:.1f}%"

        # Total Outstanding
        elif any(word in user_input_lower for word in ['total outstanding', 'total debt', 'overall debt']):
            data = run_query("""
                SELECT 
                    SUM(amount_due - amount_paid) as total_debt,
                    COUNT(DISTINCT CASE WHEN amount_paid < amount_due THEN taxpayer_id END) as total_debtors
                FROM ebs_master
            """)
            if not data.empty:
                return f"⚠️ **State-wide Outstanding Debt:**\n\n• Total Debt: {format_number(data['total_debt'][0])}\n• Total Debtors: {data['total_debtors'][0]:,} taxpayers"

        # Top LGA
        elif any(word in user_input_lower for word in ['top lga', 'best lga', 'highest revenue lga']):
            data = run_query(
                "SELECT lga, SUM(amount_paid) as revenue FROM ebs_master GROUP BY lga ORDER BY revenue DESC LIMIT 1")
            if not data.empty:
                return f"🏆 **{data['lga'][0]}** is the top-performing LGA with {format_number(data['revenue'][0])} in revenue"

        # Compare LGAs
        elif any(word in user_input_lower for word in ['compare', 'difference between']):
            lgas_found = [lga for lga in lga_list if lga.lower() in user_input_lower]
            if len(lgas_found) >= 2:
                lga1, lga2 = lgas_found[0], lgas_found[1]
                data1 = run_query(f"SELECT SUM(amount_paid) as revenue FROM ebs_master WHERE lga = '{lga1}'")
                data2 = run_query(f"SELECT SUM(amount_paid) as revenue FROM ebs_master WHERE lga = '{lga2}'")
                rev1 = data1['revenue'][0] if not data1.empty else 0
                rev2 = data2['revenue'][0] if not data2.empty else 0
                diff = rev1 - rev2
                winner = lga1 if diff > 0 else lga2
                return f"📊 **Comparison: {lga1} vs {lga2}**\n\n• {lga1}: {format_number(rev1)}\n• {lga2}: {format_number(rev2)}\n• **{winner}** has {format_number(abs(diff))} more in revenue"

        # Top Debtors
        elif any(word in user_input_lower for word in ['top debtors', 'highest debtors', 'who owes most']):
            data = run_query("""
                SELECT full_name, lga, ROUND(amount_due - amount_paid, 2) as debt
                FROM ebs_master WHERE amount_paid < amount_due
                ORDER BY debt DESC LIMIT 5
            """)
            if not data.empty:
                result = "⚠️ **Top 5 Debtors State-wide:**\n\n"
                for idx, row in data.iterrows():
                    result += f"{idx + 1}. **{row['full_name']}** ({row['lga']}): {format_number(row['debt'])}\n"
                return result

        # Top Taxpayers
        elif any(word in user_input_lower for word in ['top taxpayers', 'highest payers', 'who pays most']):
            data = run_query("""
                SELECT full_name, lga, SUM(amount_paid) as paid
                FROM ebs_master GROUP BY full_name, taxpayer_id, lga
                ORDER BY paid DESC LIMIT 5
            """)
            if not data.empty:
                result = "👑 **Top 5 Taxpayers State-wide:**\n\n"
                for idx, row in data.iterrows():
                    result += f"{idx + 1}. **{row['full_name']}** ({row['lga']}): {format_number(row['paid'])}\n"
                return result

        # Best Sector
        elif any(word in user_input_lower for word in ['best sector', 'top sector']):
            data = run_query("""
                SELECT sector, SUM(amount_paid) as revenue
                FROM ebs_master GROUP BY sector ORDER BY revenue DESC LIMIT 1
            """)
            if not data.empty:
                return f"🏢 **{data['sector'][0]}** sector is the top performer with {format_number(data['revenue'][0])} in revenue"

        # Help
        elif any(word in user_input_lower for word in ['help', 'what can you do']):
            return """🤖 **I can help you with:**

**💰 REVENUE:** "total revenue", "revenue in Agege", "top LGA"
**⚠️ DEBT:** "total outstanding", "debt in Lekki", "top debtors"
**📊 COMPLIANCE:** "compliance rate", "compliance in Ikeja"
**👥 TAXPAYERS:** "top taxpayers", "who pays most"
**🏢 SECTORS:** "best sector", "sector performance"
**📍 LGA DETAILS:** "wards in Agege", "compare Lekki and Ikeja"
**🏠 PROPERTY:** "property value in Lekki"
**💼 BUSINESS:** "top businesses in Ikeja"

Type your question naturally!"""

        return "I'm not sure about that. Try asking about revenue, debt, compliance, sectors, or specific LGAs. Type 'help' to see all capabilities!"


    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask me about your revenue data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = get_bot_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

    st.markdown('</div>', unsafe_allow_html=True)

# Close dark mode div
if st.session_state.dark_mode:
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown(f"""
<div class="custom-footer">
    <p>© {current_year} Revenue Intelligence System | Data-driven insights for better revenue management</p>
    <p style="font-size: 0.8rem; opacity: 0.8;">Powered by Streamlit | built by Richiwin</p>
</div>
""", unsafe_allow_html=True)