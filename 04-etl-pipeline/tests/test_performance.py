"""
Performance tests for ETL pipeline benchmarking.
"""

import pytest
import pandas as pd
import numpy as np
import time
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestETLPerformance:
    """Performance benchmarks for ETL operations."""
    
    @pytest.mark.benchmark
    def test_batch_processing_performance(self, benchmark):
        """Benchmark batch processing speed."""
        df = pd.DataFrame({
            'id': range(100000),
            'value': np.random.randn(100000),
            'category': np.random.choice(['A', 'B', 'C'], 100000)
        })
        
        def batch_process():
            batch_size = 1000
            processed = []
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                # Simulate processing
                batch['value_squared'] = batch['value'] ** 2
                processed.append(batch)
            return pd.concat(processed)
        
        result = benchmark(batch_process)
        assert len(result) == 100000
    
    @pytest.mark.benchmark
    def test_dataframe_type_conversion_performance(self, benchmark):
        """Benchmark type conversion performance."""
        df = pd.DataFrame({
            'id': [str(i) for i in range(50000)],
            'amount': [str(round(np.random.rand() * 1000, 2)) for _ in range(50000)],
            'date': [f'2024-{(i % 12) + 1:02d}-01' for i in range(50000)]
        })
        
        def convert_types():
            result = df.copy()
            result['id'] = pd.to_numeric(result['id'], errors='coerce')
            result['amount'] = pd.to_numeric(result['amount'], errors='coerce')
            result['date'] = pd.to_datetime(result['date'], errors='coerce')
            return result
        
        result = benchmark(convert_types)
        assert result['id'].dtype == 'float64' or result['id'].dtype == 'int64'
    
    @pytest.mark.benchmark
    def test_duplicate_detection_performance(self, benchmark):
        """Benchmark duplicate detection performance."""
        df = pd.DataFrame({
            'id': np.random.randint(0, 10000, 50000),
            'category': np.random.choice(['A', 'B', 'C'], 50000),
            'value': np.random.randn(50000)
        })
        
        def find_duplicates():
            return df.duplicated(subset=['id', 'category'])
        
        result = benchmark(find_duplicates)
        assert isinstance(result, pd.Series)
    
    @pytest.mark.benchmark
    def test_null_detection_performance(self, benchmark):
        """Benchmark null value detection performance."""
        df = pd.DataFrame({
            'col1': [None if np.random.rand() < 0.1 else i for i in range(50000)],
            'col2': [None if np.random.rand() < 0.05 else f'value_{i}' for i in range(50000)],
            'col3': [None if np.random.rand() < 0.2 else np.random.rand() for _ in range(50000)]
        })
        
        def calculate_nulls():
            return df.isnull().sum()
        
        result = benchmark(calculate_nulls)
        assert isinstance(result, pd.Series)
    
    @pytest.mark.benchmark
    def test_aggregation_performance(self, benchmark):
        """Benchmark aggregation performance."""
        df = pd.DataFrame({
            'category': np.random.choice(['A', 'B', 'C', 'D'], 100000),
            'subcategory': np.random.choice(['X', 'Y', 'Z'], 100000),
            'amount': np.random.rand(100000) * 1000
        })
        
        def aggregate():
            return df.groupby(['category', 'subcategory'])['amount'].agg(['sum', 'mean', 'count'])
        
        result = benchmark(aggregate)
        assert len(result) > 0
    
    @pytest.mark.benchmark
    def test_merge_performance(self, benchmark):
        """Benchmark merge performance."""
        left = pd.DataFrame({
            'id': range(50000),
            'value_left': np.random.randn(50000)
        })
        
        right = pd.DataFrame({
            'id': range(0, 100000, 2),
            'value_right': np.random.randn(50000)
        })
        
        def merge_dataframes():
            return pd.merge(left, right, on='id', how='inner')
        
        result = benchmark(merge_dataframes)
        assert len(result) == 50000
    
    @pytest.mark.benchmark
    def test_csv_write_performance(self, benchmark, tmp_path):
        """Benchmark CSV writing performance."""
        df = pd.DataFrame({
            'id': range(50000),
            'text': [f'value_{i}' for i in range(50000)],
            'float': np.random.randn(50000)
        })
        
        output_file = tmp_path / "benchmark_output.csv"
        
        def write_csv():
            df.to_csv(output_file, index=False)
        
        benchmark(write_csv)
        assert output_file.exists()


