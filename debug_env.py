#!/usr/bin/env python3
"""
Debug script to help identify environment and file location issues
"""

import os
import sys
from pathlib import Path

def debug_environment():
    """Debug environment variables and file locations"""
    print("🔍 DEBUGGING ENVIRONMENT")
    print("=" * 50)
    
    # Current working directory
    print(f"📁 Current working directory: {os.getcwd()}")
    print(f"🐍 Python executable: {sys.executable}")
    print(f"📦 Python path: {sys.path[:3]}...")
    
    # Check for .env files
    print("\n🔍 Looking for .env files:")
    possible_env_paths = [
        '.env',
        os.path.join(os.path.dirname(__file__), '.env'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'),
        '/Users/kene/Documents/codes/headstarters/mcp/newsletter-mcp-server/mcp-server/.env'
    ]
    
    for env_path in possible_env_paths:
        exists = os.path.exists(env_path)
        print(f"  {'✅' if exists else '❌'} {env_path}")
        if exists:
            try:
                with open(env_path, 'r') as f:
                    content = f.read()
                    has_slack_token = 'SLACK_BOT_TOKEN' in content
                    print(f"    Contains SLACK_BOT_TOKEN: {'✅' if has_slack_token else '❌'}")
            except Exception as e:
                print(f"    Error reading file: {e}")
    
    # Check environment variables
    print("\n🔍 Environment variables:")
    important_vars = ['SLACK_BOT_TOKEN', 'PYTHONPATH', 'PATH']
    for var in important_vars:
        value = os.getenv(var, 'NOT SET')
        if var == 'SLACK_BOT_TOKEN' and value != 'NOT SET':
            # Mask the token for security
            masked_value = value[:10] + '...' + value[-4:] if len(value) > 14 else '***'
            print(f"  {var}: {masked_value}")
        else:
            print(f"  {var}: {value}")
    
    # Check for credential files
    print("\n🔍 Looking for credential files:")
    credential_paths = [
        'credentials.json',
        'token.pickle',
        os.path.join(os.path.dirname(__file__), 'credentials.json'),
        os.path.join(os.path.dirname(__file__), 'token.pickle'),
        '/Users/kene/Documents/codes/headstarters/mcp/newsletter-mcp-server/mcp-server/credentials.json',
        '/Users/kene/Documents/codes/headstarters/mcp/newsletter-mcp-server/mcp-server/token.pickle'
    ]
    
    for cred_path in credential_paths:
        exists = os.path.exists(cred_path)
        print(f"  {'✅' if exists else '❌'} {cred_path}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    debug_environment() 