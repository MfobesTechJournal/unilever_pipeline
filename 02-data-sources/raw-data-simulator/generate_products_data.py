"""
PHASE 2: DATA SOURCE SETUP
Product Dimension Generator
"""

import pandas as pd
import random
import os
from datetime import datetime
import csv

class ProductGenerator:
    """Generate product dimension data"""
    
    CATEGORIES = [
        "Hair Care", "Skin Care", "Bath & Body", "Oral Care", 
        "Deodorants", "Shampoo", "Conditioner", "Face Wash",
        "Soap", "Lotion", "Perfume", "Toothpaste"
    ]
    
    BRANDS = [
        "Dove", "VO5", "Lipton", "Hellmann's", "Ben & Jerry's",
        "Magnum", "Axe", "Rexona", "Tresemmé", "Sunsilk",
        "Lux", "Pond's", "Vaseline", "Suave", "St. Ives"
    ]
    
    def __init__(self):
        self.products = []
        
    def generate(self, count=500):
        """Generate product records"""
        self.products = []
        
        for i in range(1, count + 1):
            product = {
                'product_id': f'PROD{i:05d}',
                'product_name': f"{random.choice(self.BRANDS)} {random.choice(self.CATEGORIES)}",
                'category': random.choice(self.CATEGORIES),
                'brand': random.choice(self.BRANDS),
                'unit_price': round(random.uniform(2.99, 49.99), 2),
                'unit_cost': round(random.uniform(0.99, 20.00), 2),
                'supplier': f"Supplier_{random.randint(1, 50)}",
                'sku': f"SKU{i:08d}",
                'created_date': datetime.now().isoformat(),
                'active': random.choices([True, False], weights=[0.95, 0.05])[0]
            }
            self.products.append(product)
            
        return self.products
    
    def save_csv(self, output_path='raw_data'):
        """Save to CSV file"""
        os.makedirs(output_path, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y-%m-%d')
        filename = f"{output_path}/products_{timestamp}.csv"
        
        df = pd.DataFrame(self.products)
        df.to_csv(filename, index=False)
        print(f"✓ Generated {len(self.products)} products → {filename}")
        return filename


if __name__ == "__main__":
    gen = ProductGenerator()
    gen.generate(500)
    gen.save_csv()
