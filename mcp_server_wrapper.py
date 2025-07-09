#!/usr/bin/env python3
"""
MCP Server Wrapper - Can be run from any directory
Automatically finds the project root and sets up environment
"""

import os
import sys
from pathlib import Path

def find_project_root():
    """Find the project root directory by looking for key files"""
    current_dir = Path.cwd()
    
    # First, try to find the project by looking for the script's location
    script_dir = Path(__file__).parent
    if (script_dir / '.env').exists() and (script_dir / 'credentials.json').exists():
        return script_dir
    
    # Look for the project root by checking for key files from current directory
    for parent in [current_dir] + list(current_dir.parents):
        if (parent / '.env').exists() and (parent / 'credentials.json').exists():
            return parent
    
    # Fallback: try to find the project by looking for the server file
    for parent in [current_dir] + list(current_dir.parents):
        server_file = parent / 'src' / 'newsletter_mcp' / 'server.py'
        if server_file.exists():
            return parent
    
    return None

def setup_environment():
    """Setup environment for MCP server"""
    
    # Find project root
    project_root = find_project_root()
    if not project_root:
        print("❌ Could not find project root. Make sure you're running from the project directory or a subdirectory.")
        return False
    
    print(f"📁 Project root found: {project_root}")
    
    # Change to project root directory
    os.chdir(project_root)
    print(f"📁 Changed working directory to: {os.getcwd()}")
    
    # Add src to Python path
    src_path = project_root / 'src'
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        print(f"📦 Added to Python path: {src_path}")
    
    # Load environment variables
    env_file = project_root / '.env'
    if env_file.exists():
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
    
    return True

def main():
    """Main wrapper function"""
    print("🎯 Newsletter MCP Server Wrapper")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed.")
        sys.exit(1)
    
    print("\n🚀 Launching MCP Server...")
    print("=" * 50)
    
    # Import and run the server
    try:
        from newsletter_mcp.server import main as server_main
        server_main()
    except Exception as e:
        print(f"❌ Failed to launch server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 