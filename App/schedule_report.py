# scheduled_report.py

import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import create_engine
from datetime import datetime

engine = create_engine('postgresql://postgres:Richiwin@localhost:5432/lagos_ebs')


def generate_report():
    """Generate and email weekly report"""

    # Run your queries
    revenue_lga = pd.read_sql("""
        SELECT lga, SUM(amount_paid) as total_revenue
        FROM ebs_master
        GROUP BY lga
        ORDER BY total_revenue DESC
    """, engine)

    # Create HTML email
    html = f"""
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
        </style>
    </head>
    <body>
        <h2>Lagos EBS Weekly Report - {datetime.now().strftime('%Y-%m-%d')}</h2>
        <h3>Revenue by LGA</h3>
        {revenue_lga.to_html(index=False)}
    </body>
    </html>
    """

    # Send email (configure your SMTP settings)
    # ... email sending code here


if __name__ == "__main__":
    generate_report()