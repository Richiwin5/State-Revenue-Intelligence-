import random
import numpy as np
import pandas as pd
from faker import Faker
from datetime import date

fake = Faker()

# ----------------------------
# CONFIGURATION
# ----------------------------
NUM_LGAS = 20
NUM_TAXPAYERS = 20000
NUM_BUSINESSES = 5000
YEARS = [2022, 2023, 2024, 2025, 2026]
NUM_WARDS_PER_LGA = 5
NUM_STREETS_PER_WARD = 10
SECTORS = ["Tech", "Retail", "Manufacturing", "Finance", "Real Estate", "Hospitality", "Transport"]

# ----------------------------
# LGA DEFINITIONS
# ----------------------------
lga_names = [
    "Ikeja", "Lekki", "Surulere", "Alimosho", "Eti-Osa",
    "Yaba", "Victoria Island", "Ikorodu", "Epe", "Badagry",
    "Apapa", "Oshodi-Isolo", "Mushin", "Agege", "Kosofe",
    "Somolu", "Amuwo-Odofin", "Ifako-Ijaiye", "Shomolu", "Ajah"
]

lga_income_multiplier = {
    "Lekki": 4,
    "Victoria Island": 4,
    "Eti-Osa": 3,
    "Ikeja": 2.5,
    "Surulere": 2,
    "Yaba": 2,
    "Alimosho": 1,
    "Ikorodu": 1,
    "Agege": 1,
}

# ----------------------------
# TAX LOGIC
# ----------------------------
def calculate_tax(income):
    if income < 500_000:
        return income * 0.05
    elif income < 2_000_000:
        return income * 0.10
    elif income < 10_000_000:
        return income * 0.18
    else:
        return income * 0.25

# ----------------------------
# GENERATE LGA, WARDS, STREETS
# ----------------------------
lgas, wards, streets = [], [], []

for i, name in enumerate(lga_names):
    lga_id = i + 1
    lgas.append({
        "id": lga_id,
        "name": name,
        "population": random.randint(150_000, 1_500_000),
        "area_sq_km": round(random.uniform(20, 200),2),
        "urbanization_level": random.choice(["High","Medium","Low"]),
        "average_property_value": random.randint(5_000_000,200_000_000)
    })
    
    for w in range(1, NUM_WARDS_PER_LGA+1):
        ward_id = len(wards) + 1
        ward_name = f"Ward {w} {name}"
        wards.append({"ward_id": ward_id, "lga_id": lga_id, "ward_name": ward_name})
        
        for s in range(1, NUM_STREETS_PER_WARD+1):
            street_id = len(streets) + 1
            street_name = f"Street {s} {ward_name}"
            streets.append({"street_id": street_id, "ward_id": ward_id, "street_name": street_name})

lgas_df = pd.DataFrame(lgas)
wards_df = pd.DataFrame(wards)
streets_df = pd.DataFrame(streets)

# ----------------------------
# GENERATE TAXPAYERS
# ----------------------------
taxpayers = []
for i in range(NUM_TAXPAYERS):
    lga = random.choice(lga_names)
    multiplier = lga_income_multiplier.get(lga,1.5)
    base_income = random.randint(200_000,5_000_000)
    income = base_income * multiplier
    property_value = income * random.uniform(1.5,4)
    
    lga_id = lgas_df.loc[lgas_df['name']==lga,'id'].values[0]
    ward = random.choice(wards_df.loc[wards_df['lga_id']==lga_id,'ward_name'].values)
    ward_id = wards_df.loc[wards_df['ward_name']==ward,'ward_id'].values[0]
    street = random.choice(streets_df.loc[streets_df['ward_id']==ward_id,'street_name'].values)
    
    taxpayers.append({
        "id": i+1,
        "full_name": fake.name(),
        "age": random.randint(21,70),
        "occupation": fake.job(),
        "lga": lga,
        "ward": ward,
        "street": street,
        "declared_income": round(income,2),
        "property_value": round(property_value,2),
        "business_owner": random.choice([True, False]),
        "sector": random.choice(SECTORS),
        "compliance_score": round(random.uniform(40,100),2),
        "created_at": fake.date_this_decade()
    })

taxpayers_df = pd.DataFrame(taxpayers)

# ----------------------------
# TAX RECORDS (Multi-Year)
# ----------------------------
tax_records = []
for taxpayer in taxpayers:
    for year in YEARS:
        income = taxpayer["declared_income"]
        expected_tax = calculate_tax(income)
        compliance_factor = taxpayer["compliance_score"]/100
        tax_paid = expected_tax * compliance_factor
        tax_records.append({
            "taxpayer_id": taxpayer["id"],
            "tax_year": year,
            "declared_income": income,
            "expected_tax": round(expected_tax,2),
            "tax_paid": round(tax_paid,2),
            "payment_status": (
                "Paid" if compliance_factor>0.9 else
                "Partial" if compliance_factor>0.5 else
                "Unpaid"
            )
        })

