try:
    from airflow.sdk.bases.operator import BaseOperator
except ImportError:
    from airflow.models import BaseOperator

from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook
from typing import Dict, Any, Optional, Sequence
import json
import requests
from datetime import datetime


class PagerDutyAlertOperator(BaseOperator):
    """
    Creates incidents and alerts in PagerDuty for on-call notification and incident management.
    
    This operator uses the PagerDuty Events API v2 to create, acknowledge, or resolve incidents.
    It supports custom event details, severity levels, and deduplication keys.
    
    :param summary: Brief summary of the incident or alert
    :type summary: str
    :param severity: Severity level - critical, error, warning, or info
    :type severity: str
    :param action: Action type - trigger, acknowledge, or resolve
    :type action: str
    :param dedup_key: Deduplication key to correlate events
    :type dedup_key: Optional[str]
    :param custom_details: Additional custom details for the event
    :type custom_details: Dict[str, Any]
    :param pagerduty_conn_id: Airflow connection ID containing PagerDuty routing key
    :type pagerduty_conn_id: str
    """
    
    template_fields: Sequence[str] = ['summary', 'severity', 'dedup_key', 'custom_details']
    ui_color: str = "#06ac38"
    
    def __init__(
        self,
        summary: str,
        severity: str = 'error',
        action: str = 'trigger',
        dedup_key: Optional[str] = None,
        custom_details: Dict[str, Any] = None,
        pagerduty_conn_id: str = 'pagerduty_default',
        **kwargs
    ):
        super().__init__(**kwargs)
        
        self.summary = summary
        self.severity = severity
        self.action = action
        self.dedup_key = dedup_key
        self.custom_details = custom_details or {}
        self.pagerduty_conn_id = pagerduty_conn_id
        
        # Validate non-template fields
        valid_actions = ['trigger', 'acknowledge', 'resolve']
        if self.action not in valid_actions:
            raise AirflowException(f"Invalid action '{self.action}'. Must be one of: {valid_actions}")
        
        # Validate template fields only if they don't contain Jinja templates
        valid_severities = ['critical', 'error', 'warning', 'info']
        if '{{' not in str(self.severity) and self.severity not in valid_severities:
            raise AirflowException(f"Invalid severity '{self.severity}'. Must be one of: {valid_severities}")
        
        self.log.info(f"Initialized PagerDutyAlertOperator with action: {self.action}, severity: {self.severity}")
    
    def execute(self, context: Dict[str, Any]) -> str:
        """
        Execute the PagerDuty alert operation.
        
        Args:
            context: Airflow context dict with task_instance, execution_date, etc.
            
        Returns:
            str: Incident key from PagerDuty response
            
        Raises:
            AirflowException: On validation errors or API failures
        """
        self.log.info(f"Executing PagerDutyAlertOperator for task: {self.task_id}")
        
        # Validate template fields after Jinja rendering
        valid_severities = ['critical', 'error', 'warning', 'info']
        if self.severity not in valid_severities:
            raise AirflowException(f"Invalid severity '{self.severity}'. Must be one of: {valid_severities}")
        
        if not self.summary or not self.summary.strip():
            raise AirflowException("Summary cannot be empty")
        
        # Get PagerDuty connection
        try:
            connection = BaseHook.get_connection(self.pagerduty_conn_id)
            routing_key = connection.password or connection.extra_dejson.get('routing_key')
            
            if not routing_key:
                raise AirflowException(f"No routing key found in connection '{self.pagerduty_conn_id}'. "
                                     "Set it in the password field or extra JSON as 'routing_key'")
        except Exception as e:
            raise AirflowException(f"Failed to get PagerDuty connection '{self.pagerduty_conn_id}': {str(e)}")
        
        # Prepare event payload
        event_payload = {
            "routing_key": routing_key,
            "event_action": self.action,
            "payload": {
                "summary": self.summary,
                "severity": self.severity,
                "source": f"airflow-{self.dag_id}-{self.task_id}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "custom_details": self.custom_details
            }
        }
        
        # Add deduplication key if provided
        if self.dedup_key:
            event_payload["dedup_key"] = self.dedup_key
        
        # For acknowledge/resolve actions, we need the dedup_key
        if self.action in ['acknowledge', 'resolve'] and not self.dedup_key:
            raise AirflowException(f"dedup_key is required for action '{self.action}'")
        
        # Send event to PagerDuty
        url = "https://events.pagerduty.com/v2/enqueue"
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            self.log.info(f"Sending {self.action} event to PagerDuty for summary: {self.summary}")
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(event_payload),
                timeout=30
            )
            response.raise_for_status()
            
            response_data = response.json()
            incident_key = response_data.get('dedup_key', 'unknown')
            
            self.log.info(f"Successfully sent PagerDuty event. Incident key: {incident_key}")
            
            # Push incident key to XCom for downstream tasks
            return incident_key
            
        except requests.exceptions.RequestException as e:
            raise AirflowException(f"Failed to send PagerDuty event: {str(e)}")
        except json.JSONDecodeError as e:
            raise AirflowException(f"Failed to parse PagerDuty response: {str(e)}")
        except Exception as e:
            raise AirflowException(f"Unexpected error sending PagerDuty event: {str(e)}")