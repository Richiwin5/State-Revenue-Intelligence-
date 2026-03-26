# run_queries.py

import psycopg2
import pandas as pd

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="lagos_ebs",
    user="postgres",
    password="Richiwin"  # Replace with your actual password
)

# Query 1: Revenue by LGA
print("=" * 50)
print("REVENUE BY LGA")
print("=" * 50)

query1 = """
SELECT lga, SUM(amount_paid) as total_revenue
FROM ebs_master
GROUP BY lga
ORDER BY total_revenue DESC;
"""

df1 = pd.read_sql(query1, conn)
print(df1.to_string())

# Save to CSV
df1.to_csv('revenue_by_lga.csv', index=False)

# Query 2: Compliance by sector
print("\n" + "=" * 50)
print("COMPLIANCE BY SECTOR")
print("=" * 50)

query2 = """
SELECT sector, 
       AVG(CASE WHEN status = 'Paid' THEN 1 ELSE 0 END) as compliance_rate
FROM ebs_master
GROUP BY sector
ORDER BY compliance_rate DESC;
"""

df2 = pd.read_sql(query2, conn)
print(df2.to_string())
df2.to_csv('compliance_by_sector.csv', index=False)

# Query 3: Top taxpayers
print("\n" + "=" * 50)
print("TOP 10 TAXPAYERS")
print("=" * 50)

query3 = """
SELECT full_name, SUM(amount_paid) as total_paid
FROM ebs_master
GROUP BY full_name, taxpayer_id
ORDER BY total_paid DESC
LIMIT 10;
"""

df3 = pd.read_sql(query3, conn)
print(df3.to_string())
df3.to_csv('top_taxpayers.csv', index=False)

# Query 4: Monthly trend
print("\n" + "=" * 50)
print("MONTHLY COLLECTION TREND")
print("=" * 50)

query4 = """
SELECT DATE_TRUNC('month', payment_date) as month,
       COUNT(*) as transactions,
       SUM(amount_paid) as total
FROM payments
WHERE payment_date IS NOT NULL
GROUP BY month
ORDER BY month;
"""

df4 = pd.read_sql(query4, conn)
print(df4.to_string())
df4.to_csv('monthly_trend.csv', index=False)

# Close connection
conn.close()

print("\n Results saved to CSV files!")