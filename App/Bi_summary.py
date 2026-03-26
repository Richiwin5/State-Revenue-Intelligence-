import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

engine = create_engine("postgresql://richiwin:CrmLD5Q7qi04L3xvRTw6baEdkT0Xovyj@dpg-d72099dactks73f9lc4g-a.frankfurt-postgres.render.com/lagos_ebs")

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

def generate_bi_summary():
    """Generate comprehensive Business Intelligence summary"""
    
    print("\n" + "="*80)
    print("LAGOS STATE REVENUE MANAGEMENT SYSTEM - BUSINESS INTELLIGENCE REPORT")
    print("="*80)
    print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # ==================== 1. OVERALL REVENUE SUMMARY ====================
    print("\n\n1. OVERALL REVENUE SUMMARY")
    print("-" * 60)
    
    with engine.connect() as conn:
        # Total revenue from all sources
        result = conn.execute(text("""
            SELECT 
                SUM(tax_paid) as total_tax_revenue,
                COUNT(DISTINCT taxpayer_id) as unique_taxpayers,
                AVG(tax_paid) as avg_tax_per_taxpayer,
                SUM(tax_paid) / COUNT(DISTINCT taxpayer_id) as revenue_per_taxpayer
            FROM tax_records
            WHERE payment_status IN ('Paid', 'Partial')
        """))
        revenue = result.fetchone()
        
        print(f"Total Tax Revenue: {format_naira(revenue[0])}")
        print(f"Unique Taxpayers: {revenue[1]:,}")
        print(f"Average Tax Paid per Taxpayer: {format_naira(revenue[2])}")
        print(f"Revenue per Taxpayer: {format_naira(revenue[3])}")
        
        # Total payments collected
        result = conn.execute(text("""
            SELECT SUM(amount_paid) as total_payments
            FROM payments
            WHERE status = 'successful'
        """))
        payments = result.fetchone()
        print(f"Total Payments Collected: {format_naira(payments[0])}")
    
    # ==================== 2. REVENUE BY LOCAL GOVERNMENT ====================
    print("\n\n2. REVENUE BY LOCAL GOVERNMENT AREA (LGA)")
    print("-" * 60)
    
    with engine.connect() as conn:
        df_lga_revenue = pd.read_sql("""
            SELECT 
                t.lga,
                COUNT(DISTINCT t.id) as taxpayers,
                COUNT(tr.id) as tax_records,
                SUM(tr.tax_paid) as total_revenue,
                AVG(tr.tax_paid) as avg_revenue_per_record,
                AVG(t.compliance_score) as avg_compliance_score,
                SUM(tr.expected_tax) as expected_revenue,
                ROUND(SUM(tr.tax_paid) / NULLIF(SUM(tr.expected_tax), 0) * 100, 2) as collection_rate
            FROM taxpayers t
            JOIN tax_records tr ON t.id = tr.taxpayer_id
            GROUP BY t.lga
            ORDER BY total_revenue DESC
        """, engine)
        
        # Format the DataFrame for display
        df_display = df_lga_revenue.copy()
        df_display['total_revenue'] = df_display['total_revenue'].apply(format_naira)
        df_display['avg_revenue_per_record'] = df_display['avg_revenue_per_record'].apply(format_naira)
        df_display['expected_revenue'] = df_display['expected_revenue'].apply(format_naira)
        print(df_display.to_string(index=False))
        
        # Top 5 LGAs by revenue
        print("\n🏆 TOP 5 LGAs BY REVENUE:")
        for idx, row in df_lga_revenue.head(5).iterrows():
            print(f"  {idx+1}. {row['lga']}: {format_naira(row['total_revenue'])} ({row['collection_rate']}% collection rate)")
        
        # Bottom 5 LGAs by revenue
        print("\n⚠️ BOTTOM 5 LGAs BY REVENUE (Need Attention):")
        for idx, row in df_lga_revenue.tail(5).iterrows():
            print(f"  {idx+1}. {row['lga']}: {format_naira(row['total_revenue'])} ({row['collection_rate']}% collection rate)")
    
    # ==================== 3. REVENUE BY WARD ====================
    print("\n\n3. REVENUE BY WARD (Top 10)")
    print("-" * 60)
    
    with engine.connect() as conn:
        df_ward_revenue = pd.read_sql("""
            SELECT 
                t.lga,
                t.ward,
                COUNT(DISTINCT t.id) as taxpayers,
                SUM(tr.tax_paid) as total_revenue,
                AVG(tr.tax_paid) as avg_revenue,
                AVG(t.compliance_score) as compliance_score
            FROM taxpayers t
            JOIN tax_records tr ON t.id = tr.taxpayer_id
            GROUP BY t.lga, t.ward
            ORDER BY total_revenue DESC
            LIMIT 10
        """, engine)
        
        df_ward_display = df_ward_revenue.copy()
        df_ward_display['total_revenue'] = df_ward_display['total_revenue'].apply(format_naira)
        df_ward_display['avg_revenue'] = df_ward_display['avg_revenue'].apply(format_naira)
        print(df_ward_display.to_string(index=False))
    
    # ==================== 4. REVENUE BY STREET ====================
    print("\n\n4. REVENUE BY STREET (Top 10)")
    print("-" * 60)
    
    with engine.connect() as conn:
        df_street_revenue = pd.read_sql("""
            SELECT 
                t.street,
                t.lga,
                t.ward,
                COUNT(DISTINCT t.id) as taxpayers,
                SUM(tr.tax_paid) as total_revenue,
                AVG(tr.tax_paid) as avg_tax_per_taxpayer
            FROM taxpayers t
            JOIN tax_records tr ON t.id = tr.taxpayer_id
            GROUP BY t.street, t.lga, t.ward
            ORDER BY total_revenue DESC
            LIMIT 10
        """, engine)
        
        df_street_display = df_street_revenue.copy()
        df_street_display['total_revenue'] = df_street_display['total_revenue'].apply(format_naira)
        df_street_display['avg_tax_per_taxpayer'] = df_street_display['avg_tax_per_taxpayer'].apply(format_naira)
        print(df_street_display.to_string(index=False))
    
    # ==================== 5. BUSINESS SECTOR ANALYSIS ====================
    print("\n\n5. BUSINESS SECTOR ANALYSIS")
    print("-" * 60)
    
    with engine.connect() as conn:
        df_sector = pd.read_sql("""
            SELECT 
                t.sector,
                COUNT(DISTINCT t.id) as businesses,
                SUM(tr.tax_paid) as total_tax_paid,
                AVG(tr.tax_paid) as avg_tax_paid,
                AVG(t.compliance_score) as avg_compliance,
                SUM(b.annual_revenue) as total_annual_revenue,
                AVG(b.employee_count) as avg_employees
            FROM taxpayers t
            JOIN tax_records tr ON t.id = tr.taxpayer_id
            LEFT JOIN businesses b ON t.id = b.id
            WHERE t.business_owner = true
            GROUP BY t.sector
            ORDER BY total_tax_paid DESC
        """, engine)
        
        df_sector_display = df_sector.copy()
        df_sector_display['total_tax_paid'] = df_sector_display['total_tax_paid'].apply(format_naira)
        df_sector_display['avg_tax_paid'] = df_sector_display['avg_tax_paid'].apply(format_naira)
        df_sector_display['total_annual_revenue'] = df_sector_display['total_annual_revenue'].apply(format_naira)
        print(df_sector_display.to_string(index=False))
        
        # Top sectors
        print("\n🏆 TOP 5 BUSINESS SECTORS BY TAX CONTRIBUTION:")
        for idx, row in df_sector.head(5).iterrows():
            print(f"  {idx+1}. {row['sector']}: {format_naira(row['total_tax_paid'])} ({row['businesses']} businesses, {row['avg_compliance']:.1f}% compliance)")
        
        # Recommendations for low-performing sectors
        print("\n💡 SECTORS WITH LOW COMPLIANCE (Need Intervention):")
        low_compliance = df_sector[df_sector['avg_compliance'] < 70].head(3)
        for idx, row in low_compliance.iterrows():
            print(f"  • {row['sector']}: {row['avg_compliance']:.1f}% compliance rate - Consider targeted education programs")
    
    # ==================== 6. PROPERTY TAX ANALYSIS ====================
    print("\n\n6. PROPERTY TAX ANALYSIS")
    print("-" * 60)
    
    with engine.connect() as conn:
        df_property = pd.read_sql("""
            SELECT 
                p.property_type,
                COUNT(p.id) as properties,
                SUM(p.estimated_value) as total_value,
                AVG(p.estimated_value) as avg_value,
                SUM(tr.tax_paid) as tax_revenue,
                ROUND(SUM(tr.tax_paid) / NULLIF(SUM(p.estimated_value), 0) * 100, 2) as tax_rate_effective
            FROM properties p
            JOIN taxpayers t ON p.owner_id = t.id
            JOIN tax_records tr ON t.id = tr.taxpayer_id
            GROUP BY p.property_type
            ORDER BY tax_revenue DESC
        """, engine)
        
        df_property_display = df_property.copy()
        df_property_display['total_value'] = df_property_display['total_value'].apply(format_naira)
        df_property_display['avg_value'] = df_property_display['avg_value'].apply(format_naira)
        df_property_display['tax_revenue'] = df_property_display['tax_revenue'].apply(format_naira)
        print(df_property_display.to_string(index=False))
    
    # ==================== 7. REVENUE TRENDS OVER TIME ====================
    print("\n\n7. REVENUE TRENDS OVER TIME")
    print("-" * 60)
    
    with engine.connect() as conn:
        df_trends = pd.read_sql("""
            SELECT 
                tax_year,
                COUNT(*) as assessments,
                SUM(expected_tax) as expected_revenue,
                SUM(tax_paid) as actual_revenue,
                ROUND(SUM(tax_paid) / NULLIF(SUM(expected_tax), 0) * 100, 2) as collection_rate,
                AVG(tax_paid) as avg_tax_paid
            FROM tax_records
            GROUP BY tax_year
            ORDER BY tax_year
        """, engine)
        
        df_trends_display = df_trends.copy()
        df_trends_display['expected_revenue'] = df_trends_display['expected_revenue'].apply(format_naira)
        df_trends_display['actual_revenue'] = df_trends_display['actual_revenue'].apply(format_naira)
        df_trends_display['avg_tax_paid'] = df_trends_display['avg_tax_paid'].apply(format_naira)
        print(df_trends_display.to_string(index=False))
        
        # Year-over-year growth
        if len(df_trends) > 1:
            latest = df_trends.iloc[-1]
            previous = df_trends.iloc[-2]
            growth = ((latest['actual_revenue'] - previous['actual_revenue']) / previous['actual_revenue']) * 100 if previous['actual_revenue'] > 0 else 0
            print(f"\n📈 Year-over-Year Revenue Growth: {growth:.2f}%")
    
    # ==================== 8. PAYMENT CHANNEL ANALYSIS ====================
    print("\n\n8. PAYMENT CHANNEL ANALYSIS")
    print("-" * 60)
    
    with engine.connect() as conn:
        df_payments = pd.read_sql("""
            SELECT 
                payment_channel,
                COUNT(*) as transactions,
                SUM(amount_paid) as total_amount,
                AVG(amount_paid) as avg_transaction,
                COUNT(DISTINCT taxpayer_id) as unique_payers,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM payments
            WHERE status = 'successful'
            GROUP BY payment_channel
            ORDER BY total_amount DESC
        """, engine)
        
        df_payments_display = df_payments.copy()
        df_payments_display['total_amount'] = df_payments_display['total_amount'].apply(format_naira)
        df_payments_display['avg_transaction'] = df_payments_display['avg_transaction'].apply(format_naira)
        print(df_payments_display.to_string(index=False))
        
        # Most popular channel
        top_channel = df_payments.iloc[0]
        print(f"\n💳 Most Popular Channel: {top_channel['payment_channel']} ({top_channel['percentage']}% of transactions)")
    
    # ==================== 9. TAXPAYER COMPLIANCE ANALYSIS (FIXED) ====================
    print("\n\n9. TAXPAYER COMPLIANCE ANALYSIS")
    print("-" * 60)
    
    with engine.connect() as conn:
        df_compliance = pd.read_sql("""
            SELECT 
                compliance_level,
                COUNT(*) as taxpayers,
                AVG(avg_income) as avg_income,
                AVG(avg_tax_paid) as avg_tax_paid,
                SUM(total_tax_paid) as total_tax_paid
            FROM (
                SELECT 
                    CASE 
                        WHEN t.compliance_score >= 80 THEN 'High Compliant'
                        WHEN t.compliance_score >= 60 THEN 'Medium Compliant'
                        ELSE 'Low Compliant'
                    END as compliance_level,
                    t.id as taxpayer_id,
                    t.declared_income as avg_income,
                    AVG(tr.tax_paid) as avg_tax_paid,
                    SUM(tr.tax_paid) as total_tax_paid
                FROM taxpayers t
                JOIN tax_records tr ON t.id = tr.taxpayer_id
                GROUP BY t.id, t.compliance_score, t.declared_income
            ) subquery
            GROUP BY compliance_level
            ORDER BY 
                CASE compliance_level
                    WHEN 'High Compliant' THEN 1
                    WHEN 'Medium Compliant' THEN 2
                    ELSE 3
                END
        """, engine)
        
        if not df_compliance.empty:
            df_compliance_display = df_compliance.copy()
            df_compliance_display['avg_income'] = df_compliance_display['avg_income'].apply(format_naira)
            df_compliance_display['avg_tax_paid'] = df_compliance_display['avg_tax_paid'].apply(format_naira)
            df_compliance_display['total_tax_paid'] = df_compliance_display['total_tax_paid'].apply(format_naira)
            print(df_compliance_display.to_string(index=False))
            
            # Percentage of low compliance
            low_compliance_row = df_compliance[df_compliance['compliance_level'] == 'Low Compliant']
            if not low_compliance_row.empty:
                low_compliance_count = low_compliance_row['taxpayers'].values[0]
                total_taxpayers = df_compliance['taxpayers'].sum()
                print(f"\n⚠️ Low Compliance Taxpayers: {low_compliance_count:,} ({low_compliance_count/total_taxpayers*100:.1f}%)")
            else:
                print(f"\n✅ No low compliance taxpayers detected!")
        else:
            print("No compliance data available")
    
    # ==================== 10. LIRS PERFORMANCE ANALYSIS ====================
    print("\n\n10. LIRS PERFORMANCE ANALYSIS")
    print("-" * 60)
    
    with engine.connect() as conn:
        # Collection efficiency by LGA
        df_lirs = pd.read_sql("""
            SELECT 
                t.lga,
                COUNT(DISTINCT t.id) as taxpayers,
                SUM(tr.expected_tax) as expected,
                SUM(tr.tax_paid) as collected,
                ROUND(SUM(tr.tax_paid) / NULLIF(SUM(tr.expected_tax), 0) * 100, 2) as efficiency,
                AVG(t.compliance_score) as avg_compliance
            FROM taxpayers t
            JOIN tax_records tr ON t.id = tr.taxpayer_id
            GROUP BY t.lga
            ORDER BY efficiency DESC
        """, engine)
        
        df_lirs_display = df_lirs.copy()
        df_lirs_display['expected'] = df_lirs_display['expected'].apply(format_naira)
        df_lirs_display['collected'] = df_lirs_display['collected'].apply(format_naira)
        print("LIRS Collection Efficiency by LGA:")
        print(df_lirs_display.to_string(index=False))
        
        # Overall LIRS performance
        total_expected = df_lirs['expected'].sum()
        total_collected = df_lirs['collected'].sum()
        overall_efficiency = (total_collected / total_expected) * 100 if total_expected > 0 else 0
        
        print(f"\n📊 LIRS OVERALL PERFORMANCE:")
        print(f"  Total Expected Revenue: {format_naira(total_expected)}")
        print(f"  Total Collected: {format_naira(total_collected)}")
        print(f"  Collection Efficiency: {overall_efficiency:.2f}%")
        print(f"  Revenue Gap: {format_naira(total_expected - total_collected)}")
    
    # ==================== 11. KEY RECOMMENDATIONS ====================
    print("\n\n11. KEY RECOMMENDATIONS & ACTION ITEMS")
    print("=" * 60)
    
    # Generate recommendations based on data
    recommendations = []
    
    # Low performing LGAs
    low_performing_lgas = df_lga_revenue[df_lga_revenue['collection_rate'] < 50]['lga'].tolist()
    if low_performing_lgas:
        recommendations.append(f"🎯 TARGET LOW-PERFORMING LGAs: Implement intensive collection drives in {', '.join(low_performing_lgas[:3])} (collection rate < 50%)")
    
    # Low compliance sectors
    if 'avg_compliance' in df_sector.columns:
        low_compliance_sectors = df_sector[df_sector['avg_compliance'] < 70]['sector'].tolist()
        if low_compliance_sectors:
            recommendations.append(f"📚 SECTOR EDUCATION: Launch compliance awareness campaigns in {', '.join(low_compliance_sectors[:3])} sectors")
    
    # Collection efficiency improvement
    if overall_efficiency < 80:
        recommendations.append(f"💰 COLLECTION EFFICIENCY: Current efficiency at {overall_efficiency:.1f}%. Target 85% by improving enforcement")
    
    # Digital payment adoption
    if 'percentage' in df_payments.columns:
        digital_channels = df_payments[df_payments['payment_channel'].isin(['Online', 'Bank Transfer'])]['percentage'].sum() if len(df_payments[df_payments['payment_channel'].isin(['Online', 'Bank Transfer'])]) > 0 else 0
        if digital_channels < 50:
            recommendations.append(f"📱 DIGITAL TRANSFORMATION: Increase digital payment adoption from {digital_channels:.1f}% to 80%")
    
    # Revenue gap
    revenue_gap = total_expected - total_collected
    if revenue_gap > 100000000:  # 100 million
        recommendations.append(f"🎯 REVENUE RECOVERY: Focus on collecting {format_naira(revenue_gap)} in outstanding taxes")
    
    # Property tax opportunities
    if len(df_property) > 0 and 'tax_rate_effective' in df_property.columns:
        commercial_properties = df_property[df_property['property_type'] == 'Commercial']['tax_rate_effective'].values if len(df_property[df_property['property_type'] == 'Commercial']) > 0 else []
        if len(commercial_properties) > 0 and commercial_properties[0] < 2:
            recommendations.append(f"🏢 PROPERTY TAX OPTIMIZATION: Review commercial property valuations to optimize tax revenue")
    
    # List recommendations
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    if not recommendations:
        print("✅ Excellent performance! Maintain current strategies.")
    
    # ==================== 12. EXECUTIVE SUMMARY ====================
    print("\n\n12. EXECUTIVE SUMMARY")
    print("=" * 60)
    
    # Get top LGA
    top_lga = df_lga_revenue.iloc[0]['lga'] if len(df_lga_revenue) > 0 else "N/A"
    top_lga_revenue = df_lga_revenue.iloc[0]['total_revenue'] if len(df_lga_revenue) > 0 else 0
    
    # Get top sector
    top_sector = df_sector.iloc[0]['sector'] if len(df_sector) > 0 else "N/A"
    top_sector_revenue = df_sector.iloc[0]['total_tax_paid'] if len(df_sector) > 0 else 0
    
    # Get high compliance count
    high_compliance = df_compliance[df_compliance['compliance_level'] == 'High Compliant']['taxpayers'].values[0] if len(df_compliance) > 0 and len(df_compliance[df_compliance['compliance_level'] == 'High Compliant']) > 0 else 0
    
    # Get digital channels percentage
    digital_channels = df_payments[df_payments['payment_channel'].isin(['Online', 'Bank Transfer'])]['percentage'].sum() if len(df_payments[df_payments['payment_channel'].isin(['Online', 'Bank Transfer'])]) > 0 else 0
    
    print(f"""
    TOTAL REVENUE: {format_naira(revenue[0])}
    ACTIVE TAXPAYERS: {revenue[1]:,}
    COLLECTION EFFICIENCY: {overall_efficiency:.2f}%
    TOP PERFORMING LGA: {top_lga} ({format_naira(top_lga_revenue)})
    TOP BUSINESS SECTOR: {top_sector} ({format_naira(top_sector_revenue)})
    
    KEY INSIGHTS:
    • {len(df_lga_revenue[df_lga_revenue['collection_rate'] > 80])} LGAs have >80% collection efficiency
    • Digital payments account for {digital_channels:.1f}% of transactions
    • {high_compliance:,} taxpayers are highly compliant
    • Revenue growth trend: {growth:.2f}% year-over-year
    
    URGENT ACTIONS NEEDED:
    • Improve collection in low-performing LGAs
    • Increase digital payment adoption
    • Target low-compliance sectors with education programs
    • Recover outstanding tax revenue of {format_naira(revenue_gap)}
    """)
    
    print("\n" + "="*80)
    print("END OF REPORT")
    print("="*80)

if __name__ == "__main__":
    generate_bi_summary()