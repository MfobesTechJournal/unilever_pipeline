"""
PHASE 4: Python ETL Pipeline
Extract Module - Data Source Connectors
"""

import pandas as pd
import json
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Base class for all data extractors"""
    
    def __init__(self, source_path: str):
        self.source_path = source_path
        self.data = None
        self.row_count = 0
        
    @abstractmethod
    def extract(self) -> pd.DataFrame:
        """Extract data from source"""
        pass
    
    def validate_source(self) -> bool:
        """Validate source exists and is accessible"""
        if not os.path.exists(self.source_path):
            logger.error(f"Source not found: {self.source_path}")
            return False
        return True


class CSVExtractor(BaseExtractor):
    """Extract data from CSV files"""
    
    def __init__(self, source_path: str, delimiter: str = ',', encoding: str = 'utf-8'):
        super().__init__(source_path)
        self.delimiter = delimiter
        self.encoding = encoding
    
    def extract(self) -> pd.DataFrame:
        """Extract CSV file"""
        if not self.validate_source():
            return pd.DataFrame()
        
        try:
            logger.info(f"Extracting CSV: {self.source_path}")
            self.data = pd.read_csv(
                self.source_path,
                delimiter=self.delimiter,
                encoding=self.encoding,
                dtype_backend='numpy_nullable'
            )
            self.row_count = len(self.data)
            logger.info(f"✓ Extracted {self.row_count} rows from CSV")
            return self.data
        except Exception as e:
            logger.error(f"CSV extraction failed: {str(e)}")
            return pd.DataFrame()


class JSONExtractor(BaseExtractor):
    """Extract data from JSON files"""
    
    def extract(self) -> pd.DataFrame:
        """Extract JSON file"""
        if not self.validate_source():
            return pd.DataFrame()
        
        try:
            logger.info(f"Extracting JSON: {self.source_path}")
            with open(self.source_path, 'r') as f:
                data = json.load(f)
            
            # Handle both list and dict formats
            if isinstance(data, list):
                self.data = pd.DataFrame(data)
            elif isinstance(data, dict):
                self.data = pd.DataFrame([data])
            else:
                logger.error("JSON format not supported")
                return pd.DataFrame()
            
            self.row_count = len(self.data)
            logger.info(f"✓ Extracted {self.row_count} rows from JSON")
            return self.data
        except Exception as e:
            logger.error(f"JSON extraction failed: {str(e)}")
            return pd.DataFrame()


class ExcelExtractor(BaseExtractor):
    """Extract data from Excel files"""
    
    def __init__(self, source_path: str, sheet_name: int = 0):
        super().__init__(source_path)
        self.sheet_name = sheet_name
    
    def extract(self) -> pd.DataFrame:
        """Extract Excel file"""
        if not self.validate_source():
            return pd.DataFrame()
        
        try:
            logger.info(f"Extracting Excel: {self.source_path}")
            self.data = pd.read_excel(
                self.source_path,
                sheet_name=self.sheet_name
            )
            self.row_count = len(self.data)
            logger.info(f"✓ Extracted {self.row_count} rows from Excel")
            return self.data
        except Exception as e:
            logger.error(f"Excel extraction failed: {str(e)}")
            return pd.DataFrame()


class DatabaseExtractor(BaseExtractor):
    """Extract data from PostgreSQL database"""
    
    def __init__(self, connection_string: str, query: str):
        super().__init__(connection_string)
        self.query = query
    
    def extract(self) -> pd.DataFrame:
        """Extract from database using SQL query"""
        try:
            logger.info(f"Extracting from database: {self.query[:50]}...")
            import psycopg2
            conn = psycopg2.connect(self.source_path)
            self.data = pd.read_sql(self.query, conn)
            self.row_count = len(self.data)
            conn.close()
            logger.info(f"✓ Extracted {self.row_count} rows from database")
            return self.data
        except Exception as e:
            logger.error(f"Database extraction failed: {str(e)}")
            return pd.DataFrame()


class IncrementalExtractor(BaseExtractor):
    """Extract only new/changed records since last run"""
    
    def __init__(self, source_path: str, timestamp_column: str, last_run_time: datetime):
        super().__init__(source_path)
        self.timestamp_column = timestamp_column
        self.last_run_time = last_run_time
    
    def extract(self) -> pd.DataFrame:
        """Extract incremental data"""
        csv_extractor = CSVExtractor(self.source_path)
        full_data = csv_extractor.extract()
        
        if full_data.empty:
            return pd.DataFrame()
        
        # Filter by timestamp
        mask = pd.to_datetime(full_data[self.timestamp_column]) > self.last_run_time
        self.data = full_data[mask]
        self.row_count = len(self.data)
        logger.info(f"✓ Extracted {self.row_count} incremental rows")
        return self.data


if __name__ == "__main__":
    # Example usage
    csv_ext = CSVExtractor("data.csv")
    df = csv_ext.extract()
    print(f"Extracted {csv_ext.row_count} rows")
