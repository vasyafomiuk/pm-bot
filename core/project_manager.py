import logging
import asyncio
from typing import List, Optional, Dict, Any
from config import settings
from models import Epic, EpicRequest, EpicResponse, UserStory
from services import OpenAIService, JiraService, SlackService, GoogleMeetService

logger = logging.getLogger(__name__)


class ProjectManager:
    """Main project management orchestrator"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.jira_service = JiraService()
        self.slack_service = SlackService()
        self.google_meet_service = GoogleMeetService()
        
        # Setup Slack handlers
        self._setup_slack_handlers()
    
    def _setup_slack_handlers(self):
        """Setup custom Slack handlers"""
        
        @self.slack_service.app.command("/create-epic")
        async def handle_create_epic(ack, body, say):
            """Handle epic creation from Slack command"""
            await ack()
            
            try:
                text = body.get('text', '').strip()
                channel = body['channel_id']
                user_id = body['user_id']
                
                if not text:
                    await say(self.slack_service._get_epic_help_message())
                    return
                
                # Parse epic request
                epic_data = self.slack_service._parse_epic_request(text)
                if not epic_data:
                    await say("Invalid format. " + self.slack_service._get_epic_help_message())
                    return
                
                # Create EpicRequest object
                epic_request = EpicRequest(**epic_data)
                
                # Send initial response
                await say(f"🚀 Creating epic: **{epic_request.title}**\n" +
                         "Please wait while I generate features and user stories...")
                
                # Process epic creation in background
                asyncio.create_task(
                    self._process_epic_creation(epic_request, channel, user_id)
                )
                
            except Exception as e:
                logger.error(f"Error in create epic handler: {str(e)}")
                await say("Sorry, I encountered an error processing your request. Please try again.")
        
        @self.slack_service.app.command("/process-meetings")
        async def handle_process_meetings(ack, body, say):
            """Handle meeting notes processing from Slack command"""
            await ack()
            
            try:
                text = body.get('text', '').strip()
                channel = body['channel_id']
                user_id = body['user_id']
                
                # Parse arguments
                args = text.split() if text else []
                confluence_space = None
                
                if args and args[0].startswith('space='):
                    confluence_space = args[0].split('=')[1]
                
                if not confluence_space:
                    # Get available spaces
                    spaces = await self.get_confluence_spaces()
                    if spaces:
                        space_list = '\n'.join([f"• {space.get('key', '')} - {space.get('name', '')}" for space in spaces[:10]])
                        await say(f"Please specify a Confluence space. Available spaces:\n{space_list}\n\nUsage: `/process-meetings space=SPACE_KEY`")
                    else:
                        await say("Please specify a Confluence space key.\nUsage: `/process-meetings space=SPACE_KEY`")
                    return
                
                # Send initial response
                await say(f"🔍 Processing recent meeting notes to Confluence space: **{confluence_space}**\n" +
                         "This may take a few moments...")
                
                # Process meetings in background
                asyncio.create_task(
                    self._process_meetings_command(confluence_space, channel, user_id)
                )
                
            except Exception as e:
                logger.error(f"Error in process meetings handler: {str(e)}")
                await say("Sorry, I encountered an error processing your request. Please try again.")
        
        @self.slack_service.app.command("/search-meetings")
        async def handle_search_meetings(ack, body, say):
            """Handle meeting search and processing from Slack command"""
            await ack()
            
            try:
                text = body.get('text', '').strip()
                channel = body['channel_id']
                user_id = body['user_id']
                
                if not text:
                    await say("Please provide a search keyword.\nUsage: `/search-meetings keyword [space=SPACE_KEY] [days=30]`")
                    return
                
                # Parse arguments
                args = text.split()
                keyword = args[0]
                confluence_space = None
                days_back = 30
                
                for arg in args[1:]:
                    if arg.startswith('space='):
                        confluence_space = arg.split('=')[1]
                    elif arg.startswith('days='):
                        try:
                            days_back = int(arg.split('=')[1])
                        except ValueError:
                            pass
                
                # Send initial response
                await say(f"🔍 Searching for meetings with keyword: **{keyword}**\n" +
                         f"Looking back {days_back} days...")
                
                # Process meetings in background
                asyncio.create_task(
                    self._search_meetings_command(keyword, confluence_space, days_back, channel, user_id)
                )
                
            except Exception as e:
                logger.error(f"Error in search meetings handler: {str(e)}")
                await say("Sorry, I encountered an error processing your request. Please try again.")
        
        # Override the conversational message handlers to integrate with ProjectManager
        original_handle_epic_creation = self.slack_service._handle_epic_creation_flow
        original_handle_meeting_processing = self.slack_service._handle_meeting_processing_flow
        original_handle_meeting_search = self.slack_service._handle_meeting_search_flow
        original_handle_document_epic = self.slack_service._handle_document_epic_flow
        original_handle_epic_approval = self.slack_service._handle_epic_approval
        original_handle_epic_feedback = self.slack_service._handle_epic_feedback
        
        async def enhanced_handle_epic_creation(user_id: str, text: str, say):
            """Enhanced epic creation handler that integrates with ProjectManager"""
            result = await original_handle_epic_creation(user_id, text, say)
            
            # If epic data was confirmed, process it
            if result and isinstance(result, dict):
                try:
                    epic_request = EpicRequest(**result)
                    # Get channel from user DM
                    user_info = await self.slack_service.app.client.conversations_open(users=user_id)
                    channel = user_info['channel']['id']
                    
                    # Process epic creation in background
                    asyncio.create_task(
                        self._process_epic_creation(epic_request, channel, user_id)
                    )
                except Exception as e:
                    logger.error(f"Error processing conversational epic creation: {str(e)}")
                    await say("Sorry, I encountered an error creating your epic. Please try again.")
        
        async def enhanced_handle_document_epic(user_id: str, text: str, say):
            """Enhanced document-based epic handler"""
            result = await original_handle_document_epic(user_id, text, say)
            
            # If documents were collected for analysis
            if result and isinstance(result, dict) and any(result.values()):
                try:
                    # Get channel from user DM
                    user_info = await self.slack_service.app.client.conversations_open(users=user_id)
                    channel = user_info['channel']['id']
                    
                    # Process documents in background
                    asyncio.create_task(
                        self.process_epic_creation_from_documents(user_id, channel, result)
                    )
                except Exception as e:
                    logger.error(f"Error processing document-based epic creation: {str(e)}")
                    await say("Sorry, I encountered an error processing your documents. Please try again.")
        
        async def enhanced_handle_epic_approval(user_id: str, text: str, say):
            """Enhanced epic approval handler"""
            result = await original_handle_epic_approval(user_id, text, say)
            
            if result and result.get('action') == 'epic_approval':
                try:
                    # Get channel from user DM
                    user_info = await self.slack_service.app.client.conversations_open(users=user_id)
                    channel = user_info['channel']['id']
                    
                    # Handle approval response
                    await self.handle_epic_approval_response(user_id, result['response'], channel)
                except Exception as e:
                    logger.error(f"Error handling epic approval: {str(e)}")
                    await say("Sorry, I encountered an error processing your response.")
        
        async def enhanced_handle_epic_feedback(user_id: str, text: str, say):
            """Enhanced epic feedback handler"""
            result = await original_handle_epic_feedback(user_id, text, say)
            
            if result and result.get('action') == 'regenerate_epics':
                try:
                    # Get channel from user DM
                    user_info = await self.slack_service.app.client.conversations_open(users=user_id)
                    channel = user_info['channel']['id']
                    
                    # Get stored proposals and regenerate with feedback
                    if hasattr(self.slack_service, 'epic_proposals') and user_id in self.slack_service.epic_proposals:
                        proposal_data = self.slack_service.epic_proposals[user_id]
                        
                        # Regenerate epics with feedback
                        await self.regenerate_epics_with_feedback(
                            user_id, 
                            channel, 
                            proposal_data['proposals'], 
                            result['feedback']
                        )
                except Exception as e:
                    logger.error(f"Error handling epic feedback: {str(e)}")
                    await say("Sorry, I encountered an error processing your feedback.")
        
        async def enhanced_handle_meeting_processing(user_id: str, text: str, say):
            """Enhanced meeting processing handler that integrates with ProjectManager"""
            result = await original_handle_meeting_processing(user_id, text, say)
            
            # If meeting processing was confirmed, process it
            if result and isinstance(result, dict) and result.get("action") == "process_meetings":
                try:
                    space_key = result.get("space_key")
                    # Get channel from user DM
                    user_info = await self.slack_service.app.client.conversations_open(users=user_id)
                    channel = user_info['channel']['id']
                    
                    # Process meetings in background
                    asyncio.create_task(
                        self._process_meetings_command_conversational(space_key, channel, user_id)
                    )
                except Exception as e:
                    logger.error(f"Error processing conversational meeting processing: {str(e)}")
                    await say("Sorry, I encountered an error processing meetings. Please try again.")
        
        async def enhanced_handle_meeting_search(user_id: str, text: str, say):
            """Enhanced meeting search handler that integrates with ProjectManager"""
            result = await original_handle_meeting_search(user_id, text, say)
            
            # If meeting search was confirmed, process it
            if result and isinstance(result, dict) and result.get("action") == "search_meetings":
                try:
                    keyword = result.get("keyword")
                    # Get channel from user DM
                    user_info = await self.slack_service.app.client.conversations_open(users=user_id)
                    channel = user_info['channel']['id']
                    
                    # Process meeting search in background
                    asyncio.create_task(
                        self._search_meetings_command_conversational(keyword, None, 30, channel, user_id)
                    )
                except Exception as e:
                    logger.error(f"Error processing conversational meeting search: {str(e)}")
                    await say("Sorry, I encountered an error searching meetings. Please try again.")
        
        # Replace the original handlers
        self.slack_service._handle_epic_creation_flow = enhanced_handle_epic_creation
        self.slack_service._handle_document_epic_flow = enhanced_handle_document_epic
        self.slack_service._handle_epic_approval = enhanced_handle_epic_approval
        self.slack_service._handle_epic_feedback = enhanced_handle_epic_feedback
        self.slack_service._handle_meeting_processing_flow = enhanced_handle_meeting_processing
        self.slack_service._handle_meeting_search_flow = enhanced_handle_meeting_search
    
    async def _process_epic_creation(self, epic_request: EpicRequest, channel: str, user_id: str):
        """
        Process epic creation workflow
        
        Args:
            epic_request: Epic creation request
            channel: Slack channel ID
            user_id: User ID who made the request
        """
        try:
            # Step 1: Generate features if not provided
            if not epic_request.preferred_features:
                await self.slack_service.send_message(
                    channel, "🧠 Generating features using AI..."
                )
                
                features = await self.openai_service.generate_features(
                    epic_request.title,
                    epic_request.description,
                    f"Project: {settings.jira_project_key}"
                )
                
                if not features:
                    await self.slack_service.send_message(
                        channel, "❌ Failed to generate features. Please try again."
                    )
                    # Return to main menu
                    async def say_func(msg):
                        await self.slack_service.send_message(channel, msg)
                    await self.slack_service._start_conversation(user_id, say_func)
                    return
                
                epic_request.preferred_features = features
                await self.slack_service.send_message(
                    channel, f"✅ Generated {len(features)} features"
                )
            
            # Step 2: Create epic in Jira
            await self.slack_service.send_message(
                channel, "📝 Creating epic in Jira..."
            )
            
            epic = await self.jira_service.create_epic(epic_request)
            
            # Step 3: Generate user stories
            await self.slack_service.send_message(
                channel, "📋 Generating user stories..."
            )
            
            user_stories = await self.openai_service.generate_user_stories(
                epic.description,
                epic_request.preferred_features,
                f"Project: {settings.jira_project_key}"
            )
            
            # Step 4: Create user stories in Jira
            created_stories = []
            if user_stories:
                await self.slack_service.send_message(
                    channel, f"🔗 Creating {len(user_stories)} user stories in Jira..."
                )
                
                for story in user_stories:
                    try:
                        created_story = await self.jira_service.create_user_story(story, epic.key)
                        created_stories.append(created_story)
                    except Exception as e:
                        logger.error(f"Error creating user story: {str(e)}")
                        # Continue with other stories
            
            # Step 5: Send success response
            epic_response = EpicResponse(
                success=True,
                epic=epic,
                message="Epic and user stories created successfully!",
                user_stories_count=len(created_stories)
            )
            
            await self.slack_service.send_epic_response(channel, epic_response)
            
            # Step 6: Send user stories summary
            if created_stories:
                await self.slack_service.send_user_stories_summary(
                    channel, epic.key, created_stories
                )
            
            # Step 7: Return to main conversation menu
            await self.slack_service.send_message(
                channel, "\n" + "="*50 + "\n"
            )
            async def say_func(msg):
                await self.slack_service.send_message(channel, msg)
            await self.slack_service._start_conversation(user_id, say_func)
            
            logger.info(f"Successfully created epic {epic.key} with {len(created_stories)} user stories")
            
        except Exception as e:
            logger.error(f"Error in conversational epic creation workflow: {str(e)}")
            
            await self.slack_service.send_message(
                channel, f"❌ **Error creating epic:** {str(e)}"
            )
            
            # Return to main menu
            async def say_func(msg):
                await self.slack_service.send_message(channel, msg)
            await self.slack_service._start_conversation(user_id, say_func)
    
    async def _process_meetings_command(self, confluence_space: str, channel: str, user_id: str):
        """Background processing for meetings command"""
        try:
            result = await self.process_meeting_notes_to_confluence(
                confluence_space=confluence_space
            )
            
            if result.get("success"):
                results = result.get("results", [])
                successful = [r for r in results if r.get("success")]
                failed = [r for r in results if not r.get("success")]
                
                message = f"✅ **Meeting Notes Processing Complete**\n\n"
                message += f"📊 **Summary**: {len(successful)} successful, {len(failed)} failed\n\n"
                
                if successful:
                    message += "**Successfully processed meetings:**\n"
                    for r in successful[:5]:  # Limit to first 5
                        page_url = r.get("confluence_page", {}).get("url", "N/A")
                        message += f"• {r['meeting_title']} ({r['meeting_date']}) - [View Page]({page_url})\n"
                    
                    if len(successful) > 5:
                        message += f"• ... and {len(successful) - 5} more\n"
                
                if failed:
                    message += "\n**Failed to process:**\n"
                    for r in failed[:3]:  # Limit to first 3
                        message += f"• {r['meeting_title']} - {r.get('error', 'Unknown error')}\n"
                
                await self.slack_service.send_message(channel, message)
            else:
                error_msg = result.get("error", "Unknown error")
                await self.slack_service.send_message(
                    channel, 
                    f"❌ Failed to process meetings: {error_msg}"
                )
                
        except Exception as e:
            logger.error(f"Error in meetings command processing: {str(e)}")
            await self.slack_service.send_message(
                channel,
                f"❌ Error processing meetings: {str(e)}"
            )
    
    async def _search_meetings_command(self, keyword: str, confluence_space: str, 
                                     days_back: int, channel: str, user_id: str):
        """Background processing for search meetings command"""
        try:
            result = await self.search_and_process_meetings(
                keyword=keyword,
                confluence_space=confluence_space,
                days_back=days_back
            )
            
            if result.get("success"):
                found_meetings = result.get("found_meetings", 0)
                results = result.get("results", [])
                successful = [r for r in results if r.get("success")]
                
                message = f"✅ **Meeting Search Complete**\n\n"
                message += f"🔍 **Keyword**: {keyword}\n"
                message += f"📊 **Found**: {found_meetings} meetings, processed {len(successful)}\n\n"
                
                if successful:
                    message += "**Processed meetings:**\n"
                    for r in successful[:5]:  # Limit to first 5
                        if confluence_space:
                            page_url = r.get("confluence_page", {}).get("url", "N/A")
                            message += f"• {r['meeting_title']} - [View Page]({page_url})\n"
                        else:
                            message += f"• {r['meeting_title']} - Content generated\n"
                    
                    if len(successful) > 5:
                        message += f"• ... and {len(successful) - 5} more\n"
                
                if not confluence_space:
                    message += "\n💡 Add `space=SPACE_KEY` to publish to Confluence"
                
                await self.slack_service.send_message(channel, message)
            else:
                error_msg = result.get("error", "Unknown error")
                await self.slack_service.send_message(
                    channel, 
                    f"❌ Search failed: {error_msg}"
                )
                
        except Exception as e:
            logger.error(f"Error in search meetings command processing: {str(e)}")
            await self.slack_service.send_message(
                channel,
                f"❌ Error searching meetings: {str(e)}"
            )
    
    async def create_epic_with_stories(
        self,
        epic_request: EpicRequest,
        generate_features: bool = True
    ) -> EpicResponse:
        """
        Main workflow for creating epic with user stories
        
        Args:
            epic_request: Epic creation request
            generate_features: Whether to generate features if not provided
            
        Returns:
            Epic creation response
        """
        try:
            # Generate features if needed
            features = epic_request.preferred_features
            if not features and generate_features:
                features = await self.openai_service.generate_features(
                    epic_request.title,
                    epic_request.description,
                    f"Project: {settings.jira_project_key}"
                )
                epic_request.preferred_features = features
            
            # Create epic
            epic = await self.jira_service.create_epic(epic_request)
            
            # Generate and create user stories
            user_stories = []
            if features:
                generated_stories = await self.openai_service.generate_user_stories(
                    epic.description,
                    features,
                    f"Project: {settings.jira_project_key}"
                )
                
                for story in generated_stories:
                    try:
                        created_story = await self.jira_service.create_user_story(story, epic.key)
                        user_stories.append(created_story)
                    except Exception as e:
                        logger.error(f"Error creating user story: {str(e)}")
            
            return EpicResponse(
                success=True,
                epic=epic,
                message="Epic and user stories created successfully!",
                user_stories_count=len(user_stories)
            )
            
        except Exception as e:
            logger.error(f"Error in create_epic_with_stories: {str(e)}")
            return EpicResponse(
                success=False,
                epic=None,
                message=f"Failed to create epic: {str(e)}"
            )
    
    async def get_epic_status(self, epic_key: str) -> Optional[Epic]:
        """Get epic status and details"""
        try:
            return await self.jira_service.get_epic(epic_key)
        except Exception as e:
            logger.error(f"Error getting epic status: {str(e)}")
            return None
    
    async def get_epic_stories(self, epic_key: str) -> List[UserStory]:
        """Get all user stories for an epic"""
        try:
            return await self.jira_service.get_epic_stories(epic_key)
        except Exception as e:
            logger.error(f"Error getting epic stories: {str(e)}")
            return []
    
    def start_slack_bot(self):
        """Start the Slack bot"""
        try:
            logger.info("Starting Project Management Slack Bot...")
            self.slack_service.start_socket_mode()
        except Exception as e:
            logger.error(f"Error starting Slack bot: {str(e)}")
            raise
    
    def stop_slack_bot(self):
        """Stop the Slack bot"""
        self.slack_service.stop()
    
    async def process_meeting_notes_to_confluence(self, meeting_id: str = None, 
                                                confluence_space: str = None) -> Dict[str, Any]:
        """
        Main workflow for processing meeting notes and creating Confluence pages
        
        Args:
            meeting_id: Specific meeting ID to process (optional)
            confluence_space: Confluence space key to create page in
            
        Returns:
            Processing result with page information
        """
        try:
            # Step 1: Get recent meetings if no specific meeting ID provided
            if meeting_id:
                # Get specific meeting (would need implementation for specific meeting retrieval)
                meetings = await self.google_meet_service.get_recent_meetings(days_back=30)
                meeting = next((m for m in meetings if m.meeting_id == meeting_id), None)
                if not meeting:
                    return {
                        "success": False,
                        "error": f"Meeting with ID {meeting_id} not found"
                    }
                meetings = [meeting]
            else:
                # Get recent meetings
                meetings = await self.google_meet_service.get_recent_meetings()
            
            if not meetings:
                return {
                    "success": False,
                    "error": "No meetings found"
                }
            
            results = []
            
            # Process each meeting
            for meeting in meetings:
                try:
                    # Step 2: Process meeting notes with AI
                    processed_notes = await self.openai_service.process_meeting_notes(
                        meeting_title=meeting.title,
                        meeting_date=meeting.date.strftime("%Y-%m-%d %H:%M"),
                        attendees=meeting.attendees,
                        raw_notes=meeting.notes,
                        transcript=meeting.transcript
                    )
                    
                    # Step 3: Create Confluence content
                    confluence_content = await self.openai_service.create_confluence_content_from_meeting(
                        processed_notes=processed_notes,
                        meeting_date=meeting.date.strftime("%Y-%m-%d"),
                        attendees=meeting.attendees
                    )
                    
                    # Step 4: Create Confluence page
                    if confluence_space:
                        page_data = await self.jira_service.create_confluence_page(
                            space_key=confluence_space,
                            title=processed_notes.get("title", meeting.title),
                            content=confluence_content,
                            labels=processed_notes.get("tags", ["meeting", "automated"])
                        )
                        
                        results.append({
                            "meeting_title": meeting.title,
                            "meeting_date": meeting.date.strftime("%Y-%m-%d"),
                            "confluence_page": page_data,
                            "processed_notes": processed_notes,
                            "success": True
                        })
                    else:
                        results.append({
                            "meeting_title": meeting.title,
                            "meeting_date": meeting.date.strftime("%Y-%m-%d"),
                            "confluence_content": confluence_content,
                            "processed_notes": processed_notes,
                            "success": True,
                            "note": "No Confluence space specified - content generated but not published"
                        })
                
                except Exception as e:
                    logger.error(f"Error processing meeting {meeting.title}: {str(e)}")
                    results.append({
                        "meeting_title": meeting.title,
                        "meeting_date": meeting.date.strftime("%Y-%m-%d"),
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "processed_meetings": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in meeting notes to Confluence workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_and_process_meetings(self, keyword: str, confluence_space: str = None, 
                                        days_back: int = 30) -> Dict[str, Any]:
        """
        Search for meetings by keyword and process them to Confluence
        
        Args:
            keyword: Search keyword for meeting titles/content
            confluence_space: Confluence space key
            days_back: Number of days to search back
            
        Returns:
            Processing result
        """
        try:
            # Search for meetings
            meetings = await self.google_meet_service.search_meetings_by_keyword(
                keyword=keyword,
                days_back=days_back
            )
            
            if not meetings:
                return {
                    "success": False,
                    "error": f"No meetings found matching '{keyword}'"
                }
            
            results = []
            
            # Process found meetings
            for meeting in meetings:
                try:
                    processed_notes = await self.openai_service.process_meeting_notes(
                        meeting_title=meeting.title,
                        meeting_date=meeting.date.strftime("%Y-%m-%d %H:%M"),
                        attendees=meeting.attendees,
                        raw_notes=meeting.notes,
                        transcript=meeting.transcript
                    )
                    
                    confluence_content = await self.openai_service.create_confluence_content_from_meeting(
                        processed_notes=processed_notes,
                        meeting_date=meeting.date.strftime("%Y-%m-%d"),
                        attendees=meeting.attendees
                    )
                    
                    if confluence_space:
                        page_data = await self.jira_service.create_confluence_page(
                            space_key=confluence_space,
                            title=f"{processed_notes.get('title', meeting.title)} - {keyword}",
                            content=confluence_content,
                            labels=processed_notes.get("tags", ["meeting", keyword, "automated"])
                        )
                        
                        results.append({
                            "meeting_title": meeting.title,
                            "confluence_page": page_data,
                            "success": True
                        })
                    else:
                        results.append({
                            "meeting_title": meeting.title,
                            "confluence_content": confluence_content,
                            "success": True
                        })
                
                except Exception as e:
                    logger.error(f"Error processing meeting {meeting.title}: {str(e)}")
                    results.append({
                        "meeting_title": meeting.title,
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "keyword": keyword,
                "found_meetings": len(meetings),
                "processed_meetings": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in search and process meetings workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_confluence_spaces(self) -> List[Dict[str, Any]]:
        """Get available Confluence spaces"""
        try:
            return await self.jira_service.get_confluence_spaces()
        except Exception as e:
            logger.error(f"Error getting Confluence spaces: {str(e)}")
            return []
    
    async def validate_services(self) -> Dict[str, bool]:
        """
        Validate all service connections
        
        Returns:
            Dictionary with service validation status
        """
        validation_results = {}
        
        try:
            # Validate Atlassian MCP connection
            validation_results['mcp_atlassian'] = await self.jira_service.validate_connection()
        except Exception as e:
            logger.error(f"Atlassian MCP validation error: {str(e)}")
            validation_results['mcp_atlassian'] = False
        
        try:
            # Validate AI service (agents)
            if settings.use_azure_openai:
                validation_results['ai_service'] = bool(
                    settings.azure_openai_endpoint and 
                    settings.azure_openai_api_key and 
                    settings.azure_openai_deployment
                )
            else:
                validation_results['ai_service'] = bool(settings.openai_api_key)
            
            # Additional check for agent status
            if validation_results['ai_service']:
                try:
                    agent_status = await self.openai_service.get_agent_status()
                    validation_results['agents'] = 'error' not in agent_status
                except Exception:
                    validation_results['agents'] = False
            else:
                validation_results['agents'] = False
                
        except Exception as e:
            logger.error(f"AI service validation error: {str(e)}")
            validation_results['ai_service'] = False
            validation_results['agents'] = False
        
        try:
            # Validate Slack (simple check)
            validation_results['slack'] = bool(
                settings.slack_bot_token and 
                settings.slack_signing_secret
            )
        except Exception as e:
            logger.error(f"Slack validation error: {str(e)}")
            validation_results['slack'] = False
        
        try:
            # Validate Google Meet service
            validation_results['google_meet'] = self.google_meet_service.validate_connection()
        except Exception as e:
            logger.error(f"Google Meet validation error: {str(e)}")
            validation_results['google_meet'] = False
        
        return validation_results 

    async def _process_meetings_command_conversational(self, confluence_space: str, channel: str, user_id: str):
        """Background processing for meetings command in conversational flow"""
        try:
            result = await self.process_meeting_notes_to_confluence(
                confluence_space=confluence_space
            )
            
            if result.get("success"):
                results = result.get("results", [])
                successful = [r for r in results if r.get("success")]
                failed = [r for r in results if not r.get("success")]
                
                message = f"✅ **Meeting Notes Processing Complete**\n\n"
                message += f"📊 **Summary**: {len(successful)} successful, {len(failed)} failed\n\n"
                
                if successful:
                    message += "**Successfully processed meetings:**\n"
                    for r in successful[:5]:  # Limit to first 5
                        page_url = r.get("confluence_page", {}).get("url", "N/A")
                        message += f"• {r['meeting_title']} ({r['meeting_date']}) - [View Page]({page_url})\n"
                    
                    if len(successful) > 5:
                        message += f"• ... and {len(successful) - 5} more\n"
                
                if failed:
                    message += "\n**Failed to process:**\n"
                    for r in failed[:3]:  # Limit to first 3
                        message += f"• {r['meeting_title']} - {r.get('error', 'Unknown error')}\n"
                
                await self.slack_service.send_message(channel, message)
            else:
                error_msg = result.get("error", "Unknown error")
                await self.slack_service.send_message(
                    channel, 
                    f"❌ Failed to process meetings: {error_msg}"
                )
            
            # Return to main conversation menu
            await self.slack_service.send_message(
                channel, "\n" + "="*50 + "\n"
            )
            async def say_func(msg):
                await self.slack_service.send_message(channel, msg)
            await self.slack_service._start_conversation(user_id, say_func)
                
        except Exception as e:
            logger.error(f"Error in conversational meetings command processing: {str(e)}")
            await self.slack_service.send_message(
                channel,
                f"❌ Error processing meetings: {str(e)}"
            )
            
            # Return to main menu
            async def say_func(msg):
                await self.slack_service.send_message(channel, msg)
            await self.slack_service._start_conversation(user_id, say_func)
    
    async def _search_meetings_command_conversational(self, keyword: str, confluence_space: str, 
                                                    days_back: int, channel: str, user_id: str):
        """Background processing for search meetings command in conversational flow"""
        try:
            result = await self.search_and_process_meetings(
                keyword=keyword,
                confluence_space=confluence_space,
                days_back=days_back
            )
            
            if result.get("success"):
                found_meetings = result.get("found_meetings", 0)
                results = result.get("results", [])
                successful = [r for r in results if r.get("success")]
                
                message = f"✅ **Meeting Search Complete**\n\n"
                message += f"🔍 **Keyword**: {keyword}\n"
                message += f"📊 **Found**: {found_meetings} meetings, processed {len(successful)}\n\n"
                
                if successful:
                    message += "**Processed meetings:**\n"
                    for r in successful[:5]:  # Limit to first 5
                        if confluence_space:
                            page_url = r.get("confluence_page", {}).get("url", "N/A")
                            message += f"• {r['meeting_title']} - [View Page]({page_url})\n"
                        else:
                            message += f"• {r['meeting_title']} - Content generated\n"
                    
                    if len(successful) > 5:
                        message += f"• ... and {len(successful) - 5} more\n"
                
                if not confluence_space:
                    message += "\n💡 Note: Content was generated but not published to Confluence"
                
                await self.slack_service.send_message(channel, message)
            else:
                error_msg = result.get("error", "Unknown error")
                await self.slack_service.send_message(
                    channel, 
                    f"❌ Search failed: {error_msg}"
                )
            
            # Return to main conversation menu
            await self.slack_service.send_message(
                channel, "\n" + "="*50 + "\n"
            )
            async def say_func(msg):
                await self.slack_service.send_message(channel, msg)
            await self.slack_service._start_conversation(user_id, say_func)
                
        except Exception as e:
            logger.error(f"Error in conversational search meetings command processing: {str(e)}")
            await self.slack_service.send_message(
                channel,
                f"❌ Error searching meetings: {str(e)}"
            )
            
            # Return to main menu
            async def say_func(msg):
                await self.slack_service.send_message(channel, msg)
            await self.slack_service._start_conversation(user_id, say_func)
    
    async def process_epic_creation_from_documents(
        self, 
        user_id: str,
        channel: str,
        documents: Dict[str, Any],
        context: str = None
    ) -> Dict[str, Any]:
        """
        Process epic creation workflow from various document sources
        Following the workflow: User provides documents → AI analyzes → Creates markdown → User approves/rejects
        
        Args:
            user_id: User ID initiating the request
            channel: Slack channel ID
            documents: Dictionary containing document references:
                - confluence_links: List of Confluence page URLs
                - prd_documents: List of PRD document contents
                - meeting_notes: List of meeting notes
                - attachments: Other attached documents
            context: Additional context from user
            
        Returns:
            Workflow result with status and created epics
        """
        try:
            # Step 1: Acknowledge receipt and analyze documents
            await self.slack_service.send_message(
                channel,
                "📚 **Analyzing your documents...**\n" +
                "I'll review the provided HLDs, PRDs, and meeting notes to create comprehensive epics."
            )
            
            # Step 2: Gather content from various sources
            all_content = []
            
            # Process Confluence links
            if documents.get('confluence_links'):
                for link in documents['confluence_links']:
                    try:
                        # Extract page content from Confluence
                        page_content = await self._extract_confluence_content(link)
                        if page_content:
                            all_content.append({
                                'type': 'confluence',
                                'source': link,
                                'content': page_content
                            })
                    except Exception as e:
                        logger.error(f"Error extracting Confluence content from {link}: {str(e)}")
            
            # Process PRD documents
            if documents.get('prd_documents'):
                for prd in documents['prd_documents']:
                    all_content.append({
                        'type': 'prd',
                        'source': 'PRD Document',
                        'content': prd
                    })
            
            # Process meeting notes
            if documents.get('meeting_notes'):
                for notes in documents['meeting_notes']:
                    all_content.append({
                        'type': 'meeting_notes',
                        'source': 'Meeting Notes',
                        'content': notes
                    })
            
            # Step 3: Analyze content and generate epic proposals
            await self.slack_service.send_message(
                channel,
                "🤖 **AI Analysis in progress...**\n" +
                "Extracting key requirements and generating epic proposals..."
            )
            
            epic_proposals = await self._analyze_documents_for_epics(all_content, context)
            
            if not epic_proposals:
                await self.slack_service.send_message(
                    channel,
                    "❌ Unable to generate epic proposals from the provided documents. " +
                    "Please ensure the documents contain sufficient project information."
                )
                return {'success': False, 'error': 'No epics could be generated'}
            
            # Step 4: Generate markdown with epic proposals
            markdown_content = self._generate_epic_markdown(epic_proposals)
            
            # Step 5: Send markdown for approval
            await self.slack_service.send_message(
                channel,
                "📝 **Epic Proposals Generated**\n\n" +
                "Here's the markdown with proposed epics based on your documents:\n\n" +
                "```markdown\n" +
                markdown_content +
                "\n```\n\n" +
                "**Please review and respond:**\n" +
                "• Type `approve` to create these epics in Jira\n" +
                "• Type `reject` to provide feedback and regenerate\n" +
                "• Type `cancel` to stop the process"
            )
            
            # Store the proposals in conversation state for approval flow
            if not hasattr(self.slack_service, 'epic_proposals'):
                self.slack_service.epic_proposals = {}
            
            self.slack_service.epic_proposals[user_id] = {
                'proposals': epic_proposals,
                'markdown': markdown_content,
                'channel': channel,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            # Set conversation state to await approval
            self.slack_service.conversation_states[user_id] = {
                'step': 'awaiting_epic_approval',
                'proposals': epic_proposals
            }
            
            return {
                'success': True,
                'status': 'awaiting_approval',
                'proposals': epic_proposals,
                'markdown': markdown_content
            }
            
        except Exception as e:
            logger.error(f"Error in document-based epic creation workflow: {str(e)}")
            await self.slack_service.send_message(
                channel,
                f"❌ **Error processing documents:** {str(e)}"
            )
            return {'success': False, 'error': str(e)}
    
    async def _extract_confluence_content(self, confluence_url: str) -> Optional[str]:
        """Extract content from a Confluence page URL"""
        try:
            # Parse the URL to get page ID or title
            # This is a simplified implementation - real implementation would parse the URL properly
            import re
            
            # Try to extract page ID from URL patterns like /pages/12345/
            page_id_match = re.search(r'/pages/(\d+)/', confluence_url)
            if page_id_match:
                page_id = page_id_match.group(1)
                # Get page content using the Confluence API
                # Note: This would need proper implementation based on actual Confluence API
                logger.info(f"Extracting content from Confluence page ID: {page_id}")
                # For now, return placeholder
                return f"[Confluence content from page {page_id}]"
            
            # Try to extract space and title
            space_title_match = re.search(r'/wiki/spaces/([^/]+)/pages/[^/]+/([^/?]+)', confluence_url)
            if space_title_match:
                space = space_title_match.group(1)
                title = space_title_match.group(2).replace('+', ' ')
                logger.info(f"Extracting content from Confluence page: {space}/{title}")
                # For now, return placeholder
                return f"[Confluence content from {space}/{title}]"
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting Confluence content: {str(e)}")
            return None
    
    async def _analyze_documents_for_epics(
        self, 
        documents: List[Dict[str, Any]], 
        context: str = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze documents using AI to generate epic proposals
        
        Args:
            documents: List of document contents with type and source
            context: Additional context from user
            
        Returns:
            List of epic proposals
        """
        try:
            # Combine all document contents
            combined_content = "\n\n---\n\n".join([
                f"[{doc['type'].upper()} - {doc['source']}]\n{doc['content']}"
                for doc in documents
            ])
            
            # Add context if provided
            if context:
                combined_content = f"User Context: {context}\n\n{combined_content}"
            
            # Call AI service to analyze and generate epics
            epic_proposals = await self.openai_service.analyze_documents_for_epics(
                combined_content,
                project_context=f"Project: {settings.jira_project_key}"
            )
            
            return epic_proposals
            
        except Exception as e:
            logger.error(f"Error analyzing documents for epics: {str(e)}")
            return []
    
    def _generate_epic_markdown(self, epic_proposals: List[Dict[str, Any]]) -> str:
        """Generate markdown representation of epic proposals"""
        markdown = "# Epic Proposals\n\n"
        
        for i, epic in enumerate(epic_proposals, 1):
            markdown += f"## Epic {i}: {epic.get('title', 'Untitled Epic')}\n\n"
            markdown += f"**Description:**\n{epic.get('description', 'No description')}\n\n"
            
            if epic.get('features'):
                markdown += "**Features:**\n"
                for feature in epic['features']:
                    markdown += f"- {feature}\n"
                markdown += "\n"
            
            if epic.get('acceptance_criteria'):
                markdown += "**Acceptance Criteria:**\n"
                for criteria in epic['acceptance_criteria']:
                    markdown += f"- {criteria}\n"
                markdown += "\n"
            
            if epic.get('priority'):
                markdown += f"**Priority:** {epic['priority']}\n\n"
            
            if epic.get('labels'):
                markdown += f"**Labels:** {', '.join(epic['labels'])}\n\n"
            
            markdown += "---\n\n"
        
        return markdown
    
    async def handle_epic_approval_response(
        self, 
        user_id: str, 
        response: str, 
        channel: str
    ) -> Dict[str, Any]:
        """
        Handle user's response to epic proposals (approve/reject/cancel)
        
        Args:
            user_id: User ID
            response: User's response (approve/reject/cancel)
            channel: Slack channel ID
            
        Returns:
            Result of the action
        """
        try:
            # Get stored proposals
            if not hasattr(self.slack_service, 'epic_proposals') or user_id not in self.slack_service.epic_proposals:
                await self.slack_service.send_message(
                    channel,
                    "❌ No pending epic proposals found. Please start a new epic creation process."
                )
                return {'success': False, 'error': 'No pending proposals'}
            
            proposal_data = self.slack_service.epic_proposals[user_id]
            epic_proposals = proposal_data['proposals']
            
            if response.lower() == 'approve':
                # Create epics in Jira
                await self.slack_service.send_message(
                    channel,
                    "✅ **Approval received!**\n" +
                    "Creating epics and user stories in Jira..."
                )
                
                created_epics = []
                failed_epics = []
                
                for epic_data in epic_proposals:
                    try:
                        # Create epic request
                        epic_request = EpicRequest(
                            title=epic_data['title'],
                            description=epic_data['description'],
                            preferred_features=epic_data.get('features', []),
                            priority=epic_data.get('priority', 'Medium'),
                            labels=epic_data.get('labels', [])
                        )
                        
                        # Create epic and stories
                        epic_response = await self.create_epic_with_stories(epic_request)
                        
                        if epic_response.success:
                            created_epics.append(epic_response.epic)
                        else:
                            failed_epics.append({
                                'title': epic_data['title'],
                                'error': epic_response.message
                            })
                    
                    except Exception as e:
                        logger.error(f"Error creating epic {epic_data['title']}: {str(e)}")
                        failed_epics.append({
                            'title': epic_data['title'],
                            'error': str(e)
                        })
                
                # Send summary
                summary = "📊 **Epic Creation Summary**\n\n"
                
                if created_epics:
                    summary += f"✅ **Successfully created {len(created_epics)} epics:**\n"
                    for epic in created_epics:
                        summary += f"• {epic.title} - [{epic.key}]({settings.jira_server}/browse/{epic.key})\n"
                
                if failed_epics:
                    summary += f"\n❌ **Failed to create {len(failed_epics)} epics:**\n"
                    for failed in failed_epics:
                        summary += f"• {failed['title']} - {failed['error']}\n"
                
                await self.slack_service.send_message(channel, summary)
                
                # Clean up stored proposals
                del self.slack_service.epic_proposals[user_id]
                
                return {
                    'success': True,
                    'created': len(created_epics),
                    'failed': len(failed_epics)
                }
                
            elif response.lower() == 'reject':
                # Handle rejection - ask for feedback
                await self.slack_service.send_message(
                    channel,
                    "📝 **Please provide feedback:**\n" +
                    "What would you like to change about these epic proposals?\n" +
                    "I'll regenerate them based on your feedback."
                )
                
                # Update conversation state to collect feedback
                self.slack_service.conversation_states[user_id] = {
                    'step': 'collecting_epic_feedback',
                    'proposals': epic_proposals
                }
                
                return {'success': True, 'status': 'collecting_feedback'}
                
            elif response.lower() == 'cancel':
                # Cancel the process
                await self.slack_service.send_message(
                    channel,
                    "❌ **Epic creation cancelled.**\n" +
                    "The proposals have been discarded."
                )
                
                # Clean up
                del self.slack_service.epic_proposals[user_id]
                if user_id in self.slack_service.conversation_states:
                    del self.slack_service.conversation_states[user_id]
                
                return {'success': True, 'status': 'cancelled'}
                
            else:
                await self.slack_service.send_message(
                    channel,
                    "❓ **Invalid response.**\n" +
                    "Please type `approve`, `reject`, or `cancel`."
                )
                return {'success': False, 'error': 'Invalid response'}
                
        except Exception as e:
            logger.error(f"Error handling epic approval response: {str(e)}")
            await self.slack_service.send_message(
                channel,
                f"❌ **Error:** {str(e)}"
            )
            return {'success': False, 'error': str(e)}
    
    async def regenerate_epics_with_feedback(
        self, 
        user_id: str, 
        channel: str,
        original_proposals: List[Dict[str, Any]],
        feedback: str
    ) -> Dict[str, Any]:
        """
        Regenerate epic proposals based on user feedback
        
        Args:
            user_id: User ID
            channel: Slack channel ID
            original_proposals: Original epic proposals
            feedback: User's feedback for improvements
            
        Returns:
            Result of regeneration
        """
        try:
            await self.slack_service.send_message(
                channel,
                "🔄 **Regenerating epic proposals based on your feedback...**"
            )
            
            # Prepare context with original proposals and feedback
            context = f"User Feedback: {feedback}\n\n"
            context += "Original Proposals:\n"
            context += self._generate_epic_markdown(original_proposals)
            
            # Call AI to regenerate epics with feedback
            updated_proposals = await self.openai_service.regenerate_epics_with_feedback(
                original_proposals,
                feedback,
                project_context=f"Project: {settings.jira_project_key}"
            )
            
            if not updated_proposals:
                await self.slack_service.send_message(
                    channel,
                    "❌ Unable to regenerate epic proposals. Please try providing more specific feedback."
                )
                return {'success': False, 'error': 'Regeneration failed'}
            
            # Generate new markdown
            markdown_content = self._generate_epic_markdown(updated_proposals)
            
            # Send updated proposals for approval
            await self.slack_service.send_message(
                channel,
                "📝 **Updated Epic Proposals**\n\n" +
                "I've revised the epics based on your feedback:\n\n" +
                "```markdown\n" +
                markdown_content +
                "\n```\n\n" +
                "**Please review and respond:**\n" +
                "• Type `approve` to create these epics in Jira\n" +
                "• Type `reject` to provide more feedback\n" +
                "• Type `cancel` to stop the process"
            )
            
            # Update stored proposals
            self.slack_service.epic_proposals[user_id] = {
                'proposals': updated_proposals,
                'markdown': markdown_content,
                'channel': channel,
                'timestamp': asyncio.get_event_loop().time()
            }
            
            # Reset conversation state to await approval
            self.slack_service.conversation_states[user_id] = {
                'step': 'awaiting_epic_approval',
                'proposals': updated_proposals
            }
            
            return {
                'success': True,
                'status': 'awaiting_approval',
                'proposals': updated_proposals
            }
            
        except Exception as e:
            logger.error(f"Error regenerating epics with feedback: {str(e)}")
            await self.slack_service.send_message(
                channel,
                f"❌ **Error regenerating proposals:** {str(e)}"
            )
            return {'success': False, 'error': str(e)} 