"""
PHASE 4: Python ETL Pipeline
Load Module - Database Loading with SCD Type 2
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from typing import List, Dict, Tuple
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manage PostgreSQL database connections"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.conn.cursor()
            logger.info(f"✓ Connected to {self.database}@{self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("✓ Database connection closed")
    
    def execute(self, query: str, params: tuple = None):
        """Execute SQL query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def fetch(self, query: str) -> List[Dict]:
        """Fetch query results"""
        try:
            self.cursor.execute(query)
            columns = [desc[0] for desc in self.cursor.description]
            rows = self.cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Fetch failed: {str(e)}")
            return []


class FactTableLoader:
    """Load data into fact tables"""
    
    def __init__(self, db_conn: DatabaseConnection, table_name: str):
        self.db_conn = db_conn
        self.table_name = table_name
        self.loaded_rows = 0
    
    def bulk_insert(self, dataframe: pd.DataFrame, batch_size: int = 1000):
        """Bulk insert fact records"""
        rows = dataframe.to_dict('records')
        
        # Create INSERT query
        columns = ', '.join(dataframe.columns)
        placeholders = ', '.join(['%s'] * len(dataframe.columns))
        insert_query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        
        # Prepare batch data
        batch_data = [
            tuple(row[col] for col in dataframe.columns) 
            for row in rows
        ]
        
        try:
            execute_batch(self.db_conn.cursor, insert_query, batch_data, page_size=batch_size)
            self.db_conn.conn.commit()
            self.loaded_rows = len(batch_data)
            logger.info(f"✓ Loaded {self.loaded_rows} rows into {self.table_name}")
        except Exception as e:
            self.db_conn.conn.rollback()
            logger.error(f"Bulk insert failed: {str(e)}")
            raise
    
    def upsert(self, dataframe: pd.DataFrame, key_columns: List[str]):
        """Insert or update fact records"""
        for _, row in dataframe.iterrows():
            # Check if record exists
            key_clause = ' AND '.join([f"{col} = %s" for col in key_columns])
            key_values = tuple(row[col] for col in key_columns)
            
            check_query = f"SELECT COUNT(*) FROM {self.table_name} WHERE {key_clause}"
            self.db_conn.cursor.execute(check_query, key_values)
            exists = self.db_conn.cursor.fetchone()[0] > 0
            
            if exists:
                # Update
                set_clause = ', '.join([f"{col} = %s" for col in dataframe.columns if col not in key_columns])
                values = tuple(row[col] for col in dataframe.columns if col not in key_columns) + key_values
                update_query = f"UPDATE {self.table_name} SET {set_clause} WHERE {key_clause}"
                self.db_conn.execute(update_query, values)
            else:
                # Insert
                columns = ', '.join(dataframe.columns)
                placeholders = ', '.join(['%s'] * len(dataframe.columns))
                insert_query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
                values = tuple(row[col] for col in dataframe.columns)
                self.db_conn.execute(insert_query, values)
            
            self.loaded_rows += 1
        
        logger.info(f"✓ Upserted {self.loaded_rows} rows in {self.table_name}")


class DimensionTableLoader:
    """Load data into dimension tables with SCD Type 2 support"""
    
    def __init__(self, db_conn: DatabaseConnection, table_name: str):
        self.db_conn = db_conn
        self.table_name = table_name
        self.loaded_rows = 0
    
    def scd_type_2_load(self, dataframe: pd.DataFrame, key_column: str, 
                       change_columns: List[str], effective_date_col: str = None):
        """Load with SCD Type 2 (track history)"""
        
        if effective_date_col is None:
            dataframe[effective_date_col] = datetime.now().date()
        
        for _, row in dataframe.iterrows():
            key_value = row[key_column]
            
            # Check for existing record
            query = f"SELECT * FROM {self.table_name} WHERE {key_column} = %s AND is_current = TRUE"
            existing = self.db_conn.fetch(query)
            
            if existing:
                # Check if any tracked columns changed
                existing_row = existing[0]
                changed = any(existing_row.get(col) != row[col] for col in change_columns)
                
                if changed:
                    # Mark old record as historical
                    update_query = f"""
                        UPDATE {self.table_name} 
                        SET is_current = FALSE, end_date = %s 
                        WHERE {key_column} = %s AND is_current = TRUE
                    """
                    self.db_conn.execute(update_query, (datetime.now().date(), key_value))
                    
                    # Insert new record
                    row['is_current'] = True
                    row['start_date'] = datetime.now().date()
                    row['end_date'] = None
                    self._insert_dimension_row(row)
            else:
                # New dimension member
                row['is_current'] = True
                row['start_date'] = datetime.now().date()
                row['end_date'] = None
                self._insert_dimension_row(row)
            
            self.loaded_rows += 1
        
        logger.info(f"✓ Loaded {self.loaded_rows} dimension records (SCD Type 2)")
    
    def _insert_dimension_row(self, row: pd.Series):
        """Insert dimension row"""
        columns = ', '.join(row.index)
        placeholders = ', '.join(['%s'] * len(row))
        insert_query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        values = tuple(row.values)
        self.db_conn.execute(insert_query, values)


class DataQualityLogger:
    """Log data quality metrics"""
    
    def __init__(self, db_conn: DatabaseConnection):
        self.db_conn = db_conn
    
    def log_quality_metrics(self, table_name: str, metrics: Dict):
        """Log quality metrics to database"""
        query = """
            INSERT INTO data_quality_log 
            (table_name, metric_name, metric_value, check_timestamp)
            VALUES (%s, %s, %s, %s)
        """
        
        for metric_name, metric_value in metrics.items():
            self.db_conn.execute(
                query,
                (table_name, metric_name, metric_value, datetime.now())
            )
        
        logger.info(f"✓ Logged {len(metrics)} quality metrics for {table_name}")
    
    def log_etl_execution(self, pipeline_name: str, status: str, 
                         records_processed: int, duration_seconds: float):
        """Log ETL execution details"""
        query = """
            INSERT INTO etl_log 
            (pipeline_name, execution_status, records_processed, duration_seconds, execution_timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        self.db_conn.execute(
            query,
            (pipeline_name, status, records_processed, duration_seconds, datetime.now())
        )
        
        logger.info(f"✓ Logged ETL execution: {pipeline_name} - {status}")


if __name__ == "__main__":
    # Example usage
    db = DatabaseConnection('localhost', 5432, 'unilever_warehouse', 'postgres', 'postgres')
    db.connect()
    
    df = pd.DataFrame({
        'product_id': [1, 2, 3],
        'product_name': ['Product A', 'Product B', 'Product C'],
        'price': [10.0, 20.0, 30.0]
    })
    
    loader = FactTableLoader(db, 'fact_sales')
    loader.bulk_insert(df)
    
    db.close()
