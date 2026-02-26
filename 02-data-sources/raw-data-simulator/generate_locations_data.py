"""
PHASE 2: DATA SOURCE SETUP
Location/Store Dimension Generator
"""

import pandas as pd
import random
import os
from datetime import datetime
from faker import Faker

class LocationGenerator:
    """Generate location/store dimension data"""
    
    STORE_TYPES = ['Flagship', 'Standard', 'Express', 'Warehouse', 'Pop-up']
    REGIONS = ['North', 'South', 'East', 'West', 'Central']
    
    def __init__(self):
        self.locations = []
        self.fake = Faker()
        
    def generate(self, count=100):
        """Generate location records"""
        self.locations = []
        
        for i in range(1, count + 1):
            location = {
                'location_id': f'LOC{i:04d}',
                'store_name': f"Store {i} - {random.choice(self.REGIONS)}",
                'store_type': random.choice(self.STORE_TYPES),
                'region': random.choice(self.REGIONS),
                'country': random.choice(['USA', 'UK', 'Canada', 'Australia', 'India', 'Nigeria']),
                'state_province': self.fake.state(),
                'city': self.fake.city(),
                'postal_code': self.fake.postcode(),
                'address': self.fake.address().replace('\n', ', '),
                'latitude': round(random.uniform(-90, 90), 4),
                'longitude': round(random.uniform(-180, 180), 4),
                'store_manager': self.fake.name(),
                'manager_email': f"manager{i}@unilever.com",
                'store_size_sqft': random.choice([2000, 5000, 10000, 15000, 20000]),
                'employees_count': random.randint(5, 50),
                'opening_date': self.fake.date_between(start_date='-5y'),
                'is_active': random.choices([True, False], weights=[0.9, 0.1])[0],
                'monthly_rent': round(random.uniform(2000, 15000), 2)
            }
            self.locations.append(location)
            
        return self.locations
    
    def save_csv(self, output_path='raw_data'):
        """Save to CSV file"""
        os.makedirs(output_path, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y-%m-%d')
        filename = f"{output_path}/locations_{timestamp}.csv"
        
        df = pd.DataFrame(self.locations)
        df.to_csv(filename, index=False)
        print(f"✓ Generated {len(self.locations)} locations → {filename}")
        return filename


if __name__ == "__main__":
    gen = LocationGenerator()
    gen.generate(100)
    gen.save_csv()
