"""
PHASE 4: Python ETL Pipeline
Transform Module - Data Cleaning & Validation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCleaner:
    """Clean and standardize data"""
    
    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe.copy()
        self.original_rows = len(self.df)
        self.report = {}
    
    def remove_duplicates(self, subset: List[str] = None, keep: str = 'first') -> pd.DataFrame:
        """Remove duplicate rows"""
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep=keep)
        after = len(self.df)
        removed = before - after
        self.report['duplicates_removed'] = removed
        logger.info(f"✓ Removed {removed} duplicate rows")
        return self.df
    
    def handle_nulls(self, strategy: str = 'drop', fill_value=None) -> pd.DataFrame:
        """Handle null/missing values"""
        before = self.df.isnull().sum().sum()
        
        if strategy == 'drop':
            self.df = self.df.dropna()
        elif strategy == 'fill':
            self.df = self.df.fillna(fill_value)
        elif strategy == 'forward_fill':
            self.df = self.df.fillna(method='ffill')
        
        after = self.df.isnull().sum().sum()
        removed = before - after
        self.report['nulls_handled'] = removed
        logger.info(f"✓ Handled {removed} null values using '{strategy}' strategy")
        return self.df
    
    def standardize_types(self, type_mapping: Dict[str, type]) -> pd.DataFrame:
        """Convert columns to correct data types"""
        for col, dtype in type_mapping.items():
            if col in self.df.columns:
                try:
                    self.df[col] = self.df[col].astype(dtype)
                except Exception as e:
                    logger.warning(f"Could not convert {col} to {dtype}: {str(e)}")
        
        logger.info(f"✓ Standardized {len(type_mapping)} column types")
        return self.df
    
    def standardize_text(self, columns: List[str]) -> pd.DataFrame:
        """Standardize text columns (lowercase, strip whitespace)"""
        for col in columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].str.lower().str.strip()
        
        logger.info(f"✓ Standardized text in {len(columns)} columns")
        return self.df
    
    def remove_outliers(self, numeric_columns: List[str], method: str = 'iqr') -> pd.DataFrame:
        """Remove outliers from numeric columns"""
        before = len(self.df)
        
        for col in numeric_columns:
            if col in self.df.columns and pd.api.types.is_numeric_dtype(self.df[col]):
                if method == 'iqr':
                    Q1 = self.df[col].quantile(0.25)
                    Q3 = self.df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    mask = (self.df[col] >= Q1 - 1.5 * IQR) & (self.df[col] <= Q3 + 1.5 * IQR)
                    self.df = self.df[mask]
        
        after = len(self.df)
        removed = before - after
        self.report['outliers_removed'] = removed
        logger.info(f"✓ Removed {removed} outlier rows")
        return self.df
    
    def get_report(self) -> Dict:
        """Get cleaning report"""
        self.report['original_rows'] = self.original_rows
        self.report['final_rows'] = len(self.df)
        self.report['rows_removed'] = self.original_rows - len(self.df)
        return self.report


class DataValidator:
    """Validate data quality"""
    
    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe.copy()
        self.validation_rules = {}
        self.errors = []
    
    def check_not_null(self, columns: List[str]) -> bool:
        """Check that columns have no null values"""
        for col in columns:
            if col in self.df.columns:
                nulls = self.df[col].isnull().sum()
                if nulls > 0:
                    self.errors.append(f"Column {col} has {nulls} null values")
                    return False
        return True
    
    def check_uniqueness(self, column: str) -> bool:
        """Check that column values are unique"""
        if column in self.df.columns:
            duplicates = self.df[column].duplicated().sum()
            if duplicates > 0:
                self.errors.append(f"Column {column} has {duplicates} duplicate values")
                return False
        return True
    
    def check_value_range(self, column: str, min_val: float, max_val: float) -> bool:
        """Check values are within range"""
        if column in self.df.columns:
            out_of_range = ((self.df[column] < min_val) | (self.df[column] > max_val)).sum()
            if out_of_range > 0:
                self.errors.append(f"Column {column} has {out_of_range} values outside range [{min_val}, {max_val}]")
                return False
        return True
    
    def check_referential_integrity(self, col: str, valid_values: List) -> bool:
        """Check values exist in valid list"""
        if col in self.df.columns:
            invalid = (~self.df[col].isin(valid_values)).sum()
            if invalid > 0:
                self.errors.append(f"Column {col} has {invalid} invalid values")
                return False
        return True
    
    def get_quality_score(self) -> float:
        """Calculate data quality score (0-100)"""
        total_checks = len(self.validation_rules)
        if total_checks == 0:
            return 100.0
        
        passed = total_checks - len(self.errors)
        return (passed / total_checks) * 100
    
    def get_report(self) -> Dict:
        """Get validation report"""
        return {
            'total_rows': len(self.df),
            'quality_score': self.get_quality_score(),
            'errors': self.errors,
            'valid': len(self.errors) == 0
        }


class DataTransformer:
    """Transform data with business logic"""
    
    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe.copy()
    
    def add_derived_columns(self, transformations: Dict[str, callable]) -> pd.DataFrame:
        """Add new columns based on transformations"""
        for col_name, transform_func in transformations.items():
            self.df[col_name] = self.df.apply(transform_func, axis=1)
        
        logger.info(f"✓ Added {len(transformations)} derived columns")
        return self.df
    
    def aggregate_data(self, groupby_cols: List[str], agg_spec: Dict) -> pd.DataFrame:
        """Aggregate data by grouping columns"""
        self.df = self.df.groupby(groupby_cols, as_index=False).agg(agg_spec)
        logger.info(f"✓ Aggregated data by {', '.join(groupby_cols)}")
        return self.df
    
    def pivot_table(self, index: str, columns: str, values: str, aggfunc: str = 'sum') -> pd.DataFrame:
        """Create pivot table"""
        self.df = self.df.pivot_table(index=index, columns=columns, values=values, aggfunc=aggfunc)
        logger.info(f"✓ Created pivot table: {index} × {columns}")
        return self.df
    
    def join_data(self, other_df: pd.DataFrame, join_col: str, how: str = 'left') -> pd.DataFrame:
        """Join with another dataframe"""
        self.df = self.df.merge(other_df, on=join_col, how=how)
        logger.info(f"✓ Joined dataframes on {join_col} ({how} join)")
        return self.df


if __name__ == "__main__":
    # Example usage
    df = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'value': [10, 20, 30, 40, 50],
        'category': ['A', 'B', 'A', 'C', 'B']
    })
    
    cleaner = DataCleaner(df)
    cleaner.remove_duplicates()
    print(cleaner.get_report())
