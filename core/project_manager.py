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
        
        @self.slack_service.app.event("app_mention")
        async def handle_app_mention(event, say):
            """Handle app mentions"""
            await self.slack_service.handle_mention(event, say)
    
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
                await self.slack_service.send_epic_creation_progress(
                    channel, "🧠 Generating features using AI..."
                )
                
                features = await self.openai_service.generate_features(
                    epic_request.title,
                    epic_request.description,
                    f"Project: {settings.jira_project_key}"
                )
                
                if not features:
                    await self.slack_service.send_error_message(
                        channel, "Failed to generate features. Please try again."
                    )
                    return
                
                epic_request.preferred_features = features
                await self.slack_service.send_epic_creation_progress(
                    channel, f"✅ Generated {len(features)} features"
                )
            
            # Step 2: Create epic in Jira
            await self.slack_service.send_epic_creation_progress(
                channel, "📝 Creating epic in Jira..."
            )
            
            epic = await self.jira_service.create_epic(epic_request)
            
            # Step 3: Generate user stories
            await self.slack_service.send_epic_creation_progress(
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
                await self.slack_service.send_epic_creation_progress(
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
            
            logger.info(f"Successfully created epic {epic.key} with {len(created_stories)} user stories")
            
        except Exception as e:
            logger.error(f"Error in epic creation workflow: {str(e)}")
            
            error_response = EpicResponse(
                success=False,
                epic=None,
                message=f"Failed to create epic: {str(e)}"
            )
            
            await self.slack_service.send_epic_response(channel, error_response)
    
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