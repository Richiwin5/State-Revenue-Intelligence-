import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import folium
from folium import plugins
from folium.plugins import HeatMap
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os

engine = create_engine("postgresql+psycopg2://postgres:Richiwin@localhost:5432/lagos_ebs")

def format_naira(amount):
    """Format currency in millions/billions/trillions"""
    if amount is None or pd.isna(amount):
        return "₦0"
    if amount >= 1_000_000_000_000:
        return f"₦{amount/1_000_000_000_000:.2f} Trillion"
    elif amount >= 1_000_000_000:
        return f"₦{amount/1_000_000_000:.2f} Billion"
    elif amount >= 1_000_000:
        return f"₦{amount/1_000_000:.2f} Million"
    elif amount >= 1_000:
        return f"₦{amount/1_000:.2f} Thousand"
    else:
        return f"₦{amount:,.2f}"

def create_lga_revenue_map():
    """Create a choropleth map showing revenue distribution by LGA"""
    print("\n🗺️ Creating LGA Revenue Distribution Map...")
    
    with engine.connect() as conn:
        # Get revenue data by LGA
        df_revenue = pd.read_sql("""
            SELECT 
                t.lga,
                SUM(tr.tax_paid) as total_revenue,
                COUNT(DISTINCT t.id) as taxpayers,
                AVG(tr.tax_paid) as avg_tax_paid,
                AVG(t.compliance_score) as compliance_score
            FROM taxpayers t
            JOIN tax_records tr ON t.id = tr.taxpayer_id
            GROUP BY t.lga
            ORDER BY total_revenue DESC
        """, engine)
    
    # Sample coordinates for Lagos LGAs (you should replace with actual geo coordinates)
    lga_coordinates = {
        'Alimosho': (6.6170, 3.2089),
        'Ajeromi-Ifelodun': (6.4540, 3.3240),
        'Amuwo-Odofin': (6.4580, 3.2830),
        'Apapa': (6.4460, 3.3560),
        'Badagry': (6.4160, 2.8830),
        'Epe': (6.5840, 3.9830),
        'Eti-Osa': (6.4500, 3.6000),
        'Ibeju-Lekki': (6.4710, 3.9020),
        'Ifako-Ijaiye': (6.6390, 3.2920),
        'Ikeja': (6.6050, 3.3590),
        'Ikorodu': (6.6150, 3.5070),
        'Kosofe': (6.5970, 3.3930),
        'Lagos Island': (6.4530, 3.3940),
        'Lagos Mainland': (6.4840, 3.3710),
        'Mushin': (6.5280, 3.3540),
        'Ojo': (6.4760, 3.1790),
        'Oshodi-Isolo': (6.5580, 3.3410),
        'Shomolu': (6.5410, 3.3800),
        'Surulere': (6.4990, 3.3510),
        'Victoria Island': (6.4300, 3.4170)
    }
    
    # Add coordinates to dataframe
    df_revenue['lat'] = df_revenue['lga'].map(lambda x: lga_coordinates.get(x, (6.5, 3.5))[0])
    df_revenue['lon'] = df_revenue['lga'].map(lambda x: lga_coordinates.get(x, (6.5, 3.5))[1])
    
    # Create base map centered on Lagos
    map_center = [6.5, 3.4]
    m = folium.Map(location=map_center, zoom_start=10, tiles='cartodbpositron')
    
    # Add markers with popups
    for idx, row in df_revenue.iterrows():
        popup_text = f"""
        <b>{row['lga']}</b><br>
        Revenue: {format_naira(row['total_revenue'])}<br>
        Taxpayers: {row['taxpayers']:,}<br>
        Avg Tax: {format_naira(row['avg_tax_paid'])}<br>
        Compliance: {row['compliance_score']:.1f}%
        """
        
        # Color based on revenue (red for high, green for low)
        revenue_rank = df_revenue['total_revenue'].rank(pct=True)[idx]
        if revenue_rank > 0.8:
            color = 'red'
        elif revenue_rank > 0.5:
            color = 'orange'
        elif revenue_rank > 0.2:
            color = 'yellow'
        else:
            color = 'green'
        
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=revenue_rank * 20 + 5,
            popup=folium.Popup(popup_text, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6,
            tooltip=row['lga']
        ).add_to(m)
    
    # Add heatmap layer
    heat_data = [[row['lat'], row['lon'], row['total_revenue']] for idx, row in df_revenue.iterrows()]
    HeatMap(heat_data, radius=15, blur=10, max_zoom=1).add_to(m)
    
    # Save map
    m.save('lga_revenue_map.html')
    print("✅ LGA Revenue Map saved as 'lga_revenue_map.html'")
    
    return df_revenue

