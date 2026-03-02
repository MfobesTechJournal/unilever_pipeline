import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:123456@localhost:5433/unilever_warehouse')

# Check existing data
print('Checking dimension tables...')
products = pd.read_sql('SELECT COUNT(*) as count FROM dim_product', engine)['count'].values[0]
customers = pd.read_sql('SELECT COUNT(*) as count FROM dim_customer', engine)['count'].values[0]
dates = pd.read_sql('SELECT COUNT(*) as count FROM dim_date', engine)['count'].values[0]
print(f'  Products: {products}')
print(f'  Customers: {customers}')
print(f'  Dates: {dates}')

# Load sales and transform
print('Loading sales...')
df_sales = pd.read_csv('raw_data/2026-02-27/sales.csv').head(5000)

# Create SQL-based mapping instead of pandas merge
conn = engine.connect()

print('  Inserting into fact_sales...')
batch_size = 1000
inserted = 0
failed = 0

for i in range(0, len(df_sales), batch_size):
    batch = df_sales.iloc[i:i+batch_size]
    
    for idx, row in batch.iterrows():
        try:
            sql = text("""
                INSERT INTO fact_sales (sale_id, product_key, customer_key, quantity, revenue, date_key)
                SELECT :sale_id,
                       dp.product_key,
                       dc.customer_key,
                       :quantity,
                       :revenue,
                       dd.date_key
                FROM dim_product dp, dim_customer dc, dim_date dd
                WHERE dp.product_id = :product_id
                  AND dc.customer_id = :customer_id
                  AND dd.sale_date = :sale_date::date
            """)
            
            conn.execute(sql, {
                'sale_id': row['sale_id'],
                'product_id': str(row['product_id']),
                'customer_id': int(row['customer_id']),
                'quantity': int(row['quantity']),
                'revenue': float(row['quantity']) * float(row['unit_price']),
                'sale_date': pd.to_datetime(row['sale_date']).strftime('%Y-%m-%d')
            })
            inserted += 1
        except Exception as e:
            failed += 1

conn.commit()
conn.close()

print(f'  ✓ Inserted {inserted} records, failed: {failed}')

# Final verification
counts = {
    'dim_product': pd.read_sql('SELECT COUNT(*) as c FROM dim_product', engine)['c'].values[0],
    'dim_customer': pd.read_sql('SELECT COUNT(*) as c FROM dim_customer', engine)['c'].values[0],
    'dim_date': pd.read_sql('SELECT COUNT(*) as c FROM dim_date', engine)['c'].values[0],
    'fact_sales': pd.read_sql('SELECT COUNT(*) as c FROM fact_sales', engine)['c'].values[0],
}

print('\n✓ Data load complete! Final counts:')
for table, count in counts.items():
    print(f'  {table}: {count}')
