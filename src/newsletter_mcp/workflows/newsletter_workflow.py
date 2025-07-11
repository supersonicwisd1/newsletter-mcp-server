"""
Newsletter Workflow - Combines Slack data with Google Docs creation
End-to-end workflow for generating weekly newsletters
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional, List
from dotenv import load_dotenv
import sys
sys.path.append('src')

from newsletter_mcp.tools.slack_tool import SlackTool
from newsletter_mcp.tools.gdocs_tool import GoogleDocsTool
from newsletter_mcp.tools.gmail_tool import GmailTool, EmailRecipient

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class NewsletterWorkflow:
    """Orchestrates the complete newsletter generation workflow"""
    
    def __init__(self, slack_token: str):
        self.slack_tool = SlackTool(slack_token)
        self.docs_tool = GoogleDocsTool()
        self.gmail_tool = GmailTool()
        logger.info("✅ Newsletter workflow initialized with Slack, Google Docs, and Gmail tools")
    
    async def async_init(self):
        await self.docs_tool.async_init()
        await self.gmail_tool.async_init()
    
    async def generate_newsletter(
        self, 
        days_back: int = 7, 
        send_email: bool = False,
        custom_recipients: Optional[List[str]] = None
    ) -> dict:
        """
        Generate a complete newsletter from Slack data
        
        Args:
            days_back: Number of days to look back for messages
            send_email: Whether to send email notification (default: False)
            custom_recipients: Custom list of email recipients (default: None, uses env var)
            
        Returns:
            Dictionary with newsletter info and document URL
        """
        logger.info(f"🔍 Generating newsletter for the last {days_back} days...")
        
        # Step 1: Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Step 2: Get all channels the bot has access to
        channels = await self.slack_tool.get_bot_channels()
        if not channels:
            raise Exception("No channels found. Make sure the bot is added to some channels.")
        
        logger.info(f"📡 Found {len(channels)} channels to analyze")
        
        # Step 3: Collect messages from all channels
        all_channel_data = []
        total_messages = 0
        total_important = 0
        
        for channel in channels:
            logger.info(f"  📥 Processing #{channel['name']}...")
            
            # Get messages from this channel
            messages = await self.slack_tool.get_channel_messages(
                channel['id'], start_date, end_date
            )
            
            # Filter important messages
            important_messages = await self.slack_tool.filter_important_messages(messages)
            
            # Group messages by topic
            topic_groups = await self.slack_tool.group_messages_by_topic(important_messages)
            
            # Enrich messages with dates and user info
            enriched_messages = await self.slack_tool.enrich_messages_with_dates(important_messages)
            
            # Get user info for important messages (for better attribution)
            enriched_messages_with_user_info = []
            for msg in important_messages:
                # Parse user mentions in the message
                parsed_text = await self.slack_tool.parse_user_mentions(msg.text)
                
                user_info = await self.slack_tool.get_user_info(msg.user)
                enriched_msg = {
                    'text': parsed_text,  # Use parsed text with resolved mentions
                    'user_id': msg.user,
                    'user_name': user_info.get('display_name') or user_info.get('real_name') or user_info.get('name', 'Unknown'),
                    'timestamp': msg.timestamp,
                    'reactions': len(msg.reactions) if msg.reactions else 0,
                    'replies': msg.reply_count or 0
                }
                enriched_messages_with_user_info.append(enriched_msg)
            
            channel_data = {
                'name': channel['name'],
                'id': channel['id'],
                'total_messages': len(messages),
                'important_messages': enriched_messages_with_user_info,
                'topic_groups': topic_groups,
                'enriched_messages': enriched_messages,
                'member_count': channel['member_count']
            }
            
            all_channel_data.append(channel_data)
            total_messages += len(messages)
            total_important += len(important_messages)
            
            logger.info(f"    📊 {len(messages)} total, {len(important_messages)} important")
            logger.info(f"    📂 Organized into {len(topic_groups)} topics")
        
        # Step 4: Generate newsletter content
        newsletter_content = self._generate_newsletter_content(
            all_channel_data, start_date, end_date, total_messages, total_important
        )
        
        # Step 5: Create Google Doc
        doc_info = await self._create_newsletter_document(newsletter_content)
        
        # Step 6: Send email notification (if requested)
        email_result = None
        if send_email:
            try:
                email_result = await self._send_newsletter_email(
                    doc_info, 
                    total_important, 
                    total_messages,
                    custom_recipients
                )
                logger.info(f"✅ Email sent successfully to {len(custom_recipients) if custom_recipients else 'subscribers'}")
            except Exception as e:
                logger.error(f"⚠️  Email sending failed: {e}")
        else:
            logger.info("📧 Email sending skipped (send_email=False)")
        
        return {
            'document_url': doc_info['url'],
            'document_id': doc_info['document_id'],
            'title': doc_info['title'],
            'channels_processed': len(channels),
            'total_messages': total_messages,
            'important_messages': total_important,
            'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'email_sent': email_result is not None,
            'email_result': email_result,
            'send_email_requested': send_email
        }
    
    def _generate_newsletter_content(self, channel_data, start_date, end_date, total_messages, total_important):
        """Generate formatted newsletter content from channel data"""
        
        date_str = end_date.strftime("%B %d, %Y")
        week_range = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
        
        content = f"""Weekly Development Newsletter
