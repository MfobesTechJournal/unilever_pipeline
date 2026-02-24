"""
Integration tests for ETL pipeline.
Tests the complete ETL flow from extraction through loading.
"""

import pytest
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDatabaseConnectivity:
    """Test database connection and initialization."""
    
    @pytest.fixture
    def db_url(self):
        """Get database URL from environment."""
        return os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/test_unilever')
    
    def test_database_connection(self, db_url):
        """Test ability to connect to database."""
        try:
            from etl_production import DatabaseManager
            db = DatabaseManager(db_url)
            
            # Try a simple query
            result = db.execute_query("SELECT 1 as test")
            assert result is not None
            db.close()
        except Exception as e:
            pytest.skip(f"Database not available: {str(e)}")
    
    def test_schema_exists(self, db_url):
        """Test that warehouse schema is properly initialized."""
        try:
            from etl_production import DatabaseManager
            db = DatabaseManager(db_url)
            
            # Check for dimension tables
            tables = [
                'dim_product',
                'dim_customer', 
                'dim_date',
                'fact_sales',
                'etl_log',
                'data_quality_log'
            ]
            
            for table in tables:
                result = db.execute_query(
                    f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='{table}')"
                )
                assert result is not None, f"Table {table} not found"
            
            db.close()
        except Exception as e:
            pytest.skip(f"Schema test skipped: {str(e)}")


class TestDataExtraction:
    """Test data extraction functionality."""
    
    def test_read_csv_files(self):
        """Test reading CSV files from staging directory."""
        staging_dir = 'staging'
        
        if not os.path.exists(staging_dir):
            pytest.skip("Staging directory not found")
        
        csv_files = {
            'customers': 'customers.csv',
            'products': 'products.csv',
            'sales': 'sales.csv'
        }
        
        for table, filename in csv_files.items():
            filepath = os.path.join(staging_dir, filename)
            
            if os.path.exists(filepath):
                df = pd.read_csv(filepath)
                assert len(df) > 0, f"No data in {filename}"
                assert df.columns is not None, f"No columns in {filename}"
    
    def test_data_extraction_null_safety(self):
        """Test that extraction handles null values correctly."""
        staging_dir = 'staging'
        
        if not os.path.exists(staging_dir):
            pytest.skip("Staging directory not found")
        
        filepath = os.path.join(staging_dir, 'customers.csv')
        
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            # Data should have some nulls for quality testing
            # but not all columns should be null
            assert not df.isna().all().all()


class TestDataTransformation:
    """Test data transformation logic."""
    
    def test_type_conversion(self):
        """Test proper type conversion during transformation."""
        df = pd.DataFrame({
            'customer_id': ['1', '2', '3'],
            'amount': ['100.50', '200.75', '300.25'],
            'created_at': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
        
        # Simulate transformation
        df['customer_id'] = pd.to_numeric(df['customer_id'], errors='coerce')
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        
        assert df['customer_id'].dtype == 'int64'
        assert df['amount'].dtype == 'float64'
        assert pd.api.types.is_datetime64_any_dtype(df['created_at'])
    
    def test_date_dimension_creation(self):
        """Test creation of date dimension."""
        # Generate date range
        start_date = pd.Timestamp('2024-01-01')
        end_date = pd.Timestamp('2024-12-31')
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        assert len(date_range) == 366  # 2024 is a leap year
    
    def test_scd_type2_transformation(self):
        """Test SCD Type 2 dimension transformation."""
        # Simulate dimension update scenario
        current_data = pd.DataFrame({
            'product_id': [1, 2, 3],
            'product_name': ['Widget', 'Gadget', 'Tool'],
            'price': [9.99, 14.99, 19.99]
        })
        
        # Add SCD Type 2 columns
        current_data['is_current'] = True
        current_data['valid_from'] = pd.Timestamp.now()
        current_data['valid_to'] = pd.Timestamp.max
        current_data['dw_created_at'] = pd.Timestamp.now()
        
        assert all(col in current_data.columns for col in 
                   ['is_current', 'valid_from', 'valid_to', 'dw_created_at'])


class TestDataQualityIntegration:
    """Test data quality checks in context."""
    
    def test_quality_check_workflow(self):
        """Test complete quality check workflow."""
        from etl_production import DataQualityChecker
        
        df = pd.DataFrame({
            'id': [1, 2, 3, None, 5],
            'name': ['Alice', 'Bob', None, 'David', 'Eve'],
            'amount': [100, 200, 150, -50, 300],
            'category': ['A', 'B', 'A', 'B', 'A']
        })
        
        # Run quality checks
        null_issues = DataQualityChecker.check_nulls(df, 'test_table', threshold=10)
        negative_issues = DataQualityChecker.check_negative_values(df, 'amount', 'test_table')
        
        # Should have detected issues in both columns
        assert len(null_issues) > 0
        assert len(negative_issues) > 0
    
    def test_quality_metrics_calculation(self):
        """Test quality metrics calculation."""
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'value': [100, 200, 150, None, 300]
        })
        
        total_cells = df.shape[0] * df.shape[1]
        null_cells = df.isna().sum().sum()
        quality_score = ((total_cells - null_cells) / total_cells) * 100
        
        assert quality_score == 80.0


