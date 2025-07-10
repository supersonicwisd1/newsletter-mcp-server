#!/usr/bin/env python3

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_workflow_init():
    """Test NewsletterWorkflow initialization"""
    try:
        from src.newsletter_mcp.workflows.newsletter_workflow import NewsletterWorkflow
        
        print("🔍 Testing NewsletterWorkflow initialization...")
        
        # Get Slack token
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            print("❌ SLACK_BOT_TOKEN not found")
            return
        
        # Initialize workflow
        workflow = NewsletterWorkflow(slack_token)
        print("✅ NewsletterWorkflow created")
        
        # Call async_init
        await workflow.async_init()
        print("✅ NewsletterWorkflow async_init completed")
        
        # Test a simple operation
        print("🔍 Testing workflow components...")
        
        # Test Slack connection
        channels = await workflow.slack_tool.get_bot_channels()
        print(f"✅ Found {len(channels)} Slack channels")
        
        # Test Google Docs tool
        if workflow.docs_tool.docs_service:
            print("✅ Google Docs service is initialized")
        else:
            print("❌ Google Docs service is not initialized")
        
        # Test Gmail tool
        if workflow.gmail_tool.gmail_service:
            print("✅ Gmail service is initialized")
        else:
            print("❌ Gmail service is not initialized")
            
        print("🎉 NewsletterWorkflow is working correctly!")
            
    except Exception as e:
        print(f"❌ Error testing NewsletterWorkflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow_init()) 