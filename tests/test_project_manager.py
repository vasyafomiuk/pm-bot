#!/usr/bin/env python3
"""
Basic tests for the Project Management Bot
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch
from models import EpicRequest, Epic, UserStory
from core import ProjectManager
from services import OpenAIService, JiraService, SlackService, GoogleMeetService
from services.google_meet_service import MeetingNote


class TestProjectManager:
    """Test cases for ProjectManager class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.pm = ProjectManager()
    
    def test_initialization(self):
        """Test ProjectManager initialization"""
        assert self.pm.openai_service is not None
        assert self.pm.jira_service is not None
        assert self.pm.slack_service is not None
    
    @pytest.mark.asyncio
    async def test_epic_creation_with_features(self):
        """Test epic creation with predefined features"""
        # Mock the services
        with patch.object(self.pm.jira_service, 'create_epic') as mock_create_epic, \
             patch.object(self.pm.openai_service, 'generate_user_stories') as mock_gen_stories, \
             patch.object(self.pm.jira_service, 'create_user_story') as mock_create_story:
            
            # Setup mocks
            mock_epic = Epic(
                key="TEST-123",
                title="Test Epic",
                description="Test Description",
                priority="High"
            )
            mock_create_epic.return_value = mock_epic
            
            mock_stories = [
                UserStory(
                    title="Test Story 1",
                    description="As a user, I want test functionality",
                    story_points=3
                )
            ]
            mock_gen_stories.return_value = mock_stories
            mock_create_story.return_value = mock_stories[0]
            
            # Create epic request
            epic_request = EpicRequest(
                title="Test Epic",
                description="Test Description",
                preferred_features=["feature1", "feature2"],
                priority="High"
            )
            
            # Test epic creation
            response = await self.pm.create_epic_with_stories(epic_request, generate_features=False)
            
            # Assertions
            assert response.success is True
            assert response.epic.key == "TEST-123"
            assert response.user_stories_count == 1
            
            # Verify method calls
            mock_create_epic.assert_called_once()
            mock_gen_stories.assert_called_once()
            mock_create_story.assert_called_once()


