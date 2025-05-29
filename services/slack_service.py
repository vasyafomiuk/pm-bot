import logging
from typing import List, Dict, Any, Optional
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
        # Store conversation states per user
        self.conversation_states = {}
        self.bot_user_id = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup Slack event handlers"""
        
        @self.app.event("app_mention")
        async def handle_app_mention(event, say):
            """Handle app mentions with conversational flow"""
            await self._handle_conversational_message(event, say)
        
        @self.app.event("message")
        async def handle_direct_message(event, say):
            """Handle direct messages with conversational flow"""
            # Only handle direct messages (not channel messages)
            if event.get("channel_type") == "im":
                await self._handle_conversational_message(event, say)
        
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
    
    async def _handle_conversational_message(self, event, say):
        """Handle conversational messages with Q&A flow"""
        try:
            user_id = event.get("user")
            text = event.get("text", "").strip()
            
            # Remove bot mention from text if present
            if f"<@{await self._get_bot_user_id()}>" in text:
                text = text.replace(f"<@{await self._get_bot_user_id()}>", "").strip()
            
            # Check for greeting or initial contact
            if self._is_greeting_or_initial(text) or user_id not in self.conversation_states:
                await self._start_conversation(user_id, say)
                return
            
            # Check for done/goodbye
            if self._is_done_message(text):
                await self._end_conversation(user_id, say)
                return
            
            # Handle based on conversation state
            state = self.conversation_states.get(user_id, {})
            current_step = state.get("step", "initial")
            
            if current_step == "awaiting_choice":
                await self._handle_user_choice(user_id, text, say)
            elif current_step == "epic_creation":
                await self._handle_epic_creation_flow(user_id, text, say)
            elif current_step == "meeting_processing":
                await self._handle_meeting_processing_flow(user_id, text, say)
            elif current_step == "meeting_search":
                await self._handle_meeting_search_flow(user_id, text, say)
            elif current_step == "document_epic_creation":
                await self._handle_document_epic_flow(user_id, text, say)
            elif current_step == "awaiting_epic_approval":
                await self._handle_epic_approval(user_id, text, say)
            elif current_step == "collecting_epic_feedback":
                await self._handle_epic_feedback(user_id, text, say)
            else:
                # Default response
                await self._start_conversation(user_id, say)
                
        except Exception as e:
            logger.error(f"Error handling conversational message: {str(e)}")
            await say("Sorry, I encountered an error. Please try again.")
    
    def _is_greeting_or_initial(self, text: str) -> bool:
        """Check if message is a greeting or initial contact"""
        greetings = ["hi", "hello", "hey", "start", "help", "what can you do"]
        text_lower = text.lower()
        return any(greeting in text_lower for greeting in greetings) or len(text.split()) <= 2
    
    def _is_done_message(self, text: str) -> bool:
        """Check if user wants to end the conversation"""
        done_phrases = ["done", "finished", "complete", "bye", "goodbye", "thanks", "thank you", "that's all", "exit", "quit"]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in done_phrases)
    
    async def _start_conversation(self, user_id: str, say):
        """Start the conversation with the user"""
        self.conversation_states[user_id] = {"step": "awaiting_choice"}
        
        message = """👋 **What can I do for you?**

I can help you with:

1️⃣ **Create Epic** - Create a new epic with user stories in Jira
2️⃣ **Process Meetings** - Process recent meeting notes to Confluence
3️⃣ **Search Meetings** - Find and process specific meetings
4️⃣ **Help** - Get detailed information about my capabilities

