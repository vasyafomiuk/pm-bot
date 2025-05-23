import logging
from typing import List, Dict, Any
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from config import settings
from models import Epic, UserStory, EpicResponse

logger = logging.getLogger(__name__)


class SlackService:
    """Service for handling Slack bot interactions"""
    
    def __init__(self):
        self.app = App(
            token=settings.slack_bot_token,
            signing_secret=settings.slack_signing_secret
        )
        self.handler = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup Slack event handlers"""
        
        @self.app.message("create epic")
        async def handle_create_epic_message(message, say):
            """Handle 'create epic' messages"""
            try:
                await say("I'll help you create an epic! Please provide the epic details in this format:\n" +
                         "```\n" +
                         "Title: Your Epic Title\n" +
                         "Description: Detailed description of the epic\n" +
                         "Features: feature1, feature2, feature3 (optional)\n" +
                         "Priority: High/Medium/Low (optional)\n" +
                         "```")
            except Exception as e:
                logger.error(f"Error handling create epic message: {str(e)}")
                await say("Sorry, I encountered an error. Please try again.")
        
        @self.app.command("/create-epic")
        async def handle_create_epic_command(ack, body, say):
            """Handle /create-epic slash command"""
            await ack()
            
            try:
                text = body.get('text', '').strip()
                if not text:
                    await say(self._get_epic_help_message())
                    return
                
                # Parse the epic request from the command text
                epic_data = self._parse_epic_request(text)
                if not epic_data:
                    await say("Invalid format. " + self._get_epic_help_message())
                    return
                
                # Send initial response
                await say(f"🚀 Creating epic: **{epic_data.get('title', 'Unknown')}**\n" +
                         "Please wait while I generate features and user stories...")
                
                # Return parsed data for processing by the main handler
                return epic_data
                
            except Exception as e:
                logger.error(f"Error handling create epic command: {str(e)}")
                await say("Sorry, I encountered an error processing your request. Please try again.")
    
    def _parse_epic_request(self, text: str) -> Dict[str, Any]:
        """
        Parse epic request from text
        
        Args:
            text: Raw text from Slack command
            
        Returns:
            Parsed epic data dictionary
        """
        epic_data = {}
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key in ['title', 'name']:
                    epic_data['title'] = value
                elif key in ['description', 'desc']:
                    epic_data['description'] = value
                elif key in ['features', 'feature']:
                    # Parse comma-separated features
                    features = [f.strip() for f in value.split(',') if f.strip()]
                    epic_data['preferred_features'] = features
                elif key in ['priority', 'prio']:
                    epic_data['priority'] = value
                elif key in ['labels', 'label']:
                    labels = [l.strip() for l in value.split(',') if l.strip()]
                    epic_data['labels'] = labels
        
        # Validate required fields
        if 'title' not in epic_data or 'description' not in epic_data:
            return None
        
        return epic_data
    
    def _get_epic_help_message(self) -> str:
        """Get help message for epic creation"""
        return """
        Please provide epic details in this format:
        ```
        Title: Your Epic Title
        Description: Detailed description of the epic
        Features: feature1, feature2, feature3 (optional)
        Priority: High/Medium/Low (optional, default: Medium)
        Labels: label1, label2 (optional)
        ```
        
        Example:
        ```
        Title: User Authentication System
        Description: Implement a comprehensive user authentication system with login, registration, and password reset functionality
        Features: user registration, login/logout, password reset, two-factor authentication
        Priority: High
        Labels: security, authentication
        ```
        """
    
    async def send_epic_creation_progress(self, channel: str, message: str):
        """Send progress update message"""
        try:
            await self.app.client.chat_postMessage(
                channel=channel,
                text=message
            )
        except Exception as e:
            logger.error(f"Error sending progress message: {str(e)}")
    
    async def send_epic_response(self, channel: str, epic_response: EpicResponse):
        """
        Send formatted epic creation response
        
        Args:
            channel: Slack channel ID
            epic_response: Epic creation response
        """
        try:
            if epic_response.success and epic_response.epic:
                message = self._format_epic_success_message(epic_response)
            else:
                message = f"❌ **Epic Creation Failed**\n{epic_response.message}"
            
            await self.app.client.chat_postMessage(
                channel=channel,
                text=message,
                parse='mrkdwn'
            )
            
        except Exception as e:
            logger.error(f"Error sending epic response: {str(e)}")
    
    def _format_epic_success_message(self, epic_response: EpicResponse) -> str:
        """Format successful epic creation message"""
        epic = epic_response.epic
        
        message = f"""✅ **Epic Created Successfully!**