class TestOpenAIService:
    """Test cases for AI service with agents"""
    
    def setup_method(self):
        """Setup test environment"""
        self.openai_service = OpenAIService()
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test that agents are properly initialized"""
        assert self.openai_service.feature_agent is not None
        assert self.openai_service.story_agent is not None
        assert self.openai_service.agent_system is not None
        
        assert self.openai_service.feature_agent.name == "feature_generator"
        assert self.openai_service.story_agent.name == "story_generator"
    
    @pytest.mark.asyncio
    async def test_agent_status(self):
        """Test agent status reporting"""
        status = await self.openai_service.get_agent_status()
        
        assert "feature_agent" in status
        assert "story_agent" in status
        assert "agent_system" in status
        
        assert status["feature_agent"]["status"] == "active"
        assert status["story_agent"]["status"] == "active"
    
    def test_feature_agent_parsing(self):
        """Test feature parsing from agent response"""
        response_text = """
        User registration functionality
        Login and logout system
        Password reset capability
        Two-factor authentication
        User profile management
        """
        
        features = self.openai_service.feature_agent._parse_features_response(response_text)
        
        assert len(features) == 5
        assert "User registration functionality" in features
        assert "Two-factor authentication" in features
    
    def test_story_agent_parsing(self):
        """Test user story parsing from agent response"""
        response_text = '''
        {
            "title": "User Registration",
            "description": "As a new user, I want to register an account so that I can access the system",
            "acceptance_criteria": [
                {"criterion": "User can enter email and password", "priority": "Must"},
                {"criterion": "Email validation is performed", "priority": "Must"},
                {"criterion": "User receives confirmation email", "priority": "Should"}
            ],
            "story_points": 5,
            "priority": "High"
        }
        '''
        
        story = self.openai_service.story_agent._parse_user_story_response(response_text, "User Registration")
        
        assert story.title == "User Registration"
        assert story.story_points == 5
        assert story.priority == "High"
        assert len(story.acceptance_criteria) == 3


class TestTextParsing:
    """Test cases for text parsing utilities"""
    
    def test_epic_text_parsing(self):
        """Test parsing epic from structured text"""
        from utils import parse_epic_from_text
        
        text = """
        Title: User Management System
        Description: Comprehensive user management with authentication and profiles
        Features: registration, login, profile management, password reset
        Priority: High
        Labels: authentication, users, security
        """
        
        epic_data = parse_epic_from_text(text)
        
        assert epic_data['title'] == "User Management System"
        assert epic_data['priority'] == "High"
        assert len(epic_data['preferred_features']) == 4
        assert len(epic_data['labels']) == 3
    
    def test_priority_normalization(self):
        """Test priority normalization"""
        from utils import normalize_priority
        
        assert normalize_priority("high") == "High"
        assert normalize_priority("CRITICAL") == "Critical"
        assert normalize_priority("med") == "Medium"
        assert normalize_priority("l") == "Low"
        assert normalize_priority("invalid") == "Medium"
    
    def test_epic_validation(self):
        """Test epic data validation"""
        from utils import validate_epic_data
        
        # Valid epic data
        valid_data = {
            'title': 'Valid Epic Title',
            'description': 'This is a valid description with sufficient length to pass validation requirements.'
        }
        errors = validate_epic_data(valid_data)
        assert len(errors) == 0
        
        # Invalid epic data
        invalid_data = {
            'title': 'Bad',  # Too short
            'description': 'Short'  # Too short
        }
        errors = validate_epic_data(invalid_data)
        assert 'title' in errors
        assert 'description' in errors


class TestSlackService:
    """Test cases for Slack service"""
    
    def setup_method(self):
        """Setup test environment"""
        self.slack_service = SlackService()
    
    def test_parse_epic_request(self):
        """Test parsing epic request from Slack text"""
        text = """
        Title: E-commerce Platform
        Description: Build a comprehensive e-commerce platform with shopping cart and payment processing
        Priority: High
        Features: product catalog, shopping cart, payment gateway, user accounts
        """
        
        epic_data = self.slack_service._parse_epic_request(text)
        
        assert epic_data is not None
        assert epic_data['title'] == "E-commerce Platform"
        assert epic_data['priority'] == "High"
        assert len(epic_data['preferred_features']) == 4
    
    def test_invalid_epic_request(self):
        """Test parsing invalid epic request"""
        text = "This is not a valid epic format"
        
        epic_data = self.slack_service._parse_epic_request(text)
        
        assert epic_data is None


class TestGoogleMeetService:
    """Test cases for Google Meet service"""
    
    def setup_method(self):
        """Setup test environment"""
        self.google_service = GoogleMeetService()
    
    def test_meeting_note_creation(self):
        """Test MeetingNote data model"""
        meeting = MeetingNote(
            title="Test Meeting",
            date=datetime.now(),
            attendees=["user1@example.com", "user2@example.com"],
            description="Test meeting description",
            notes="Meeting notes content",
            transcript="Meeting transcript content"
        )
        
        assert meeting.title == "Test Meeting"
        assert len(meeting.attendees) == 2
        assert meeting.notes == "Meeting notes content"
    
    @pytest.mark.asyncio
    async def test_process_calendar_event(self):
        """Test processing calendar event data"""
        # Mock calendar event data
        mock_event = {
            "summary": "Team Standup",
            "description": "Daily standup meeting",
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T10:30:00Z"},
            "attendees": [
                {"email": "user1@example.com", "displayName": "User One"},
                {"email": "user2@example.com", "displayName": "User Two"}
            ],
            "id": "test-meeting-id"
        }
        
        meeting_note = await self.google_service._process_calendar_event(mock_event)
        
        assert meeting_note is not None
        assert meeting_note.title == "Team Standup"
        assert meeting_note.duration_minutes == 30
        assert len(meeting_note.attendees) == 2


class TestMeetingNotesProcessing:
    """Test cases for meeting notes processing workflow"""
    
    def setup_method(self):
        """Setup test environment"""
        self.pm = ProjectManager()
    
    @pytest.mark.asyncio
    async def test_process_meeting_notes_workflow(self):
        """Test complete meeting notes to Confluence workflow"""
        # Mock the services
        with patch.object(self.pm.google_meet_service, 'get_recent_meetings') as mock_get_meetings, \
             patch.object(self.pm.openai_service, 'process_meeting_notes') as mock_process_notes, \
             patch.object(self.pm.openai_service, 'create_confluence_content_from_meeting') as mock_create_content, \
             patch.object(self.pm.jira_service, 'create_confluence_page') as mock_create_page:
            
            # Setup mock data
            mock_meeting = MeetingNote(
                title="Sprint Planning",
                date=datetime.now(),
                attendees=["dev1@example.com", "pm@example.com"],
                description="Sprint planning meeting",
                notes="Discussed upcoming sprint goals",
                transcript="Detailed meeting transcript"
            )
            mock_get_meetings.return_value = [mock_meeting]
            
            mock_processed_notes = {
                "title": "Sprint Planning Meeting Notes",
                "summary": "Discussed sprint goals and priorities",
                "key_points": ["Sprint goal defined", "Tasks prioritized"],
                "decisions": ["Use feature flags for deployment"],
                "action_items": [
                    {"item": "Update backlog", "owner": "PM", "due_date": "Friday"}
                ],
                "next_steps": ["Start development", "Daily standups"],
                "tags": ["sprint", "planning"]
            }
            mock_process_notes.return_value = mock_processed_notes
            
            mock_confluence_content = "h1. Sprint Planning Meeting Notes\n\nMeeting content here..."
            mock_create_content.return_value = mock_confluence_content
            
            mock_page_data = {
                "id": "123456",
                "title": "Sprint Planning Meeting Notes",
                "url": "https://company.atlassian.net/wiki/spaces/PROJ/pages/123456"
            }
            mock_create_page.return_value = mock_page_data
            
            # Test the workflow
            result = await self.pm.process_meeting_notes_to_confluence(
                confluence_space="PROJ"
            )
            
            # Assertions
            assert result["success"] is True
            assert result["processed_meetings"] == 1
            assert len(result["results"]) == 1
            
            result_item = result["results"][0]
            assert result_item["success"] is True
            assert result_item["meeting_title"] == "Sprint Planning"
            assert "confluence_page" in result_item
            
            # Verify method calls
            mock_get_meetings.assert_called_once()
            mock_process_notes.assert_called_once()
            mock_create_content.assert_called_once()
            mock_create_page.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_meetings_workflow(self):
        """Test search and process meetings workflow"""
        with patch.object(self.pm.google_meet_service, 'search_meetings_by_keyword') as mock_search, \
             patch.object(self.pm.openai_service, 'process_meeting_notes') as mock_process, \
             patch.object(self.pm.openai_service, 'create_confluence_content_from_meeting') as mock_content:
            
            # Setup mock data
            mock_meeting = MeetingNote(
                title="Retrospective Meeting",
                date=datetime.now(),
                attendees=["team@example.com"],
                notes="Team retrospective notes"
            )
            mock_search.return_value = [mock_meeting]
            
            mock_processed = {
                "title": "Retrospective Notes",
                "summary": "Team retrospective summary"
            }
            mock_process.return_value = mock_processed
            mock_content.return_value = "Confluence content"
            
            # Test search workflow
            result = await self.pm.search_and_process_meetings(
                keyword="retrospective",
                days_back=14
            )
            
            # Assertions
            assert result["success"] is True
            assert result["keyword"] == "retrospective"
            assert result["found_meetings"] == 1
            
            # Verify search was called with correct parameters
            mock_search.assert_called_once_with(
                keyword="retrospective",
                days_back=14
            )


class TestConfluenceIntegration:
    """Test cases for Confluence integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.jira_service = JiraService()
    
    @pytest.mark.asyncio
    async def test_confluence_page_creation(self):
        """Test Confluence page creation via MCP"""
        with patch.object(self.jira_service, '_call_mcp_tool') as mock_mcp_call:
            
            # Setup mock response
            mock_response = {
                "content": [{
                    "text": "Page ID: 123456\nURL: https://company.atlassian.net/wiki/spaces/PROJ/pages/123456\nTitle: Test Page"
                }]
            }
            mock_mcp_call.return_value = mock_response
            
            # Test page creation
            page_data = await self.jira_service.create_confluence_page(
                space_key="PROJ",
                title="Test Meeting Notes",
                content="h1. Meeting Notes\n\nContent here...",
                labels=["meeting", "automated"]
            )
            
            # Assertions
            assert page_data["id"] == "123456"
            assert "URL" in page_data or "url" in page_data
            
            # Verify MCP call
            mock_mcp_call.assert_called_once_with(
                "confluence_create_page",
                {
                    "space_key": "PROJ",
                    "title": "Test Meeting Notes",
                    "content": "h1. Meeting Notes\n\nContent here...",
                    "content_format": "wiki",
                    "labels": ["meeting", "automated"]
                }
            )


def run_tests():
    """Run all tests"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests() 