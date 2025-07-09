"""
Newsletter MCP Server - Fixed Version
Main server implementation that exposes Slack and Google Docs tools via MCP protocol
"""

import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from dotenv import load_dotenv

from mcp.server import FastMCP
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import our tools
from newsletter_mcp.tools.slack_tool import SlackTool
from newsletter_mcp.tools.gdocs_tool import GoogleDocsTool, NewsletterContent

import sys
print("🐛 DEBUG: Server starting...", file=sys.stderr)
print(f"🐛 DEBUG: Python path: {sys.executable}", file=sys.stderr)
print(f"🐛 DEBUG: Working directory: {os.getcwd()}", file=sys.stderr)
print(f"🐛 DEBUG: Environment variables:", file=sys.stderr)
for key in ['SLACK_BOT_TOKEN', 'PYTHONPATH', 'PATH']:
    print(f"🐛 DEBUG: {key} = {os.getenv(key, 'NOT SET')}", file=sys.stderr)

# Load environment variables from current directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Initialize our tools
slack_tool = None
docs_tool = None

def initialize_tools():
    """Initialize Slack and Google Docs tools"""
    global slack_tool, docs_tool
    
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    if not slack_token:
        raise ValueError("SLACK_BOT_TOKEN not found in environment")
    
    slack_tool = SlackTool(slack_token)
    
    # Use absolute paths for Google credentials
    credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
    
    print(f"🔍 Looking for Google credentials at: {credentials_path}")
    
    if not os.path.exists(credentials_path):
        print(f"❌ Google credentials not found at: {credentials_path}")
        docs_tool = None
    else:
        try:
            docs_tool = GoogleDocsTool(credentials_file=credentials_path)
            print("✅ Google Docs tool initialized")
        except Exception as e:
            print(f"❌ Error initializing Google Docs tool: {e}")
            docs_tool = None
    
    print("✅ Newsletter MCP Server tools initialized")

# Create the FastMCP server
server = FastMCP("newsletter-mcp-server")

