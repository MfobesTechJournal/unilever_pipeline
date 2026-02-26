"""
PHASE 4: ETL Pipeline Tests
Unit Tests for Extract, Transform, Load modules
"""

import pytest
import pandas as pd
import tempfile
import os
from datetime import datetime

# Import ETL modules
import sys
sys.path.insert(0, '/opt/unilever_pipeline/04-etl-pipeline')
from extract.extractors import CSVExtractor, DataValidator
from transform.transformers import DataCleaner, DataTransformer


class TestCSVExtractor:
    """Test CSV extraction"""
    
    @pytest.fixture
    def sample_csv(self):
        """Create sample CSV for testing"""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10, 20, 30],
            'name': ['A', 'B', 'C']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            return f.name
    
    def test_csv_extraction(self, sample_csv):
        """Test CSV file extraction"""
        extractor = CSVExtractor(sample_csv)
        result = extractor.extract()
        
        assert len(result) == 3
        assert list(result.columns) == ['id', 'value', 'name']
        assert result['id'].sum() == 6
        
        os.unlink(sample_csv)
    
    def test_missing_file(self):
        """Test handling of missing file"""
        extractor = CSVExtractor('/nonexistent/file.csv')
        result = extractor.extract()
        
        assert result.empty


class TestDataCleaner:
    """Test data cleaning"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data"""
        return pd.DataFrame({
            'id': [1, 1, 2, 3, None],
            'value': [10, 10, 20, 1000, 30],  # 1000 is outlier
            'category': ['A', 'A', 'B', 'C', 'D']
        })
    
    def test_remove_duplicates(self, sample_data):
        """Test duplicate removal"""
        cleaner = DataCleaner(sample_data)
        result = cleaner.remove_duplicates()
        
        assert len(result) == 4  # 1 duplicate removed
    
    def test_handle_nulls(self, sample_data):
        """Test null handling"""
        cleaner = DataCleaner(sample_data)
        result = cleaner.handle_nulls(strategy='drop')
        
        assert len(result) == 4  # 1 row with null removed
    
    def test_remove_outliers(self, sample_data):
        """Test outlier removal"""
        cleaner = DataCleaner(sample_data)
        result = cleaner.remove_outliers(['value'])
        
        assert 1000 not in result['value'].values


class TestDataValidator:
    """Test data validation"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data"""
        return pd.DataFrame({
            'id': [1, 2, 3],
            'email': ['user1@example.com', 'user2@example.com', 'invalid_email'],
            'age': [25, 35, 150]  # 150 is invalid
        })
    
    def test_not_null_check(self, sample_data):
        """Test null validation"""
        validator = DataValidator(sample_data)
        result = validator.check_not_null(['id', 'email'])
        
        assert result == True
    
    def test_value_range_check(self, sample_data):
        """Test value range validation"""
        validator = DataValidator(sample_data)
        result = validator.check_value_range('age', 0, 120)
        
        assert result == False  # 150 is out of range


@pytest.mark.integration
class TestFullETL:
    """Integration tests for full ETL pipeline"""
    
    def test_end_to_end_flow(self):
        """Test complete ETL flow"""
        # Create sample data
        sample_data = pd.DataFrame({
            'id': [1, 2, 3, 3, None],
            'amount': [100, 200, 300, 300, 400],
            'status': ['active', 'active', 'inactive', 'inactive', 'active']
        })
        
        # Clean data
        cleaner = DataCleaner(sample_data)
        cleaned = cleaner.remove_duplicates()
        cleaned = cleaner.handle_nulls(strategy='drop')
        
        # Validate
        validator = DataValidator(cleaned)
        validator.check_not_null(['id', 'amount'])
        
        assert len(cleaned) == 2  # After cleaning
        assert validator.get_quality_score() == 100.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=04-etl-pipeline'])