Just type the number or name of what you'd like to do, or say "done" when you're finished!"""
        
        await say(message)
    
    async def _handle_user_choice(self, user_id: str, text: str, say):
        """Handle user's choice from the main menu"""
        text_lower = text.lower()
        
        if "1" in text or "epic" in text_lower or "create" in text_lower:
            # Check if user mentions documents, HLD, PRD, or wants advanced creation
            if any(word in text_lower for word in ['document', 'hld', 'prd', 'file', 'confluence', 'meeting']):
                self.conversation_states[user_id] = {"step": "document_epic_creation", "substep": "awaiting_documents"}
                await say("""📄 **Let's create epics from your documents!**

I can analyze various sources to create comprehensive epics:

**Supported document types:**
• **Confluence links** - Share URLs to HLDs, technical specs, or design docs
• **PRD documents** - Paste your Product Requirements Documents
• **Meeting notes** - Share notes from planning or design meetings
• **Other documents** - Any relevant project documentation

**How to proceed:**
1. Share your documents (paste content or provide links)
2. I'll analyze them and create epic proposals in markdown
3. You can review and approve/reject the proposals

Please share your documents now, or type "simple" for the basic epic creation flow.""")
            else:
                # Regular epic creation flow
                self.conversation_states[user_id] = {"step": "epic_creation", "substep": "awaiting_details"}
                await say("""🚀 **Let's create an epic!**

Please provide the epic details in this format:

```
Title: Your Epic Title
Description: Detailed description of the epic
Features: feature1, feature2, feature3 (optional)
Priority: High/Medium/Low (optional)
Labels: label1, label2 (optional)
```

**Example:**
```
Title: User Authentication System
Description: Implement a comprehensive user authentication system with login, registration, and password reset functionality
Features: user registration, login/logout, password reset, two-factor authentication
Priority: High
Labels: security, authentication
```

Or say "done" if you've changed your mind.""")
        
        elif "2" in text or "process" in text_lower or "meeting" in text_lower:
            self.conversation_states[user_id] = {"step": "meeting_processing", "substep": "awaiting_space"}
            await say("""📝 **Let's process your meeting notes!**

I need to know which Confluence space to use. Please provide the space key.

**Example:** `PROJ` or `DEV`

Or say "done" if you've changed your mind.""")
        
        elif "3" in text or "search" in text_lower:
            self.conversation_states[user_id] = {"step": "meeting_search", "substep": "awaiting_keyword"}
            await say("""🔍 **Let's search for specific meetings!**

Please provide a search keyword to find meetings.

**Examples:**
- `sprint`
- `project review`
- `standup`

You can also specify additional options:
- `sprint space=PROJ days=14`

Or say "done" if you've changed your mind.""")
        
        elif "4" in text or "help" in text_lower:
            await say(self._get_detailed_help_message())
            # Keep them in awaiting_choice state
        
        else:
            await say("""I didn't understand that choice. Please select:

1️⃣ **Create Epic**
2️⃣ **Process Meetings** 
3️⃣ **Search Meetings**
4️⃣ **Help**

Or say "done" to finish.""")
    
    async def _handle_epic_creation_flow(self, user_id: str, text: str, say):
        """Handle epic creation conversation flow"""
        state = self.conversation_states[user_id]
        
        if state.get("substep") == "awaiting_details":
            # Parse the epic request
            epic_data = self._parse_epic_request(text)
            if not epic_data:
                await say("""❌ **Invalid format.** Please provide epic details in this format:

```
Title: Your Epic Title
Description: Detailed description of the epic
Features: feature1, feature2, feature3 (optional)
Priority: High/Medium/Low (optional)
```

Or say "done" to go back to the main menu.""")
                return
            
            # Store epic data and confirm
            state["epic_data"] = epic_data
            state["substep"] = "confirming"
            
            await say(f"""✅ **Epic details received!**

**Title:** {epic_data.get('title')}
**Description:** {epic_data.get('description')}
**Features:** {', '.join(epic_data.get('preferred_features', [])) if epic_data.get('preferred_features') else 'Will be generated automatically'}
**Priority:** {epic_data.get('priority', 'Medium')}

Type "confirm" to create this epic, "edit" to modify, or "done" to cancel.""")
        
        elif state.get("substep") == "confirming":
            if "confirm" in text.lower():
                await say("🚀 **Creating your epic...** This may take a moment while I generate features and user stories.")
                # Reset conversation state
                self.conversation_states[user_id] = {"step": "awaiting_choice"}
                # Return epic data for processing (this would need to be handled by the calling code)
                return state.get("epic_data")
            elif "edit" in text.lower():
                state["substep"] = "awaiting_details"
                await say("📝 **Please provide the updated epic details:**")
            else:
                await say('Please type "confirm" to create the epic, "edit" to modify it, or "done" to cancel.')
    
    async def _handle_meeting_processing_flow(self, user_id: str, text: str, say):
        """Handle meeting processing conversation flow"""
        state = self.conversation_states[user_id]
        
        if state.get("substep") == "awaiting_space":
            space_key = text.strip().upper()
            if len(space_key) < 2 or len(space_key) > 10:
                await say("❌ **Invalid space key.** Please provide a valid Confluence space key (2-10 characters).")
                return
            
            state["space_key"] = space_key
            state["substep"] = "confirming"
            
            await say(f"""✅ **Space key received: {space_key}**

I'll process recent meeting notes and create Confluence pages in this space.

Type "confirm" to start processing, or "done" to cancel.""")
        
        elif state.get("substep") == "confirming":
            if "confirm" in text.lower():
                await say("🔍 **Processing meeting notes...** This may take a few moments.")
                # Reset conversation state
                self.conversation_states[user_id] = {"step": "awaiting_choice"}
                # Return space key for processing
                return {"action": "process_meetings", "space_key": state.get("space_key")}
            else:
                await say('Please type "confirm" to start processing, or "done" to cancel.')
    
    async def _handle_meeting_search_flow(self, user_id: str, text: str, say):
        """Handle meeting search conversation flow"""
        state = self.conversation_states[user_id]
        
        if state.get("substep") == "awaiting_keyword":
            keyword = text.strip()
            if not keyword:
                await say("❌ **Invalid keyword.** Please provide a valid search keyword.")
                return
            
            state["keyword"] = keyword
            state["substep"] = "confirming"
            
            await say(f"""✅ **Search keyword received: {keyword}**

I'll search for meetings related to this keyword.

Type "confirm" to start searching, or "done" to cancel.""")
        
        elif state.get("substep") == "confirming":
            if "confirm" in text.lower():
                await say("🔍 **Searching for meetings...** This may take a few moments.")
                # Reset conversation state
                self.conversation_states[user_id] = {"step": "awaiting_choice"}
                # Return keyword for processing
                return {"action": "search_meetings", "keyword": state.get("keyword")}
            else:
                await say('Please type "confirm" to start searching, or "done" to cancel.')
    
    async def _end_conversation(self, user_id: str, say):
        """End the conversation with the user"""
        if user_id in self.conversation_states:
            del self.conversation_states[user_id]
        
        await say("👋 **Have a good day!**")
    
    def _get_detailed_help_message(self) -> str:
        """Get detailed help message"""
        return """🤖 **Project Management Bot - Detailed Help**

**What I can do:**

🚀 **Epic Creation**
- Create comprehensive epics in Jira
- Generate user stories automatically using AI
- Link stories to epics with proper metadata
- Support for features, priorities, and labels

📝 **Meeting Processing**
- Process recent Google Meet notes
- Extract action items and decisions
- Create structured Confluence pages
- Professional formatting with summaries

🔍 **Meeting Search**
- Find specific meetings by keyword
- Process historical meeting content
- Flexible date range and space options

**Available Commands:**
- Direct message me or mention me in channels
- Use `/create-epic` for quick epic creation
- Use `/process-meetings space=KEY` for batch processing
- Use `/search-meetings keyword` for targeted search

**Tips:**
- I work best with clear, structured input
- You can always say "done" to end our conversation
- I'll guide you through each process step by step

Ready to get started? Just tell me what you'd like to do!"""
    
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
    
    async def _get_bot_user_id(self):
        """Get bot user ID"""
        if not self.bot_user_id:
            try:
                auth_response = await self.app.client.auth_test()
                self.bot_user_id = auth_response['user_id']
            except Exception as e:
                logger.error(f"Error getting bot user ID: {str(e)}")
        return self.bot_user_id 

    async def _handle_document_epic_flow(self, user_id: str, text: str, say):
        """Handle document-based epic creation flow"""
        state = self.conversation_states[user_id]
        
        if state.get("substep") == "awaiting_documents":
            if text.lower() == "simple":
                # Switch to simple epic creation
                self.conversation_states[user_id] = {"step": "epic_creation", "substep": "awaiting_details"}
                await say("Switching to simple epic creation flow...")
                await self._handle_epic_creation_flow(user_id, "", say)
                return
            
            # Collect documents from user input
            documents = {
                'confluence_links': [],
                'prd_documents': [],
                'meeting_notes': [],
                'attachments': []
            }
            
            # Parse Confluence links
            import re
            confluence_pattern = r'https?://[^\s]+(?:confluence|wiki)[^\s]*'
            confluence_links = re.findall(confluence_pattern, text)
            if confluence_links:
                documents['confluence_links'] = confluence_links
            
            # Check if the text contains substantial content (likely a document)
            if len(text) > 200 and not confluence_links:
                # Determine document type based on content
                if any(keyword in text.lower() for keyword in ['requirement', 'prd', 'product']):
                    documents['prd_documents'] = [text]
                elif any(keyword in text.lower() for keyword in ['meeting', 'notes', 'discussion']):
                    documents['meeting_notes'] = [text]
                else:
                    documents['attachments'] = [text]
            
            # Store collected documents
            if not hasattr(state, 'documents'):
                state['documents'] = documents
            else:
                # Merge with existing documents
                for key in documents:
                    if key not in state['documents']:
                        state['documents'][key] = []
                    state['documents'][key].extend(documents[key])
            
            # Check if we have any documents
            total_docs = sum(len(docs) for docs in state['documents'].values())
            
            if total_docs == 0:
                await say("""❓ **No documents detected.**

Please share:
• Confluence links (e.g., https://your-company.atlassian.net/wiki/...)
• Document content (paste PRDs, specs, or meeting notes)
• Or type "done" to proceed with what you've shared
• Type "cancel" to stop""")
                return
            
            # Show what we've collected
            summary = "📚 **Documents collected:**\n"
            if state['documents']['confluence_links']:
                summary += f"• {len(state['documents']['confluence_links'])} Confluence pages\n"
            if state['documents']['prd_documents']:
                summary += f"• {len(state['documents']['prd_documents'])} PRD documents\n"
            if state['documents']['meeting_notes']:
                summary += f"• {len(state['documents']['meeting_notes'])} meeting notes\n"
            if state['documents']['attachments']:
                summary += f"• {len(state['documents']['attachments'])} other documents\n"
            
            summary += "\n**Options:**\n"
            summary += "• Share more documents\n"
            summary += "• Type 'analyze' to process these documents\n"
            summary += "• Type 'cancel' to stop"
            
            await say(summary)
            state['substep'] = 'confirming_documents'
        
        elif state.get("substep") == "confirming_documents":
            if text.lower() == 'analyze':
                # Process documents through ProjectManager
                await say("🔄 **Processing documents...**")
                # This will be handled by the enhanced handler in ProjectManager
                return state['documents']
            elif text.lower() == 'cancel':
                await say("❌ **Document analysis cancelled.**")
                await self._start_conversation(user_id, say)
            else:
                # Continue collecting documents
                state['substep'] = 'awaiting_documents'
                await self._handle_document_epic_flow(user_id, text, say)
    
    async def _handle_epic_approval(self, user_id: str, text: str, say):
        """Handle epic proposal approval/rejection"""
        # This will be handled by the ProjectManager's approval handler
        return {'action': 'epic_approval', 'response': text}
    
    async def _handle_epic_feedback(self, user_id: str, text: str, say):
        """Handle feedback for rejected epic proposals"""
        if text.strip():
            # Store feedback and trigger regeneration
            state = self.conversation_states[user_id]
            state['feedback'] = text
            
            await say("📝 **Feedback received!**\n\nRegenerating epic proposals based on your input...")
            
            # This will be handled by the enhanced handler in ProjectManager
            return {'action': 'regenerate_epics', 'feedback': text}
        else:
            await say("Please provide specific feedback about what you'd like to change.") 