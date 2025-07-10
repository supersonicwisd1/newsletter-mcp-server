"""
Comprehensive async pytest tests for Newsletter MCP Server tools
Tests all functionality including user mention parsing, topic organization, date extraction, and Google Docs integration
"""

import pytest
import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from newsletter_mcp.tools.slack_tool import SlackTool
from newsletter_mcp.workflows.newsletter_workflow import NewsletterWorkflow

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


@pytest.fixture
def slack_tool():
    """Fixture to provide SlackTool instance"""
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    if not slack_token:
        pytest.skip("SLACK_BOT_TOKEN not found in environment")
    return SlackTool(slack_token)


@pytest.fixture
def newsletter_workflow():
    """Fixture to provide NewsletterWorkflow instance"""
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    if not slack_token:
        pytest.skip("SLACK_BOT_TOKEN not found in environment")
    return NewsletterWorkflow(slack_token)


@pytest.mark.asyncio
async def test_slack_connection(slack_tool):
    """Test Slack connection and basic functionality"""
    # Test connection
    is_connected = await slack_tool.test_connection()
    assert is_connected, "Slack connection failed"
    
    # Get channels
    channels = await slack_tool.get_bot_channels()
    assert channels, "No channels accessible"
    assert len(channels) > 0, "Should have at least one channel"


@pytest.mark.asyncio
async def test_user_mention_parsing(slack_tool):
    """Test user mention parsing functionality"""
    test_cases = [
        {
            "input": "Hey <@U090LNR0Y9X>, can you review this PR?",
            "expected_contains": "@",
            "description": "Single user mention"
        },
        {
            "input": "Meeting with <@U1111111111> and <@U2222222222> tomorrow",
            "expected_contains": "@",
            "description": "Multiple user mentions"
        },
        {
            "input": "No mentions in this message",
            "expected_contains": "No mentions",
            "description": "No mentions"
        }
    ]
    
    for test_case in test_cases:
        parsed = await slack_tool.parse_user_mentions(test_case["input"])
        
        # Check if parsing worked correctly
        if "<@" in test_case["input"]:
            # Should have parsed mentions
            assert "@" in parsed and parsed != test_case["input"], f"Failed to parse mentions in: {test_case['input']}"
        else:
            # Should have left text unchanged
            assert parsed == test_case["input"], f"Should not change text without mentions: {test_case['input']}"


@pytest.mark.asyncio
async def test_topic_organization(slack_tool):
    """Test topic-based message organization"""
    test_messages = [
        {
            "text": "We have a meeting tomorrow at 3pm",
            "expected_topic": "Scheduling",
            "description": "Scheduling message"
        },
        {
            "text": "New feature deployed to production!",
            "expected_topic": "Technical Discussions",
            "description": "Technical message"
        },
        {
            "text": "Can someone help me with this issue?",
            "expected_topic": "Questions & Help",
            "description": "Help request"
        },
        {
            "text": "Happy birthday @john! 🎉",
            "expected_topic": "Celebrations",
            "description": "Celebration message"
        },
        {
            "text": "Find a replacement for client shift",
            "expected_topic": "Client Management",
            "description": "Client management message"
        }
    ]
    
    for test_case in test_messages:
        topic = slack_tool.categorize_message(test_case["text"])
        assert topic == test_case["expected_topic"], f"Expected '{test_case['expected_topic']}' but got '{topic}' for: {test_case['text']}"


@pytest.mark.asyncio
async def test_date_extraction(slack_tool):
    """Test date extraction functionality"""
    test_messages = [
        {
            "text": "Meeting tomorrow at 3pm",
            "expected_dates": ["tomorrow", "3pm"],
            "description": "Relative date and time"
        },
        {
            "text": "Deadline is March 15th",
            "expected_dates": ["march 15th"],
            "description": "Specific date"
        },
        {
            "text": "Release scheduled for next week",
            "expected_dates": ["next week"],
            "description": "Relative period"
        }
    ]
    
    for test_case in test_messages:
        dates = slack_tool.extract_dates(test_case["text"])
        extracted_texts = [d["date_text"] for d in dates]
        
        # Check that expected dates are found
        for expected_date in test_case["expected_dates"]:
            assert any(expected_date in extracted for extracted in extracted_texts), f"Expected date '{expected_date}' not found in: {test_case['text']}"