**Epic Details:**
• **Key:** `{epic.key}`
• **Title:** {epic.title}
• **Priority:** {epic.priority}
• **Status:** {epic.status}

**Description:**
{epic.description}
"""
        
        if epic.features:
            message += f"\n**Generated Features:**\n"
            for i, feature in enumerate(epic.features, 1):
                message += f"{i}. {feature}\n"
        
        if epic_response.user_stories_count:
            message += f"\n**User Stories:** {epic_response.user_stories_count} stories created and linked to this epic"
        
        if epic.labels:
            message += f"\n**Labels:** {', '.join(epic.labels)}"
        
        message += f"\n\n🔗 View in Jira: {settings.jira_server}/browse/{epic.key}"
        
        return message
    
    async def send_user_stories_summary(self, channel: str, epic_key: str, user_stories: List[UserStory]):
        """
        Send summary of created user stories
        
        Args:
            channel: Slack channel ID
            epic_key: Epic key
            user_stories: List of created user stories
        """
        try:
            if not user_stories:
                message = f"No user stories were created for epic {epic_key}"
            else:
                message = f"📋 **User Stories Created for Epic {epic_key}:**\n\n"
                
                for i, story in enumerate(user_stories, 1):
                    message += f"**{i}. {story.title}** (`{story.key}`)\n"
                    message += f"   • Priority: {story.priority}\n"
                    message += f"   • Story Points: {story.story_points or 'TBD'}\n"
                    if story.acceptance_criteria:
                        message += f"   • Acceptance Criteria: {len(story.acceptance_criteria)} items\n"
                    message += f"   • View: {settings.jira_server}/browse/{story.key}\n\n"
            
            await self.app.client.chat_postMessage(
                channel=channel,
                text=message,
                parse='mrkdwn'
            )
            
        except Exception as e:
            logger.error(f"Error sending user stories summary: {str(e)}")
    
    async def send_error_message(self, channel: str, error_message: str):
        """Send error message to channel"""
        try:
            message = f"❌ **Error:** {error_message}"
            
            await self.app.client.chat_postMessage(
                channel=channel,
                text=message,
                parse='mrkdwn'
            )
            
        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}")
    
    async def send_message(self, channel: str, message: str):
        """Send a generic message to a channel"""
        try:
            await self.app.client.chat_postMessage(
                channel=channel,
                text=message,
                parse='mrkdwn'
            )
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
    
    def start_socket_mode(self):
        """Start the Slack bot in socket mode"""
        try:
            self.handler = SocketModeHandler(self.app, settings.slack_app_token)
            logger.info("Starting Slack bot in socket mode...")
            self.handler.start()
            
        except Exception as e:
            logger.error(f"Error starting Slack bot: {str(e)}")
            raise
    
    def stop(self):
        """Stop the Slack bot"""
        if self.handler:
            self.handler.close()
            logger.info("Slack bot stopped")
    
    async def handle_mention(self, event, say):
        """Handle @bot mentions"""
        try:
            text = event.get('text', '').lower()
            
            if 'help' in text:
                await say(self._get_help_message())
            elif 'epic' in text and 'create' in text:
                await say(self._get_epic_help_message())
            else:
                await say("Hi! I'm your Project Management Assistant. " +
                         "I can help you create epics and user stories in Jira. " +
                         "Type 'help' to see available commands.")
                
        except Exception as e:
            logger.error(f"Error handling mention: {str(e)}")
            await say("Sorry, I encountered an error. Please try again.")
    
    def _get_help_message(self) -> str:
        """Get general help message"""
        return """
        🤖 **Project Management Bot - Available Commands:**
        
        • `/create-epic` - Create a new epic with user stories
        • `@bot help` - Show this help message
        • `@bot create epic` - Get help for creating epics
        
        **Quick Start:**
        Use `/create-epic` command with the following format:
        ```
        Title: Your Epic Title
        Description: Epic description
        Features: feature1, feature2 (optional)
        Priority: High/Medium/Low (optional)
        ```
        
        I'll automatically generate user stories and link them to your epic in Jira!
        """ 