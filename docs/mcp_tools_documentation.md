# Newsletter MCP Server - Tool Documentation

## Overview

The Newsletter MCP Server provides a comprehensive set of tools for automatically generating newsletters from Slack conversations. It integrates Slack data collection, Google Docs document creation, and Gmail email distribution into a seamless workflow.

## Core Tools

### 1. Slack Data Collection Tools

#### `get_slack_channels()`
**Purpose:** Retrieve all Slack channels accessible to the bot
**Returns:** JSON with channel list, count, and channel names
**Use Case:** Discover available channels for newsletter generation
```json
{
  "channels": [
    {"id": "C123456", "name": "general", "member_count": 50},
    {"id": "C789012", "name": "dev-team", "member_count": 15}
  ],
  "count": 2,
  "channel_names": ["general", "dev-team"]
}
```

#### `get_channel_messages(channel_id: str, days_back: int = 7)`
**Purpose:** Fetch messages from a specific Slack channel within a date range
**Parameters:**
- `channel_id`: Slack channel ID
- `days_back`: Number of days to look back (default: 7)
**Returns:** JSON with message details and metadata
**Use Case:** Collect raw message data for analysis
```json
{
  "channel_id": "C123456",
  "date_range": "2025-07-03 to 2025-07-10",
  "message_count": 45,
  "messages": [
    {
      "text": "Great work on the new feature!",
      "user": "U123456",
      "timestamp": "2025-07-09T10:30:00Z",
      "reactions": 3,
      "replies": 2
    }
  ]
}
```

#### `filter_important_messages(channel_id: str, days_back: int = 7)`
**Purpose:** Identify important messages based on engagement metrics and content analysis
**Parameters:**
- `channel_id`: Slack channel ID
- `days_back`: Number of days to look back (default: 7)
**Returns:** JSON with filtered important messages and user information
**Use Case:** Focus newsletter content on high-value discussions
```json
{
  "channel_id": "C123456",
  "total_messages": 45,
  "important_messages": 12,
  "messages": [
    {
      "text": "🚀 New deployment successful!",
      "user_id": "U123456",
      "user_name": "John Doe",
      "timestamp": "2025-07-09T10:30:00Z",
      "reactions": 5,
      "replies": 3
    }
  ]
}
```

### 2. Content Enhancement Tools

#### `parse_user_mentions(text: str)`
**Purpose:** Convert Slack user mentions (`<@U123456>`) to readable names
**Parameters:**
- `text`: Raw Slack message text with user mentions
**Returns:** JSON with original and parsed text
**Use Case:** Make newsletter content more readable by resolving user IDs
```json
{
  "original_text": "Great work <@U123456> and <@U789012>!",
  "parsed_text": "Great work John Doe and Jane Smith!",
  "has_mentions": true
}
```

#### `organize_messages_by_topic(channel_id: str, days_back: int = 7)`
**Purpose:** Group important messages by topic categories for better organization
**Parameters:**
- `channel_id`: Slack channel ID
- `days_back`: Number of days to look back (default: 7)
**Returns:** JSON with messages organized by topic groups
**Use Case:** Structure newsletter content by themes (deployments, announcements, etc.)
```json
{
  "channel_id": "C123456",
  "total_messages": 45,
  "important_messages": 12,
  "topic_groups": {
    "deployments": [
      {
        "text": "🚀 New deployment successful!",
        "user_name": "John Doe",
        "timestamp": "2025-07-09T10:30:00Z",
        "reactions": 5,
        "replies": 3
      }
    ],
    "announcements": [
      {
        "text": "📢 Team meeting moved to 3 PM",
        "user_name": "Jane Smith",
        "timestamp": "2025-07-09T09:00:00Z",
        "reactions": 2,
        "replies": 1
      }
    ]
  },
  "topic_count": 2
}
```

#### `extract_dates_from_messages(channel_id: str, days_back: int = 7)`
**Purpose:** Identify dates, deadlines, and time-sensitive information in messages
**Parameters:**
- `channel_id`: Slack channel ID
- `days_back`: Number of days to look back (default: 7)
**Returns:** JSON with extracted dates and context
**Use Case:** Highlight upcoming deadlines and important dates in newsletters
```json
{
  "channel_id": "C123456",
  "total_messages": 45,
  "important_messages": 12,
  "messages_with_dates": 3,
  "total_dates_found": 4,
  "dates": [
    {
      "date_text": "July 15th",
      "date_type": "deadline",
      "context": "Project deadline",
      "user_name": "John Doe",
      "message_preview": "Remember the project deadline is July 15th..."
    }
  ]
}
```

### 3. Document Creation Tools

