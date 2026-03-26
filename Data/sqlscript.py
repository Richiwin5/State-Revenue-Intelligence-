import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql+psycopg2://postgres:Richiwin@localhost:5432/lagos_ebs")

def check_table_counts():
    """Check record counts in all tables"""
    tables = [
        "lgas", "wards", "streets", "taxpayers", 
        "tax_records", "businesses", "properties", 
        "assessments", "payments"
    ]
    
    print("\n=== DATABASE TABLE COUNTS ===\n")
    
    with engine.connect() as conn:
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"{table:20} : {count:>10,} records")
    
    print("\n=== SAMPLE DATA ===\n")
    
    # Check lgas
    print("LGAs (first 5):")
    df = pd.read_sql("SELECT * FROM lgas LIMIT 5", engine)
    print(df[['id', 'name']].to_string(index=False))
    
    print("\nTaxpayers (first 3):")
    df = pd.read_sql("SELECT id, full_name, age, sector FROM taxpayers LIMIT 3", engine)
    print(df.to_string(index=False))
    
    # Simple tax records count
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM tax_records"))
        tax_count = result.scalar()
        print(f"\nTax Records Total: {tax_count:,}")
    
    print("\n✅ All data loaded successfully!")

if __name__ == "__main__":
    check_table_counts()                                                                                                                                                                                                                                # import pandas as pd

# from sqlalchemy import create_engine, text, inspect
# from sqlalchemy.types import Integer, Float, String, Date, Numeric, Boolean

# engine = create_engine("postgresql+psycopg2://postgres:Richiwin@localhost:5432/lagos_ebs")

# def load_csv_with_sql_cast(file_path, table, conflict_columns):
#     """
#     Load CSV with explicit column type casting using the target table structure
#     """
#     print(f"\nLoading {file_path} into {table}...")
    
#     try:
#         df = pd.read_csv(file_path)
#         print(f"  Read {len(df)} records from CSV")
        
#         # Create temporary table with the same structure as target table
#         temp_table = f"{table}_temp"
        
#         with engine.connect() as conn:
#             # Drop temp table if exists
#             conn.execute(text(f"DROP TABLE IF EXISTS {temp_table}"))
#             conn.commit()
            
#             # Create temp table with same structure as target table
#             create_temp_query = f"""
#                 CREATE TABLE {temp_table} (LIKE {table} INCLUDING DEFAULTS)
#             """
#             conn.execute(text(create_temp_query))
#             conn.commit()
            
#             # Get column information from the target table to know types
#             inspector = inspect(engine)
#             columns_info = inspector.get_columns(table)
            
#             # Create a mapping of column names to their expected types
#             type_mapping = {}
#             for col_info in columns_info:
#                 type_mapping[col_info['name']] = col_info['type']
            
#             print(f"  Created temporary table with same structure")
            
#             # Process data in chunks to avoid memory issues
#             chunk_size = 1000
#             total_inserted = 0
            
#             for chunk_start in range(0, len(df), chunk_size):
#                 chunk = df.iloc[chunk_start:chunk_start+chunk_size]
                
#                 # Build insert statement with explicit casts based on column types
#                 columns = list(chunk.columns)
#                 values_placeholders = []
#                 values_list = []
                
#                 for _, row in chunk.iterrows():
#                     placeholders = []
#                     for col in columns:
#                         val = row[col]
#                         if pd.isna(val):
#                             placeholders.append('NULL')
#                         else:
#                             # Check if we need to cast based on column type
#                             col_type = type_mapping.get(col)
                            
#                             if col_type and isinstance(col_type, (Numeric, Float)):
#                                 # Cast to numeric
#                                 placeholders.append(f"CAST('{val}' AS NUMERIC)")
#                             elif col_type and isinstance(col_type, (Date)):
#                                 # Cast to date
#                                 placeholders.append(f"CAST('{val}' AS DATE)")
#                             elif col_type and isinstance(col_type, Integer):
#                                 # Cast to integer
#                                 placeholders.append(f"CAST('{val}' AS INTEGER)")
#                             elif col_type and isinstance(col_type, Boolean):
#                                 # Cast to boolean
#                                 placeholders.append(f"CAST('{val}' AS BOOLEAN)")
#                             else:
#                                 # Text - escape single quotes
#                                 val_str = str(val).replace("'", "''")
#                                 placeholders.append(f"'{val_str}'")
                    
#                     values_placeholders.append(f"({', '.join(placeholders)})")
                
#                 if values_placeholders:
#                     # Insert into temporary table
#                     insert_query = f"""
#                         INSERT INTO {temp_table} ({', '.join(columns)})
#                         VALUES {', '.join(values_placeholders)}
#                     """
#                     conn.execute(text(insert_query))
#                     conn.commit()
#                     total_inserted += len(values_placeholders)
            
#             print(f"  Staged {total_inserted} records in temporary table")
            