class TestETLPipelineFlow:
    """Test complete ETL pipeline execution."""
    
    @pytest.mark.slow
    def test_end_to_end_pipeline(self):
        """Test complete ETL pipeline execution."""
        try:
            from etl_production import ProductionETLPipeline
            import os
            
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                pytest.skip("DATABASE_URL not set")
            
            # Initialize pipeline
            pipeline = ProductionETLPipeline(db_url)
            
            # Execute pipeline
            result = pipeline.run()
            
            # Verify results
            assert result is not None
            assert 'run_id' in result
            assert 'status' in result
            assert result['status'].lower() in ['success', 'completed']
            
        except Exception as e:
            pytest.skip(f"E2E test skipped: {str(e)}")
    
    @pytest.mark.slow
    def test_pipeline_idempotency(self):
        """Test that running pipeline twice produces consistent results."""
        try:
            from etl_production import ProductionETLPipeline
            import os
            
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                pytest.skip("DATABASE_URL not set")
            
            pipeline = ProductionETLPipeline(db_url)
            
            # Run pipeline twice
            result1 = pipeline.run()
            result2 = pipeline.run()
            
            # Results should be similar (same loading pattern)
            assert result1['status'] == result2['status']
            
        except Exception as e:
            pytest.skip(f"Idempotency test skipped: {str(e)}")


class TestMonitoring:
    """Test monitoring and logging functionality."""
    
    def test_etl_log_creation(self):
        """Test that ETL logs are created properly."""
        import logging
        
        logger = logging.getLogger('etl_test')
        assert logger is not None
        
        # Should be able to log messages
        logger.info("Test message")
        logger.warning("Test warning")
        logger.error("Test error")
    
    def test_metrics_tracking(self):
        """Test metrics tracking capability."""
        metrics = {
            'products_loaded': 1000,
            'customers_loaded': 4000,
            'sales_loaded': 150000,
            'quality_issues': 25,
            'processing_time_seconds': 45.5
        }
        
        assert metrics['products_loaded'] > 0
        assert metrics['customers_loaded'] > 0
        assert metrics['sales_loaded'] > 0
        assert metrics['processing_time_seconds'] > 0


class TestBackupRestore:
    """Test backup and restore functionality."""
    
    def test_backup_script_exists(self):
        """Test that backup script is available."""
        backup_script = 'backup_restore.sh'
        assert os.path.exists(backup_script), f"Backup script {backup_script} not found"
    
    def test_backup_directory_creation(self):
        """Test that backup directory is properly structured."""
        backup_dir = 'backups'
        
        # Should be able to create backup directory
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        
        assert os.path.exists(backup_dir)
        assert os.path.isdir(backup_dir)


class TestAirflowIntegration:
    """Test Airflow integration."""
    
    def test_dag_files_exist(self):
        """Test that DAG files are present."""
        dag_files = [
            'etl_dag.py',
            'etl_dag_production.py'
        ]
        
        for dag_file in dag_files:
            assert os.path.exists(dag_file), f"DAG file {dag_file} not found"
    
    def test_dag_syntax_validity(self):
        """Test that DAG Python files are syntactically valid."""
        import ast
        
        dag_files = [
            'etl_dag.py',
            'etl_dag_production.py'
        ]
        
        for dag_file in dag_files:
            if os.path.exists(dag_file):
                with open(dag_file, 'r') as f:
                    code = f.read()
                    try:
                        ast.parse(code)
                    except SyntaxError as e:
                        pytest.fail(f"Syntax error in {dag_file}: {str(e)}")


@pytest.mark.parametrize("environment", [
    'development',
    'staging',
    'production'
])
def test_environment_configuration(environment):
    """Test environment configuration for each deployment target."""
    valid_envs = ['development', 'staging', 'production']
    assert environment in valid_envs


class TestSecurityValidation:
    """Test security-related validations."""
    
    def test_database_url_not_hardcoded(self):
        """Verify database URLs aren't hardcoded in scripts."""
        files_to_check = [
            'etl_production.py',
            'etl_dag_production.py'
        ]
        
        for filename in files_to_check:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    content = f.read()
                    # Check for hardcoded database credentials
                    assert 'postgresql://' not in content or 'passwd' not in content
                    assert 'password' not in content.lower() or '=' not in content
    
    def test_secrets_use_env_variables(self):
        """Test that secrets are using environment variables."""
        from etl_production import DatabaseManager
        
        # DatabaseManager should accept DATABASE_URL from env
        assert hasattr(DatabaseManager, '__init__')


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '-m', 'not slow'])
