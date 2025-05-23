from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class EpicRequest(BaseModel):
    """Model for epic creation request from user"""
    title: str = Field(..., description="Title of the epic")
    description: str = Field(..., description="Description of the epic")
    preferred_features: Optional[List[str]] = Field(
        default=None, 
        description="Optional list of preferred features"
    )
    priority: Optional[str] = Field(
        default="Medium", 
        description="Priority level (Low, Medium, High, Critical)"
    )
    labels: Optional[List[str]] = Field(
        default=None,
        description="Optional labels for the epic"
    )


class Epic(BaseModel):
    """Model representing a Jira Epic"""
    key: Optional[str] = Field(default=None, description="Jira epic key")
    id: Optional[str] = Field(default=None, description="Jira epic ID")
    title: str = Field(..., description="Epic title")
    description: str = Field(..., description="Epic description")
    status: Optional[str] = Field(default="To Do", description="Epic status")
    priority: str = Field(default="Medium", description="Epic priority")
    assignee: Optional[str] = Field(default=None, description="Epic assignee")
    created_date: Optional[datetime] = Field(default=None, description="Creation date")
    updated_date: Optional[datetime] = Field(default=None, description="Last update date")
    labels: Optional[List[str]] = Field(default=None, description="Epic labels")
    features: Optional[List[str]] = Field(default=None, description="Generated features")


class EpicResponse(BaseModel):
    """Model for epic creation response"""
    success: bool = Field(..., description="Whether the operation was successful")
    epic: Optional[Epic] = Field(default=None, description="Created epic details")
    message: str = Field(..., description="Response message")
    user_stories_count: Optional[int] = Field(
        default=None, 
        description="Number of user stories created"
    ) 