def create_taxpayer_density_heatmap():
    """Create a heatmap showing taxpayer density across Lagos"""
    print("\n🗺️ Creating Taxpayer Density Heatmap...")
    
    with engine.connect() as conn:
        # Get taxpayer locations
        df_taxpayers = pd.read_sql("""
            SELECT 
                lga,
                ward,
                street,
                COUNT(*) as taxpayer_count,
                SUM(tr.tax_paid) as total_revenue
            FROM taxpayers t
            JOIN tax_records tr ON t.id = tr.taxpayer_id
            GROUP BY lga, ward, street
        """, engine)
    
    # Sample coordinates mapping (you should enhance this with actual street coordinates)
    def get_coordinates(lga, ward):
        # Simplified mapping - in production, use actual geocoding
        base_coords = {
            'Ikeja': (6.605, 3.359),
            'Lekki': (6.430, 3.417),
            'Surulere': (6.499, 3.351),
            'Alimosho': (6.617, 3.209),
            'Eti-Osa': (6.450, 3.600),
            'Yaba': (6.499, 3.361),
            'Victoria Island': (6.430, 3.417),
            'Ikorodu': (6.615, 3.507),
            'Epe': (6.584, 3.983),
            'Badagry': (6.416, 2.883),
            'Mushin': (6.528, 3.354),
            'Agege': (6.620, 3.322),
            'Kosofe': (6.597, 3.393),
            'Somolu': (6.541, 3.380),
            'Amuwo-Odofin': (6.458, 3.283),
            'Ifako-Ijaiye': (6.639, 3.292),
            'Shomolu': (6.541, 3.380),
            'Ajah': (6.471, 3.902)
        }
        
        base_lat, base_lon = base_coords.get(lga, (6.5, 3.4))
        # Add small random offset for visualization
        np.random.seed(hash(ward) % 2**32)
        lat_offset = np.random.uniform(-0.05, 0.05)
        lon_offset = np.random.uniform(-0.05, 0.05)
        
        return base_lat + lat_offset, base_lon + lon_offset
    
    # Create heatmap data
    heat_data = []
    for idx, row in df_taxpayers.iterrows():
        lat, lon = get_coordinates(row['lga'], row['ward'])
        # Weight by taxpayer count and revenue
        weight = row['taxpayer_count'] * (row['total_revenue'] / row['taxpayer_count'] / 1000000)
        heat_data.append([lat, lon, weight])
    
    # Create map
    m = folium.Map(location=[6.5, 3.4], zoom_start=10, tiles='cartodbpositron')
    
    # Add heatmap
    HeatMap(heat_data, radius=20, blur=15, max_zoom=1, 
            gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1: 'red'}).add_to(m)
    
    # Add markers for high revenue areas
    top_areas = df_taxpayers.nlargest(20, 'total_revenue')
    for idx, row in top_areas.iterrows():
        lat, lon = get_coordinates(row['lga'], row['ward'])
        folium.Marker(
            [lat, lon],
            popup=f"{row['lga']} - {row['ward']}<br>Taxpayers: {row['taxpayer_count']}<br>Revenue: {format_naira(row['total_revenue'])}",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
    
    m.save('taxpayer_density_heatmap.html')
    print("✅ Taxpayer Density Heatmap saved as 'taxpayer_density_heatmap.html'")

def create_interactive_plotly_maps():
    """Create interactive Plotly maps for revenue analysis"""
    print("\n🗺️ Creating Interactive Plotly Maps...")
    
    with engine.connect() as conn:
        # Get revenue by LGA
        df_lga = pd.read_sql("""
            SELECT 
                t.lga,
                SUM(tr.tax_paid) as total_revenue,
                COUNT(DISTINCT t.id) as taxpayers,
                AVG(tr.tax_paid) as avg_tax,
                AVG(t.compliance_score) as compliance
            FROM taxpayers t
            JOIN tax_records tr ON t.id = tr.taxpayer_id
            GROUP BY t.lga
        """, engine)
    
    # Create bubble map
    fig1 = px.scatter_mapbox(
        df_lga,
        lat=[6.5]*len(df_lga),  # Center points
        lon=[3.4]*len(df_lga),
        size='total_revenue',
        color='compliance',
        hover_name='lga',
        hover_data={
            'total_revenue': ':,.2f',
            'taxpayers': True,
            'avg_tax': ':,.2f',
            'compliance': ':.1f'
        },
        size_max=50,
        color_continuous_scale='Viridis',
        title='LGA Revenue Distribution and Compliance Rates'
    )
    
    fig1.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat": 6.5, "lon": 3.4},
        mapbox_zoom=9,
        height=600
    )
    
    fig1.write_html('lga_bubble_map.html')
    print("✅ LGA Bubble Map saved as 'lga_bubble_map.html'")
    
    # Create revenue vs compliance scatter plot
    fig2 = px.scatter(
        df_lga,
        x='total_revenue',
        y='compliance',
        size='taxpayers',
        color='lga',
        hover_name='lga',
        title='Revenue vs Compliance Score by LGA',
        labels={
            'total_revenue': 'Total Revenue (₦)',
            'compliance': 'Compliance Score (%)'
        }
    )
    
    fig2.write_html('revenue_vs_compliance.html')
    print("✅ Revenue vs Compliance Chart saved as 'revenue_vs_compliance.html'")
    
    return df_lga

