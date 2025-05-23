import logging
import json
import httpx
from typing import List, Optional, Dict, Any
from config import settings
from models import Epic, UserStory, EpicRequest

logger = logging.getLogger(__name__)


class JiraService:
    """Service for interacting with Jira through Atlassian MCP Server"""
    
    def __init__(self):
        self.mcp_base_url = settings.mcp_server_url or "http://mcp-atlassian:9000"
        self.mcp_endpoint = f"{self.mcp_base_url}/mcp"
        self.auth_headers = self._get_auth_headers()
        self._initialize_client()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for MCP requests"""
        headers = {"Content-Type": "application/json"}
        
        # Add authentication based on available credentials
        if settings.jira_api_token:
            # For Atlassian Cloud with API token
            auth_token = f"Bearer {settings.jira_api_token}"
            headers["Authorization"] = auth_token
        elif hasattr(settings, 'atlassian_oauth_token'):
            # For OAuth authentication
            headers["Authorization"] = f"Bearer {settings.atlassian_oauth_token}"
        
        return headers
    
    def _initialize_client(self):
        """Initialize MCP client"""
        try:
            self.client = httpx.AsyncClient(
                base_url=self.mcp_base_url,
                headers=self.auth_headers,
                timeout=30.0
            )
            logger.info("Successfully initialized Atlassian MCP client")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {str(e)}")
            raise
    
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool and return the result"""
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
            
            response = await self.client.post("/mcp", json=payload)
            response.raise_for_status()
            
            result = response.json()
            if "error" in result:
                raise Exception(f"MCP Error: {result['error']}")
            
            return result.get("result", {})
            
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
            raise

    async def create_epic(self, epic_request: EpicRequest) -> Epic:
        """
        Create an epic in Jira using MCP
        
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
            
            # Add epic name (required for epics)
            epic_args["epic_name"] = epic_request.title
            
            # Call MCP tool to create issue
            result = await self._call_mcp_tool("jira_create_issue", epic_args)
            
            # Extract issue information from result
            if "content" in result and isinstance(result["content"], list):
                content_text = result["content"][0].get("text", "")
                # Parse the response to extract issue key and other details
                issue_data = self._parse_issue_creation_response(content_text)
            else:
                issue_data = result
            
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
    
    def _parse_issue_creation_response(self, response_text: str) -> Dict[str, Any]:
        """Parse issue creation response from MCP"""
        try:
            # Look for issue key pattern in response
            import re
            key_match = re.search(r'\b[A-Z][A-Z0-9_]*-\d+\b', response_text)
            
            issue_data = {}
            if key_match:
                issue_data["key"] = key_match.group()
                # Extract other information if available
                if "successfully created" in response_text.lower():
                    issue_data["status"] = "To Do"
            
            return issue_data
            
        except Exception as e:
            logger.error(f"Error parsing issue creation response: {str(e)}")
            return {}
    
    async def create_user_story(self, user_story: UserStory, epic_key: str) -> UserStory:
        """
        Create a user story in Jira and link it to an epic using MCP
        
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
            
            # Extract issue information from result
            if "content" in result and isinstance(result["content"], list):
                content_text = result["content"][0].get("text", "")
                issue_data = self._parse_issue_creation_response(content_text)
            else:
                issue_data = result
            
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
        """Link a user story to an epic using MCP"""
        try:
            # Use MCP tool to link story to epic
            link_args = {
                "story_key": story_key,
                "epic_key": epic_key
            }
            
            await self._call_mcp_tool("jira_link_to_epic", link_args)
            logger.info(f"Successfully linked story {story_key} to epic {epic_key}")
            
        except Exception as e:
            logger.error(f"Error linking story to epic: {str(e)}")
            # Don't raise here as the story was created successfully
    
    async def get_epic(self, epic_key: str) -> Optional[Epic]:
        """
        Retrieve an epic from Jira using MCP
        
        Args:
            epic_key: Epic key to retrieve
            
        Returns:
            Epic object or None if not found
        """
        try:
            get_args = {"issue_key": epic_key}
            result = await self._call_mcp_tool("jira_get_issue", get_args)
            
            # Parse the result
            if "content" in result and isinstance(result["content"], list):
                content_text = result["content"][0].get("text", "")
                issue_data = self._parse_issue_response(content_text)
            else:
                issue_data = result
            
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
    
    def _parse_issue_response(self, response_text: str) -> Dict[str, Any]:
        """Parse issue response from MCP"""
        try:
            issue_data = {}
            
            # Extract key
            import re
            key_match = re.search(r'Key:\s*([A-Z][A-Z0-9_]*-\d+)', response_text)
            if key_match:
                issue_data["key"] = key_match.group(1)
            
            # Extract summary/title
            summary_match = re.search(r'Summary:\s*(.+)', response_text)
            if summary_match:
                issue_data["summary"] = summary_match.group(1).strip()
            
            # Extract status
            status_match = re.search(r'Status:\s*(.+)', response_text)
            if status_match:
                issue_data["status"] = status_match.group(1).strip()
            
            # Extract priority
            priority_match = re.search(r'Priority:\s*(.+)', response_text)
            if priority_match:
                issue_data["priority"] = priority_match.group(1).strip()
            
            # Extract description
            desc_match = re.search(r'Description:\s*(.+?)(?=\n[A-Z][a-z]+:|$)', response_text, re.DOTALL)
            if desc_match:
                issue_data["description"] = desc_match.group(1).strip()
            
            return issue_data
            
        except Exception as e:
            logger.error(f"Error parsing issue response: {str(e)}")
            return {}
    
    async def get_epic_stories(self, epic_key: str) -> List[UserStory]:
        """
        Get all user stories linked to an epic using MCP
        
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
            
            # Parse the result
            if "content" in result and isinstance(result["content"], list):
                content_text = result["content"][0].get("text", "")
                stories_data = self._parse_search_response(content_text)
            else:
                stories_data = result.get("issues", [])
            
            user_stories = []
            for story_data in stories_data:
                story = UserStory(
                    key=story_data.get("key"),
                    id=story_data.get("id"),
                    title=story_data.get("summary", ""),
                    description=story_data.get("description", ""),
                    epic_key=epic_key,
                    status=story_data.get("status", ""),
                    priority=story_data.get("priority", ""),
                    assignee=story_data.get("assignee"),
                    labels=story_data.get("labels", [])
                )
                user_stories.append(story)
            
            return user_stories
            
        except Exception as e:
            logger.error(f"Error retrieving stories for epic {epic_key}: {str(e)}")
            return []
    
    def _parse_search_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse search response from MCP"""
        try:
            stories = []
            
            # Split response by issues (assuming each issue starts with a key pattern)
            import re
            issue_blocks = re.split(r'\n(?=[A-Z][A-Z0-9_]*-\d+)', response_text)
            
            for block in issue_blocks:
                if not block.strip():
                    continue
                
                story_data = self._parse_issue_response(block)
                if story_data and story_data.get("key"):
                    stories.append(story_data)
            
            return stories
            
        except Exception as e:
            logger.error(f"Error parsing search response: {str(e)}")
            return []
    
    async def update_epic_status(self, epic_key: str, status: str) -> bool:
        """
        Update epic status using MCP
        
        Args:
            epic_key: Epic key
            status: New status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get available transitions first
            get_transitions_args = {"issue_key": epic_key}
            transitions_result = await self._call_mcp_tool("jira_get_transitions", get_transitions_args)
            
            # Try to transition the issue
            transition_args = {
                "issue_key": epic_key,
                "status": status
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
        Create a Confluence page using MCP
        
        Args:
            space_key: Confluence space key
            title: Page title
            content: Page content in Confluence format
            parent_page_id: Optional parent page ID
            labels: Optional list of labels
            
        Returns:
            Created page information
        """
        try:
            page_args = {
                "space_key": space_key,
                "title": title,
                "content": content,
                "content_format": "wiki"  # Using wiki markup format
            }
            
            if parent_page_id:
                page_args["parent_page_id"] = parent_page_id
            
            if labels:
                page_args["labels"] = labels
            
            result = await self._call_mcp_tool("confluence_create_page", page_args)
            
            # Parse the result
            if "content" in result and isinstance(result["content"], list):
                content_text = result["content"][0].get("text", "")
                page_data = self._parse_confluence_page_response(content_text)
            else:
                page_data = result
            
            logger.info(f"Successfully created Confluence page: {title}")
            return page_data
                
        except Exception as e:
            logger.error(f"Error creating Confluence page: {str(e)}")
            raise
    
    async def update_confluence_page(self, page_id: str, title: str, content: str, 
                                   version: int = None) -> Dict[str, Any]:
        """
        Update an existing Confluence page using MCP
        
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
                "content": content,
                "content_format": "wiki"
            }
            
            if version:
                update_args["version"] = version
            
            result = await self._call_mcp_tool("confluence_update_page", update_args)
            
            # Parse the result
            if "content" in result and isinstance(result["content"], list):
                content_text = result["content"][0].get("text", "")
                page_data = self._parse_confluence_page_response(content_text)
            else:
                page_data = result
            
            logger.info(f"Successfully updated Confluence page: {title}")
            return page_data
                
        except Exception as e:
            logger.error(f"Error updating Confluence page: {str(e)}")
            raise
    
    async def search_confluence_pages(self, space_key: str, query: str) -> List[Dict[str, Any]]:
        """
        Search for Confluence pages using MCP
        
        Args:
            space_key: Confluence space key
            query: Search query
            
        Returns:
            List of matching pages
        """
        try:
            search_args = {
                "space_key": space_key,
                "query": query
            }
            
            result = await self._call_mcp_tool("confluence_search", search_args)
            
            # Parse the result
            if "content" in result and isinstance(result["content"], list):
                content_text = result["content"][0].get("text", "")
                pages = self._parse_confluence_search_response(content_text)
            else:
                pages = result.get("pages", [])
            
            logger.info(f"Found {len(pages)} Confluence pages matching '{query}'")
            return pages
                
        except Exception as e:
            logger.error(f"Error searching Confluence pages: {str(e)}")
            return []
    
    async def get_confluence_spaces(self) -> List[Dict[str, Any]]:
        """
        Get available Confluence spaces using MCP
        
        Returns:
            List of available spaces
        """
        try:
            result = await self._call_mcp_tool("confluence_get_spaces", {})
            
            # Parse the result
            if "content" in result and isinstance(result["content"], list):
                content_text = result["content"][0].get("text", "")
                spaces = self._parse_confluence_spaces_response(content_text)
            else:
                spaces = result.get("spaces", [])
            
            logger.info(f"Retrieved {len(spaces)} Confluence spaces")
            return spaces
                
        except Exception as e:
            logger.error(f"Error getting Confluence spaces: {str(e)}")
            return []
    
    def _parse_confluence_page_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Confluence page response from MCP"""
        try:
            page_data = {}
            
            # Extract page ID and URL
            import re
            id_match = re.search(r'Page ID:\s*(\d+)', response_text)
            if id_match:
                page_data["id"] = id_match.group(1)
            
            url_match = re.search(r'URL:\s*(https?://[^\s]+)', response_text)
            if url_match:
                page_data["url"] = url_match.group(1)
            
            # Extract title if present
            title_match = re.search(r'Title:\s*(.+)', response_text)
            if title_match:
                page_data["title"] = title_match.group(1).strip()
            
            return page_data
            
        except Exception as e:
            logger.error(f"Error parsing Confluence page response: {str(e)}")
            return {}
    
    def _parse_confluence_search_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse Confluence search response from MCP"""
        try:
            pages = []
            
            # Split response by pages (assuming each page has an ID or title)
            import re
            page_blocks = re.split(r'\n(?=Page ID:|Title:)', response_text)
            
            for block in page_blocks:
                if not block.strip():
                    continue
                
                page_data = self._parse_confluence_page_response(block)
                if page_data and (page_data.get("id") or page_data.get("title")):
                    pages.append(page_data)
            
            return pages
            
        except Exception as e:
            logger.error(f"Error parsing Confluence search response: {str(e)}")
            return []
    
    def _parse_confluence_spaces_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse Confluence spaces response from MCP"""
        try:
            spaces = []
            
            # Extract space information
            import re
            space_blocks = re.split(r'\n(?=Space:)', response_text)
            
            for block in space_blocks:
                if not block.strip():
                    continue
                
                space_data = {}
                
                # Extract space key
                key_match = re.search(r'Key:\s*([A-Z0-9]+)', block)
                if key_match:
                    space_data["key"] = key_match.group(1)
                
                # Extract space name
                name_match = re.search(r'Name:\s*(.+)', block)
                if name_match:
                    space_data["name"] = name_match.group(1).strip()
                
                if space_data.get("key"):
                    spaces.append(space_data)
            
            return spaces
            
        except Exception as e:
            logger.error(f"Error parsing Confluence spaces response: {str(e)}")
            return []
    
    async def validate_connection(self) -> bool:
        """
        Validate MCP connection to Atlassian services
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to make a simple call to validate the connection
            test_args = {"jql": "project IS NOT EMPTY", "max_results": 1}
            await self._call_mcp_tool("jira_search", test_args)
            logger.info("Atlassian MCP connection validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Atlassian MCP connection validation failed: {str(e)}")
            return False
    
    async def close(self):
        """Close the HTTP client"""
        if hasattr(self, 'client') and self.client:
            await self.client.aclose() 