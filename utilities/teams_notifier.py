"""
Microsoft Teams Notification Module

This module sends formatted notifications to a Microsoft Teams channel
using Incoming Webhook URLs. Supports success, failure, and info notifications
for ETL pipeline monitoring.

Author: Unilever ETL Pipeline
Date: 2026-02-24
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class NotificationType(Enum):
    """Notification type enumeration."""
    SUCCESS = "success"
    FAILURE = "failure"
    INFO = "info"
    WARNING = "warning"
    IN_PROGRESS = "in_progress"


class TeamsNotifier:
    """
    Sends notifications to Microsoft Teams via Incoming Webhook.
    
    Usage:
        notifier = TeamsNotifier()
        notifier.send_success("ETL Pipeline", "Data ingestion completed")
        notifier.send_failure("ETL Pipeline", "Data quality check failed", error_details="...")
    """
    
    WEBHOOK_ENV_VAR = "TEAMS_WEBHOOK"
    
    # Color scheme for Teams cards (hex without #)
    COLORS = {
        NotificationType.SUCCESS: "28a745",      # Green
        NotificationType.FAILURE: "dc3545",      # Red
        NotificationType.WARNING: "ffc107",      # Yellow/Orange
        NotificationType.INFO: "17a2b8",         # Blue
        NotificationType.IN_PROGRESS: "007bff",  # Light Blue
    }
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Teams notifier.
        
        Args:
            webhook_url: Microsoft Teams webhook URL. If None, loads from env var.
        
        Raises:
            ValueError: If webhook URL is not provided and env var is not set.
        """
        self.webhook_url = webhook_url or os.getenv(self.WEBHOOK_ENV_VAR)
        
        if not self.webhook_url:
            raise ValueError(
                f"Teams webhook URL not found. Set {self.WEBHOOK_ENV_VAR} "
                "environment variable or pass webhook_url parameter."
            )
    
    def _create_adaptive_card(
        self,
        title: str,
        message: str,
        notification_type: NotificationType,
        details: Optional[Dict[str, Any]] = None,
        timestamp: bool = True
    ) -> Dict[str, Any]:
        """
        Create a Teams Adaptive Card payload.
        
        Args:
            title: Card title
            message: Main message
            notification_type: Type of notification
            details: Additional details to display
            timestamp: Whether to include timestamp
        
        Returns:
            Adaptive Card JSON payload
        """
        color = self.COLORS[notification_type]
        
        # Build facts array for additional details
        facts = []
        if details:
            for key, value in details.items():
                facts.append({
                    "name": f"{key}:",
                    "value": str(value)
                })
        
        if timestamp:
            facts.append({
                "name": "Timestamp:",
                "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            })
        
        # Emoji mapping for notification types
        emoji_map = {
            NotificationType.SUCCESS: "✅",
            NotificationType.FAILURE: "❌",
            NotificationType.WARNING: "⚠️",
            NotificationType.INFO: "ℹ️",
            NotificationType.IN_PROGRESS: "⏳",
        }
        
        emoji = emoji_map.get(notification_type, "")
        
        # Build the card
        card = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "themeColor": color,
            "summary": f"{emoji} {title}",
            "sections": [
                {
                    "activityTitle": f"{emoji} {title}",
                    "activitySubtitle": "Unilever ETL Pipeline",
                    "text": message,
                    "facts": facts,
                }
            ]
        }
        
        return card
    
    def send_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a notification to Teams.
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            details: Additional details
        
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = self._create_adaptive_card(
                title=title,
                message=message,
                notification_type=notification_type,
                details=details
            )
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Teams notification sent: {title}")
                return True
            else:
                print(f"⚠️ Teams notification failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Teams notification timeout (10s)")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Teams notification error: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error sending Teams notification: {str(e)}")
            return False
    
    def send_success(
        self,
        pipeline: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send a success notification."""
        return self.send_notification(
            title=f"✅ {pipeline} - Success",
            message=message,
            notification_type=NotificationType.SUCCESS,
            details=details
        )
    
    def send_failure(
        self,
        pipeline: str,
        message: str,
        error_details: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send a failure notification."""
        if details is None:
            details = {}
        
        if error_details:
            details["Error"] = error_details
        
        return self.send_notification(
            title=f"❌ {pipeline} - Failed",
            message=message,
            notification_type=NotificationType.FAILURE,
            details=details
        )
    
    def send_warning(
        self,
        pipeline: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send a warning notification."""
        return self.send_notification(
            title=f"⚠️ {pipeline} - Warning",
            message=message,
            notification_type=NotificationType.WARNING,
            details=details
        )
    
    def send_info(
        self,
        pipeline: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send an info notification."""
        return self.send_notification(
            title=f"ℹ️ {pipeline} - Info",
            message=message,
            notification_type=NotificationType.INFO,
            details=details
        )
    
    def send_in_progress(
        self,
        pipeline: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send an in-progress notification."""
        return self.send_notification(
            title=f"⏳ {pipeline} - In Progress",
            message=message,
            notification_type=NotificationType.IN_PROGRESS,
            details=details
        )


if __name__ == "__main__":
    """Test the notifier with sample notifications."""
    notifier = TeamsNotifier()
    
    # Test success notification
    notifier.send_success(
        "ETL Pipeline",
        "Daily data ingestion and transformation completed successfully",
        details={
            "Records Inserted": "55,550",
            "Duration": "2m 34s",
            "Data Quality Score": "98.5%"
        }
    )
    
    # Test failure notification
    notifier.send_failure(
        "ETL Pipeline",
        "Data quality check failed during transformation",
        error_details="Duplicate records detected in sales_fact table",
        details={
            "Pipeline": "etl_dag_production",
            "Task": "data_quality_check",
            "Duplicate Count": "245"
        }
    )
    
    # Test warning notification
    notifier.send_warning(
        "ETL Pipeline",
        "Slow query detected in database optimization",
        details={
            "Query": "SELECT * FROM fact_sales JOIN dim_product...",
            "Duration": "45s (threshold: 30s)",
            "Recommendation": "Create composite index on sale_date"
        }
    )
