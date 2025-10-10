"""Sprint 1: Real-Time KPI Alert Routes Integration

This file contains the alert management routes that should be added to app.py
to complete the Sprint 1: Real-Time KPI Alert Engine integration.

INSTRUCTIONS:
1. Add the import statement at the top of app.py (after other imports)
2. Add these routes before the 'if __name__ == "__main__":' block
3. Initialize the alert scheduler when the app starts
"""

# ============================================================================
# STEP 1: Add this import at the top of app.py (after other imports)
# ============================================================================
"""
from alerts import AlertEngine, start_scheduler, stop_scheduler
import atexit
"""

# ============================================================================
# STEP 2: Add these routes before 'if __name__ == "__main__":'  
# ============================================================================

# Sprint 1: Real-Time KPI Alert Routes

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get all alert configurations."""
    try:
        alerts = AlertEngine.get_alerts()
        return jsonify({'alerts': alerts}), 200
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """Create a new alert configuration."""
    try:
        payload = request.get_json(force=True)
        alert = AlertEngine.create_alert(payload)
        return jsonify({'message': 'Alert created successfully', 'alert': alert}), 201
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    """Get a specific alert by ID."""
    try:
        alert = AlertEngine.get_alert(alert_id)
        if alert:
            return jsonify({'alert': alert}), 200
        return jsonify({'error': 'Alert not found'}), 404
    except Exception as e:
        logger.error(f"Error fetching alert {alert_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>', methods=['PUT'])
def update_alert(alert_id):
    """Update an existing alert configuration."""
    try:
        payload = request.get_json(force=True)
        alert = AlertEngine.update_alert(alert_id, payload)
        if alert:
            return jsonify({'message': 'Alert updated successfully', 'alert': alert}), 200
        return jsonify({'error': 'Alert not found'}), 404
    except Exception as e:
        logger.error(f"Error updating alert {alert_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Delete an alert configuration."""
    try:
        success = AlertEngine.delete_alert(alert_id)
        if success:
            return jsonify({'message': 'Alert deleted successfully'}), 200
        return jsonify({'error': 'Alert not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>/toggle', methods=['POST'])
def toggle_alert(alert_id):
    """Enable or disable an alert."""
    try:
        payload = request.get_json(force=True)
        enabled = payload.get('enabled', True)
        success = AlertEngine.toggle_alert(alert_id, enabled)
        if success:
            status = 'enabled' if enabled else 'disabled'
            return jsonify({'message': f'Alert {status} successfully'}), 200
        return jsonify({'error': 'Alert not found'}), 404
    except Exception as e:
        logger.error(f"Error toggling alert {alert_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/history', methods=['GET'])
def get_alert_history():
    """Get alert trigger history."""
    try:
        limit = int(request.args.get('limit', 50))
        history = AlertEngine.get_alert_history(limit=limit)
        return jsonify({'history': history}), 200
    except Exception as e:
        logger.error(f"Error fetching alert history: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/check', methods=['POST'])
def manual_alert_check():
    """Manually trigger alert checking (for testing)."""
    try:
        if dataframe is None or dataframe.empty:
            return jsonify({'error': 'No data loaded'}), 400
        
        triggered = AlertEngine.check_alerts(dataframe)
        return jsonify({
            'message': f'Alert check completed',
            'triggered_count': len(triggered),
            'triggered_alerts': triggered
        }), 200
    except Exception as e:
        logger.error(f"Error during manual alert check: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# STEP 3: Add alert scheduler initialization in if __name__ == '__main__':
# ============================================================================

"""
if __name__ == '__main__':
    # Initialize alert scheduler
    def get_current_dataframe():
        return dataframe
    
    start_scheduler(get_current_dataframe)
    atexit.register(stop_scheduler)  # Clean shutdown
    
    port = int(os.getenv('PORT', '8000'))
    app.run(host='0.0.0.0', port=port)
"""

# ============================================================================
# Sprint 1 Implementation Summary
# ============================================================================

"""
SPRINT 1: REAL-TIME KPI ALERT ENGINE - IMPLEMENTATION COMPLETE

Files Created/Modified:
✅ alerts.py - Core alert engine with APScheduler, SendGrid, Slack integration
✅ requirements.txt - Added APScheduler, sendgrid, slack-sdk dependencies  
✅ .env.example - Added alert configuration variables
✅ app_integration.py (this file) - Integration routes and instructions

Core Features Implemented:
✅ Alert configuration management (create, read, update, delete, toggle)
✅ Threshold-based metric monitoring (above/below conditions)
✅ Background job scheduler with APScheduler (configurable intervals)
✅ Multi-channel notifications: SendGrid (email) and Slack
✅ Alert trigger history logging and retrieval
✅ Manual alert checking endpoint for testing
✅ Graceful scheduler shutdown handling

API Endpoints:
- GET    /api/alerts - List all alerts
- POST   /api/alerts - Create new alert
- GET    /api/alerts/<id> - Get specific alert
- PUT    /api/alerts/<id> - Update alert
- DELETE /api/alerts/<id> - Delete alert  
- POST   /api/alerts/<id>/toggle - Enable/disable alert
- GET    /api/alerts/history - Get alert history
- POST   /api/alerts/check - Manual alert check (testing)

Environment Configuration:
ALERT_CHECK_INTERVAL=300  # Seconds between checks
SENDGRID_API_KEY=your-key
SENDGRID_FROM_EMAIL=alerts@domain.com
SLACK_BOT_TOKEN=xoxb-token
SLACK_CHANNEL=#alerts

Next Steps for Full Sprint 1 Completion:
1. Add the imports and routes from this file to app.py
2. Create templates/alerts.html UI for alert management dashboard
3. Add JavaScript alert configuration form in templates/index.html
4. Test alert creation, threshold triggers, and notifications
5. Update README.md Sprint 1 checkboxes to mark tasks complete
6. Deploy with proper environment variables configured

Testing:
1. Upload financial data with numeric columns
2. Create alert: POST /api/alerts {"name":"Revenue Alert", "metric":"Revenue", "threshold":100000, "condition":"above", "notification_channels":["email"], "recipients":["user@example.com"]}
3. Verify background scheduler is running (check logs)
4. Trigger threshold by ensuring data exceeds threshold
5. Verify notification delivery (check email/Slack)
6. Check history: GET /api/alerts/history

Production Deployment Recommendations:
- Replace in-memory storage with database (PostgreSQL recommended)
- Use Redis for job queue and distributed locking
- Implement rate limiting for notification APIs
- Add authentication and authorization for alert routes
- Configure proper logging and monitoring
- Set up health check endpoints for scheduler status
- Implement alert cooldown periods to prevent spam
- Add webhook support for custom integrations
"""
