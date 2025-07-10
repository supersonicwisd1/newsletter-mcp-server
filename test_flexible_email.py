#!/usr/bin/env python3
"""
Test script for flexible email functionality
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

async def test_flexible_newsletter():
    """Test the new flexible newsletter generation with email options"""
    
    # Load environment
    load_dotenv()
    
    try:
        from newsletter_mcp.workflows.newsletter_workflow import NewsletterWorkflow
        
        # Initialize workflow
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            print("❌ SLACK_BOT_TOKEN not found")
            return
        
        # Initialize workflow
        workflow = NewsletterWorkflow(slack_token)
        await workflow.async_init()
        
        print("🧪 Testing flexible newsletter generation...")
        
        # Test 1: Generate without sending email
        print("\n📝 Test 1: Generate newsletter without email")
        result1 = await workflow.generate_newsletter(
            days_back=1,
            send_email=False
        )
        print(f"✅ Generated: {result1['title']}")
        print(f"📊 Stats: {result1['total_messages']} messages, {result1['important_messages']} important")
        print(f"📧 Email sent: {result1['email_sent']}")
        
        # Test 2: Generate with email to environment recipients
        print("\n📝 Test 2: Generate newsletter with email (env recipients)")
        result2 = await workflow.generate_newsletter(
            days_back=1,
            send_email=True
        )
        print(f"✅ Generated: {result2['title']}")
        print(f"📧 Email sent: {result2['email_sent']}")
        
        # Test 3: Generate with custom recipients
        print("\n📝 Test 3: Generate newsletter with custom recipients")
        custom_emails = ["test1@example.com", "test2@example.com"]
        result3 = await workflow.generate_newsletter(
            days_back=1,
            send_email=True,
            custom_recipients=custom_emails
        )
        print(f"✅ Generated: {result3['title']}")
        print(f"📧 Email sent: {result3['email_sent']}")
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_flexible_newsletter()) 