#!/usr/bin/env python3

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_gdocs_init():
    """Test GoogleDocsTool initialization"""
    try:
        from src.newsletter_mcp.tools.gdocs_tool import GoogleDocsTool
        
        print("🔍 Testing GoogleDocsTool initialization...")
        
        # Initialize the tool
        tool = GoogleDocsTool()
        print("✅ GoogleDocsTool created")
        
        # Call async_init
        await tool.async_init()
        print("✅ GoogleDocsTool async_init completed")
        
        # Test connection
        result = await tool.test_connection()
        print(f"✅ Connection test result: {result}")
        
        if result:
            print("🎉 GoogleDocsTool is working correctly!")
        else:
            print("❌ GoogleDocsTool connection test failed")
            
    except Exception as e:
        print(f"❌ Error testing GoogleDocsTool: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gdocs_init()) 