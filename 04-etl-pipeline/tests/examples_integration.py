"""
Example Integration: Teams Notifications with Unilever ETL Pipeline

This file demonstrates how to integrate Microsoft Teams notifications
into your existing ETL scripts without modifying the original logic.

Use these patterns as templates for your own implementations.

Author: GitHub Copilot
Date: 2026-02-24
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utilities.teams_notifier import TeamsNotifier


# ============================================================================
# EXAMPLE 1: Wrapper Function Pattern
# ============================================================================

def run_etl_with_notifications(etl_function, pipeline_name="ETL Pipeline"):
    """
    Wrapper function that adds Teams notifications to any ETL function.
    
    Usage:
        from examples_integration import run_etl_with_notifications
        from etl_production import run_etl_pipeline
        
        run_etl_with_notifications(
            run_etl_pipeline,
            pipeline_name="Unilever ETL Pipeline"
        )
    """
    notifier = TeamsNotifier()
    
    try:
        # Notify start
        notifier.send_in_progress(
            pipeline_name,
            "Starting data ingestion and transformation pipeline...",
            details={
                "Start Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Environment": os.getenv("ENV", "development")
            }
        )
        
        # Execute the ETL function
        result = etl_function()
        
        # Notify success
        success_details = {
            "End Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Status": "Completed Successfully"
        }
        
        # Add result details if available
        if isinstance(result, dict):
            success_details.update(result)
        
        notifier.send_success(
            pipeline_name,
            "Data pipeline executed successfully",
            details=success_details
        )
        
        return result
        
    except Exception as e:
        # Notify failure
        notifier.send_failure(
            pipeline_name,
            "Pipeline execution failed",
            error_details=str(e),
            details={
                "Error Type": type(e).__name__,
                "Failure Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
        raise


# ============================================================================
# EXAMPLE 2: Context Manager Pattern (Pythonic)
# ============================================================================

class ETLNotificationContext:
    """
    Context manager for ETL pipeline notifications.
    
    Usage:
        with ETLNotificationContext("Data Ingestion") as notifier:
            # Your ETL code here
            data = load_raw_data()
            transform_data(data)
            load_to_warehouse(data)
            
    Automatically sends success notification on exit, failure if exception.
    """
    
    def __init__(self, pipeline_name, send_start_notification=True):
        self.pipeline_name = pipeline_name
        self.send_start_notification = send_start_notification
        self.notifier = TeamsNotifier()
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        
        if self.send_start_notification:
            self.notifier.send_in_progress(
                self.pipeline_name,
                f"Starting {self.pipeline_name.lower()} process...",
                details={
                    "Start Time": self.start_time.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
        
        return self.notifier
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            # Success
            self.notifier.send_success(
                self.pipeline_name,
                f"{self.pipeline_name} completed successfully",
                details={
                    "Duration": f"{duration:.2f}s",
                    "End Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            )
        else:
            # Failure
            self.notifier.send_failure(
                self.pipeline_name,
                f"{self.pipeline_name} failed during execution",
                error_details=str(exc_val),
                details={
                    "Error Type": exc_type.__name__,
                    "Duration": f"{duration:.2f}s",
                    "Failure Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            )


# ============================================================================
# EXAMPLE 3: Decorator Pattern
# ============================================================================

def notify_on_execution(pipeline_name="ETL Pipeline"):
    """
    Decorator to add Teams notifications to any function.
    
    Usage:
        @notify_on_execution("Data Quality Check")
        def check_data_quality(data):
            # Your function
            return quality_score
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            notifier = TeamsNotifier()
            start_time = datetime.now()
            
            try:
                notifier.send_in_progress(
                    pipeline_name,
                    f"Running {func.__name__}...",
                    details={"Start Time": start_time.strftime("%Y-%m-%d %H:%M:%S")}
                )
                
                result = func(*args, **kwargs)
                
                duration = (datetime.now() - start_time).total_seconds()
                notifier.send_success(
                    pipeline_name,
                    f"{func.__name__} completed successfully",
                    details={"Duration": f"{duration:.2f}s"}
                )
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                notifier.send_failure(
                    pipeline_name,
                    f"{func.__name__} failed",
                    error_details=str(e),
                    details={"Duration": f"{duration:.2f}s"}
                )
                raise
        
        return wrapper
    return decorator


# ============================================================================
# EXAMPLE 4: Class-Based Pattern (For ETL Classes)
# ============================================================================

