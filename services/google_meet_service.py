import logging
import pickle
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from config import settings

logger = logging.getLogger(__name__)


class MeetingNote:
    """Data model for meeting notes"""
    
    def __init__(self, 
                 title: str,
                 date: datetime,
                 attendees: List[str],
                 description: str = "",
                 notes: str = "",
                 recording_url: str = "",
                 transcript: str = "",
                 meeting_id: str = "",
                 duration_minutes: int = 0):
        self.title = title
        self.date = date
        self.attendees = attendees
        self.description = description
        self.notes = notes
        self.recording_url = recording_url
        self.transcript = transcript
        self.meeting_id = meeting_id
        self.duration_minutes = duration_minutes


class GoogleMeetService:
    """Service for fetching Google Meet notes and recordings"""
    
    def __init__(self):
        self.credentials = None
        self.calendar_service = None
        self.drive_service = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Google API services"""
        try:
            self.credentials = self._get_credentials()
            if self.credentials:
                self.calendar_service = build('calendar', 'v3', credentials=self.credentials)
                self.drive_service = build('drive', 'v3', credentials=self.credentials)
                logger.info("Successfully initialized Google services")
            else:
                logger.warning("Google credentials not available")
                
        except Exception as e:
            logger.error(f"Failed to initialize Google services: {str(e)}")
    
    def _get_credentials(self) -> Optional[Credentials]:
        """Get Google API credentials"""
        creds = None
        
        # Load existing token
        if os.path.exists(settings.google_token_file):
            with open(settings.google_token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {str(e)}")
                    creds = None
            
            if not creds and settings.google_credentials_file:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        settings.google_credentials_file, 
                        settings.google_scopes
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"Failed to get new credentials: {str(e)}")
                    return None
        
        # Save the credentials for the next run
        if creds:
            try:
                with open(settings.google_token_file, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                logger.error(f"Failed to save credentials: {str(e)}")
        
        return creds
    
    async def get_recent_meetings(self, days_back: int = None) -> List[MeetingNote]:
        """
        Get recent Google Meet meetings from Calendar
        
        Args:
            days_back: Number of days to look back (default from settings)
            
        Returns:
            List of meeting notes
        """
        if not self.calendar_service:
            logger.error("Calendar service not initialized")
            return []
        
        try:
            days_back = days_back or settings.google_meeting_lookback_days
            
            # Calculate time range
            now = datetime.utcnow()
            time_min = now - timedelta(days=days_back)
            
            # Get calendar events
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=time_min.isoformat() + 'Z',
                timeMax=now.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime',
                q='meet.google.com OR zoom.us OR teams.microsoft.com'  # Filter for video meetings
            ).execute()
            
            events = events_result.get('items', [])
            
            meeting_notes = []
            for event in events:
                meeting_note = await self._process_calendar_event(event)
                if meeting_note:
                    meeting_notes.append(meeting_note)
            
            logger.info(f"Found {len(meeting_notes)} meetings in the last {days_back} days")
            return meeting_notes
            
        except Exception as e:
            logger.error(f"Error fetching recent meetings: {str(e)}")
            return []
    
    async def _process_calendar_event(self, event: Dict[str, Any]) -> Optional[MeetingNote]:
        """Process a calendar event and extract meeting information"""
        try:
            # Extract basic information
            title = event.get('summary', 'Untitled Meeting')
            description = event.get('description', '')
            
            # Parse start time
            start = event.get('start', {})
            if 'dateTime' in start:
                start_time = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
            else:
                # All-day event, skip
                return None
            
            # Calculate duration
            end = event.get('end', {})
            duration_minutes = 0
            if 'dateTime' in end:
                end_time = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
                duration_minutes = int((end_time - start_time).total_seconds() / 60)
            
            # Extract attendees
            attendees = []
            for attendee in event.get('attendees', []):
                email = attendee.get('email', '')
                name = attendee.get('displayName', email)
                if name:
                    attendees.append(name)
            
            # Look for meeting links and recordings
            meeting_url = ""
            recording_url = ""
            
            if description:
                # Extract Google Meet links
                import re
                meet_pattern = r'https://meet\.google\.com/[a-z-]+'
                meet_match = re.search(meet_pattern, description)
                if meet_match:
                    meeting_url = meet_match.group()
            
            # Check for attachments (recordings, notes)
            notes_content = ""
            transcript_content = ""
            
            attachments = event.get('attachments', [])
            for attachment in attachments:
                file_id = attachment.get('fileId')
                if file_id:
                    file_content = await self._get_drive_file_content(file_id)
                    if file_content:
                        if 'transcript' in attachment.get('title', '').lower():
                            transcript_content = file_content
                        else:
                            notes_content += file_content + "\n"
            
            # Create meeting note object
            meeting_note = MeetingNote(
                title=title,
                date=start_time,
                attendees=attendees,
                description=description,
                notes=notes_content,
                recording_url=recording_url,
                transcript=transcript_content,
                meeting_id=event.get('id', ''),
                duration_minutes=duration_minutes
            )
            
            return meeting_note
            
        except Exception as e:
            logger.error(f"Error processing calendar event: {str(e)}")
            return None
    
    async def _get_drive_file_content(self, file_id: str) -> str:
        """Get content from a Google Drive file"""
        if not self.drive_service:
            return ""
        
        try:
            # Get file metadata
            file_metadata = self.drive_service.files().get(fileId=file_id).execute()
            mime_type = file_metadata.get('mimeType', '')
            
            # Handle different file types
            if 'text' in mime_type or 'document' in mime_type:
                # Export as plain text
                request = self.drive_service.files().export_media(
                    fileId=file_id, 
                    mimeType='text/plain'
                )
                content = request.execute()
                return content.decode('utf-8')
            
            elif 'application/pdf' in mime_type:
                # For PDFs, we'd need additional processing
                logger.info(f"PDF file detected: {file_metadata.get('name')}")
                return f"[PDF FILE: {file_metadata.get('name')}]"
            
            else:
                logger.info(f"Unsupported file type: {mime_type}")
                return f"[FILE: {file_metadata.get('name')} - {mime_type}]"
                
        except Exception as e:
            logger.error(f"Error getting Drive file content: {str(e)}")
            return ""
    
    async def search_meetings_by_keyword(self, keyword: str, days_back: int = 30) -> List[MeetingNote]:
        """
        Search for meetings containing specific keywords
        
        Args:
            keyword: Search keyword
            days_back: Number of days to search back
            
        Returns:
            List of matching meeting notes
        """
        if not self.calendar_service:
            logger.error("Calendar service not initialized")
            return []
        
        try:
            # Calculate time range
            now = datetime.utcnow()
            time_min = now - timedelta(days=days_back)
            
            # Search for events with keyword
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=time_min.isoformat() + 'Z',
                timeMax=now.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime',
                q=keyword
            ).execute()
            
            events = events_result.get('items', [])
            
            meeting_notes = []
            for event in events:
                meeting_note = await self._process_calendar_event(event)
                if meeting_note:
                    meeting_notes.append(meeting_note)
            
            logger.info(f"Found {len(meeting_notes)} meetings matching '{keyword}'")
            return meeting_notes
            
        except Exception as e:
            logger.error(f"Error searching meetings: {str(e)}")
            return []
    
    def validate_connection(self) -> bool:
        """Validate Google API connection"""
        try:
            if not self.calendar_service:
                return False
            
            # Test API call
            self.calendar_service.calendarList().list().execute()
            logger.info("Google Meet service connection validated")
            return True
            
        except Exception as e:
            logger.error(f"Google Meet service validation failed: {str(e)}")
            return False 