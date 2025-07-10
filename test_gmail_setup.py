#!/usr/bin/env python3

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_gmail_setup():
    """Test Gmail tool setup"""
    try:
        from src.newsletter_mcp.tools.gmail_tool import GmailTool
        
        print("🔍 Testing Gmail tool setup...")
        
        # Initialize the tool
        tool = GmailTool()
        print("✅ GmailTool created")
        
        # Call async_init
        await tool.async_init()
        print("✅ GmailTool async_init completed")
        
        # Test connection
        result = await tool.test_connection()
        print(f"✅ Gmail connection test result: {result}")
        
        if result:
            print("🎉 Gmail tool is working correctly!")
        else:
            print("❌ Gmail tool connection test failed")
            
    except Exception as e:
        print(f"❌ Error testing Gmail tool: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gmail_setup()) 