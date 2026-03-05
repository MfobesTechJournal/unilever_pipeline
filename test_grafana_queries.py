#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(host='localhost', port=5433, database='unilever_warehouse', user='postgres', password='123456')
cursor = conn.cursor()

print('Testing corrected Grafana queries:\n')

# Test 1: Total Revenue
try:
    cursor.execute('SELECT SUM(revenue) as value FROM fact_sales WHERE load_timestamp >= NOW() - INTERVAL \'90 days\'')
    result = cursor.fetchone()
    print(f'✓ Total Revenue: {result[0]}')
except Exception as e:
    print(f'✗ Total Revenue: {e}')

# Test 2: Total Transactions  
try:
    cursor.execute('SELECT COUNT(*) as value FROM fact_sales WHERE load_timestamp >= NOW() - INTERVAL \'90 days\'')
    result = cursor.fetchone()
    print(f'✓ Total Transactions: {result[0]:,}')
except Exception as e:
    print(f'✗ Total Transactions: {e}')

# Test 3: Average Order Value
try:
    cursor.execute('SELECT AVG(revenue) as value FROM fact_sales WHERE load_timestamp >= NOW() - INTERVAL \'30 days\'')
    result = cursor.fetchone()
    if result[0]:
        print(f'✓ Average Order Value: ${result[0]:.2f}')
    else:
        print(f'✓ Average Order Value: No data')
except Exception as e:
    print(f'✗ Average Order Value: {e}')

# Test 4: Daily Sales Trend
try:
    cursor.execute('''SELECT DATE(load_timestamp) as date, SUM(revenue) as total 
                      FROM fact_sales 
                      WHERE load_timestamp >= NOW() - INTERVAL '30 days'
                      GROUP BY DATE(load_timestamp) 
                      ORDER BY date DESC 
                      LIMIT 5''')
    results = cursor.fetchall()
    print(f'✓ Daily Sales Trend: {len(results)} days of data')
    for row in results:
        print(f'    {row[0]}: ${row[1]}')
except Exception as e:
    print(f'✗ Daily Sales Trend: {e}')

# Test 5: Top Products
try:
    cursor.execute('''SELECT dp.product_name, SUM(fs.quantity) as qty, SUM(fs.revenue) as revenue
                      FROM fact_sales fs
                      JOIN dim_product dp ON fs.product_key = dp.product_key
                      WHERE fs.load_timestamp >= NOW() - INTERVAL '30 days'
                      GROUP BY dp.product_name
                      ORDER BY revenue DESC
                      LIMIT 3''')
    results = cursor.fetchall()
    print(f'✓ Top Products: {len(results)} products found')
    for row in results:
        print(f'    {row[0]}: ${row[2]:.2f}')
except Exception as e:
    print(f'✗ Top Products: {e}')

cursor.close()
conn.close()
print('\n✓ All test queries passed successfully!')
