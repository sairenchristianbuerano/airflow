from airflow.models import BaseOperator
from airflow.exceptions import AirflowException
from airflow.providers.slack.hooks.slack_webhook import SlackWebhookHook
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
from typing import Dict, Any, Optional, List, Sequence, Union
import json


class SlackNotificationOperator(BaseOperator):
    """
    Operator for sending notifications to Slack channels with support for formatted messages and attachments.
    
    This operator sends messages to Slack channels using the Slack webhook API. It supports
    custom usernames, emoji icons, and rich attachments for enhanced messaging capabilities.
    
    Args:
        channel: Slack channel to send message to (e.g., '#general' or '@username')
        message: Message text to send to the channel
        username: Bot username to display (optional)
        icon_emoji: Emoji icon for the bot (e.g., ':robot_face:') (optional)
        attachments: List of Slack attachments for rich formatting (optional)
        slack_conn_id: Airflow connection ID for Slack webhook (default: 'slack_default')
    
    Example:
        slack_notification = SlackNotificationOperator(
            task_id='send_slack_notification',
            channel='#alerts',
            message='Task completed successfully!',
            username='Airflow Bot',
            icon_emoji=':white_check_mark:',
            slack_conn_id='slack_webhook'
        )
    """
    
    template_fields: Sequence[str] = ['channel', 'message', 'username', 'icon_emoji', 'attachments']
    ui_color: str = "#36C5F0"
    
    def __init__(
        self,
        channel: str,
        message: str,
        username: Optional[str] = None,
        icon_emoji: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        slack_conn_id: str = 'slack_default',
        **kwargs
    ):
        super().__init__(**kwargs)
        
        # Validate required parameters (skip if Jinja templates)
        if '{{' not in str(channel) and not channel:
            raise AirflowException("Parameter 'channel' is required and cannot be empty")
        
        if '{{' not in str(message) and not message:
            raise AirflowException("Parameter 'message' is required and cannot be empty")
        
        # Validate channel format if not a template
        if '{{' not in str(channel) and channel and not (channel.startswith('#') or channel.startswith('@')):
            raise AirflowException("Channel must start with '#' for channels or '@' for direct messages")
        
        # Validate emoji format if provided and not a template
        if icon_emoji and '{{' not in str(icon_emoji):
            if not (icon_emoji.startswith(':') and icon_emoji.endswith(':')):
                raise AirflowException("icon_emoji must be in format ':emoji_name:' (e.g., ':robot_face:')")
        
        # Validate attachments format if provided and not a template
        if attachments and '{{' not in str(attachments):
            if not isinstance(attachments, list):
                raise AirflowException("attachments must be a list of dictionaries")
            for i, attachment in enumerate(attachments):
                if not isinstance(attachment, dict):
                    raise AirflowException(f"Attachment at index {i} must be a dictionary")
        
        self.channel = channel
        self.message = message
        self.username = username
        self.icon_emoji = icon_emoji
        self.attachments = attachments or []
        self.slack_conn_id = slack_conn_id
        
        self.log.info(f"Initialized SlackNotificationOperator for channel: {channel}")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Slack notification by sending message to specified channel.
        
        Args:
            context: Airflow context dictionary containing task_instance, execution_date, etc.
            
        Returns:
            Dict containing notification details and status
            
        Raises:
            AirflowException: If message sending fails or validation errors occur
        """
        self.log.info(f"Executing SlackNotificationOperator for task: {self.task_id}")
        
        # Validate template fields after Jinja rendering
        if not self.channel:
            raise AirflowException("Parameter 'channel' cannot be empty after template rendering")
        
        if not self.message:
            raise AirflowException("Parameter 'message' cannot be empty after template rendering")
        
        # Validate channel format after template rendering
        if not (self.channel.startswith('#') or self.channel.startswith('@')):
            raise AirflowException("Channel must start with '#' for channels or '@' for direct messages")
        
        # Validate emoji format after template rendering
        if self.icon_emoji and not (self.icon_emoji.startswith(':') and self.icon_emoji.endswith(':')):
            raise AirflowException("icon_emoji must be in format ':emoji_name:' (e.g., ':robot_face:')")
        
        try:
            # Initialize Slack webhook hook
            slack_hook = SlackWebhookHook(
                http_conn_id=self.slack_conn_id,
                message=self.message,
                channel=self.channel,
                username=self.username,
                icon_emoji=self.icon_emoji,
                attachments=self.attachments
            )
            
            self.log.info(f"Sending Slack notification to channel: {self.channel}")
            self.log.info(f"Message preview: {self.message[:100]}{'...' if len(self.message) > 100 else ''}")
            
            # Send the message
            response = slack_hook.execute()
            
            # Prepare result for XCom
            result = {
                'channel': self.channel,
                'message_length': len(self.message),
                'username': self.username,
                'icon_emoji': self.icon_emoji,
                'attachments_count': len(self.attachments),
                'status': 'success',
                'task_id': self.task_id,
                'execution_date': context.get('execution_date', '').isoformat() if context.get('execution_date') else None
            }
            
            self.log.info(f"Successfully sent Slack notification to {self.channel}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to send Slack notification: {str(e)}"
            self.log.error(error_msg)
            raise AirflowException(error_msg) from e