# # check_local.py
#
# import pandas as pd
# from sqlalchemy import create_engine
#
# # Local database connection
# local_engine = create_engine('postgresql://postgres:Richiwin@localhost:5432/lagos_ebs')
#
# try:
#     # Test connection
#     test_df = pd.read_sql("SELECT 1 as test", local_engine)
#     print("✅ Local database connected successfully!")
#
#     # Check tables
#     tables = pd.read_sql("""
#         SELECT table_name
#         FROM information_schema.tables
#         WHERE table_schema = 'public'
#         ORDER BY table_name
#     """, local_engine)
#
#     print(f"\n📊 Tables found in local database: {len(tables)}")
#     print("=" * 50)
#
#     for table in tables['table_name']:
#         count_df = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", local_engine)
#         count = count_df['count'][0]
#         print(f"✅ {table}: {count:,} records")
#
#     # Check ebs_master specifically
#     ebs_count = pd.read_sql("SELECT COUNT(*) as count FROM ebs_master", local_engine)
#     print(f"\n📊 ebs_master has {ebs_count['count'][0]:,} records")
#
# except Exception as e:
#     print(f"❌ Error: {e}")

# setup_render_database.py

import pandas as pd
from sqlalchemy import create_engine, text
import time

print("=" * 70)
print("🚀 SETTING UP RENDER DATABASE WITH YOUR DATA")
print("=" * 70)

# ============================================
# CONNECTIONS
# ============================================

# Render database (destination)
render_url = "postgresql://richiwin:CrmLD5Q7qi04L3xvRTw6baEdkT0Xovyj@dpg-d72099dactks73f9lc4g-a.oregon-postgres.render.com:5432/lagos_ebs"
render_engine = create_engine(render_url)

# Local database (source)
local_engine = create_engine('postgresql://postgres:Richiwin@localhost:5432/lagos_ebs')

# Test connections
print("\n📡 Testing connections...")
try:
    local_test = pd.read_sql("SELECT 1 as test", local_engine)
    print("✅ Local database connected")
except Exception as e:
    print(f"❌ Local database error: {e}")
    exit(1)

try:
    render_test = pd.read_sql("SELECT 1 as test", render_engine)
    print("✅ Render database connected")
except Exception as e:
    print(f"❌ Render database error: {e}")
    exit(1)

# ============================================
# DROP ALL EXISTING TABLES ON RENDER
# ============================================
print("\n🗑️ Cleaning Render database...")

tables_to_drop = ['heatmap', 'ebs_master', 'receipts', 'payments', 'assessments',
                  'properties', 'businesses', 'tax_records', 'taxpayers',
                  'streets', 'wards', 'lgas']

with render_engine.connect() as conn:
    for table in tables_to_drop:
        try:
            conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            conn.commit()
            print(f"  ✅ Dropped {table}")
        except Exception as e:
            print(f"  ⚠️ Could not drop {table}: {e}")

# ============================================
# CREATE TABLES AND MIGRATE DATA
# ============================================
print("\n📤 Migrating data to Render...")
print("-" * 50)

# Tables in correct order (dependencies first)
table_order = ['lgas', 'wards', 'streets', 'taxpayers', 'tax_records',
               'businesses', 'properties', 'assessments', 'payments',
               'receipts', 'ebs_master', 'heatmap']

migration_results = []

for table in table_order:
    try:
        print(f"\n📊 Processing {table}...")
        start = time.time()

        # Read from local
        df = pd.read_sql(f"SELECT * FROM {table}", local_engine)
        print(f"   📥 Read {len(df):,} records from local")

        if len(df) > 0:
            # For large tables, import in batches
            if len(df) > 20000:
                batch_size = 5000
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i + batch_size]
                    if i == 0:
                        batch.to_sql(table, render_engine, if_exists='replace', index=False)
                    else:
                        batch.to_sql(table, render_engine, if_exists='append', index=False)
                    print(f"   📤 Batch {i // batch_size + 1}: {len(batch)} records")
            else:
                df.to_sql(table, render_engine, if_exists='replace', index=False)

            elapsed = time.time() - start
            print(f"   ✅ Imported {len(df):,} records in {elapsed:.1f}s")
            migration_results.append({'table': table, 'records': len(df), 'status': 'SUCCESS'})
        else:
            print(f"   ⚠️ No data, creating empty table")
            df.to_sql(table, render_engine, if_exists='replace', index=False)
            migration_results.append({'table': table, 'records': 0, 'status': 'EMPTY'})

    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")
        migration_results.append({'table': table, 'records': 0, 'status': f'FAILED'})