class NotifiableETLPipeline:
    """
    Base class for ETL pipelines with built-in notification support.
    
    Usage:
        class MyETLPipeline(NotifiableETLPipeline):
            def run(self):
                with self.notification_context():
                    # Your ETL logic
                    data = self.extract()
                    data = self.transform(data)
                    self.load(data)
    """
    
    def __init__(self, pipeline_name):
        self.pipeline_name = pipeline_name
        self.notifier = TeamsNotifier()
    
    def notification_context(self, send_start=True):
        """Get a notification context for the pipeline."""
        return ETLNotificationContext(self.pipeline_name, send_start)
    
    def notify_success(self, message, details=None):
        """Send success notification."""
        self.notifier.send_success(self.pipeline_name, message, details)
    
    def notify_failure(self, message, error_details=None, details=None):
        """Send failure notification."""
        self.notifier.send_failure(
            self.pipeline_name, message, error_details, details
        )
    
    def notify_warning(self, message, details=None):
        """Send warning notification."""
        self.notifier.send_warning(self.pipeline_name, message, details)


# ============================================================================
# EXAMPLE 5: Practical Implementation
# ============================================================================

# Example using the decorator pattern
@notify_on_execution("Data Quality Check")
def validate_data_quality(data):
    """
    Real-world example: Data quality validation with notifications.
    """
    # Your validation logic
    total_records = len(data)
    quality_score = 98.5
    
    return {
        "total_records": total_records,
        "quality_score": quality_score,
        "status": "passed"
    }


# Example using context manager pattern
def example_pipeline_with_context():
    """
    Real-world example: ETL pipeline using context manager.
    """
    with ETLNotificationContext("Daily ETL Pipeline") as notifier:
        # Simulate ETL stages
        print("1. Extracting data from source...")
        raw_data = {"customers": 1000, "products": 500, "sales": 55550}
        
        print("2. Transforming data...")
        # transformation logic
        
        print("3. Loading to warehouse...")
        # load logic
        
        # Send intermediate notification
        notifier.send_info(
            "Daily ETL Pipeline",
            "Data quality validation passed",
            details={
                "Total Records": 55550,
                "Quality Score": "98.5%"
            }
        )
        
        return raw_data


# Example using wrapper pattern
def example_pipeline_with_wrapper():
    """
    Real-world example: ETL pipeline using wrapper function.
    """
    def my_etl():
        # Your ETL logic
        print("Running ETL pipeline...")
        return {
            "records_inserted": 55550,
            "duration_seconds": 154.5,
            "quality_score": "98.5%"
        }
    
    return run_etl_with_notifications(my_etl, "Unilever ETL Pipeline")


# Example using class-based pattern
class UnileverETLPipeline(NotifiableETLPipeline):
    """
    Real-world example: Unilever ETL Pipeline with notifications.
    """
    
    def __init__(self):
        super().__init__("Unilever ETL Pipeline")
    
    def extract(self):
        """Extract phase."""
        print("Extracting data from raw data directory...")
        return {"customers": 1000, "products": 500, "sales": 55550}
    
    def transform(self, data):
        """Transform phase."""
        print("Transforming data...")
        # transformation logic
        return data
    
    def load(self, data):
        """Load phase."""
        print("Loading to data warehouse...")
        # load logic
        return {"records_loaded": sum(len(v) for v in data.values())}
    
    def run(self):
        """Execute pipeline with notifications."""
        with self.notification_context():
            data = self.extract()
            data = self.transform(data)
            result = self.load(data)
            
            # Send completion details
            self.notify_success(
                "Pipeline executed successfully",
                details=result
            )


# ============================================================================
# TEST EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("Teams Notification Integration Examples")
    print("="*70)
    
    # Uncomment to test each pattern:
    
    # Test 1: Context Manager Pattern
    print("\n[Example 1] Testing Context Manager Pattern...")
    try:
        example_pipeline_with_context()
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Wrapper Function Pattern
    print("\n[Example 2] Testing Wrapper Function Pattern...")
    try:
        example_pipeline_with_wrapper()
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Decorator Pattern
    print("\n[Example 3] Testing Decorator Pattern...")
    try:
        result = validate_data_quality([1, 2, 3, 4, 5])
        print(f"Quality check result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Class-Based Pattern
    print("\n[Example 4] Testing Class-Based Pattern...")
    try:
        pipeline = UnileverETLPipeline()
        pipeline.run()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("Check your Teams channel for notifications")
    print("="*70)
