# api.py

from fastapi import FastAPI, Query
from sqlalchemy import create_engine, text
import pandas as pd
from typing import Optional

app = FastAPI(title="Lagos EBS API")

# Database connection
engine = create_engine('postgresql://postgres:Richiwin@localhost:5432/lagos_ebs')

@app.get("/")
def read_root():
    return {"message": "Lagos EBS Revenue API"}

@app.get("/revenue/by-lga")
def revenue_by_lga(limit: Optional[int] = 20):
    """Get revenue aggregated by LGA"""
    query = f"""
        SELECT lga, SUM(amount_paid) as total_revenue
        FROM ebs_master
        GROUP BY lga
        ORDER BY total_revenue DESC
        LIMIT {limit}
    """
    df = pd.read_sql(query, engine)
    return df.to_dict(orient='records')

@app.get("/compliance/by-sector")
def compliance_by_sector():
    """Get compliance rate by sector"""
    query = """
        SELECT sector, 
               AVG(CASE WHEN status = 'Paid' THEN 1 ELSE 0 END) as compliance_rate
        FROM ebs_master
        GROUP BY sector
        ORDER BY compliance_rate DESC
    """
    df = pd.read_sql(query, engine)
    return df.to_dict(orient='records')

@app.get("/taxpayers/top")
def top_taxpayers(limit: Optional[int] = 10):
    """Get top taxpayers by payment"""
    query = f"""
        SELECT full_name, SUM(amount_paid) as total_paid
        FROM ebs_master
        GROUP BY full_name, taxpayer_id
        ORDER BY total_paid DESC
        LIMIT {limit}
    """
    df = pd.read_sql(query, engine)
    return df.to_dict(orient='records')

@app.get("/revenue/monthly")
def monthly_trend():
    """Get monthly revenue trend"""
    query = """
        SELECT DATE_TRUNC('month', payment_date) as month,
               COUNT(*) as transactions,
               SUM(amount_paid) as total
        FROM payments
        WHERE payment_date IS NOT NULL
        GROUP BY month
        ORDER BY month
    """
    df = pd.read_sql(query, engine)
    return df.to_dict(orient='records')

@app.get("/revenue/by-lga/{lga}")
def revenue_by_specific_lga(lga: str):
    """Get detailed revenue for a specific LGA"""
    query = f"""
        SELECT ward, SUM(amount_paid) as revenue
        FROM ebs_master
        WHERE lga = '{lga}'
        GROUP BY ward
        ORDER BY revenue DESC
    """
    df = pd.read_sql(query, engine)
    return df.to_dict(orient='records')