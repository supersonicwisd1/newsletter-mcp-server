"""
Slack Tool for Newsletter MCP Server
Handles fetching messages, channel info, and filtering important conversations
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from pydantic import BaseModel
import json
import re
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SlackMessage(BaseModel):
    """Model for Slack message data"""
    text: str
    user: str
    timestamp: str
    channel: str
    thread_ts: Optional[str] = None
    reply_count: Optional[int] = 0
    reactions: Optional[List[Dict[str, Any]]] = []


class SlackTool:
    """Tool for interacting with Slack API"""
    
    def __init__(self, bot_token: str):
        self.client = AsyncWebClient(token=bot_token)
        self.bot_token = bot_token
    
    async def get_channel_messages(
        self, 
        channel_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[SlackMessage]:
        """
        Fetch messages from a specific channel within date range
        
        Args:
            channel_id: Slack channel ID
            start_date: Start date for message fetching
            end_date: End date for message fetching
            
        Returns:
            List of SlackMessage objects
        """
        try:
            # Convert datetime to Slack timestamp format
            start_ts = str(start_date.timestamp())
            end_ts = str(end_date.timestamp())
            
            # Fetch messages
            response = await self.client.conversations_history(
                channel=channel_id,
                oldest=start_ts,
                latest=end_ts,
                inclusive=True,
                limit=1000  # Adjust as needed
            )
            
            messages = []
            for msg in response["messages"]:
                # Skip bot messages and system messages
                if msg.get("subtype") in ["bot_message", "channel_join", "channel_leave"]:
                    continue
                    
                # Get reactions if any
                reactions = msg.get("reactions", [])
                
                slack_msg = SlackMessage(
                    text=msg.get("text", ""),
                    user=msg.get("user", ""),
                    timestamp=msg.get("ts", ""),
                    channel=channel_id,
                    thread_ts=msg.get("thread_ts"),
                    reply_count=msg.get("reply_count", 0),
                    reactions=reactions
                )
                messages.append(slack_msg)
            
            return messages
            
        except SlackApiError as e:
            logger.error(f"Error fetching messages: {e}")
            return []
    
    async def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """
        Get channel information including name and member count
        
        Args:
            channel_id: Slack channel ID
            
        Returns:
            Dictionary with channel information
        """
        try:
            response = await self.client.conversations_info(channel=channel_id)
            channel = response["channel"]
            
            return {
                "id": channel["id"],
                "name": channel["name"],
                "is_private": channel["is_private"],
                "member_count": channel.get("num_members", 0),
                "purpose": channel.get("purpose", {}).get("value", ""),
                "topic": channel.get("topic", {}).get("value", "")
            }
            
        except SlackApiError as e:
            logger.error(f"Error getting channel info: {e}")
            return {}
    
    async def filter_important_messages(self, messages: List[SlackMessage]) -> List[SlackMessage]:
        """
        Filter messages based on importance criteria
        
        Args:
            messages: List of SlackMessage objects
            
        Returns:
            Filtered list of important messages
        """
        important_messages = []
        
        for msg in messages:
            # Criteria for important messages:
            # 1. Has reactions (engagement)
            # 2. Has replies (discussion)
            # 3. Contains certain keywords
            # 4. Long messages (substantial content)
            
            is_important = False
            
            # Check reactions
            if msg.reactions and len(msg.reactions) > 0:
                total_reactions = sum(reaction.get("count", 0) for reaction in msg.reactions)
                if total_reactions >= 2:  # At least 2 reactions
                    is_important = True
            
            # Check replies
            if msg.reply_count and msg.reply_count > 1:
                is_important = True
            
            # Check message length (substantial content)
            if len(msg.text) > 100:
                is_important = True
            
            # Check for important keywords
            important_keywords = [
                "release", "deploy", "ship", "launch", "update", "decision", 
                "meeting", "demo", "announcement", "milestone", "completed",
                "bug", "issue", "fix", "feature", "breaking", "shift", "client",
                "caregiver", "cover"
            ]
            
            text_lower = msg.text.lower()
            if any(keyword in text_lower for keyword in important_keywords):
                is_important = True
            
            if is_important:
                important_messages.append(msg)
        
        return important_messages
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information for message attribution
        
        Args:
            user_id: Slack user ID
            
        Returns:
            Dictionary with user information
        """
        try:
            response = await self.client.users_info(user=user_id)
            user = response["user"]
            
            return {
                "id": user["id"],
                "name": user.get("name", ""),
                "real_name": user.get("real_name", ""),
                "display_name": user.get("profile", {}).get("display_name", ""),
                "email": user.get("profile", {}).get("email", "")
            }
            
        except SlackApiError as e:
            logger.error(f"Error getting user info: {e}")
            return {}
    
    async def test_connection(self) -> bool:
        """
        Test if the Slack connection is working
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = await self.client.auth_test()
            logger.info(f"Connected to Slack as: {response['user']}")
            return True
        except SlackApiError as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def get_bot_channels(self) -> List[Dict[str, Any]]:
        """
        Get list of channels the bot is a member of
        
        Returns:
            List of channel information dictionaries
        """
        try:
            response = await self.client.conversations_list(
                types="public_channel,private_channel",
                exclude_archived=True
            )
            
            channels = []
            for channel in response["channels"]:
                if channel.get("is_member", False):
                    channels.append({
                        "id": channel["id"],
                        "name": channel["name"],
                        "is_private": channel["is_private"],
                        "member_count": channel.get("num_members", 0)
                    })
            
            return channels
            
        except SlackApiError as e:
            logger.error(f"Error getting bot channels: {e}")
            return []

    async def parse_user_mentions(self, text: str) -> str:
        """
        Parse Slack user mentions like <@U090LNR0Y9X> and replace with actual names
        
        Args:
            text: Message text with user mentions
            
        Returns:
            Text with user mentions replaced by display names
        """
        # Pattern to match Slack user mentions: <@USER_ID>
        mention_pattern = r'<@([A-Z0-9]+)>'
        
        # Find all unique user mentions
        mentions = set(re.findall(mention_pattern, text))
        
        # Cache user info to avoid duplicate API calls
        user_cache = {}
        for user_id in mentions:
            try:
                user_info = await self.get_user_info(user_id)
                display_name = user_info.get('display_name') or user_info.get('real_name') or f'@{user_info.get("name", "unknown")}'
                user_cache[user_id] = f'@{display_name}'
            except Exception as e:
                logger.error(f"Error getting user info for {user_id}: {e}")
                user_cache[user_id] = f'<@{user_id}>'  # Keep original mention if we can't resolve it
        
        # Replace all mentions in the text
        result = text
        for user_id, display_name in user_cache.items():
            result = result.replace(f'<@{user_id}>', display_name)
        
        return result

    def categorize_message(self, text: str) -> str:
        """
        Categorize a message based on its content and keywords
        
        Args:
            text: Message text to categorize
            
        Returns:
            Category name
        """
        text_lower = text.lower()
        
        # Define topic keywords with priority order
        topics = {
            "Scheduling": ["meeting", "calendar", "schedule", "deadline", "due date", "appointment", "call", "sync", "shift", "replacement", "cover"],
            "Client Management": ["client", "caregiver", "replacement", "cover", "shift", "assignment"],
            "Announcements": ["announcement", "update", "news", "important", "urgent", "breaking", "notice"],
            "Technical Discussions": ["code", "bug", "feature", "pr", "review", "deploy", "test", "api", "database", "system"],
            "Questions & Help": ["help", "question", "how to", "troubleshoot", "issue", "problem", "support"],
            "Celebrations": ["congratulations", "birthday", "anniversary", "celebration", "achievement", "milestone"],
            "Project Updates": ["project", "progress", "status", "milestone", "deliverable", "timeline"],
            "Team Building": ["team", "culture", "fun", "social", "event", "gathering"],
            "Tools & Resources": ["tool", "resource", "link", "document", "guide", "tutorial"]
        }
        
        # Score each topic based on keyword matches
        scores = {}
        for topic, keywords in topics.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[topic] = score
        
        # Return the topic with the highest score, or "General" if no matches
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        else:
            return "General"
    
    async def group_messages_by_topic(self, messages: List[SlackMessage]) -> Dict[str, List[SlackMessage]]:
        """
        Group messages by topic categories
        
        Args:
            messages: List of Slack messages
            
        Returns:
            Dictionary with topics as keys and lists of messages as values
        """
        topic_groups: Dict[str, List[SlackMessage]] = {}
        
        for message in messages:
            # Parse user mentions in the message
            parsed_text = await self.parse_user_mentions(message.text)
            
            # Categorize the message
            topic = self.categorize_message(parsed_text)
            
            # Add to the appropriate topic group
            if topic not in topic_groups:
                topic_groups[topic] = []
            
            # Create a copy of the message with parsed text
            message_copy = SlackMessage(
                text=parsed_text,
                user=message.user,
                timestamp=message.timestamp,
                reactions=message.reactions,
                reply_count=message.reply_count,
                channel=message.channel
            )
            
            topic_groups[topic].append(message_copy)
        
        return topic_groups

    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract dates mentioned in text
        
        Args:
            text: Message text to analyze
            
        Returns:
            List of dictionaries with extracted dates and their context
        """
        import re
        from datetime import datetime, timedelta
        
        dates = []
        text_lower = text.lower()
        
        # Patterns for different date formats
        patterns = [
            # Specific dates: "March 15th", "15th March", "3/15", "2024-03-15"
            (r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?\b', 'month_day'),
            (r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\b', 'day_month'),
            (r'\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b', 'slash_date'),
            (r'\b\d{4}-\d{1,2}-\d{1,2}\b', 'iso_date'),
            
            # Relative dates: "tomorrow", "next week", "in 2 days"
            (r'\b(?:today|tomorrow|yesterday)\b', 'relative_day'),
            (r'\b(?:next|last)\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|week|month|year)\b', 'relative_period'),
            (r'\bin\s+\d+\s+(?:day|week|month|year)s?\b', 'relative_future'),
            (r'\b\d+\s+(?:day|week|month|year)s?\s+ago\b', 'relative_past'),
            
            # Time references: "at 3pm", "by 5:30"
            (r'\b(?:at|by|before|after)\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b', 'time_reference'),
        ]
        
        for pattern, date_type in patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                date_text = match.group(0)
                start_pos = match.start()
                end_pos = match.end()
                
                # Get context around the date (20 characters before and after)
                context_start = max(0, start_pos - 20)
                context_end = min(len(text), end_pos + 20)
                context = text[context_start:context_end]
                
                dates.append({
                    'date_text': date_text,
                    'date_type': date_type,
                    'context': context,
                    'position': (start_pos, end_pos)
                })
        
        return dates
    
    async def enrich_messages_with_dates(self, messages: List[SlackMessage]) -> List[Dict[str, Any]]:
        """
        Enrich messages with extracted date information
        
        Args:
            messages: List of Slack messages
            
        Returns:
            List of enriched message dictionaries
        """
        enriched_messages = []
        
        for message in messages:
            # Parse user mentions
            parsed_text = await self.parse_user_mentions(message.text)
            
            # Extract dates
            dates = self.extract_dates(parsed_text)
            
            # Get user info
            user_info = await self.get_user_info(message.user)
            
            enriched_message = {
                'text': parsed_text,
                'user_id': message.user,
                'user_name': user_info.get('display_name') or user_info.get('real_name') or 'Unknown',
                'timestamp': message.timestamp,
                'reactions': len(message.reactions) if message.reactions else 0,
                'replies': message.reply_count or 0,
                'dates': dates,
                'has_dates': len(dates) > 0
            }
            
            enriched_messages.append(enriched_message)
        
        return enriched_messages


# Example usage and testing
async def test_slack_tool():
    """Test function to verify Slack tool functionality"""
    
    # Initialize with bot token from environment
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    if not bot_token:
        logger.error("SLACK_BOT_TOKEN not found in environment variables")
        return
    
    slack_tool = SlackTool(bot_token)
    
    # Test connection
    logger.info("Testing Slack connection...")
    if await slack_tool.test_connection():
        logger.info("✓ Slack connection successful")
    else:
        logger.error("✗ Slack connection failed")
        return
    
    # Get bot channels
    logger.info("\nFetching bot channels...")
    channels = await slack_tool.get_bot_channels()
    logger.info(f"Bot is member of {len(channels)} channels:")
    for channel in channels:
        logger.info(f"  - {channel['name']} (ID: {channel['id']})")
    
    # Test message fetching (if channels exist)
    if channels:
        channel_id = channels[0]["id"]
        logger.info(f"\nFetching recent messages from #{channels[0]['name']}...")
        
        # Get messages from the last week
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        messages = await slack_tool.get_channel_messages(channel_id, start_date, end_date)
        logger.info(f"Found {len(messages)} messages")
        
        # Filter important messages
        important_messages = await slack_tool.filter_important_messages(messages)
        logger.info(f"Filtered to {len(important_messages)} important messages")
        
        # Show sample message
        if important_messages:
            sample_msg = important_messages[0]
            logger.info(f"\nSample important message:")
            logger.info(f"  User: {sample_msg.user}")
            logger.info(f"  Text: {sample_msg.text[:100]}...")
            logger.info(f"  Reactions: {len(sample_msg.reactions)}")
            logger.info(f"  Replies: {sample_msg.reply_count}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_slack_tool())