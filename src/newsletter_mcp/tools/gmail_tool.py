"""
Gmail Tool for Newsletter MCP Server
Handles sending newsletters via email using Gmail API
"""

import os
import asyncio
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class EmailRecipient(BaseModel):
    """Model for email recipient"""
    email: str
    name: Optional[str] = None


class EmailContent(BaseModel):
    """Model for email content"""
    subject: str
    html_body: str
    text_body: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class GmailError(Exception):
    """Custom exception for Gmail operations"""
    pass


class GmailTool:
    """Tool for sending emails via Gmail API"""
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: Optional[str] = None):
        self.credentials_file = credentials_file
        # Use absolute path for token file to avoid working directory issues
        if token_file is None:
            self.token_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'gmail_token.pickle')
        else:
            self.token_file = token_file
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.compose'
        ]
        self.gmail_service = None
        # REMOVE: asyncio.get_event_loop().run_until_complete(self._setup_services_async())

    async def run_blocking(self, func, *args, **kwargs):
        """Helper method to run blocking functions in executor"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def _setup_services_async(self):
        """Async wrapper for _setup_services"""
        await self.run_blocking(self._setup_services)

    def _setup_services(self):
        """Initialize Gmail API service with OAuth2 (blocking)"""
        try:
            import pickle
            creds = None
            
            # Load existing token
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # If no valid credentials, get them
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("🔄 Refreshing Gmail credentials...")
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        raise GmailError(f"Credentials file not found: {self.credentials_file}")
                    
                    logger.info("🔐 Starting Gmail OAuth2 flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            # Build the service
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            
            logger.info("✅ Gmail API service initialized with OAuth2")
            
        except Exception as e:
            raise GmailError(f"Failed to initialize Gmail service: {e}")

    async def async_init(self):
        await self._setup_services_async()

    async def test_connection(self) -> bool:
        """Test if Gmail connection is working"""
        try:
            # Try to get user profile to test connection
            profile = await self.run_blocking(self.gmail_service.users().getProfile(userId='me').execute)
            logger.info(f"✅ Gmail connection test successful - Connected as: {profile.get('emailAddress', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"❌ Gmail connection test failed: {e}")
            return False

    async def send_newsletter_email(
        self, 
        recipients: List[EmailRecipient], 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None,
        sender_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send newsletter email to recipients
        
        Args:
            recipients: List of email recipients
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)
            sender_email: Sender email address (optional, uses authenticated user if not provided)
            
        Returns:
            Dictionary with send results
        """
        try:
            # Get sender email if not provided
            if not sender_email:
                profile = await self.run_blocking(self.gmail_service.users().getProfile(userId='me').execute)
                sender_email = profile.get('emailAddress')
            
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = sender_email
            message['To'] = ', '.join([r.email for r in recipients])
            
            # Add text part
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                message.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)
            
            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send the email
            sent_message = await self.run_blocking(
                self.gmail_service.users().messages().send(userId='me', body={'raw': raw_message}).execute
            )
            
            return {
                'success': True,
                'message_id': sent_message.get('id'),
                'thread_id': sent_message.get('threadId'),
                'recipients': [r.email for r in recipients],
                'subject': subject,
                'sent_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise GmailError(f"Failed to send email: {e}")

    async def send_newsletter_with_document_link(
        self, 
        recipients: List[EmailRecipient], 
        newsletter_title: str,
        document_url: str,
        summary: str,
        sender_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send newsletter email with Google Doc link
        
        Args:
            recipients: List of email recipients
            newsletter_title: Title of the newsletter
            document_url: URL to the Google Doc
            summary: Summary of the newsletter content
            sender_email: Sender email address (optional)
            
        Returns:
            Dictionary with send results
        """
        subject = f"📰 {newsletter_title}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px;">
                    📰 {newsletter_title}
                </h1>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h2 style="color: #2c3e50; margin-top: 0;">📋 Summary</h2>
                    <p style="font-size: 16px;">{summary}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{document_url}" 
                       style="background-color: #3498db; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; font-weight: bold; 
                              display: inline-block;">
                        📄 Read Full Newsletter
                    </a>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; 
                            font-size: 14px; color: #7f8c8d;">
                    <p>This newsletter was automatically generated from Slack conversations.</p>
                    <p>Generated by Newsletter MCP Bot 🤖</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
{newsletter_title}

SUMMARY:
{summary}

Read the full newsletter at: {document_url}

---
This newsletter was automatically generated from Slack conversations.
Generated by Newsletter MCP Bot 🤖
        """
        
        return await self.send_newsletter_email(
            recipients=recipients,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            sender_email=sender_email
        )

    async def get_sender_email(self) -> str:
        """Get the authenticated user's email address"""
        try:
            profile = await self.run_blocking(self.gmail_service.users().getProfile(userId='me').execute)
            return profile.get('emailAddress', 'unknown@example.com')
        except Exception as e:
            logger.warning(f"Warning: Could not get sender email: {e}")
            return 'newsletter@example.com'


# Example usage and testing
async def test_gmail_tool():
    """Test function to verify Gmail tool functionality"""
    
    # Initialize with credentials from environment
    credentials_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'credentials.json')
    
    if not os.path.exists(credentials_path):
        logger.error("❌ Gmail credentials not found")
        return
    
    try:
        gmail_tool = GmailTool(credentials_file=credentials_path)
        
        # Test connection
        logger.info("🔍 Testing Gmail connection...")
        if await gmail_tool.test_connection():
            logger.info("✅ Gmail connection successful")
            
            # Test sending email
            test_recipients = [
                EmailRecipient(email="test@example.com", name="Test User")
            ]
            
            result = await gmail_tool.send_newsletter_with_document_link(
                recipients=test_recipients,
                newsletter_title="Test Newsletter",
                document_url="https://docs.google.com/document/d/test",
                summary="This is a test newsletter summary."
            )
            
            logger.info(f"✅ Test email sent successfully: {result}")
            
        else:
            logger.error("❌ Gmail connection failed")
            
    except Exception as e:
        logger.error(f"❌ Gmail tool test failed: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_gmail_tool()) 