#### `create_simple_document(title: str, content: str)`
**Purpose:** Create a basic Google Doc with custom content
**Parameters:**
- `title`: Document title
- `content`: Document content (text)
**Returns:** JSON with document information and URL
**Use Case:** Create simple documents or test Google Docs integration
```json
{
  "success": true,
  "document_id": "1ABC123DEF456",
  "title": "Test Document",
  "url": "https://docs.google.com/document/d/1ABC123DEF456/edit",
  "created_at": "2025-07-10T15:30:00Z"
}
```

### 4. Newsletter Generation Tools

#### `generate_full_newsletter(days_back: int = 7, send_email: bool = False, custom_recipients: Optional[str] = None)`
**Purpose:** Complete end-to-end newsletter generation from all accessible Slack channels
**Parameters:**
- `days_back`: Number of days to look back (default: 7)
- `send_email`: Whether to send email notification (default: False)
- `custom_recipients`: Comma-separated list of email addresses (optional)
**Returns:** JSON with comprehensive newsletter information
**Use Case:** Generate complete newsletters with optional email distribution
```json
{
  "document_url": "https://docs.google.com/document/d/1ABC123DEF456/edit",
  "document_id": "1ABC123DEF456",
  "title": "Weekly Dev Newsletter - July 10, 2025",
  "channels_processed": 3,
  "total_messages": 150,
  "important_messages": 25,
  "date_range": "2025-07-03 to 2025-07-10",
  "email_sent": true,
  "email_result": {
    "success": true,
    "message_id": "msg123",
    "recipients": ["team@company.com", "stakeholders@company.com"]
  },
  "send_email_requested": true
}
```

### 5. Email Distribution Tools

#### `send_newsletter_email(document_url: str, newsletter_title: str, summary: str, recipients: str)`
**Purpose:** Send newsletter email to specified recipients
**Parameters:**
- `document_url`: URL to the Google Doc newsletter
- `newsletter_title`: Title of the newsletter
- `summary`: Summary of newsletter content
- `recipients`: Comma-separated list of email addresses
**Returns:** JSON with email sending results
**Use Case:** Distribute newsletters via email with custom recipient lists
```json
{
  "success": true,
  "message": "Newsletter email sent to 3 recipients",
  "recipients": ["team@company.com", "stakeholders@company.com", "management@company.com"],
  "email_result": {
    "success": true,
    "message_id": "msg123",
    "thread_id": "thread456",
    "subject": "📰 Weekly Dev Newsletter - July 10, 2025",
    "sent_at": "2025-07-10T15:30:00Z"
  }
}
```

## Workflow Integration

### Newsletter Workflow Features

The server integrates all tools through a comprehensive workflow that:

1. **Data Collection:** Fetches messages from all accessible Slack channels
2. **Content Processing:** 
   - Filters important messages based on engagement
   - Resolves user mentions to readable names
   - Groups messages by topic categories
   - Extracts dates and deadlines
3. **Document Creation:** Generates formatted Google Docs with structured content
4. **Email Distribution:** Sends newsletters to specified recipients

### Key Features

- **Flexible Email Control:** Choose whether to send emails and specify custom recipients
- **Topic Organization:** Automatically categorize content by themes
- **Date Extraction:** Highlight important dates and deadlines
- **User Mention Resolution:** Convert Slack user IDs to readable names
- **Engagement Metrics:** Prioritize content based on reactions and replies
- **Multi-Channel Support:** Process multiple Slack channels simultaneously

## Configuration Requirements

### Environment Variables
- `SLACK_BOT_TOKEN`: Slack bot user OAuth token
- `NEWSLETTER_SUBSCRIBER_EMAILS`: Comma-separated list of default email recipients

### Google API Setup
- `credentials.json`: Google OAuth2 credentials file
- Gmail API enabled in Google Cloud Console
- Google Docs API enabled in Google Cloud Console

## Error Handling

All tools include comprehensive error handling:
- Connection failures are reported with clear error messages
- Missing credentials trigger helpful setup instructions
- API rate limits are handled gracefully
- Invalid parameters return descriptive error messages

## Usage Examples

### Basic Newsletter Generation
```python
# Generate newsletter for last 7 days without email
result = await generate_full_newsletter(days_back=7, send_email=False)
```

### Newsletter with Email Distribution
```python
# Generate and send to custom recipients
result = await generate_full_newsletter(
    days_back=7, 
    send_email=True, 
    custom_recipients="team@company.com,stakeholders@company.com"
)
```

### Manual Email Sending
```python
# Send existing newsletter to recipients
result = await send_newsletter_email(
    document_url="https://docs.google.com/document/d/1ABC123DEF456/edit",
    newsletter_title="Weekly Dev Newsletter",
    summary="This week's important updates and discussions",
    recipients="team@company.com,management@company.com"
)
```

This comprehensive toolset enables automated, intelligent newsletter generation from Slack conversations with full control over content processing and distribution. 