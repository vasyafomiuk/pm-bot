import logging
import json
import httpx
from typing import List, Optional, Dict, Any
from config import settings
from models import Epic, UserStory, EpicRequest

logger = logging.getLogger(__name__)


class JiraService:
    """Service for interacting with Jira through MCP Atlassian Server"""
    
    def __init__(self):
        self.mcp_base_url = settings.mcp_server_url or "http://mcp-atlassian:9000"
        self.mcp_endpoint = f"{self.mcp_base_url}/mcp"
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize HTTP client for MCP communication"""
        try:
            self.client = httpx.AsyncClient(
                base_url=self.mcp_base_url,
                headers={"Content-Type": "application/json"},
                timeout=60.0
            )
            logger.info("Successfully initialized MCP Atlassian client")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {str(e)}")
            raise
    
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool via HTTP and return the result"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            logger.debug(f"Calling MCP tool {tool_name} with arguments: {arguments}")
            
            response = await self.client.post("/mcp", json=payload)
            response.raise_for_status()
            
            result = response.json()
            if "error" in result:
                error_msg = result["error"].get("message", str(result["error"]))
                raise Exception(f"MCP Error: {error_msg}")
            
            return result.get("result", {})
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling MCP tool {tool_name}: {e.response.status_code} - {e.response.text}")
            raise Exception(f"HTTP error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
            raise

    async def create_epic(self, epic_request: EpicRequest) -> Epic:
        """
        Create an epic in Jira using MCP Atlassian
        
        Args:
            epic_request: Epic creation request
            
        Returns:
            Created Epic object
        """
        try:
            # Prepare epic creation arguments for MCP
            epic_args = {
                "project_key": settings.jira_project_key,
                "summary": epic_request.title,
                "description": epic_request.description,
                "issue_type": "Epic",
                "priority": epic_request.priority or "Medium"
            }
            
            # Add labels if provided
            if epic_request.labels:
                epic_args["labels"] = epic_request.labels
            
            # Add epic name (required for epics in Jira)
            epic_args["epic_name"] = epic_request.title
            
            # Call MCP tool to create issue
            result = await self._call_mcp_tool("jira_create_issue", epic_args)
            
            # Parse the response
            issue_data = self._parse_tool_response(result)
            
            # Convert to Epic model
            epic = Epic(
                key=issue_data.get("key"),
                id=issue_data.get("id"),
                title=epic_request.title,
                description=epic_request.description,
                status=issue_data.get("status", "To Do"),
                priority=epic_request.priority or "Medium",
                labels=epic_request.labels,
                features=epic_request.preferred_features
            )
            
            logger.info(f"Successfully created epic: {epic.key}")
            return epic
            
        except Exception as e:
            logger.error(f"Error creating epic: {str(e)}")
            raise
    
    async def create_user_story(self, user_story: UserStory, epic_key: str) -> UserStory:
        """
        Create a user story in Jira and link it to an epic using MCP Atlassian
        
        Args:
            user_story: User story to create
            epic_key: Epic key to link the story to
            
        Returns:
            Created UserStory object with Jira details
        """
        try:
            # Prepare acceptance criteria description
            acceptance_criteria_text = ""
            if user_story.acceptance_criteria:
                acceptance_criteria_text = "\n\nAcceptance Criteria:\n"
                for i, criteria in enumerate(user_story.acceptance_criteria, 1):
                    acceptance_criteria_text += f"{i}. {criteria.criterion} ({criteria.priority})\n"
            
            # Prepare story creation arguments for MCP
            story_args = {
                "project_key": settings.jira_project_key,
                "summary": user_story.title,
                "description": user_story.description + acceptance_criteria_text,
                "issue_type": "Story",
                "priority": user_story.priority or "Medium"
            }
            
            # Add story points if available
            if user_story.story_points:
                story_args["story_points"] = user_story.story_points
            
            # Add labels if provided
            if user_story.labels:
                story_args["labels"] = user_story.labels
            
            # Create the user story
            result = await self._call_mcp_tool("jira_create_issue", story_args)
            
            # Parse the response
            issue_data = self._parse_tool_response(result)
            
            # Link to epic if story was created successfully
            if issue_data.get("key"):
                await self._link_story_to_epic(issue_data["key"], epic_key)
            
            # Update the user story object with Jira details
            user_story.key = issue_data.get("key")
            user_story.id = issue_data.get("id")
            user_story.epic_key = epic_key
            user_story.status = issue_data.get("status", "To Do")
            
            logger.info(f"Successfully created user story: {user_story.key}")
            return user_story
            
        except Exception as e:
            logger.error(f"Error creating user story: {str(e)}")
            raise
    
    async def _link_story_to_epic(self, story_key: str, epic_key: str):
        """Link a user story to an epic using MCP Atlassian"""
        try:
            # Use MCP tool to link story to epic
            link_args = {
                "issue_key": story_key,
                "epic_key": epic_key
            }
            
            await self._call_mcp_tool("jira_link_to_epic", link_args)
            logger.info(f"Successfully linked story {story_key} to epic {epic_key}")
            
        except Exception as e:
            logger.error(f"Error linking story to epic: {str(e)}")
            # Don't raise here as the story was created successfully
    
    async def get_epic(self, epic_key: str) -> Optional[Epic]:
        """
        Retrieve an epic from Jira using MCP Atlassian
        
        Args:
            epic_key: Epic key to retrieve
            
        Returns:
            Epic object or None if not found
        """
        try:
            get_args = {"issue_key": epic_key}
            result = await self._call_mcp_tool("jira_get_issue", get_args)
            
            # Parse the response
            issue_data = self._parse_tool_response(result)
            
            if not issue_data:
                return None
            
            epic = Epic(
                key=issue_data.get("key", epic_key),
                id=issue_data.get("id"),
                title=issue_data.get("summary", ""),
                description=issue_data.get("description", ""),
                status=issue_data.get("status", ""),
                priority=issue_data.get("priority", ""),
                assignee=issue_data.get("assignee"),
                labels=issue_data.get("labels", [])
            )
            
            return epic
            
        except Exception as e:
            logger.error(f"Error retrieving epic {epic_key}: {str(e)}")
            return None
    
    async def get_epic_stories(self, epic_key: str) -> List[UserStory]:
        """
        Get all user stories linked to an epic using MCP Atlassian
        
        Args:
            epic_key: Epic key
            
        Returns:
            List of user stories
        """
        try:
            # Search for issues linked to the epic using MCP
            search_args = {
                "jql": f'project = {settings.jira_project_key} AND "Epic Link" = {epic_key} AND issuetype = Story',
                "max_results": 100
            }
            
            result = await self._call_mcp_tool("jira_search", search_args)
            
            # Parse the response
            search_data = self._parse_tool_response(result)
            issues = search_data.get("issues", [])
            
            user_stories = []
            for issue_data in issues:
                story = UserStory(
                    key=issue_data.get("key"),
                    id=issue_data.get("id"),
                    title=issue_data.get("summary", ""),
                    description=issue_data.get("description", ""),
                    epic_key=epic_key,
                    status=issue_data.get("status", ""),
                    priority=issue_data.get("priority", ""),
                    assignee=issue_data.get("assignee"),
                    labels=issue_data.get("labels", [])
                )
                user_stories.append(story)
            
            return user_stories
            
        except Exception as e:
            logger.error(f"Error retrieving stories for epic {epic_key}: {str(e)}")
            return []
    
    async def update_epic_status(self, epic_key: str, status: str) -> bool:
        """
        Update epic status using MCP Atlassian
        
        Args:
            epic_key: Epic key
            status: New status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to transition the issue
            transition_args = {
                "issue_key": epic_key,
                "transition": status
            }
            
            await self._call_mcp_tool("jira_transition_issue", transition_args)
            logger.info(f"Successfully updated epic {epic_key} status to {status}")
            return True
                
        except Exception as e:
            logger.error(f"Error updating epic status: {str(e)}")
            return False
    
    async def create_confluence_page(self, space_key: str, title: str, content: str, 
                                   parent_page_id: str = None, labels: List[str] = None) -> Dict[str, Any]:
        """
        Create a Confluence page using MCP Atlassian
        
        Args:
            space_key: Confluence space key
            title: Page title
            content: Page content
            parent_page_id: Optional parent page ID
            labels: Optional list of labels
            
        Returns:
            Created page information
        """
        try:
            page_args = {
                "space_key": space_key,
                "title": title,
                "content": content
            }
            
            if parent_page_id:
                page_args["parent_page_id"] = parent_page_id
            
            if labels:
                page_args["labels"] = labels
            
            result = await self._call_mcp_tool("confluence_create_page", page_args)
            
            # Parse the response
            page_data = self._parse_tool_response(result)
            
            logger.info(f"Successfully created Confluence page: {title}")
            return page_data
                
        except Exception as e:
            logger.error(f"Error creating Confluence page: {str(e)}")
            raise
    
    async def update_confluence_page(self, page_id: str, title: str, content: str, 
                                   version: int = None) -> Dict[str, Any]:
        """
        Update an existing Confluence page using MCP Atlassian
        
        Args:
            page_id: Page ID to update
            title: Updated page title
            content: Updated page content
            version: Page version (if known)
            
        Returns:
            Updated page information
        """
        try:
            update_args = {
                "page_id": page_id,
                "title": title,
                "content": content
            }
            
            if version:
                update_args["version"] = version
            
            result = await self._call_mcp_tool("confluence_update_page", update_args)
            
            # Parse the response
            page_data = self._parse_tool_response(result)
            
            logger.info(f"Successfully updated Confluence page: {title}")
            return page_data
                
        except Exception as e:
            logger.error(f"Error updating Confluence page: {str(e)}")
            raise
    
    async def search_confluence_pages(self, space_key: str, query: str) -> List[Dict[str, Any]]:
        """
        Search for Confluence pages using MCP Atlassian
        
        Args:
            space_key: Confluence space key
            query: Search query
            
        Returns:
            List of matching pages
        """
        try:
            search_args = {
                "cql": f'space = "{space_key}" AND text ~ "{query}"',
                "limit": 50
            }
            
            result = await self._call_mcp_tool("confluence_search", search_args)
            
            # Parse the response
            search_data = self._parse_tool_response(result)
            pages = search_data.get("results", [])
            
            logger.info(f"Found {len(pages)} Confluence pages matching '{query}'")
            return pages
                
        except Exception as e:
            logger.error(f"Error searching Confluence pages: {str(e)}")
            return []
    
    async def get_confluence_spaces(self) -> List[Dict[str, Any]]:
        """
        Get available Confluence spaces using MCP Atlassian
        
        Returns:
            List of available spaces
        """
        try:
            # Note: This would require a specific tool for getting spaces
            # For now, return empty list as this functionality may not be available
            logger.warning("get_confluence_spaces not implemented in MCP Atlassian")
            return []
                
        except Exception as e:
            logger.error(f"Error getting Confluence spaces: {str(e)}")
            return []
    
    def _parse_tool_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse tool response from MCP Atlassian"""
        try:
            # MCP Atlassian returns responses in different formats
            # Check for content array first (common format)
            if "content" in response and isinstance(response["content"], list):
                if response["content"]:
                    content_item = response["content"][0]
                    if "text" in content_item:
                        # Try to parse as JSON if it looks like JSON
                        text = content_item["text"]
                        if text.strip().startswith(("{", "[")):
                            try:
                                return json.loads(text)
                            except json.JSONDecodeError:
                                pass
                        
                        # Parse structured text response
                        return self._parse_text_response(text)
                    
            # If direct data is available, use it
            if isinstance(response, dict) and any(key in response for key in ["key", "id", "summary", "issues"]):
                return response
            
            # Return the response as-is if we can't parse it
            return response
            
        except Exception as e:
            logger.error(f"Error parsing tool response: {str(e)}")
            return {}
    
    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """Parse text response from MCP tools"""
        try:
            data = {}
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if ':' in line and not line.startswith('http'):
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()
                    
                    # Handle common field mappings
                    if key in ['key', 'issue_key']:
                        data['key'] = value
                    elif key in ['id', 'issue_id']:
                        data['id'] = value
                    elif key in ['summary', 'title']:
                        data['summary'] = value
                    elif key in ['status']:
                        data['status'] = value
                    elif key in ['priority']:
                        data['priority'] = value
                    elif key in ['description']:
                        data['description'] = value
                    elif key in ['assignee']:
                        data['assignee'] = value
                    elif key in ['labels']:
                        data['labels'] = [label.strip() for label in value.split(',') if label.strip()]
            
            return data
            
        except Exception as e:
            logger.error(f"Error parsing text response: {str(e)}")
            return {}
    
    async def validate_connection(self) -> bool:
        """
        Validate MCP connection to Atlassian services
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to make a simple search to validate the connection
            test_args = {"jql": "project IS NOT EMPTY", "max_results": 1}
            await self._call_mcp_tool("jira_search", test_args)
            logger.info("MCP Atlassian connection validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"MCP Atlassian connection validation failed: {str(e)}")
            return False
    
    async def close(self):
        """Close the HTTP client"""
        if hasattr(self, 'client') and self.client:
            await self.client.aclose() 