tax_records_df = pd.DataFrame(tax_records)

# ----------------------------
# BUSINESSES
# ----------------------------
businesses = []
for i in range(NUM_BUSINESSES):
    lga = random.choice(lga_names)
    lga_id = lgas_df.loc[lgas_df['name']==lga,'id'].values[0]
    ward = random.choice(wards_df.loc[wards_df['lga_id']==lga_id,'ward_name'].values)
    ward_id = wards_df.loc[wards_df['ward_name']==ward,'ward_id'].values[0]
    street = random.choice(streets_df.loc[streets_df['ward_id']==ward_id,'street_name'].values)
    
    businesses.append({
        "id": i+1,
        "business_name": fake.company(),
        "sector": random.choice(SECTORS),
        "lga": lga,
        "ward": ward,
        "street": street,
        "annual_revenue": random.randint(5_000_000,500_000_000),
        "employee_count": random.randint(5,500),
        "registered": random.choice([True, False])
    })

businesses_df = pd.DataFrame(businesses)

# ----------------------------
# PROPERTIES
# ----------------------------
properties = []
for i in range(NUM_TAXPAYERS):
    properties.append({
        "id": i+1,
        "owner_id": i+1,
        "lga": taxpayers[i]["lga"],
        "ward": taxpayers[i]["ward"],
        "street": taxpayers[i]["street"],
        "property_type": random.choice(["Residential","Commercial"]),
        "estimated_value": round(taxpayers[i]["property_value"],2)
    })

properties_df = pd.DataFrame(properties)

# ----------------------------
# EBS REVENUE ITEMS
# ----------------------------
revenue_items = [
    {"id":1, "name":"PAYE", "mda":"LIRS"},
    {"id":2, "name":"Direct Assessment", "mda":"LIRS"},
    {"id":3, "name":"Land Use Charge", "mda":"Ministry of Finance"},
    {"id":4, "name":"Business Premises Levy", "mda":"Ministry of Commerce"},
]

# ----------------------------
# ASSESSMENTS & PAYMENTS
# ----------------------------
assessments = []
payments = []
receipts = []

def generate_ebs_code():
    return f"EBS-{random.randint(100000,999999)}"

assessment_id_counter = 1
payment_id_counter = 1
receipt_id_counter = 1

for taxpayer in taxpayers:
    for year in YEARS:
        revenue = random.choice(revenue_items)
        base_amount = taxpayer["declared_income"] * random.uniform(0.05,0.25)
        due_date = fake.date_between(start_date=date(year,1,1), end_date=date(year,12,31))
        
        assessments.append({
            "assessment_id": assessment_id_counter,
            "taxpayer_id": taxpayer["id"],
            "revenue_item": revenue["name"],
            "mda": revenue["mda"],
            "lga": taxpayer["lga"],
            "ward": taxpayer["ward"],
            "street": taxpayer["street"],
            "sector": taxpayer["sector"],
            "amount_due": round(base_amount,2),
            "due_date": due_date,
            "status": "pending"
        })

        if random.random()>0.3:
            amount_paid = base_amount * random.uniform(0.7,1.0)
            payment_date = fake.date_between(start_date=due_date, end_date=date(year,12,31))
            payments.append({
                "payment_id": payment_id_counter,
                "assessment_id": assessment_id_counter,
                "taxpayer_id": taxpayer["id"],
                "ebs_code": generate_ebs_code(),
                "amount_paid": round(amount_paid,2),
                "payment_channel": random.choice(["Bank Transfer","POS","Online","USSD"]),
                "payment_date": payment_date,
                "status": "successful" if amount_paid>=base_amount*0.9 else "partial"
            })
            receipts.append({
                "receipt_id": receipt_id_counter,
                "payment_id": payment_id_counter,
                "receipt_number": f"RCT-{random.randint(100000,999999)}",
                "generated_at": payment_date
            })
            payment_id_counter+=1
            receipt_id_counter+=1

        assessment_id_counter+=1

assessments_df = pd.DataFrame(assessments)
payments_df = pd.DataFrame(payments)
receipts_df = pd.DataFrame(receipts)

# ----------------------------
# MASTER TABLE - FIXED VERSION
# ----------------------------
print("Creating master table...")

# Start from assessments
ebs_master_df = assessments_df.copy()

# Debug: Check available columns
print("Available columns in assessments_df:", assessments_df.columns.tolist())

