"""
Google Docs Tool for Newsletter MCP Server - OAuth2 Version
Handles document creation, formatting, and content management using OAuth2
"""

import os
import json
import pickle
from typing import Dict, Any, List, Optional
from datetime import datetime
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



class NewsletterContent(BaseModel):
    """Model for newsletter content structure"""
    title: str
    date: str
    channels: List[Dict[str, Any]]
    summary: str


class GoogleDocsError(Exception):
    """Custom exception for Google Docs operations"""
    pass


class GoogleDocsTool:
    """Tool for interacting with Google Docs API using OAuth2"""
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: Optional[str] = None):
        self.credentials_file = credentials_file
        # Use absolute path for token file to avoid working directory issues
        if token_file is None:
            self.token_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'token.pickle')
        else:
            self.token_file = token_file
        self.scopes = [
            'https://www.googleapis.com/auth/documents',
            'https://www.googleapis.com/auth/drive.file'
        ]
        self.docs_service = None
        self.drive_service = None
        # REMOVE: asyncio.get_event_loop().run_until_complete(self._setup_services_async())
    
    async def run_blocking(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    async def _setup_services_async(self):
        """Async wrapper for _setup_services"""
        await self.run_blocking(self._setup_services)

    def _setup_services(self):
        """Initialize Google API services with OAuth2 (blocking)"""
        try:
            creds = None
            
            # Load existing token
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # If no valid credentials, get them
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("🔄 Refreshing Google credentials...")
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        raise GoogleDocsError(f"Credentials file not found: {self.credentials_file}")
                    
                    logger.info("🔐 Starting OAuth2 flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            # Build the services
            self.docs_service = build('docs', 'v1', credentials=creds)
            self.drive_service = build('drive', 'v3', credentials=creds)
            
            logger.info("✅ Google API services initialized with OAuth2")
            
        except Exception as e:
            raise GoogleDocsError(f"Failed to initialize Google services: {e}")
    
    async def async_init(self):
        await self._setup_services_async()

    async def test_connection(self) -> bool:
        """
        Test if Google Docs connection is working
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to create a simple test document and then delete it
            test_doc = await self.create_document("Connection Test", "This is a test document.")
            if test_doc:
                # Delete the test document
                await self.delete_document(test_doc['document_id'])
                logger.info("✅ Google Docs connection test successful")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Google Docs connection test failed: {e}")
            return False
    
    async def create_document(self, title: str, content: str = "") -> Dict[str, Any]:
        """
        Create a new Google Doc
        
        Args:
            title: Document title
            content: Initial content (optional)
            
        Returns:
            Dictionary with document info
        """
        try:
            # Create the document
            document = {
                'title': title
            }
            
            doc = await self.run_blocking(lambda: self.docs_service.documents().create(body=document).execute())
            document_id = doc.get('documentId')
            
            # Add content if provided
            if content:
                await self.add_content(document_id, content)
            
            # Get the document URL
            doc_url = f"https://docs.google.com/document/d/{document_id}/edit"
            
            return {
                'document_id': document_id,
                'title': title,
                'url': doc_url,
                'created_at': datetime.now().isoformat()
            }
            
        except HttpError as e:
            raise GoogleDocsError(f"Failed to create document: {e}")
    
    async def add_content(self, document_id: str, content: str, insert_at: int = 1):
        """
        Add text content to a document
        
        Args:
            document_id: Google Doc ID
            content: Text content to add
            insert_at: Position to insert content (default: end of document)
        """
        try:
            requests = [
                {
                    'insertText': {
                        'location': {
                            'index': insert_at,
                        },
                        'text': content
                    }
                }
            ]
            
            await self.run_blocking(lambda: self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute())
            
        except HttpError as e:
            raise GoogleDocsError(f"Failed to add content: {e}")
    
    async def format_newsletter_content(self, newsletter_data: NewsletterContent) -> str:
        """
        Format newsletter data into readable content
        
        Args:
            newsletter_data: Structured newsletter content
            
        Returns:
            Formatted text content
        """
        content = f"""{newsletter_data.title}
Generated on: {newsletter_data.date}

SUMMARY
{newsletter_data.summary}

CHANNEL UPDATES

"""
        
        for channel in newsletter_data.channels:
            channel_name = channel.get('name', 'Unknown Channel')
            messages = channel.get('messages', [])
            important_count = len(messages)
            
            content += f"#{channel_name.upper()}\n"
            content += f"Important updates: {important_count}\n\n"
            
            for i, msg in enumerate(messages[:5], 1):  # Limit to top 5 messages
                text = msg.get('text', '')[:200]  # Truncate long messages
                user = msg.get('user_name', msg.get('user', 'Unknown User'))
                reactions = msg.get('reactions', 0)
                replies = msg.get('replies', 0)
                
                engagement = ""
                if reactions > 0:
                    engagement += f"👍{reactions} "
                if replies > 0:
                    engagement += f"💬{replies} "
                
                content += f"{i}. {user}: {text}"
                if engagement:
                    content += f" [{engagement.strip()}]"
                content += "\n\n"
            
            if len(messages) > 5:
                content += f"... and {len(messages) - 5} more updates\n\n"
            
            content += "─" * 50 + "\n\n"
        
        content += """ABOUT THIS NEWSLETTER
This newsletter is automatically generated from Slack conversations using our MCP server. 
It identifies important messages based on engagement and content analysis.

Generated by Newsletter MCP Bot 🤖"""
        
        return content
    
    async def create_newsletter_document(self, newsletter_data: NewsletterContent) -> Dict[str, Any]:
        """
        Create a formatted newsletter document
        
        Args:
            newsletter_data: Structured newsletter content
            
        Returns:
            Dictionary with document info
        """
        try:
            # Format the content
            content = await self.format_newsletter_content(newsletter_data)
            
            # Create the document
            doc_info = await self.create_document(newsletter_data.title, content)
            
            # Apply basic formatting
            await self._apply_basic_formatting(doc_info['document_id'])
            
            return doc_info
            
        except Exception as e:
            raise GoogleDocsError(f"Failed to create newsletter document: {e}")
    
    async def _apply_basic_formatting(self, document_id: str):
        """
        Apply basic formatting to make the newsletter look better
        
        Args:
            document_id: Google Doc ID
        """
        try:
            # Get the document content to understand structure
            doc = await self.run_blocking(lambda: self.docs_service.documents().get(documentId=document_id).execute())
            content = doc.get('body', {}).get('content', [])
            
            requests = []
            
            # Look for the title (first line) and format it
            for element in content:
                if 'paragraph' in element:
                    paragraph = element['paragraph']
                    elements = paragraph.get('elements', [])
                    
                    if elements:
                        first_element = elements[0]
                        if 'textRun' in first_element:
                            text = first_element['textRun'].get('content', '')
                            start_idx = first_element.get('startIndex', 0)
                            end_idx = first_element.get('endIndex', 0)
                            
                            # Format the title (first line with "Newsletter" in it)
                            if 'Newsletter' in text and start_idx < 50:  # Likely the title
                                requests.append({
                                    'updateTextStyle': {
                                        'range': {
                                            'startIndex': start_idx,
                                            'endIndex': end_idx - 1  # Exclude newline
                                        },
                                        'textStyle': {
                                            'fontSize': {'magnitude': 16, 'unit': 'PT'},
                                            'bold': True
                                        },
                                        'fields': 'fontSize,bold'
                                    }
                                })
                                break  # Only format the first title we find
            
            # Apply formatting if we have requests
            if requests:
                await self.run_blocking(lambda: self.docs_service.documents().batchUpdate(
                    documentId=document_id,
                    body={'requests': requests}
                ).execute())
                
        except Exception as e:
            logger.warning(f"Warning: Could not apply formatting: {e}")
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document (move to trash)
        
        Args:
            document_id: Google Doc ID
            
        Returns:
            True if successful
        """
        try:
            return await self.run_blocking(lambda: self.drive_service.files().delete(fileId=document_id).execute())
        except HttpError as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    async def share_document(self, document_id: str, email: str, role: str = 'reader') -> bool:
        """
        Share document with someone
        
        Args:
            document_id: Google Doc ID
            email: Email to share with
            role: Permission level ('reader', 'writer', 'owner')
            
        Returns:
            True if successful
        """
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            return await self.run_blocking(lambda: self.drive_service.permissions().create(
                fileId=document_id,
                body=permission,
                sendNotificationEmail=False
            ).execute())
            
        except HttpError as e:
            logger.error(f"Failed to share document: {e}")
            return False


# Test function
async def test_oauth_google_docs():
    """Test function to verify OAuth2 Google Docs functionality"""
    
    try:
        logger.info("🔍 Testing OAuth2 Google Docs integration...")
        docs_tool = GoogleDocsTool()  # Uses default OAuth2 files
        
        # Test creating a simple document
        logger.info("\n🔍 Creating test document...")
        doc_info = await docs_tool.create_document(
            "OAuth2 Test Newsletter", 
            "This document was created using OAuth2 authentication!\n\nThe integration is working properly."
        )
        
        logger.info(f"✅ Document created successfully!")
        logger.info(f"   Title: {doc_info['title']}")
        logger.info(f"   URL: {doc_info['url']}")
        logger.info(f"   ID: {doc_info['document_id']}")
        
        # Test creating a structured newsletter
        logger.info("\n🔍 Creating structured newsletter...")
        
        sample_newsletter = NewsletterContent(
            title="Weekly Dev Update - OAuth2 Test",
            date=datetime.now().strftime("%Y-%m-%d"),
            summary="This week the team worked on MCP server development and OAuth2 integration.",
            channels=[
                {
                    'name': 'general',
                    'messages': [
                        {
                            'text': 'Successfully integrated OAuth2 with Google Docs API', 
                            'user_name': 'developer',
                            'reactions': 3,
                            'replies': 2
                        },
                        {
                            'text': 'Newsletter generation is now working end-to-end', 
                            'user_name': 'project_manager',
                            'reactions': 5,
                            'replies': 1
                        }
                    ]
                },
                {
                    'name': 'random',
                    'messages': [
                        {
                            'text': 'Great progress on the MCP project this week!', 
                            'user_name': 'team_lead',
                            'reactions': 2,
                            'replies': 0
                        }
                    ]
                }
            ]
        )
        
        newsletter_doc = await docs_tool.create_newsletter_document(sample_newsletter)
        logger.info(f"✅ Newsletter document created!")
        logger.info(f"   URL: {newsletter_doc['url']}")
        
        logger.info(f"\n🎉 OAuth2 integration working perfectly!")
        logger.info(f"   Test Doc: {doc_info['url']}")
        logger.info(f"   Newsletter: {newsletter_doc['url']}")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_oauth_google_docs())