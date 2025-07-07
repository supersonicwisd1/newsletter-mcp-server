# Newsletter MCP Server

A Model Context Protocol (MCP) server that generates newsletters from Slack conversations and creates Google Docs.

## Features

### Core Functionality
- **Slack Integration**: Fetch messages from multiple channels
- **Google Docs Creation**: Generate formatted newsletters in Google Docs
- **Smart Filtering**: Identify important messages based on engagement and content
- **Multi-channel Support**: Process multiple Slack channels simultaneously

### Advanced Features (New!)
- **User Mention Parsing**: Convert Slack user mentions (`<@U123456>` → `@username`) for better readability
- **Topic-Based Organization**: Automatically categorize messages into topics like:
  - Scheduling (meetings, deadlines, appointments)
  - Technical Discussions (code, bugs, features)
  - Announcements (updates, news, important notices)
  - Questions & Help (support, troubleshooting)
  - Celebrations (birthdays, achievements)
  - Project Updates (milestones, progress)
  - Team Building (social events, culture)
  - Tools & Resources (links, documentation)
- **Date Extraction**: Identify and highlight dates/deadlines mentioned in messages:
  - Specific dates: "March 15th", "3/15/2024"
  - Relative dates: "tomorrow", "next week", "in 2 days"
  - Time references: "at 3pm", "by 5:30"
  - Future/past references: "in 2 weeks", "2 days ago"

## Setup

### Prerequisites
- Python 3.8+
- Slack Bot Token
- Google OAuth credentials

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd mcp-server

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Slack bot token

# Set up Google OAuth
# Download credentials.json from Google Cloud Console
# Place it in the project root
```

### Environment Variables
```bash
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
```

## Usage

### Running the Server
```bash
# Run as a module (recommended)
python -m src.newsletter_mcp.server

# Or run the script directly
python src/newsletter_mcp/server.py
```

### Available Tools

#### Basic Tools
- `get_slack_channels()` - List accessible Slack channels
- `get_channel_messages(channel_id, days_back=7)` - Fetch messages from a channel
- `filter_important_messages(channel_id, days_back=7)` - Get important messages only
- `create_simple_document(title, content)` - Create a Google Doc
- `generate_full_newsletter(days_back=7)` - Complete newsletter generation

#### New Advanced Tools
- `parse_user_mentions(text)` - Parse and resolve Slack user mentions
- `organize_messages_by_topic(channel_id, days_back=7)` - Group messages by topic categories
- `extract_dates_from_messages(channel_id, days_back=7)` - Extract dates and deadlines

## Newsletter Output

The generated newsletters now include:

1. **Executive Summary** - Overview of activity across channels
2. **Topic-Based Sections** - Messages organized by category
3. **Date Highlights** - Upcoming deadlines and important dates
4. **Engagement Metrics** - Reaction and reply counts
5. **User Attribution** - Real names instead of user IDs

### Codebase Structure
newsletter-mcp-server/
├── pyproject.toml
├── README.md
├── .env                           # Environment variables
├── src/
│   └── newsletter_mcp/
│       ├── __init__.py
│       ├── server.py              # Main MCP server
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── slack_tool.py      # Slack integration
│       │   ├── gdocs_tool.py      # Google Docs integration
│       │   └── gmail_tool.py      # Email distribution
│       ├── workflows/
│       │   ├── __init__.py
│       │   └── newsletter_workflow.py  # Orchestrates the flow
│       └── config/
│           ├── __init__.py
│           └── auth_config.py     # Authentication management
└── tests/
    ├── __init__.py
    └── test_tools.py
    
### Example Newsletter Structure
```
Weekly Development Newsletter
Generated on March 15, 2024
Report Period: Mar 8 - Mar 15, 2024

📊 SUMMARY
This week, our team was active across 3 channels with 156 total messages...

🏢 CHANNEL UPDATES

#GENERAL
Members: 25 | Important Updates: 12

📂 ORGANIZED BY TOPIC:

🔹 TECHNICAL DISCUSSIONS (8 updates)
  1. @john: Fixed the authentication bug in the API [👍3 💬2]
  2. @sarah: Deployed new feature to staging [👍5]
  3. @mike: Code review completed for PR #123 [💬4]

🔹 SCHEDULING (3 updates)
  1. @alice: Team meeting tomorrow at 3pm
  2. @bob: Deadline for project milestone is March 20th

📅 UPCOMING DATES & DEADLINES:
  • @alice: tomorrow (Team meeting tomorrow at 3pm)
  • @bob: March 20th (Deadline for project milestone is March 20th)

──────────────────────────────────────────────────
```

## Architecture

- **SlackTool**: Handles Slack API interactions and message processing
- **GoogleDocsTool**: Manages Google Docs creation and formatting
- **NewsletterWorkflow**: Orchestrates the complete newsletter generation process
- **MCP Server**: Exposes tools via the Model Context Protocol

## Troubleshooting

### Common Issues
1. **Module Import Errors**: Ensure you're running from the correct directory
2. **Slack API Errors**: Verify your bot token has the necessary permissions
3. **Google OAuth Issues**: Check that credentials.json is in the correct location
4. **Environment Variables**: Make sure .env file is loaded properly

### Debug Mode
The server includes debug logging. Check the console output for detailed information about the connection and processing steps.