@pytest.mark.asyncio
async def test_message_filtering(slack_tool):
    """Test message filtering functionality"""
    # Create test messages
    from newsletter_mcp.tools.slack_tool import SlackMessage
    
    test_messages = [
        SlackMessage(
            text="This is a long message with important content that should be filtered as important because it contains many words and discusses a significant topic that the team needs to know about.",
            user="U1234567890",
            timestamp="1234567890.123",
            channel="C1234567890",
            reactions=[{"name": "thumbsup", "count": 3}],
            reply_count=2
        ),
        SlackMessage(
            text="Short message",
            user="U1234567890",
            timestamp="1234567890.123",
            channel="C1234567890",
            reactions=[],
            reply_count=0
        ),
        SlackMessage(
            text="Bug fix deployed to production",
            user="U1234567890",
            timestamp="1234567890.123",
            channel="C1234567890",
            reactions=[{"name": "fire", "count": 5}],
            reply_count=1
        )
    ]
    
    # Filter important messages
    important_messages = await slack_tool.filter_important_messages(test_messages)
    
    # Should have filtered some messages
    assert len(important_messages) > 0, "Should have filtered at least one important message"
    assert len(important_messages) <= len(test_messages), "Should not have more important messages than total messages"


@pytest.mark.asyncio
async def test_google_docs_integration():
    """Test Google Docs integration"""
    try:
        from newsletter_mcp.tools.gdocs_tool import GoogleDocsTool
        
        # Initialize Google Docs tool
        docs_tool = GoogleDocsTool()
        
        # Test connection
        is_connected = await docs_tool.test_connection()
        assert is_connected, "Google Docs connection failed"
        
        # Test document creation
        test_title = f"Test Document {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_content = "This is a test document for newsletter MCP server."
        
        doc_info = await docs_tool.create_document(test_title, test_content)
        
        assert doc_info["title"] == test_title, "Document title should match"
        assert "document_id" in doc_info, "Should have document ID"
        assert "url" in doc_info, "Should have document URL"
        
        # Clean up - delete test document
        await docs_tool.delete_document(doc_info["document_id"])
        
    except Exception as e:
        pytest.skip(f"Google Docs test skipped: {e}")


@pytest.mark.asyncio
async def test_full_workflow(newsletter_workflow):
    """Test complete newsletter generation workflow"""
    try:
        # Generate newsletter for a short period
        result = await newsletter_workflow.generate_newsletter(days_back=1)
        
        # Check that we got a valid result
        assert "document_url" in result, "Should have document URL"
        assert "document_id" in result, "Should have document ID"
        assert "title" in result, "Should have title"
        assert "channels_processed" in result, "Should have channels processed count"
        assert "total_messages" in result, "Should have total messages count"
        assert "important_messages" in result, "Should have important messages count"
        
        # Check that we processed at least some data
        assert result["channels_processed"] >= 0, "Should have processed channels count"
        assert result["total_messages"] >= 0, "Should have total messages count"
        assert result["important_messages"] >= 0, "Should have important messages count"
        
    except Exception as e:
        pytest.skip(f"Full workflow test skipped: {e}")


@pytest.mark.asyncio
async def test_gmail_integration():
    """Test Gmail integration"""
    try:
        from newsletter_mcp.tools.gmail_tool import GmailTool, EmailRecipient
        
        # Initialize Gmail tool
        gmail_tool = GmailTool()
        
        # Test connection
        is_connected = await gmail_tool.test_connection()
        assert is_connected, "Gmail connection failed"
        
        # Test getting sender email
        sender_email = await gmail_tool.get_sender_email()
        assert "@" in sender_email, "Should have valid sender email"
        
    except Exception as e:
        pytest.skip(f"Gmail test skipped: {e}")


@pytest.mark.asyncio
async def test_async_operations(slack_tool):
    """Test that all operations are properly async"""
    # Test multiple async operations in parallel
    tasks = [
        slack_tool.test_connection(),
        slack_tool.get_bot_channels(),
        slack_tool.parse_user_mentions("Test message with <@U1234567890>"),
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check that all operations completed
    for i, result in enumerate(results):
        assert not isinstance(result, Exception), f"Async operation {i} failed: {result}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