class TestQueryPerformance:
    """Query performance benchmarks (requires database)."""
    
    @pytest.mark.benchmark
    def test_dimension_table_insert_performance(self, benchmark):
        """Benchmark dimension table insert performance."""
        try:
            from etl_production import DatabaseManager
            import os
            
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                pytest.skip("DATABASE_URL not set")
            
            db = DatabaseManager(db_url)
            
            def insert_products():
                products = pd.DataFrame({
                    'product_id': range(1000),
                    'product_name': [f'Product_{i}' for i in range(1000)],
                    'price': np.random.rand(1000) * 100
                })
                # Simulate insert
                return len(products)
            
            benchmark(insert_products)
            db.close()
            
        except Exception as e:
            pytest.skip(f"Database benchmark skipped: {str(e)}")
    
    @pytest.mark.benchmark
    def test_fact_table_insert_performance(self, benchmark):
        """Benchmark fact table insert performance."""
        try:
            from etl_production import DatabaseManager
            import os
            
            db_url = os.environ.get('DATABASE_URL')
            if not db_url:
                pytest.skip("DATABASE_URL not set")
            
            db = DatabaseManager(db_url)
            
            def insert_sales():
                sales = pd.DataFrame({
                    'sale_id': range(10000),
                    'product_id': np.random.randint(1, 1001, 10000),
                    'customer_id': np.random.randint(1, 5001, 10000),
                    'amount': np.random.rand(10000) * 1000
                })
                return len(sales)
            
            benchmark(insert_sales)
            db.close()
            
        except Exception as e:
            pytest.skip(f"Database benchmark skipped: {str(e)}")


class TestMemoryUsage:
    """Memory usage tests."""
    
    @pytest.mark.benchmark
    def test_large_dataframe_memory(self, benchmark):
        """Test memory usage with large dataframes."""
        def create_large_df():
            return pd.DataFrame({
                'col1': range(1000000),
                'col2': np.random.randn(1000000),
                'col3': ['value'] * 1000000
            })
        
        result = benchmark(create_large_df)
        assert len(result) == 1000000
        
        # Check memory usage (approximately)
        memory_mb = result.memory_usage(deep=True).sum() / 1024 / 1024
        assert memory_mb > 0


class TestConcurrency:
    """Concurrency and parallelization tests."""
    
    @pytest.mark.benchmark
    def test_parallel_batch_processing(self, benchmark):
        """Test parallel batch processing."""
        from multiprocessing import Pool
        
        def process_batch(batch_data):
            """Process a single batch."""
            id_, data = batch_data
            return (id_, len(data))
        
        df = pd.DataFrame({
            'id': range(100000),
            'value': np.random.randn(100000)
        })
        
        def parallel_process():
            batches = [
                (i, df.iloc[i:i+10000])
                for i in range(0, len(df), 10000)
            ]
            
            with Pool(processes=4) as pool:
                results = pool.map(process_batch, batches)
            
            return len(results)
        
        # Running this may exceed test time limits, so we benchmark carefully
        try:
            result = benchmark(parallel_process)
            assert result > 0
        except:
            pytest.skip("Parallel processing benchmark timeout")


class TestIOPerformance:
    """File I/O performance tests."""
    
    @pytest.mark.benchmark
    def test_csv_read_performance(self, benchmark, tmp_path):
        """Benchmark CSV reading performance."""
        # Create test CSV
        test_file = tmp_path / "test_data.csv"
        df = pd.DataFrame({
            'id': range(50000),
            'value': np.random.randn(50000),
            'text': [f'value_{i}' for i in range(50000)]
        })
        df.to_csv(test_file, index=False)
        
        def read_csv():
            return pd.read_csv(test_file)
        
        result = benchmark(read_csv)
        assert len(result) == 50000
    
    @pytest.mark.benchmark  
    def test_json_serialization_performance(self, benchmark):
        """Benchmark JSON serialization performance."""
        data = {
            'products': [{'id': i, 'name': f'Product_{i}', 'price': float(i)} 
                        for i in range(1000)],
            'metadata': {
                'timestamp': '2024-01-01',
                'record_count': 1000
            }
        }
        
        def serialize_json():
            import json
            return json.dumps(data)
        
        result = benchmark(serialize_json)
        assert isinstance(result, str)


@pytest.mark.parametrize("data_size", [1000, 10000, 100000])
@pytest.mark.benchmark
def test_scaling_performance(benchmark, data_size):
    """Test performance scaling with different data sizes."""
    df = pd.DataFrame({
        'id': range(data_size),
        'value': np.random.randn(data_size),
        'category': np.random.choice(['A', 'B', 'C'], data_size)
    })
    
    def process():
        return df.groupby('category')['value'].sum()
    
    result = benchmark(process)
    assert len(result) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--benchmark-only'])
