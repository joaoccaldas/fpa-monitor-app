"""Sprint 1: Real-Time KPI Alert Engine
Manages alert configuration, background metric monitoring, and notifications.
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

# Alert storage (in-memory for simplicity; use database in production)
alerts_config: List[Dict[str, Any]] = []
alert_history: List[Dict[str, Any]] = []

# Configuration from environment variables
ALERT_CHECK_INTERVAL = int(os.getenv('ALERT_CHECK_INTERVAL', 300))  # Default 5 minutes
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
SENDGRID_FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL', 'alerts@example.com')
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN', '')
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', '#alerts')

# Initialize Slack client
slack_client = None
if SLACK_BOT_TOKEN:
    try:
        slack_client = WebClient(token=SLACK_BOT_TOKEN)
        logger.info("Slack client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Slack client: {e}")

# Initialize scheduler
scheduler = BackgroundScheduler()


class AlertEngine:
    """Manages alert configuration and monitoring."""
    
    @staticmethod
    def create_alert(alert_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new alert configuration.
        
        Args:
            alert_config: Dict with keys:
                - name: Alert name
                - metric: Column/metric to monitor
                - threshold: Threshold value
                - condition: 'above' or 'below'
                - notification_channels: List of channels ['email', 'slack']
                - recipients: List of email addresses or Slack users
        
        Returns:
            Created alert configuration with ID
        """
        alert_id = len(alerts_config) + 1
        alert = {
            'id': alert_id,
            'name': alert_config.get('name', f'Alert {alert_id}'),
            'metric': alert_config.get('metric'),
            'threshold': float(alert_config.get('threshold', 0)),
            'condition': alert_config.get('condition', 'above'),
            'notification_channels': alert_config.get('notification_channels', ['email']),
            'recipients': alert_config.get('recipients', []),
            'enabled': True,
            'created_at': datetime.now().isoformat(),
            'last_checked': None,
            'last_triggered': None
        }
        alerts_config.append(alert)
        logger.info(f"Alert created: {alert['name']} (ID: {alert_id})")
        return alert
    
    @staticmethod
    def get_alerts() -> List[Dict[str, Any]]:
        """Get all alert configurations."""
        return alerts_config
    
    @staticmethod
    def get_alert(alert_id: int) -> Dict[str, Any]:
        """Get a specific alert by ID."""
        for alert in alerts_config:
            if alert['id'] == alert_id:
                return alert
        return None
    
    @staticmethod
    def update_alert(alert_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing alert configuration."""
        for alert in alerts_config:
            if alert['id'] == alert_id:
                alert.update(updates)
                logger.info(f"Alert updated: {alert['name']} (ID: {alert_id})")
                return alert
        return None
    
    @staticmethod
    def delete_alert(alert_id: int) -> bool:
        """Delete an alert configuration."""
        global alerts_config
        for i, alert in enumerate(alerts_config):
            if alert['id'] == alert_id:
                deleted_alert = alerts_config.pop(i)
                logger.info(f"Alert deleted: {deleted_alert['name']} (ID: {alert_id})")
                return True
        return False
    
    @staticmethod
    def toggle_alert(alert_id: int, enabled: bool) -> bool:
        """Enable or disable an alert."""
        for alert in alerts_config:
            if alert['id'] == alert_id:
                alert['enabled'] = enabled
                logger.info(f"Alert {'enabled' if enabled else 'disabled'}: {alert['name']}")
                return True
        return False
    
    @staticmethod
    def check_alerts(dataframe: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Check all enabled alerts against current data.
        
        Args:
            dataframe: Current dataset to check
        
        Returns:
            List of triggered alerts
        """
        if dataframe is None or dataframe.empty:
            logger.warning("No data available for alert checking")
            return []
        
        triggered_alerts = []
        
        for alert in alerts_config:
            if not alert['enabled']:
                continue
            
            try:
                metric = alert['metric']
                threshold = alert['threshold']
                condition = alert['condition']
                
                # Update last checked time
                alert['last_checked'] = datetime.now().isoformat()
                
                # Check if metric exists in dataframe
                if metric not in dataframe.columns:
                    logger.warning(f"Metric '{metric}' not found in dataframe for alert {alert['name']}")
                    continue
                
                # Get current value (use last row for time-series data)
                current_value = dataframe[metric].iloc[-1]
                
                # Check condition
                is_triggered = False
                if condition == 'above' and current_value > threshold:
                    is_triggered = True
                elif condition == 'below' and current_value < threshold:
                    is_triggered = True
                
                if is_triggered:
                    alert_event = {
                        'alert_id': alert['id'],
                        'alert_name': alert['name'],
                        'metric': metric,
                        'threshold': threshold,
                        'condition': condition,
                        'current_value': float(current_value),
                        'triggered_at': datetime.now().isoformat()
                    }
                    triggered_alerts.append(alert_event)
                    alert['last_triggered'] = alert_event['triggered_at']
                    
                    # Log to history
                    alert_history.append(alert_event)
                    
                    # Send notifications
                    AlertEngine._send_notifications(alert, alert_event)
                    
                    logger.info(f"Alert triggered: {alert['name']} - {metric}={current_value} {condition} {threshold}")
            
            except Exception as e:
                logger.error(f"Error checking alert {alert['name']}: {e}")
        
        return triggered_alerts
    
    @staticmethod
    def _send_notifications(alert: Dict[str, Any], event: Dict[str, Any]):
        """Send notifications through configured channels."""
        channels = alert.get('notification_channels', [])
        recipients = alert.get('recipients', [])
        
        # Prepare notification message
        message = (
            f"🚨 Alert Triggered: {alert['name']}\n"
            f"Metric: {event['metric']}\n"
            f"Current Value: {event['current_value']:.2f}\n"
            f"Threshold: {event['condition']} {event['threshold']}\n"
            f"Time: {event['triggered_at']}"
        )
        
        # Send email notifications
        if 'email' in channels and recipients:
            AlertEngine._send_email(recipients, alert['name'], message)
        
        # Send Slack notifications
        if 'slack' in channels:
            AlertEngine._send_slack(message)
    
    @staticmethod
    def _send_email(recipients: List[str], subject: str, message: str):
        """Send email notification via SendGrid."""
        if not SENDGRID_API_KEY:
            logger.warning("SendGrid API key not configured, skipping email notification")
            return
        
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            
            for recipient in recipients:
                mail = Mail(
                    from_email=SENDGRID_FROM_EMAIL,
                    to_emails=recipient,
                    subject=f"FP&A Alert: {subject}",
                    html_content=f"<pre>{message}</pre>"
                )
                
                response = sg.send(mail)
                logger.info(f"Email sent to {recipient}: Status {response.status_code}")
        
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    @staticmethod
    def _send_slack(message: str):
        """Send Slack notification."""
        if not slack_client:
            logger.warning("Slack client not configured, skipping Slack notification")
            return
        
        try:
            response = slack_client.chat_postMessage(
                channel=SLACK_CHANNEL,
                text=message
            )
            logger.info(f"Slack message sent to {SLACK_CHANNEL}")
        
        except SlackApiError as e:
            logger.error(f"Failed to send Slack notification: {e.response['error']}")
    
    @staticmethod
    def get_alert_history(limit: int = 50) -> List[Dict[str, Any]]:
        """Get alert history (most recent first)."""
        return alert_history[-limit:][::-1]
    
    @staticmethod
    def clear_history():
        """Clear alert history."""
        global alert_history
        alert_history = []
        logger.info("Alert history cleared")


def start_scheduler(dataframe_getter):
    """
    Start the background scheduler for alert checking.
    
    Args:
        dataframe_getter: Callable that returns the current dataframe
    """
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return
    
    def check_job():
        """Background job to check alerts."""
        try:
            df = dataframe_getter()
            if df is not None and not df.empty:
                triggered = AlertEngine.check_alerts(df)
                if triggered:
                    logger.info(f"{len(triggered)} alert(s) triggered")
        except Exception as e:
            logger.error(f"Error in alert check job: {e}")
    
    # Schedule the job
    scheduler.add_job(
        check_job,
        'interval',
        seconds=ALERT_CHECK_INTERVAL,
        id='alert_checker',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Alert scheduler started (interval: {ALERT_CHECK_INTERVAL}s)")


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Alert scheduler stopped")
