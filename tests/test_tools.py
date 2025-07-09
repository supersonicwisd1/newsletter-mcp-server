"""
Comprehensive evaluations for Newsletter MCP Server tools
Tests all functionality including user mention parsing, topic organization, date extraction, and Google Docs integration
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from newsletter_mcp.tools.slack_tool import SlackTool
from newsletter_mcp.workflows.newsletter_workflow import NewsletterWorkflow

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

class NewsletterToolEvaluations:
    """Comprehensive evaluations for Newsletter MCP tools"""
    
    def __init__(self):
        self.slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not self.slack_token:
            raise ValueError("SLACK_BOT_TOKEN not found in environment")
        
        self.slack_tool = SlackTool(self.slack_token)
        self.workflow = NewsletterWorkflow(self.slack_token)
        
    async def eval_slack_connection(self):
        """Evaluate Slack connection and basic functionality"""
        print("🔍 Evaluating Slack Connection...")
        
        try:
            # Test connection
            is_connected = await self.slack_tool.test_connection()
            if not is_connected:
                return {"status": "FAIL", "message": "Slack connection failed"}
            
            # Get channels
            channels = await self.slack_tool.get_bot_channels()
            if not channels:
                return {"status": "FAIL", "message": "No channels accessible"}
            
            return {
                "status": "PASS",
                "message": f"Connected to {len(channels)} channels",
                "channels": [ch['name'] for ch in channels]
            }
        except Exception as e:
            return {"status": "FAIL", "message": f"Slack connection error: {e}"}
    
    async def eval_user_mention_parsing(self):
        """Evaluate user mention parsing functionality"""
        print("🔍 Evaluating User Mention Parsing...")
        
        test_cases = [
            {
                "input": "Hey <@U090LNR0Y9X>, can you review this PR?",
                "expected_contains": "@",
                "description": "Single user mention"
            },
            {
                "input": "Meeting with <@U1111111111> and <@U2222222222> tomorrow",
                "expected_contains": "@",
                "description": "Multiple user mentions"
            },
            {
                "input": "No mentions in this message",
                "expected_contains": "No mentions",
                "description": "No mentions"
            }
        ]
        
        results = []
        for i, test_case in enumerate(test_cases, 1):
            try:
                parsed = await self.slack_tool.parse_user_mentions(test_case["input"])
                
                # Check if parsing worked correctly
                if "<@" in test_case["input"]:
                    # Should have parsed mentions
                    success = "@" in parsed and parsed != test_case["input"]
                else:
                    # Should have left text unchanged
                    success = parsed == test_case["input"]
                
                results.append({
                    "test_case": i,
                    "description": test_case["description"],
                    "input": test_case["input"],
                    "output": parsed,
                    "status": "PASS" if success else "FAIL",
                    "success": success
                })
                
            except Exception as e:
                results.append({
                    "test_case": i,
                    "description": test_case["description"],
                    "input": test_case["input"],
                    "output": f"ERROR: {e}",
                    "status": "FAIL",
                    "success": False
                })
        
        passed = sum(1 for r in results if r["success"])
        return {
            "status": "PASS" if passed == len(results) else "FAIL",
            "message": f"User mention parsing: {passed}/{len(results)} tests passed",
            "results": results
        }
    
    async def eval_topic_organization(self):
        """Evaluate topic-based message organization"""
        print("🔍 Evaluating Topic Organization...")
        
        test_messages = [
            {
                "text": "We have a meeting tomorrow at 3pm",
                "expected_topic": "Scheduling",
                "description": "Scheduling message"
            },
            {
                "text": "New feature deployed to production!",
                "expected_topic": "Technical Discussions",
                "description": "Technical message"
            },
            {
                "text": "Can someone help me with this issue?",
                "expected_topic": "Questions & Help",
                "description": "Help request"
            },
            {
                "text": "Happy birthday @john! 🎉",
                "expected_topic": "Celebrations",
                "description": "Celebration message"
            },
            {
                "text": "Find a replacement for client shift",
                "expected_topic": "Client Management",
                "description": "Client management message"
            }
        ]
        
        results = []
        for i, test_case in enumerate(test_messages, 1):
            try:
                topic = self.slack_tool.categorize_message(test_case["text"])
                success = topic == test_case["expected_topic"]
                
                results.append({
                    "test_case": i,
                    "description": test_case["description"],
                    "input": test_case["text"],
                    "expected_topic": test_case["expected_topic"],
                    "actual_topic": topic,
                    "status": "PASS" if success else "FAIL",
                    "success": success
                })
                
            except Exception as e:
                results.append({
                    "test_case": i,
                    "description": test_case["description"],
                    "input": test_case["text"],
                    "expected_topic": test_case["expected_topic"],
                    "actual_topic": f"ERROR: {e}",
                    "status": "FAIL",
                    "success": False
                })
        
        passed = sum(1 for r in results if r["success"])
        return {
            "status": "PASS" if passed == len(results) else "FAIL",
            "message": f"Topic organization: {passed}/{len(results)} tests passed",
            "results": results
        }
    
    async def eval_date_extraction(self):
        """Evaluate date extraction functionality"""
        print("🔍 Evaluating Date Extraction...")
        
        test_messages = [
            {
                "text": "Meeting tomorrow at 3pm",
                "expected_dates": ["tomorrow", "3pm"],
                "description": "Relative date and time"
            },
            {
                "text": "Deadline is March 15th",
                "expected_dates": ["march 15th"],
                "description": "Specific date"
            },
            {
                "text": "Release scheduled for next week",
                "expected_dates": ["next week"],
                "description": "Relative period"
            },
            {
                "text": "Project due in 2 weeks",
                "expected_dates": ["in 2 weeks"],
                "description": "Future reference"
            },
            {
                "text": "No dates mentioned here",
                "expected_dates": [],
                "description": "No dates"
            }
        ]
        
        results = []
        for i, test_case in enumerate(test_messages, 1):
            try:
                dates = self.slack_tool.extract_dates(test_case["text"])
                extracted_dates = [d["date_text"] for d in dates]
                
                # Check if expected dates were found
                expected_found = all(any(exp.lower() in date.lower() for date in extracted_dates) 
                                   for exp in test_case["expected_dates"])
                
                # Check if no unexpected dates when none expected
                if not test_case["expected_dates"]:
                    success = len(dates) == 0
                else:
                    success = expected_found
                
                results.append({
                    "test_case": i,
                    "description": test_case["description"],
                    "input": test_case["text"],
                    "expected_dates": test_case["expected_dates"],
                    "extracted_dates": extracted_dates,
                    "status": "PASS" if success else "FAIL",
                    "success": success
                })
                
            except Exception as e:
                results.append({
                    "test_case": i,
                    "description": test_case["description"],
                    "input": test_case["text"],
                    "expected_dates": test_case["expected_dates"],
                    "extracted_dates": f"ERROR: {e}",
                    "status": "FAIL",
                    "success": False
                })
        
        passed = sum(1 for r in results if r["success"])
        return {
            "status": "PASS" if passed == len(results) else "FAIL",
            "message": f"Date extraction: {passed}/{len(results)} tests passed",
            "results": results
        }
    
    async def eval_message_filtering(self):
        """Evaluate important message filtering"""
        print("🔍 Evaluating Message Filtering...")
        
        try:
            # Get channels
            channels = await self.slack_tool.get_bot_channels()
            if not channels:
                return {"status": "FAIL", "message": "No channels available for testing"}
            
            channel = channels[0]
            
            # Get messages from last 7 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            messages = await self.slack_tool.get_channel_messages(channel['id'], start_date, end_date)
            
            if not messages:
                return {"status": "FAIL", "message": "No messages available for testing"}
            
            # Filter important messages
            important_messages = await self.slack_tool.filter_important_messages(messages)
            
            # Check filtering logic
            total_messages = len(messages)
            important_count = len(important_messages)
            
            # Basic sanity checks
            if important_count > total_messages:
                return {"status": "FAIL", "message": "Filtered count greater than total count"}
            
            if important_count == 0 and total_messages > 0:
                return {"status": "WARN", "message": "No important messages found (might be normal)"}
            
            return {
                "status": "PASS",
                "message": f"Filtered {important_count}/{total_messages} messages as important",
                "total_messages": total_messages,
                "important_messages": important_count,
                "filtering_ratio": important_count / total_messages if total_messages > 0 else 0
            }
            
        except Exception as e:
            return {"status": "FAIL", "message": f"Message filtering error: {e}"}
    
    async def eval_google_docs_integration(self):
        """Evaluate Google Docs integration"""
        print("🔍 Evaluating Google Docs Integration...")
        
        try:
            # Test creating a simple document
            test_content = f"""Test Newsletter Evaluation
