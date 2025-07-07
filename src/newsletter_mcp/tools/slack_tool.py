"""
Slack Tool for Newsletter MCP Server
Handles fetching messages, channel info, and filtering important conversations
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from pydantic import BaseModel
import json


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
        self.client = WebClient(token=bot_token)
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
            response = self.client.conversations_history(
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
            print(f"Error fetching messages: {e}")
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
            response = self.client.conversations_info(channel=channel_id)
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
            print(f"Error getting channel info: {e}")
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
            response = self.client.users_info(user=user_id)
            user = response["user"]
            
            return {
                "id": user["id"],
                "name": user.get("name", ""),
                "real_name": user.get("real_name", ""),
                "display_name": user.get("profile", {}).get("display_name", ""),
                "email": user.get("profile", {}).get("email", "")
            }
            
        except SlackApiError as e:
            print(f"Error getting user info: {e}")
            return {}
    
    async def test_connection(self) -> bool:
        """
        Test if the Slack connection is working
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = self.client.auth_test()
            print(f"Connected to Slack as: {response['user']}")
            return True
        except SlackApiError as e:
            print(f"Connection test failed: {e}")
            return False
    
    async def get_bot_channels(self) -> List[Dict[str, Any]]:
        """
        Get list of channels the bot is a member of
        
        Returns:
            List of channel information dictionaries
        """
        try:
            response = self.client.conversations_list(
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
            print(f"Error getting bot channels: {e}")
            return []


# Example usage and testing
async def test_slack_tool():
    """Test function to verify Slack tool functionality"""
    
    # Initialize with bot token from environment
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    if not bot_token:
        print("SLACK_BOT_TOKEN not found in environment variables")
        return
    
    slack_tool = SlackTool(bot_token)
    
    # Test connection
    print("Testing Slack connection...")
    if await slack_tool.test_connection():
        print("✓ Slack connection successful")
    else:
        print("✗ Slack connection failed")
        return
    
    # Get bot channels
    print("\nFetching bot channels...")
    channels = await slack_tool.get_bot_channels()
    print(f"Bot is member of {len(channels)} channels:")
    for channel in channels:
        print(f"  - {channel['name']} (ID: {channel['id']})")
    
    # Test message fetching (if channels exist)
    if channels:
        channel_id = channels[0]["id"]
        print(f"\nFetching recent messages from #{channels[0]['name']}...")
        
        # Get messages from the last week
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        messages = await slack_tool.get_channel_messages(channel_id, start_date, end_date)
        print(f"Found {len(messages)} messages")
        
        # Filter important messages
        important_messages = await slack_tool.filter_important_messages(messages)
        print(f"Filtered to {len(important_messages)} important messages")
        
        # Show sample message
        if important_messages:
            sample_msg = important_messages[0]
            print(f"\nSample important message:")
            print(f"  User: {sample_msg.user}")
            print(f"  Text: {sample_msg.text[:100]}...")
            print(f"  Reactions: {len(sample_msg.reactions)}")
            print(f"  Replies: {sample_msg.reply_count}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_slack_tool())