def create_sector_heatmap():
    """Create heatmap showing sector performance"""
    print("\n🗺️ Creating Sector Performance Heatmap...")
    
    with engine.connect() as conn:
        df_sector = pd.read_sql("""
            SELECT 
                t.sector,
                t.lga,
                COUNT(DISTINCT t.id) as businesses,
                SUM(tr.tax_paid) as total_revenue,
                AVG(t.compliance_score) as compliance
            FROM taxpayers t
            JOIN tax_records tr ON t.id = tr.taxpayer_id
            WHERE t.business_owner = true
            GROUP BY t.sector, t.lga
        """, engine)
    
    # Create heatmap table
    pivot_table = df_sector.pivot_table(
        values='total_revenue',
        index='sector',
        columns='lga',
        aggfunc='sum',
        fill_value=0
    )
    
    # Create heatmap
    fig = px.imshow(
        pivot_table,
        text_auto=True,
        aspect="auto",
        title="Revenue Heatmap by Sector and LGA (₦ Billions)",
        labels=dict(x="LGA", y="Sector", color="Revenue (₦)"),
        color_continuous_scale="RdYlGn"
    )
    
    # Format values in billions
    fig.update_traces(
        texttemplate='₦%{text:,.0f}B',
        textfont={"size": 10}
    )
    
    fig.write_html('sector_lga_heatmap.html')
    print("✅ Sector-LGA Heatmap saved as 'sector_lga_heatmap.html'")
    
    return df_sector

def create_temporal_heatmap():
    """Create temporal heatmap showing revenue trends over time by LGA"""
    print("\n🗺️ Creating Temporal Heatmap...")
    
    with engine.connect() as conn:
        df_temporal = pd.read_sql("""
            SELECT 
                t.lga,
                tr.tax_year,
                SUM(tr.tax_paid) as annual_revenue
            FROM taxpayers t
            JOIN tax_records tr ON t.id = tr.taxpayer_id
            GROUP BY t.lga, tr.tax_year
            ORDER BY t.lga, tr.tax_year
        """, engine)
    
    # Create pivot table for temporal heatmap
    pivot_temp = df_temporal.pivot_table(
        values='annual_revenue',
        index='lga',
        columns='tax_year',
        aggfunc='sum',
        fill_value=0
    )
    
    # Create heatmap
    fig = px.imshow(
        pivot_temp,
        text_auto=True,
        aspect="auto",
        title="Annual Revenue Trends by LGA (₦ Billions)",
        labels=dict(x="Tax Year", y="LGA", color="Revenue (₦)"),
        color_continuous_scale="Blues"
    )
    
    # Format values in billions
    fig.update_traces(
        texttemplate='₦%{text:,.0f}B',
        textfont={"size": 10}
    )
    
    fig.write_html('temporal_revenue_heatmap.html')
    print("✅ Temporal Revenue Heatmap saved as 'temporal_revenue_heatmap.html'")
    
    return df_temporal

