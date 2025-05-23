from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class AcceptanceCriteria(BaseModel):
    """Model for acceptance criteria"""
    criterion: str = Field(..., description="Acceptance criterion description")
    priority: Optional[str] = Field(default="Should", description="Priority (Must, Should, Could, Won't)")


class UserStory(BaseModel):
    """Model representing a Jira User Story"""
    key: Optional[str] = Field(default=None, description="Jira user story key")
    id: Optional[str] = Field(default=None, description="Jira user story ID")
    title: str = Field(..., description="User story title")
    description: str = Field(..., description="User story description")
    epic_key: Optional[str] = Field(default=None, description="Parent epic key")
    status: Optional[str] = Field(default="To Do", description="User story status")
    priority: str = Field(default="Medium", description="User story priority")
    assignee: Optional[str] = Field(default=None, description="User story assignee")
    story_points: Optional[int] = Field(default=None, description="Story points estimate")
    acceptance_criteria: Optional[List[AcceptanceCriteria]] = Field(
        default=None, 
        description="Acceptance criteria list"
    )
    labels: Optional[List[str]] = Field(default=None, description="User story labels")
    created_date: Optional[datetime] = Field(default=None, description="Creation date")
    updated_date: Optional[datetime] = Field(default=None, description="Last update date")


class UserStoryGeneration(BaseModel):
    """Model for user story generation request"""
    epic_description: str = Field(..., description="Epic description to generate stories from")
    features: List[str] = Field(..., description="Features to create stories for")
    project_context: Optional[str] = Field(
        default=None, 
        description="Additional project context"
    )


class UserStoryResponse(BaseModel):
    """Model for user story creation response"""
    success: bool = Field(..., description="Whether the operation was successful")
    user_stories: List[UserStory] = Field(default=[], description="Created user stories")
    message: str = Field(..., description="Response message")
    total_created: int = Field(default=0, description="Total number of stories created") 