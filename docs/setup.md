# Newsletter MCP Server Setup Guide

## Prerequisites

1. **Python 3.10+** installed
2. **uv** package manager (or pip)
3. **Slack workspace** with admin access
4. **Google Cloud Project** with APIs enabled

## Step 1: Project Setup

```bash
# Create project directory
mkdir newsletter-mcp-server
cd newsletter-mcp-server

# Create directory structure
mkdir -p src/newsletter_mcp/{tools,workflows,config}
mkdir tests

# Create __init__.py files
touch src/newsletter_mcp/__init__.py
touch src/newsletter_mcp/tools/__init__.py
touch src/newsletter_mcp/workflows/__init__.py
touch src/newsletter_mcp/config/__init__.py
touch tests/__init__.py

# Initialize with uv
uv init
```

## Step 2: Install Dependencies

```bash
# Install dependencies with uv
uv add mcp slack-sdk google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 httpx pydantic python-dotenv

# Install dev dependencies
uv add --dev pytest pytest-asyncio black ruff
```

if pyproject.toml is already initiated, just sync

```bash
uv sync
```

## Step 3: Slack Bot Setup

### Create Slack App

1. Go to [Slack API Dashboard](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name it "Newsletter Bot" and select your workspace
4. Go to "OAuth & Permissions" in the sidebar

### Configure Bot Permissions

Add these OAuth Scopes under "Bot Token Scopes":
- `channels:read` - View basic information about public channels
- `channels:history` - View messages in public channels
- `chat:write` - Send messages as the bot
- `users:read` - View people in the workspace
- `groups:read` - List private channels and groups
- `groups:history` - View messages in private channels and groups

### Install App to Workspace

1. Click "Install to Workspace" 
2. Authorize the app
3. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### Get Bot Token

The bot token will be used in your `.env` file as `SLACK_BOT_TOKEN`

## Step 4: Google Cloud Setup

### Enable APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable these APIs:
   - Google Docs API
   - Google Drive API
   - Gmail API

### Create Service Account

1. Go to "IAM & Admin" → "Service Accounts"
2. Click "Create Service Account"
3. Name it "newsletter-mcp-bot"
4. Create and download the JSON key file
5. Place the file in your project directory

### Google Docs set steps
Let's Set Up Google Cloud First
Here's the simple setup process:
Step 1: Create Google Cloud Project

Go to Google Cloud Console
Click "New Project"
Name it something like "newsletter-mcp-bot"
Click "Create"

Step 2: Enable APIs
Once in your project:

Go to "APIs & Services" → "Library"
Search and enable:

Google Docs API
Google Drive API
(Skip Gmail for now)

Step 1: Create OAuth2 Credentials

Go back to Google Cloud Console
Go to "APIs & Services" → "Credentials"
Click "Create Credentials" → "OAuth client ID"
Choose "Desktop application"
Name it "Newsletter MCP Client"
Download the JSON file
Rename it to credentials.json and put it in your project root

Step 3: Create Service Account

Go to "APIs & Services" → "Credentials"
Click "Create Credentials" → "Service Account"
Name it "newsletter-bot"
Click "Create and Continue"
Skip role assignment for now (click "Continue")
Click "Done"

Step 4: Generate Key

Click on your service account email
Go to "Keys" tab
Click "Add Key" → "Create New Key"
Choose "JSON"
Download the file
Move it to your project folder and rename it service-account-key.json

Step 5: Update .env
Add to your .env file:
```bash
GOOGLE_SERVICE_ACCOUNT_FILE=./service-account-key.json
```

### Set up Authentication

Option 1: Service Account (Recommended for automation)
- Use the downloaded JSON key file
- Set `GOOGLE_SERVICE_ACCOUNT_FILE` in `.env`

Option 2: OAuth2 (For user-specific access)
- Create OAuth2 credentials
- Download client secrets file

## Step 5: Configure Environment

Create `.env` file in your project root:

```bash
# Copy the provided .env template
cp .env.example .env

# Edit with your actual values
nano .env
```

Fill in your actual values:
- `SLACK_BOT_TOKEN`: Your bot token from Slack
- `GOOGLE_SERVICE_ACCOUNT_FILE`: Path to your service account JSON
- `NEWSLETTER_SUBSCRIBER_EMAILS`: Comma-separated email list

## Step 6: Test Slack Integration

```bash
# Test the Slack tool
cd src
python -m newsletter_mcp.tools.slack_tool
```

This will:
- Test Slack connection
- List channels the bot can access
- Fetch recent messages
- Filter important messages

## Step 7: Add Bot to Channels

In Slack:
1. Go to the channel you want to monitor
2. Type `/invite @Newsletter Bot`
3. The bot will now have access to that channel

## Step 8: Run Tests

```bash
# Run basic tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=src/newsletter_mcp
```

## Troubleshooting

### Common Issues

**"Channel not found" error:**
- Make sure the bot is added to the channel
- Check if the channel ID is correct

**"Invalid auth" error:**
- Verify your bot token is correct
- Check token permissions in Slack App settings

**Google API errors:**
- Ensure APIs are enabled in Google Cloud Console
- Check service account permissions
- Verify JSON key file path

### Testing Commands

```bash
# Test Slack connection
python -c "
from src.newsletter_mcp.tools.slack_tool import SlackTool
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
tool = SlackTool(os.getenv('SLACK_BOT_TOKEN'))
asyncio.run(tool.test_connection())
"
```

## Next Steps

Once setup is complete:
1. Test individual tools
2. Implement Google Docs integration
3. Build workflow orchestration
4. Add MCP server wrapper
5. Test end-to-end flow

## Security Notes

- Never commit `.env` file to version control
- Use environment variables in production
- Regularly rotate API keys
- Follow principle of least privilege for bot permissions