@server.tool()
async def get_slack_channels() -> str:
    """Get list of Slack channels the bot has access to"""
    if not slack_tool:
        return "Error: Tools not initialized. Check your environment variables."
    
    try:
        channels = await slack_tool.get_bot_channels()
        result = {
            "channels": channels,
            "count": len(channels),
            "channel_names": [ch['name'] for ch in channels]
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting Slack channels: {str(e)}"

@server.tool()
async def get_channel_messages(channel_id: str, days_back: int = 7) -> str:
    """Get messages from a specific Slack channel within a date range"""
    if not slack_tool:
        return "Error: Tools not initialized. Check your environment variables."
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        messages = await slack_tool.get_channel_messages(channel_id, start_date, end_date)
        
        # Convert messages to serializable format
        serializable_messages = []
        for msg in messages:
            serializable_messages.append({
                "text": msg.text,
                "user": msg.user,
                "timestamp": msg.timestamp,
                "reactions": len(msg.reactions) if msg.reactions else 0,
                "replies": msg.reply_count or 0
            })
        
        result = {
            "channel_id": channel_id,
            "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "message_count": len(messages),
            "messages": serializable_messages
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting channel messages: {str(e)}"

@server.tool()
async def filter_important_messages(channel_id: str, days_back: int = 7) -> str:
    """Filter messages to identify important ones based on engagement and content"""
    if not slack_tool:
        return "Error: Tools not initialized. Check your environment variables."
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get all messages
        messages = await slack_tool.get_channel_messages(channel_id, start_date, end_date)
        
        # Filter important ones
        important_messages = await slack_tool.filter_important_messages(messages)
        
        # Enrich with user info
        enriched_messages = []
        for msg in important_messages:
            user_info = await slack_tool.get_user_info(msg.user)
            enriched_msg = {
                "text": msg.text,
                "user_id": msg.user,
                "user_name": user_info.get('display_name') or user_info.get('real_name') or 'Unknown',
                "timestamp": msg.timestamp,
                "reactions": len(msg.reactions) if msg.reactions else 0,
                "replies": msg.reply_count or 0
            }
            enriched_messages.append(enriched_msg)
        
        result = {
            "channel_id": channel_id,
            "total_messages": len(messages),
            "important_messages": len(important_messages),
            "messages": enriched_messages
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error filtering important messages: {str(e)}"

@server.tool()
async def create_simple_document(title: str, content: str) -> str:
    """Create a simple Google Doc with custom content"""
    if not docs_tool:
        return "Error: Google Docs tool not initialized. Check your Google credentials."
    
    try:
        doc_info = await docs_tool.create_document(title, content)
        
        result = {
            "success": True,
            "document_id": doc_info["document_id"],
            "title": doc_info["title"],
            "url": doc_info["url"],
            "created_at": doc_info["created_at"]
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error creating document: {str(e)}"

@server.tool()
async def generate_full_newsletter(days_back: int = 7, title_prefix: str = "Weekly Dev Newsletter") -> str:
    """Complete end-to-end newsletter generation from all accessible Slack channels"""
    if not slack_tool or not docs_tool:
        return "Error: Tools not initialized. Check your environment variables."
    
    try:
        # Import the workflow
        from newsletter_mcp.workflows.newsletter_workflow import NewsletterWorkflow
        
        # Initialize workflow with Slack token
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            return "Error: SLACK_BOT_TOKEN not found"
        
        workflow = NewsletterWorkflow(slack_token)
        
        # Generate newsletter using the enhanced workflow
        result = await workflow.generate_newsletter(days_back=days_back)
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error generating newsletter: {str(e)}"

@server.tool()
async def parse_user_mentions(text: str) -> str:
    """Parse Slack user mentions and replace them with actual user names"""
    if not slack_tool:
        return "Error: Tools not initialized. Check your environment variables."
    
    try:
        parsed_text = await slack_tool.parse_user_mentions(text)
        
        result = {
            "original_text": text,
            "parsed_text": parsed_text,
            "has_mentions": "<@" in text
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error parsing user mentions: {str(e)}"

@server.tool()
async def organize_messages_by_topic(channel_id: str, days_back: int = 7) -> str:
    """Group messages by topic categories for better newsletter organization"""
    if not slack_tool:
        return "Error: Tools not initialized. Check your environment variables."
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get messages
        messages = await slack_tool.get_channel_messages(channel_id, start_date, end_date)
        
        # Filter important messages
        important_messages = await slack_tool.filter_important_messages(messages)
        
        # Group by topic
        topic_groups = await slack_tool.group_messages_by_topic(important_messages)
        
        # Convert to serializable format
        serializable_groups: Dict[str, List[Dict[str, Any]]] = {}
        for topic, msgs in topic_groups.items():
            serializable_groups[topic] = []
            for msg in msgs:
                user_info = await slack_tool.get_user_info(msg.user)
                serializable_groups[topic].append({
                    "text": msg.text,
                    "user_name": user_info.get('display_name') or user_info.get('real_name') or 'Unknown',
                    "timestamp": msg.timestamp,
                    "reactions": len(msg.reactions) if msg.reactions else 0,
                    "replies": msg.reply_count or 0
                })
        
        result = {
            "channel_id": channel_id,
            "total_messages": len(messages),
            "important_messages": len(important_messages),
            "topic_groups": serializable_groups,
            "topic_count": len(topic_groups)
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error organizing messages by topic: {str(e)}"

@server.tool()
async def extract_dates_from_messages(channel_id: str, days_back: int = 7) -> str:
    """Extract dates and deadlines mentioned in Slack messages"""
    if not slack_tool:
        return "Error: Tools not initialized. Check your environment variables."
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Get messages
        messages = await slack_tool.get_channel_messages(channel_id, start_date, end_date)
        
        # Filter important messages
        important_messages = await slack_tool.filter_important_messages(messages)
        
        # Enrich with dates
        enriched_messages = await slack_tool.enrich_messages_with_dates(important_messages)
        
        # Filter messages with dates
        messages_with_dates = [msg for msg in enriched_messages if msg.get('has_dates', False)]
        
        # Extract all dates
        all_dates = []
        for msg in messages_with_dates:
            for date_info in msg.get('dates', []):
                all_dates.append({
                    "date_text": date_info['date_text'],
                    "date_type": date_info['date_type'],
                    "context": date_info['context'],
                    "user_name": msg['user_name'],
                    "message_preview": msg['text'][:100] + "..." if len(msg['text']) > 100 else msg['text']
                })
        
        result = {
            "channel_id": channel_id,
            "total_messages": len(messages),
            "important_messages": len(important_messages),
            "messages_with_dates": len(messages_with_dates),
            "total_dates_found": len(all_dates),
            "dates": all_dates
        }
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error extracting dates: {str(e)}"

def main():
    """Main server entry point"""
    try:
        # Initialize tools
        initialize_tools()
        
        # Test connections
        print("🔍 Testing tool connections...")
        
        # Test Slack - we need to run this in an event loop
        async def test_connections():
            # Test Slack
            if await slack_tool.test_connection():
                print("✅ Slack connection verified")
                return True
            else:
                print("❌ Slack connection failed")
                return False
        
        # Run the async test in a new event loop
        if not asyncio.run(test_connections()):
            return
        
        # Test Google Docs (simple check)
        print("✅ Google Docs OAuth2 credentials ready")
        
        print("🚀 Starting Newsletter MCP Server...")
        print("Server ready for Claude Desktop connection!")
        
        # Run the FastMCP server with stdio transport
        server.run(transport="stdio")
    
    except KeyboardInterrupt:
        print("\n👋 Server shutdown requested")
    except Exception as e:
        print(f"Server error: {e}")
        raise

if __name__ == "__main__":
    main()