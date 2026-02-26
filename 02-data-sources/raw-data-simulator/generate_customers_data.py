"""
PHASE 2: DATA SOURCE SETUP
Customer Dimension Generator
"""

import pandas as pd
import random
import os
from datetime import datetime
from faker import Faker

class CustomerGenerator:
    """Generate customer dimension data"""
    
    def __init__(self):
        self.customers = []
        self.fake = Faker()
        
    def generate(self, count=1000):
        """Generate customer records"""
        self.customers = []
        
        for i in range(1, count + 1):
            customer = {
                'customer_id': f'CUST{i:06d}',
                'first_name': self.fake.first_name(),
                'last_name': self.fake.last_name(),
                'email': f"customer{i}@example.com",
                'phone': self.fake.phone_number(),
                'country': random.choice(['USA', 'UK', 'Canada', 'Australia', 'India', 'Nigeria']),
                'state_province': self.fake.state(),
                'city': self.fake.city(),
                'postal_code': self.fake.postcode(),
                'customer_segment': random.choice(['Premium', 'Standard', 'Budget', 'Enterprise']),
                'lifetime_value': round(random.uniform(50, 5000), 2),
                'created_date': self.fake.date_between(start_date='-2y'),
                'is_active': random.choices([True, False], weights=[0.85, 0.15])[0],
                'preferred_contact': random.choice(['Email', 'Phone', 'SMS', 'None'])
            }
            self.customers.append(customer)
            
        return self.customers
    
    def save_csv(self, output_path='raw_data'):
        """Save to CSV file"""
        os.makedirs(output_path, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y-%m-%d')
        filename = f"{output_path}/customers_{timestamp}.csv"
        
        df = pd.DataFrame(self.customers)
        df.to_csv(filename, index=False)
        print(f"✓ Generated {len(self.customers)} customers → {filename}")
        return filename


if __name__ == "__main__":
    gen = CustomerGenerator()
    gen.generate(1000)
    gen.save_csv()