def generate_comprehensive_dashboard():
    """Generate a comprehensive dashboard with all maps"""
    print("\n" + "="*80)
    print("GENERATING COMPREHENSIVE REVENUE DASHBOARD")
    print("="*80)
    
    # Create all maps
    df_revenue = create_lga_revenue_map()
    create_taxpayer_density_heatmap()
    create_interactive_plotly_maps()
    create_sector_heatmap()
    create_temporal_heatmap()
    
    # Create a combined HTML dashboard
    print("\n Creating Combined Dashboard...")
    
    dashboard_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lagos Revenue Intelligence Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px; margin-bottom: 20px; }}
            .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }}
            .card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }}
            .card h3 {{ margin: 0 0 10px 0; color: #333; }}
            .card .value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
            .map-container {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .map-title {{ font-size: 20px; font-weight: bold; margin-bottom: 10px; color: #333; }}
            iframe {{ width: 100%; height: 500px; border: none; border-radius: 5px; }}
            .footer {{ text-align: center; padding: 20px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Lagos State Revenue Intelligence Dashboard</h1>
            <p>Comprehensive Tax Revenue Analysis and Visualization</p>
        </div>
        
        <div class="summary">
            <div class="card">
                <h3>Total Revenue</h3>
                <div class="value">{format_naira(df_revenue['total_revenue'].sum())}</div>
            </div>
            <div class="card">
                <h3>Top Performing LGA</h3>
                <div class="value">{df_revenue.iloc[0]['lga']}</div>
                <div style="font-size: 12px;">{format_naira(df_revenue.iloc[0]['total_revenue'])}</div>
            </div>
            <div class="card">
                <h3>Total Taxpayers</h3>
                <div class="value">{df_revenue['taxpayers'].sum():,}</div>
            </div>
            <div class="card">
                <h3>Average Compliance</h3>
                <div class="value">{df_revenue['compliance_score'].mean():.1f}%</div>
            </div>
        </div>
        
        <div class="map-container">
            <div class="map-title"> LGA Revenue Distribution Map</div>
            <iframe src="lga_revenue_map.html"></iframe>
        </div>
        
        <div class="map-container">
            <div class="map-title"> Taxpayer Density Heatmap</div>
            <iframe src="taxpayer_density_heatmap.html"></iframe>
        </div>
        
        <div class="map-container">
            <div class="map-title"> LGA Bubble Map (Revenue vs Compliance)</div>
            <iframe src="lga_bubble_map.html"></iframe>
        </div>
        
        <div class="map-container">
            <div class="map-title"> Revenue vs Compliance Scatter Plot</div>
            <iframe src="revenue_vs_compliance.html"></iframe>
        </div>
        
        <div class="map-container">
            <div class="map-title"> Sector-LGA Revenue Heatmap</div>
            <iframe src="sector_lga_heatmap.html"></iframe>
        </div>
        
        <div class="map-container">
            <div class="map-title"> Temporal Revenue Trends Heatmap</div>
            <iframe src="temporal_revenue_heatmap.html"></iframe>
        </div>
        
        <div class="footer">
            <p>Report Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Lagos State Revenue Management System</p>
        </div>
    </body>
    </html>
    """
    
    with open('revenue_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    print(" Comprehensive Dashboard saved as 'revenue_dashboard.html'")
    print("\n All maps and dashboards generated successfully!")
    print("\n Generated Files:")
    print("   • revenue_dashboard.html - Main dashboard")
    print("   • lga_revenue_map.html - LGA revenue distribution")
    print("   • taxpayer_density_heatmap.html - Taxpayer density heatmap")
    print("   • lga_bubble_map.html - Interactive bubble map")
    print("   • revenue_vs_compliance.html - Scatter plot")
    print("   • sector_lga_heatmap.html - Sector-LGA heatmap")
    print("   • temporal_revenue_heatmap.html - Temporal trends")

if __name__ == "__main__":
    generate_comprehensive_dashboard()