# ============================================
# CREATE INDEXES
# ============================================
print("\n🔧 Creating indexes for performance...")

indexes = [
    "CREATE INDEX IF NOT EXISTS idx_lgas_name ON lgas(name)",
    "CREATE INDEX IF NOT EXISTS idx_wards_lga_id ON wards(lga_id)",
    "CREATE INDEX IF NOT EXISTS idx_taxpayers_lga ON taxpayers(lga)",
    "CREATE INDEX IF NOT EXISTS idx_taxpayers_sector ON taxpayers(sector)",
    "CREATE INDEX IF NOT EXISTS idx_assessments_taxpayer ON assessments(taxpayer_id)",
    "CREATE INDEX IF NOT EXISTS idx_payments_assessment ON payments(assessment_id)",
    "CREATE INDEX IF NOT EXISTS idx_ebs_master_lga ON ebs_master(lga)",
    "CREATE INDEX IF NOT EXISTS idx_ebs_master_sector ON ebs_master(sector)",
    "CREATE INDEX IF NOT EXISTS idx_ebs_master_status ON ebs_master(status)",
    "CREATE INDEX IF NOT EXISTS idx_payments_date ON payments(payment_date)",
]

with render_engine.connect() as conn:
    for index_sql in indexes:
        try:
            conn.execute(text(index_sql))
            conn.commit()
            print(f"  ✅ {index_sql[:50]}...")
        except Exception as e:
            print(f"  ⚠️ Could not create: {e}")

# ============================================
# VERIFY MIGRATION
# ============================================
print("\n" + "=" * 70)
print("✅ VERIFYING RENDER DATABASE")
print("=" * 70)

print("\n📊 TABLE COUNTS:")
print("-" * 40)

for result in migration_results:
    try:
        verify_df = pd.read_sql(f"SELECT COUNT(*) as count FROM {result['table']}", render_engine)
        actual = verify_df['count'][0]
        status = "✅" if actual == result['records'] else "⚠️"
        print(f"{status} {result['table']:15} {actual:>10,} records")
    except Exception as e:
        print(f"❌ {result['table']:15} Error: {str(e)[:40]}")

# ============================================
# SUMMARY
# ============================================
print("\n" + "=" * 70)
print("📊 MIGRATION SUMMARY")
print("=" * 70)

total_records = sum([r['records'] for r in migration_results])
successful = len([r for r in migration_results if r['status'] == 'SUCCESS'])
print(f"✅ Tables migrated: {successful}/12")
print(f"📊 Total records: {total_records:,}")

# Show ebs_master details
try:
    ebs_summary = pd.read_sql("""
        SELECT 
            COUNT(*) as assessments,
            COUNT(DISTINCT taxpayer_id) as taxpayers,
            ROUND(SUM(amount_paid) / 1000000000, 2) as revenue_billions
        FROM ebs_master
    """, render_engine)

    print(f"\n💰 EBS_MASTER on Render:")
    print(f"   • Assessments: {ebs_summary['assessments'][0]:,}")
    print(f"   • Taxpayers: {ebs_summary['taxpayers'][0]:,}")
    print(f"   • Revenue: ₦{ebs_summary['revenue_billions'][0]:.2f}B")

except Exception as e:
    print(f"\n⚠️ Could not get ebs_master summary: {e}")

print("\n" + "=" * 70)
print("🎉 RENDER DATABASE IS READY!")
print("=" * 70)