#             # Perform upsert from temp table to target table
#             conflict_columns_str = ', '.join(conflict_columns)
#             upsert_query = f"""
#                 INSERT INTO {table} 
#                 SELECT * FROM {temp_table}
#                 ON CONFLICT ({conflict_columns_str}) DO NOTHING
#             """
            
#             result = conn.execute(text(upsert_query))
#             conn.commit()
            
#             inserted_count = result.rowcount if hasattr(result, 'rowcount') else len(df)
#             print(f"✅ {table} loaded successfully with {inserted_count} new records!")
            
#             # Clean up temporary table
#             conn.execute(text(f"DROP TABLE IF EXISTS {temp_table}"))
#             conn.commit()
            
#     except Exception as e:
#         print(f"❌ Error loading {table}: {e}")
#         # Clean up temp table if it exists
#         try:
#             with engine.connect() as conn:
#                 conn.execute(text(f"DROP TABLE IF EXISTS {temp_table}"))
#                 conn.commit()
#         except:
#             pass

# # Simplified version for tax_records only if you prefer
# def load_tax_records():
#     """Special handling for tax_records which has numeric fields"""
#     file_path = "tax_records.csv"
#     table = "tax_records"
#     conflict_columns = ["taxpayer_id", "tax_year"]
    
#     print(f"\nLoading {file_path} into {table}...")
    
#     try:
#         # Read CSV and convert numeric columns
#         df = pd.read_csv(file_path)
#         print(f"  Read {len(df)} records from CSV")
        
#         # Convert numeric columns to appropriate types
#         numeric_cols = ['declared_income', 'expected_tax', 'tax_paid']
#         for col in numeric_cols:
#             if col in df.columns:
#                 df[col] = pd.to_numeric(df[col], errors='coerce')
        
#         # Convert date columns if any
#         if 'assessment_date' in df.columns:
#             df['assessment_date'] = pd.to_datetime(df['assessment_date'], errors='coerce').dt.date
        
#         # Create temporary table
#         temp_table = f"{table}_temp"
        
#         with engine.connect() as conn:
#             # Drop temp table if exists
#             conn.execute(text(f"DROP TABLE IF EXISTS {temp_table}"))
#             conn.commit()
            
#             # Create temp table with same structure
#             conn.execute(text(f"CREATE TABLE {temp_table} (LIKE {table} INCLUDING DEFAULTS)"))
#             conn.commit()
            
#             # Insert data in chunks
#             chunk_size = 1000
#             total_inserted = 0
            
#             for chunk_start in range(0, len(df), chunk_size):
#                 chunk = df.iloc[chunk_start:chunk_start+chunk_size]
                
#                 # Build insert statement
#                 columns = list(chunk.columns)
#                 values_list = []
                
#                 for _, row in chunk.iterrows():
#                     placeholders = []
#                     for col in columns:
#                         val = row[col]
#                         if pd.isna(val):
#                             placeholders.append('NULL')
#                         elif isinstance(val, (int, float)):
#                             placeholders.append(str(val))
#                         else:
#                             # Escape single quotes
#                             val_str = str(val).replace("'", "''")
#                             placeholders.append(f"'{val_str}'")
#                     values_list.append(f"({', '.join(placeholders)})")
                
#                 if values_list:
#                     insert_query = f"""
#                         INSERT INTO {temp_table} ({', '.join(columns)})
#                         VALUES {', '.join(values_list)}
#                     """
#                     conn.execute(text(insert_query))
#                     conn.commit()
#                     total_inserted += len(values_list)
            
#             print(f"  Staged {total_inserted} records in temporary table")
            
#             # Perform upsert
#             conflict_columns_str = ', '.join(conflict_columns)
#             upsert_query = f"""
#                 INSERT INTO {table} 
#                 SELECT * FROM {temp_table}
#                 ON CONFLICT ({conflict_columns_str}) DO NOTHING
#             """
            
#             result = conn.execute(text(upsert_query))
#             conn.commit()
            
#             print(f"✅ {table} loaded successfully!")
            
#             # Clean up
#             conn.execute(text(f"DROP TABLE IF EXISTS {temp_table}"))
#             conn.commit()
            
#     except Exception as e:
#         print(f"❌ Error loading {table}: {e}")
#         try:
#             with engine.connect() as conn:
#                 conn.execute(text(f"DROP TABLE IF EXISTS {temp_table}"))
#                 conn.commit()
#         except:
#             pass

# # Use the standard function for all tables
# load_csv_with_sql_cast("lgas.csv", "lgas", ["id"])
# load_csv_with_sql_cast("wards.csv", "wards", ["ward_id"])
# load_csv_with_sql_cast("streets.csv", "streets", ["street_id"])
# load_csv_with_sql_cast("taxpayers.csv", "taxpayers", ["id"])

# # Use special handling for tax_records
# load_tax_records()

# load_csv_with_sql_cast("businesses.csv", "businesses", ["id"])
# load_csv_with_sql_cast("properties.csv", "properties", ["id"])
# load_csv_with_sql_cast("assessments.csv", "assessments", ["assessment_id"])
# load_csv_with_sql_cast("payments.csv", "payments", ["ebs_code"])