Generated on {datetime.now().strftime('%B %d, %Y')}

This is a test document to evaluate Google Docs integration.

Features being tested:
✅ Document creation
✅ Content insertion
✅ URL generation

Generated by Newsletter MCP Bot 🤖"""
            
            doc_info = await self.workflow._create_newsletter_document(test_content)
            
            # Check required fields
            required_fields = ['document_id', 'title', 'url']
            missing_fields = [field for field in required_fields if field not in doc_info]
            
            if missing_fields:
                return {
                    "status": "FAIL",
                    "message": f"Missing required fields: {missing_fields}",
                    "doc_info": doc_info
                }
            
            # Check URL format
            if not doc_info['url'].startswith('https://docs.google.com/'):
                return {
                    "status": "FAIL",
                    "message": "Invalid Google Docs URL format",
                    "url": doc_info['url']
                }
            
            return {
                "status": "PASS",
                "message": "Google Docs integration working",
                "document_id": doc_info['document_id'],
                "title": doc_info['title'],
                "url": doc_info['url']
            }
            
        except Exception as e:
            return {"status": "FAIL", "message": f"Google Docs integration error: {e}"}
    
    async def eval_full_workflow(self):
        """Evaluate complete newsletter generation workflow"""
        print("🔍 Evaluating Full Workflow...")
        
        try:
            # Generate newsletter for last 3 days (shorter for testing)
            result = await self.workflow.generate_newsletter(days_back=3)
            
            # Check required fields
            required_fields = ['document_url', 'document_id', 'title', 'channels_processed', 'total_messages', 'important_messages']
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                return {
                    "status": "FAIL",
                    "message": f"Missing required fields in workflow result: {missing_fields}",
                    "result": result
                }
            
            # Basic sanity checks
            if result['channels_processed'] <= 0:
                return {"status": "FAIL", "message": "No channels processed"}
            
            if result['total_messages'] < 0:
                return {"status": "FAIL", "message": "Invalid message count"}
            
            return {
                "status": "PASS",
                "message": f"Complete workflow successful: {result['important_messages']} important messages from {result['channels_processed']} channels",
                "statistics": {
                    "channels_processed": result['channels_processed'],
                    "total_messages": result['total_messages'],
                    "important_messages": result['important_messages'],
                    "document_url": result['document_url']
                }
            }
            
        except Exception as e:
            return {"status": "FAIL", "message": f"Full workflow error: {e}"}
    
    async def run_all_evaluations(self):
        """Run all evaluations and generate comprehensive report"""
        print("🚀 Running Newsletter MCP Tool Evaluations\n")
        
        evaluations = [
            ("Slack Connection", self.eval_slack_connection),
            ("User Mention Parsing", self.eval_user_mention_parsing),
            ("Topic Organization", self.eval_topic_organization),
            ("Date Extraction", self.eval_date_extraction),
            ("Message Filtering", self.eval_message_filtering),
            ("Google Docs Integration", self.eval_google_docs_integration),
            ("Full Workflow", self.eval_full_workflow)
        ]
        
        results = {}
        total_passed = 0
        total_tests = len(evaluations)
        
        for name, eval_func in evaluations:
            print(f"\n{'='*50}")
            print(f"Evaluating: {name}")
            print(f"{'='*50}")
            
            try:
                result = await eval_func()
                results[name] = result
                
                if result["status"] == "PASS":
                    total_passed += 1
                    print(f"✅ {name}: PASS")
                elif result["status"] == "WARN":
                    print(f"⚠️  {name}: WARN - {result['message']}")
                else:
                    print(f"❌ {name}: FAIL - {result['message']}")
                
                print(f"   {result['message']}")
                
            except Exception as e:
                results[name] = {"status": "FAIL", "message": f"Evaluation error: {e}"}
                print(f"❌ {name}: FAIL - Evaluation error: {e}")
        
        # Generate summary report
        print(f"\n{'='*60}")
        print("📊 EVALUATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_tests - total_passed}")
        print(f"Success Rate: {(total_passed/total_tests)*100:.1f}%")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS")
        print(f"{'='*60}")
        for name, result in results.items():
            status_icon = "✅" if result["status"] == "PASS" else "⚠️" if result["status"] == "WARN" else "❌"
            print(f"{status_icon} {name}: {result['message']}")
        
        # Save detailed results to file
        with open("evaluation_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: evaluation_results.json")
        
        return {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_tests - total_passed,
            "success_rate": (total_passed/total_tests)*100,
            "results": results
        }

async def main():
    """Run all evaluations"""
    try:
        evaluator = NewsletterToolEvaluations()
        summary = await evaluator.run_all_evaluations()
        
        if summary["success_rate"] >= 80:
            print(f"\n🎉 Excellent! {summary['success_rate']:.1f}% success rate")
        elif summary["success_rate"] >= 60:
            print(f"\n👍 Good! {summary['success_rate']:.1f}% success rate")
        else:
            print(f"\n⚠️  Needs improvement: {summary['success_rate']:.1f}% success rate")
            
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
