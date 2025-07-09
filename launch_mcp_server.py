#!/usr/bin/env python3
"""
Launcher script for the Newsletter MCP Server
Handles environment setup and proper file paths
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Setup environment variables and paths"""
    
    # Get the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = script_dir
    
    print(f"🚀 Setting up MCP Server environment...")
    print(f"📁 Project root: {project_root}")
    print(f"📁 Current working directory: {os.getcwd()}")
    
    # Add src to Python path
    src_path = os.path.join(project_root, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        print(f"📦 Added to Python path: {src_path}")
    
    # Load environment variables
    env_file = os.path.join(project_root, '.env')
    if os.path.exists(env_file):
        print(f"✅ Loading .env from: {env_file}")
        from dotenv import load_dotenv
        load_dotenv(env_file)
        
        # Verify key environment variables
        slack_token = os.getenv('SLACK_BOT_TOKEN')
        if slack_token:
            print(f"✅ SLACK_BOT_TOKEN loaded: {slack_token[:10]}...{slack_token[-4:]}")
        else:
            print("❌ SLACK_BOT_TOKEN not found in .env file")
            return False
    else:
        print(f"❌ .env file not found at: {env_file}")
        return False
    
    # Check for required files
    required_files = [
        os.path.join(project_root, 'credentials.json'),
        os.path.join(project_root, 'token.pickle')
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ Found: {os.path.basename(file_path)}")
        else:
            print(f"⚠️  Missing: {os.path.basename(file_path)}")
    
    return True

def main():
    """Main launcher function"""
    print("🎯 Newsletter MCP Server Launcher")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed. Please check your .env file and credentials.")
        sys.exit(1)
    
    print("\n🚀 Launching MCP Server...")
    print("=" * 50)
    
    # Import and run the server
    try:
        from newsletter_mcp.server import main as server_main
        server_main()
    except Exception as e:
        print(f"❌ Failed to launch server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 