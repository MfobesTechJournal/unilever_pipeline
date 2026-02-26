"""
Phase 2: Generate Sample Sales CSV Data with Quality Issues

Generates realistic sales data with intentionally injected data quality issues:
- Missing values (nulls)
- Duplicates
- Incorrect formats
- Outliers
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
import json

class SalesDataGenerator:
    """Generate sample sales CSV data with quality issues"""
    
    def __init__(self, num_records=55550, null_rate=0.02, duplicate_rate=0.01, outlier_rate=0.005):
        self.num_records = num_records
        self.null_rate = null_rate
        self.duplicate_rate = duplicate_rate
        self.outlier_rate = outlier_rate
        self.products = self._load_products()
        self.customers = self._load_customers()
    
    def _load_products(self):
        """Load product catalog"""
        return {str(i): f"Product_{i}" for i in range(1, 101)}
    
    def _load_customers(self):
        """Load customer list"""
        return {str(i): f"Customer_{i}" for i in range(1, 4001)}
    
    def generate_sales_data(self, output_path="raw_data"):
        """Generate sales CSV with quality issues"""
        
        Path(output_path).mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        
        csv_path = Path(output_path) / today / "sales.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'sale_id', 'customer_id', 'product_id', 'quantity', 
                'unit_price', 'sale_date', 'sale_status'
            ])
            writer.writeheader()
            
            for i in range(self.num_records):
                record = {
                    'sale_id': i + 1,
                    'customer_id': random.choice(list(self.customers.keys())),
                    'product_id': random.choice(list(self.products.keys())),
                    'quantity': random.randint(1, 100),
                    'unit_price': round(random.uniform(10, 1000), 2),
                    'sale_date': (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
                    'sale_status': random.choice(['completed', 'pending', 'cancelled'])
                }
                
                # Inject nulls
                if random.random() < self.null_rate:
                    record[random.choice(['customer_id', 'product_id', 'quantity'])] = ''
                
                # Inject duplicates
                if random.random() < self.duplicate_rate:
                    record = dict(record)
                
                # Inject outliers
                if random.random() < self.outlier_rate:
                    record['quantity'] = random.randint(1000, 10000)
                    record['unit_price'] = round(random.uniform(10000, 100000), 2)
                
                writer.writerow(record)
        
        print(f"✓ Generated {self.num_records} sales records to {csv_path}")
        return csv_path

if __name__ == "__main__":
    generator = SalesDataGenerator(num_records=55550)
    generator.generate_sales_data()
