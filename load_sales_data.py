import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:123456@localhost:5433/unilever_warehouse')

# Check existing data
print('Checking dimension tables...')
df_products = pd.read_sql('SELECT COUNT(*) as count FROM dim_product', engine)
df_customers = pd.read_sql('SELECT COUNT(*) as count FROM dim_customer', engine)
df_dates = pd.read_sql('SELECT COUNT(*) as count FROM dim_date', engine)
print(f'  Products: {df_products["count"].values[0]} rows')
print(f'  Customers: {df_customers["count"].values[0]} rows')
print(f'  Dates: {df_dates["count"].values[0]} rows')

# Load sales with proper foreign keys
print('Loading sales data...')
df_sales = pd.read_csv('raw_data/2026-02-27/sales.csv').head(5000)
df_sales['sale_date'] = pd.to_datetime(df_sales['sale_date'])
df_sales['revenue'] = df_sales['quantity'] * df_sales['unit_price']

# Get dimension mappings
df_date_map = pd.read_sql('SELECT date_key, sale_date::date as sale_date FROM dim_date', engine)
df_date_map['sale_date'] = pd.to_datetime(df_date_map['sale_date'])

df_product_map = pd.read_sql('SELECT product_key, product_id FROM dim_product', engine)
df_customer_map = pd.read_sql('SELECT customer_key, customer_id FROM dim_customer', engine)

# Normalize types for joining
df_product_map['product_id'] = df_product_map['product_id'].astype(str)
df_sales['product_id'] = df_sales['product_id'].astype(str)

# Merge to get all foreign keys
df_sales['sale_date_only'] = df_sales['sale_date'].dt.date
df_date_map['sale_date_only'] = pd.to_datetime(df_date_map['sale_date']).dt.date
df_sales = df_sales.merge(df_date_map[['date_key', 'sale_date_only']], left_on='sale_date_only', right_on='sale_date_only', how='left')

# Join product keys
df_sales = df_sales.merge(df_product_map, on='product_id', how='left')

# Join customer keys
df_sales = df_sales.merge(df_customer_map, on='customer_id', how='left')

print(f'  Sales with valid dates: {df_sales["date_key"].notna().sum()}/{len(df_sales)}')
print(f'  Sales with valid products: {df_sales["product_key"].notna().sum()}/{len(df_sales)}')
print(f'  Sales with valid customers: {df_sales["customer_key"].notna().sum()}/{len(df_sales)}')

df_sales = df_sales[['sale_id', 'product_key', 'customer_key', 'quantity', 'revenue', 'date_key']]
df_sales = df_sales.dropna(subset=['product_key', 'customer_key', 'date_key'])
df_sales['product_key'] = df_sales['product_key'].astype('Int64')
df_sales['customer_key'] = df_sales['customer_key'].astype('Int64')
df_sales['date_key'] = df_sales['date_key'].astype('Int64')

df_sales.to_sql('fact_sales', engine, if_exists='append', index=False)
print(f'✓ Loaded {len(df_sales)} sales records')

# Verify final counts
print('\nFinal data counts:')
for table in ['dim_product', 'dim_customer', 'dim_date', 'fact_sales']:
    count = pd.read_sql(f'SELECT COUNT(*) as count FROM {table}', engine)['count'].values[0]
    print(f'  {table}: {count} rows')

print('Done!')
engine.dispose()
