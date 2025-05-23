#!/usr/bin/env python3
"""
Project Management Bot - Main Application Entry Point

A Slack bot that acts as a project manager in agile teams,
creating Jira epics and user stories using AI.
"""

import logging
import os
import sys
import signal
import asyncio
from typing import Optional

from config import settings
from core import ProjectManager


# Configure logging
def setup_logging():
    """Setup logging configuration"""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    logs_dir = "logs" if os.path.exists("/app/logs") else "."
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure log file path
    log_file = os.path.join(logs_dir, 'pm_bot.log')
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file)
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('slack_bolt').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def validate_configuration():
    """Validate required configuration"""
    required_settings = [
        ('SLACK_BOT_TOKEN', settings.slack_bot_token),
        ('SLACK_SIGNING_SECRET', settings.slack_signing_secret),
        ('SLACK_APP_TOKEN', settings.slack_app_token),
        ('OPENAI_API_KEY', settings.openai_api_key),
        ('JIRA_SERVER', settings.jira_server),
        ('JIRA_USERNAME', settings.jira_username),
        ('JIRA_API_TOKEN', settings.jira_api_token),
        ('JIRA_PROJECT_KEY', settings.jira_project_key),
    ]
    
    missing_settings = []
    for name, value in required_settings:
        if not value:
            missing_settings.append(name)
    
    if missing_settings:
        logger.error(f"Missing required configuration: {', '.join(missing_settings)}")
        logger.error("Please check your .env file or environment variables")
        return False
    
    return True


class PMBotApplication:
    """Main application class"""
    
    def __init__(self):
        self.project_manager: Optional[ProjectManager] = None
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self) -> bool:
        """Initialize the application"""
        try:
            self.logger.info("Initializing Project Management Bot...")
            
            # Validate configuration
            if not validate_configuration():
                return False
            
            # Initialize project manager
            self.project_manager = ProjectManager()
            
            # Validate services
            validation_results = await self.project_manager.validate_services()
            
            failed_services = [
                service for service, status in validation_results.items() 
                if not status
            ]
            
            if failed_services:
                self.logger.error(f"Service validation failed for: {', '.join(failed_services)}")
                return False
            
            self.logger.info("All services validated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {str(e)}")
            return False
    
    def run(self):
        """Run the application"""
        try:
            # Run async initialization
            if not asyncio.run(self.initialize()):
                self.logger.error("Application initialization failed")
                sys.exit(1)
            
            self.logger.info("Starting Project Management Bot...")
            self.logger.info(f"Bot configured for Jira project: {settings.jira_project_key}")
            self.logger.info(f"Using OpenAI model: {settings.openai_model}")
            self.logger.info(f"Using Atlassian MCP server: {settings.mcp_server_url}")
            
            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Start the Slack bot
            self.project_manager.start_slack_bot()
            
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error(f"Application error: {str(e)}")
        finally:
            self.shutdown()
    
    def _signal_handler(self, signum, frame):
        """Handle system signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def shutdown(self):
        """Shutdown the application"""
        try:
            self.logger.info("Shutting down Project Management Bot...")
            if self.project_manager:
                self.project_manager.stop_slack_bot()
            self.logger.info("Shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")


async def test_epic_creation():
    """Test function for epic creation (for development/testing)"""
    from models import EpicRequest
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize project manager
        pm = ProjectManager()
        
        # Test epic request
        epic_request = EpicRequest(
            title="Test Epic - User Management System",
            description="Implement a comprehensive user management system with authentication, authorization, and user profile management capabilities.",
            priority="High"
        )
        
        logger.info("Testing epic creation...")
        response = await pm.create_epic_with_stories(epic_request)
        
        if response.success:
            logger.info(f"✅ Test successful! Created epic: {response.epic.key}")
            logger.info(f"Created {response.user_stories_count} user stories")
        else:
            logger.error(f"❌ Test failed: {response.message}")
        
        return response
        
    except Exception as e:
        logger.error(f"Test error: {str(e)}")
        return None


def main():
    """Main entry point"""
    setup_logging()
    
    global logger
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("🤖 Project Management Bot Starting Up")
    logger.info("=" * 60)
    
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        logger.info("Running in test mode...")
        asyncio.run(test_epic_creation())
        return
    
    # Run the main application
    app = PMBotApplication()
    app.run()


if __name__ == "__main__":
    main() 