Generated on {date_str}
Report Period: {week_range}

📊 SUMMARY
This week, our team was active across {len(channel_data)} channels with {total_messages} total messages. We've identified {total_important} important updates and discussions worth highlighting.

"""
        
        # Add channel-by-channel breakdown
        content += "🏢 CHANNEL UPDATES\n\n"
        
        for channel in channel_data:
            if not channel['important_messages']:
                continue
                
            content += f"#{channel['name'].upper()}\n"
            content += f"Members: {channel['member_count']} | Important Updates: {len(channel['important_messages'])}\n\n"
            
            # Add topic-based organization
            topic_groups = channel.get('topic_groups', {})
            if topic_groups and any(len(msgs) > 0 for msgs in topic_groups.values()):
                content += "📂 ORGANIZED BY TOPIC:\n\n"
                
                for topic, messages in topic_groups.items():
                    if len(messages) > 0:
                        content += f"🔹 {topic.upper()} ({len(messages)} updates)\n"
                        
                        for i, msg in enumerate(messages[:3], 1):  # Top 3 per topic
                            # Clean up the message text
                            text = msg.text.replace('\n', ' ').strip()
                            if len(text) > 120:
                                text = text[:120] + "..."
                            
                            # Add engagement indicators
                            engagement = ""
                            if msg.reactions and len(msg.reactions) > 0:
                                engagement += f"👍{len(msg.reactions)} "
                            if msg.reply_count and msg.reply_count > 0:
                                engagement += f"💬{msg.reply_count} "
                            
                            content += f"  {i}. {text}"
                            if engagement:
                                content += f" [{engagement.strip()}]"
                            content += "\n"
                        
                        if len(messages) > 3:
                            remaining = len(messages) - 3
                            content += f"    ... and {remaining} more\n"
                        content += "\n"
            
            # Add date highlights
            enriched_messages = channel.get('enriched_messages', [])
            messages_with_dates = [msg for msg in enriched_messages if msg.get('has_dates', False)]
            
            if messages_with_dates:
                content += "📅 UPCOMING DATES & DEADLINES:\n"
                for msg in messages_with_dates[:5]:  # Top 5 with dates
                    for date_info in msg.get('dates', [])[:2]:  # First 2 dates per message
                        content += f"  • {msg['user_name']}: {date_info['date_text']} ({date_info['context'].strip()})\n"
                content += "\n"
            
            # Add top important messages (always show this section)
            content += "📝 TOP UPDATES:\n\n"
            for i, msg in enumerate(channel['important_messages'][:5], 1):  # Top 5 per channel
                # Clean up the message text
                text = msg['text'].replace('\n', ' ').strip()
                if len(text) > 150:
                    text = text[:150] + "..."
                
                # Add engagement indicators
                engagement = ""
                if msg['reactions'] > 0:
                    engagement += f"👍{msg['reactions']} "
                if msg['replies'] > 0:
                    engagement += f"💬{msg['replies']} "
                
                content += f"{i}. {msg['user_name']}: {text}"
                if engagement:
                    content += f" [{engagement.strip()}]"
                content += "\n\n"
            
            if len(channel['important_messages']) > 5:
                remaining = len(channel['important_messages']) - 5
                content += f"... and {remaining} more important updates\n\n"
            
            content += "─" * 50 + "\n\n"
        
        # Add footer
        content += """📝 ABOUT THIS NEWSLETTER
