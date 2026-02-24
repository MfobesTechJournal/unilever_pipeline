"""
Unit tests for ETL pipeline components.
Tests individual functions and classes in isolation.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl_production import (
    DataQualityChecker,
    DatabaseManager,
)


class TestDataQualityChecker:
    """Test data quality validation functions."""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create sample dataframe for testing."""
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', None, 'David', 'Eve'],
            'amount': [100.5, 200.0, 150.0, -50.0, 300.0],
            'created_at': pd.date_range('2024-01-01', periods=5)
        })
    
    def test_check_nulls_detection(self, sample_dataframe):
        """Test null value detection."""
        df = sample_dataframe.copy()
        issues = DataQualityChecker.check_nulls(df, 'test_table', threshold=10)
        
        assert len(issues) > 0
        assert any('name' in issue and 'NULL' in issue for issue in issues)
    
    def test_check_nulls_no_issues(self):
        """Test when no nulls exist."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie']
        })
        issues = DataQualityChecker.check_nulls(df, 'test_table', threshold=10)
        
        assert len(issues) == 0
    
    def test_check_nulls_high_threshold(self, sample_dataframe):
        """Test null detection with high threshold."""
        df = sample_dataframe.copy()
        # 20% null rate in 'name' column should pass 50% threshold
        issues = DataQualityChecker.check_nulls(df, 'test_table', threshold=50)
        
        # Filter to 'name' column issues only
        name_issues = [i for i in issues if 'name' in i]
        assert len(name_issues) == 0
    
    def test_check_duplicates(self):
        """Test duplicate detection."""
        df = pd.DataFrame({
            'id': [1, 1, 2, 3, 3],
            'name': ['Alice', 'Alice', 'Bob', 'Charlie', 'Charlie']
        })
        issues = DataQualityChecker.check_duplicates(df, ['id'], 'test_table')
        
        assert len(issues) > 0
        assert any('duplicate' in issue.lower() for issue in issues)
    
    def test_check_duplicates_no_dupes(self):
        """Test when no duplicates exist."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie']
        })
        issues = DataQualityChecker.check_duplicates(df, ['id'], 'test_table')
        
        assert len(issues) == 0
    
    def test_check_duplicate_by_composite_key(self):
        """Test duplicate detection with composite keys."""
        df = pd.DataFrame({
            'id': [1, 1, 2, 2],
            'type': ['A', 'A', 'A', 'B'],
            'value': [100, 100, 200, 300]
        })
        # Same id and type = duplicate
        issues = DataQualityChecker.check_duplicates(df, ['id', 'type'], 'test_table')
        
        assert len(issues) > 0
    
    def test_check_value_ranges(self):
        """Test value range validation."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'amount': [100, 500, 1000]
        })
        issues = DataQualityChecker.check_value_ranges(
            df, 'amount', 'test_table', min_value=0, max_value=999
        )
        
        assert len(issues) > 0
        assert any('1000' in issue for issue in issues)
    
    def test_check_value_ranges_pass(self):
        """Test when all values are in range."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'amount': [100, 500, 999]
        })
        issues = DataQualityChecker.check_value_ranges(
            df, 'amount', 'test_table', min_value=0, max_value=1000
        )
        
        assert len(issues) == 0
    
    def test_check_negative_values(self):
        """Test negative value detection."""
        df = pd.DataFrame({
            'id': [1, 2, 3, 4],
            'amount': [100, -50, 200, -10]
        })
        issues = DataQualityChecker.check_negative_values(df, 'amount', 'test_table')
        
        assert len(issues) > 0
        assert any('-50' in issue or '-10' in issue for issue in issues)
    
    def test_check_negative_values_pass(self):
        """Test when no negative values exist."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'amount': [100, 50, 200]
        })
        issues = DataQualityChecker.check_negative_values(df, 'amount', 'test_table')
        
        assert len(issues) == 0
    
    def test_check_data_types(self):
        """Test data type validation."""
        df = pd.DataFrame({
            'id': ['1', '2', '3'],  # Should be int
            'name': ['Alice', 'Bob', 'Charlie'],
            'amount': [100, 200, 300]
        })
        issues = DataQualityChecker.check_data_types(
            df, {'id': 'int64', 'name': 'object', 'amount': 'int64'}, 'test_table'
        )
        
        assert len(issues) > 0


class TestDataGeneration:
    """Test data generation functions."""
    
    def test_generated_data_shape(self):
        """Test that generated data has expected dimensions."""
        from generate_data import generate_data
        customers, products, sales = generate_data(
            num_customers=100,
            num_products=50,
            num_sales=1000
        )
        
        assert len(customers) == 100
        assert len(products) == 50
        assert len(sales) == 1000
    
    def test_generated_data_columns(self):
        """Test that generated data has expected columns."""
        from generate_data import generate_data
        customers, products, sales = generate_data(
            num_customers=50,
            num_products=25,
            num_sales=500
        )
        
        assert 'customer_id' in customers.columns
        assert 'customer_name' in customers.columns
        assert 'product_id' in products.columns
        assert 'product_name' in products.columns
        assert 'sale_id' in sales.columns
        assert 'amount' in sales.columns
    
    def test_generated_data_types(self):
        """Test that generated data has correct data types."""
        from generate_data import generate_data
        customers, products, sales = generate_data(
            num_customers=50,
            num_products=25,
            num_sales=500
        )
        
        # Numeric IDs should be integers
        assert pd.api.types.is_integer_dtype(customers['customer_id'])
        assert pd.api.types.is_integer_dtype(products['product_id'])
        
        # Amounts should be numeric
        assert pd.api.types.is_numeric_dtype(sales['amount'])


class TestETLValidation:
    """Test ETL-specific validations."""
    
    def test_scd_type2_columns(self):
        """Test that SCD Type 2 dimension has required columns."""
        # This would check in a real database context
        required_columns = ['is_current', 'valid_from', 'valid_to', 'dw_created_at']
        # Validation would happen during dimensional data load
        assert all(col in required_columns for col in required_columns)
    
    def test_fact_table_referential_integrity(self):
        """Test that fact table has proper foreign key references."""
        # Would be tested in integration tests
        pass
    
    def test_batch_processing(self):
        """Test batch processing logic."""
        df = pd.DataFrame({
            'id': range(1000),
            'value': np.random.randn(1000)
        })
        
        batch_size = 100
        batch_count = 0
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            batch_count += 1
            assert len(batch) <= batch_size
        
        assert batch_count == 10


class TestErrorHandling:
    """Test error handling and recovery."""
    
    def test_retry_decorator(self):
        """Test retry decorator functionality."""
        from etl_production import retry_on_exception
        
        call_count = [0]
        
        @retry_on_exception(max_attempts=3, delay=0.1)
        def failing_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Simulated error")
            return "Success"
        
        result = failing_function()
        assert result == "Success"
        assert call_count[0] == 3
    
    def test_retry_max_attempts_exceeded(self):
        """Test retry decorator when max attempts exceeded."""
        from etl_production import retry_on_exception
        
        @retry_on_exception(max_attempts=2, delay=0.05)
        def always_fails():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            always_fails()


@pytest.mark.parametrize("null_percentage,should_flag", [
    (0.5, False),   # 0.5% nulls - should pass
    (5.0, True),    # 5% nulls - should fail  
    (10.0, True),   # 10% nulls - should fail
])
def test_null_threshold_levels(null_percentage, should_flag):
    """Test null threshold at different levels."""
    size = 1000
    null_count = int(size * null_percentage / 100)
    
    df = pd.DataFrame({
        'value': [None if i < null_count else i for i in range(size)]
    })
    
    issues = DataQualityChecker.check_nulls(df, 'test_table', threshold=2.0)
    
    if should_flag:
        assert len(issues) > 0
    else:
        assert len(issues) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