# Merge payments safely
if not payments_df.empty:
    ebs_master_df = pd.merge(
        ebs_master_df,
        payments_df[['assessment_id', 'amount_paid', 'payment_channel', 'payment_date', 'status']],
        on='assessment_id',
        how='left',
        suffixes=('', '_payment')
    )
    
    # Rename payment status to avoid conflict
    if 'status_payment' in ebs_master_df.columns:
        ebs_master_df.rename(columns={'status_payment': 'payment_status'}, inplace=True)
        ebs_master_df.drop(columns=['status'], inplace=True, errors='ignore')
        ebs_master_df.rename(columns={'payment_status': 'status'}, inplace=True)

# Merge taxpayer info
taxpayer_info = taxpayers_df[['id', 'full_name', 'lga', 'ward', 'street', 'sector']].copy()
taxpayer_info.rename(columns={'id': 'taxpayer_id'}, inplace=True)

ebs_master_df = pd.merge(
    ebs_master_df,
    taxpayer_info,
    on='taxpayer_id',
    how='left'
)

# Debug: Check columns after merge
print("Columns after merge:", ebs_master_df.columns.tolist())

# Make sure all needed columns exist
required_columns = ['lga', 'ward', 'street', 'sector', 'amount_paid', 'payment_channel', 'payment_date']
for col in required_columns:
    if col not in ebs_master_df.columns:
        print(f"Adding missing column: {col}")
        ebs_master_df[col] = None

# Fill missing payment status
if 'status' not in ebs_master_df.columns:
    ebs_master_df['status'] = 'Unpaid'
else:
    ebs_master_df['status'] = ebs_master_df['status'].fillna('Unpaid')

# Debug: Check final columns before selection
print("Final columns before selection:", ebs_master_df.columns.tolist())

# Select final columns safely - check which ones actually exist
final_columns = [
    'taxpayer_id', 'full_name', 'lga', 'ward', 'street', 'sector', 
    'revenue_item', 'amount_due', 'amount_paid', 'payment_channel', 
    'payment_date', 'status'
]

# Filter to only include columns that exist
available_final_columns = [col for col in final_columns if col in ebs_master_df.columns]
missing_columns = set(final_columns) - set(available_final_columns)

if missing_columns:
    print(f"Warning: These columns are missing and will be skipped: {missing_columns}")
    # Add missing columns with None values
    for col in missing_columns:
        ebs_master_df[col] = None
    available_final_columns = final_columns  # Now all columns exist

ebs_master_df = ebs_master_df[final_columns]

# ----------------------------
# HEATMAP
# ----------------------------
print("Creating heatmap...")
heatmap_df = ebs_master_df.groupby(["lga", "ward"])["amount_paid"].sum().reset_index()
heatmap_df.columns = ["lga", "ward", "total_revenue"]

# ----------------------------
# EXPORT CSVs
# ----------------------------
print("Exporting CSV files...")

lgas_df.to_csv("lgas.csv", index=False)
wards_df.to_csv("wards.csv", index=False)
streets_df.to_csv("streets.csv", index=False)
taxpayers_df.to_csv("taxpayers.csv", index=False)
tax_records_df.to_csv("tax_records.csv", index=False)
businesses_df.to_csv("businesses.csv", index=False)
properties_df.to_csv("properties.csv", index=False)
assessments_df.to_csv("assessments.csv", index=False)
payments_df.to_csv("payments.csv", index=False)
receipts_df.to_csv("receipts.csv", index=False)
ebs_master_df.to_csv("ebs_master.csv", index=False)
heatmap_df.to_csv("heatmap.csv", index=False)

# Print summary
print("\n" + "="*50)
print("✅ Upgraded Lagos EBS Synthetic Dataset Generated Successfully!")
print("="*50)
print(f"📊 Files created:")
print(f"   - lgas.csv: {len(lgas_df)} records")
print(f"   - wards.csv: {len(wards_df)} records")
print(f"   - streets.csv: {len(streets_df)} records")
print(f"   - taxpayers.csv: {len(taxpayers_df)} records")
print(f"   - tax_records.csv: {len(tax_records_df)} records")
print(f"   - businesses.csv: {len(businesses_df)} records")
print(f"   - properties.csv: {len(properties_df)} records")
print(f"   - assessments.csv: {len(assessments_df)} records")
print(f"   - payments.csv: {len(payments_df)} records")
print(f"   - receipts.csv: {len(receipts_df)} records")
print(f"   - ebs_master.csv: {len(ebs_master_df)} records")
print(f"   - heatmap.csv: {len(heatmap_df)} records")
print("="*50)

# Display first few rows of master table
print("\n🔍 Sample of master table:")
print(ebs_master_df.head())