This newsletter is automatically generated from Slack conversations using our MCP (Model Context Protocol) server. It identifies important messages based on engagement (reactions, replies) and content analysis.

Generated by Newsletter MCP Bot 🤖"""
        
        return content
    
    async def _create_newsletter_document(self, content):
        """Create the Google Doc with newsletter content using GoogleDocsTool"""
        
        # Generate title with current date
        title = f"Weekly Dev Newsletter - {datetime.now().strftime('%B %d, %Y')}"
        
        try:
            # Use GoogleDocsTool to create the document
            doc_info = await self.docs_tool.create_document(title, content)
            
            return {
                'document_id': doc_info['document_id'],
                'title': doc_info['title'],
                'url': doc_info['url']
            }
            
        except Exception as e:
            raise Exception(f"Failed to create newsletter document: {e}")

    async def _send_newsletter_email(
        self, 
        doc_info: dict, 
        important_count: int, 
        total_count: int,
        custom_recipients: Optional[List[str]] = None
    ) -> Optional[dict]:
        """Send newsletter email notification"""
        try:
            # Determine recipients
            if custom_recipients:
                # Use custom recipients
                recipients = []
                for email in custom_recipients:
                    if email and '@' in email:
                        recipients.append(EmailRecipient(email=email.strip()))
                logger.info(f"📧 Using custom recipients: {len(recipients)} addresses")
            else:
                # Get recipients from environment
                recipients_str = os.getenv('NEWSLETTER_SUBSCRIBER_EMAILS', '')
                if not recipients_str:
                    logger.error("⚠️  No newsletter subscribers configured (NEWSLETTER_SUBSCRIBER_EMAILS)")
                    return None
                
                # Parse recipients
                recipients = []
                for email in recipients_str.split(','):
                    email = email.strip()
                    if email and '@' in email:
                        recipients.append(EmailRecipient(email=email))
                logger.info(f"📧 Using environment recipients: {len(recipients)} addresses")
            
            if not recipients:
                logger.error("⚠️  No valid email recipients found")
                return None
            
            # Create summary
            summary = f"Generated newsletter with {important_count} important updates from {total_count} total messages across multiple channels."
            
            # Send email
            result = await self.gmail_tool.send_newsletter_with_document_link(
                recipients=recipients,
                newsletter_title=doc_info['title'],
                document_url=doc_info['url'],
                summary=summary
            )
            
            logger.info(f"✅ Newsletter email sent to {len(recipients)} recipients")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to send newsletter email: {e}")
            return None


async def test_full_workflow():
    """Test the complete newsletter generation workflow"""
    
    load_dotenv()
    
    # Get Slack token
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    if not slack_token:
        logger.error("❌ SLACK_BOT_TOKEN not found in .env file")
        return
    
    try:
        logger.info("🚀 Starting Newsletter Generation Workflow...")
        
        # Initialize workflow
        workflow = NewsletterWorkflow(slack_token)
        await workflow.async_init() # Call async_init here
        
        # Generate newsletter
        result = await workflow.generate_newsletter(days_back=7)
        
        logger.info(f"\n🎉 Newsletter Generated Successfully!")
        logger.info(f"📄 Document Title: {result['title']}")
        logger.info(f"🔗 Document URL: {result['document_url']}")
        logger.info(f"📊 Statistics:")
        logger.info(f"   - Channels processed: {result['channels_processed']}")
        logger.info(f"   - Total messages: {result['total_messages']}")
        logger.info(f"   - Important messages: {result['important_messages']}")
        logger.info(f"   - Date range: {result['date_range']}")
        
        logger.info(f"\n✨ Open the document to see your newsletter: {result['document_url']}")
        
    except Exception as e:
        logger.error(f"❌ Workflow failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_full_workflow())