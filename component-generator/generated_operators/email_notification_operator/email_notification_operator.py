from airflow.models import BaseOperator
from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook
from airflow.utils.email import send_email
from typing import Dict, Any, Optional, Sequence
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from pathlib import Path


class EmailNotificationOperator(BaseOperator):
    """
    Operator for sending email notifications with HTML support and attachments.
    
    This operator sends email notifications using SMTP configuration from Airflow connections.
    Supports both plain text and HTML email bodies with optional file attachments.
    
    Args:
        to (str): Recipient email address
        subject (str): Email subject line
        body (str): Email body content (plain text or HTML)
        html (bool, optional): Whether body content is HTML format. Defaults to False.
        smtp_conn_id (str, optional): Airflow connection ID for SMTP configuration. 
                                     Defaults to 'smtp_default'.
        attachments (list, optional): List of file paths to attach to email
        cc (str, optional): CC email addresses (comma-separated)
        bcc (str, optional): BCC email addresses (comma-separated)
    
    Example:
        email_task = EmailNotificationOperator(
            task_id='send_notification',
            to='user@example.com',
            subject='Task Completed',
            body='<h1>Task finished successfully</h1>',
            html=True,
            smtp_conn_id='my_smtp_conn'
        )
    """
    
    template_fields: Sequence[str] = ['to', 'subject', 'body', 'cc', 'bcc']
    ui_color: str = "#e8f4fd"
    
    def __init__(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
        smtp_conn_id: str = 'smtp_default',
        attachments: Optional[list] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        # Store parameters
        self.to = to
        self.subject = subject
        self.body = body
        self.html = html
        self.smtp_conn_id = smtp_conn_id
        self.attachments = attachments or []
        self.cc = cc
        self.bcc = bcc
        
        # Validate non-template fields
        if not isinstance(html, bool):
            raise AirflowException("Parameter 'html' must be a boolean value")
            
        if not isinstance(smtp_conn_id, str) or not smtp_conn_id.strip():
            raise AirflowException("Parameter 'smtp_conn_id' must be a non-empty string")
            
        if attachments and not isinstance(attachments, list):
            raise AirflowException("Parameter 'attachments' must be a list of file paths")
            
        # Validate template fields only if they don't contain Jinja templates
        if '{{' not in str(to) and not self._is_valid_email(to):
            raise AirflowException(f"Invalid email address format: {to}")
            
        if '{{' not in str(subject) and not subject.strip():
            raise AirflowException("Email subject cannot be empty")
            
        if '{{' not in str(body) and not body.strip():
            raise AirflowException("Email body cannot be empty")
            
        self.log.info(f"Initialized EmailNotificationOperator for task {self.task_id}")
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email address format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
    def _validate_template_fields(self):
        """Validate template fields after Jinja rendering"""
        if not self._is_valid_email(self.to):
            raise AirflowException(f"Invalid recipient email address: {self.to}")
            
        if not self.subject.strip():
            raise AirflowException("Email subject cannot be empty after template rendering")
            
        if not self.body.strip():
            raise AirflowException("Email body cannot be empty after template rendering")
            
        if self.cc and not all(self._is_valid_email(email.strip()) for email in self.cc.split(',')):
            raise AirflowException(f"Invalid CC email address(es): {self.cc}")
            
        if self.bcc and not all(self._is_valid_email(email.strip()) for email in self.bcc.split(',')):
            raise AirflowException(f"Invalid BCC email address(es): {self.bcc}")
    
    def _get_smtp_connection(self):
        """Get SMTP connection details from Airflow connection"""
        try:
            connection = BaseHook.get_connection(self.smtp_conn_id)
            return {
                'host': connection.host,
                'port': connection.port or 587,
                'username': connection.login,
                'password': connection.password,
                'use_tls': connection.extra_dejson.get('use_tls', True),
                'use_ssl': connection.extra_dejson.get('use_ssl', False)
            }
        except Exception as e:
            raise AirflowException(f"Failed to get SMTP connection '{self.smtp_conn_id}': {str(e)}")
    
    def _create_message(self, smtp_config: Dict[str, Any]) -> MIMEMultipart:
        """Create email message with attachments"""
        msg = MIMEMultipart()
        msg['From'] = smtp_config.get('username', 'airflow@localhost')
        msg['To'] = self.to
        msg['Subject'] = self.subject
        
        if self.cc:
            msg['Cc'] = self.cc
            
        if self.bcc:
            msg['Bcc'] = self.bcc
        
        # Add body
        body_type = 'html' if self.html else 'plain'
        msg.attach(MIMEText(self.body, body_type))
        
        # Add attachments
        for attachment_path in self.attachments:
            try:
                file_path = Path(attachment_path)
                if not file_path.exists():
                    self.log.warning(f"Attachment file not found: {attachment_path}")
                    continue
                    
                with open(file_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {file_path.name}'
                )
                msg.attach(part)
                self.log.info(f"Added attachment: {file_path.name}")
                
            except Exception as e:
                self.log.error(f"Failed to attach file {attachment_path}: {str(e)}")
                raise AirflowException(f"Failed to process attachment {attachment_path}: {str(e)}")
        
        return msg
    
    def _get_all_recipients(self) -> list:
        """Get all email recipients including CC and BCC"""
        recipients = [self.to]
        
        if self.cc:
            recipients.extend([email.strip() for email in self.cc.split(',')])
            
        if self.bcc:
            recipients.extend([email.strip() for email in self.bcc.split(',')])
            
        return recipients
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute email notification sending
        
        Args:
            context: Airflow context dictionary
            
        Returns:
            Dict containing email sending results
            
        Raises:
            AirflowException: On email sending failure
        """
        self.log.info(f"Executing EmailNotificationOperator for task {self.task_id}")
        
        # Validate template fields after Jinja rendering
        self._validate_template_fields()
        
        try:
            # Get SMTP configuration
            smtp_config = self._get_smtp_connection()
            self.log.info(f"Using SMTP server: {smtp_config['host']}:{smtp_config['port']}")
            
            # Create email message
            message = self._create_message(smtp_config)
            
            # Get all recipients
            all_recipients = self._get_all_recipients()
            
            # Send email
            server = None
            try:
                if smtp_config.get('use_ssl'):
                    server = smtplib.SMTP_SSL(smtp_config['host'], smtp_config['port'])
                else:
                    server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
                    if smtp_config.get('use_tls'):
                        server.starttls()
                
                if smtp_config.get('username') and smtp_config.get('password'):
                    server.login(smtp_config['username'], smtp_config['password'])
                
                # Send the email
                server.send_message(message, to_addrs=all_recipients)
                
                self.log.info(f"Email sent successfully to {len(all_recipients)} recipient(s)")
                
                result = {
                    'status': 'success',
                    'recipients': all_recipients,
                    'subject': self.subject,
                    'timestamp': context.get('execution_date', '').isoformat() if context.get('execution_date') else None,
                    'attachments_count': len(self.attachments)
                }
                
                return result
                
            finally:
                if server:
                    server.quit()
                    
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred while sending email: {str(e)}"
            self.log.error(error_msg)
            raise AirflowException(error_msg)
            
        except Exception as e:
            error_msg = f"Failed to send email notification: {str(e)}"
            self.log.error(error_msg)
            raise AirflowException(error_msg)