import os
from dotenv import load_dotenv
from pydantic import BaseSettings
from typing import Optional, List

load_dotenv()


class Settings(BaseSettings):
    # Slack Configuration
    slack_bot_token: str = os.getenv("SLACK_BOT_TOKEN", "")
    slack_signing_secret: str = os.getenv("SLACK_SIGNING_SECRET", "")
    slack_app_token: str = os.getenv("SLACK_APP_TOKEN", "")
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Azure OpenAI Configuration (optional)
    azure_openai_endpoint: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    azure_openai_deployment: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    
    # AI Agent Configuration
    use_azure_openai: bool = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"
    agent_max_iterations: int = int(os.getenv("AGENT_MAX_ITERATIONS", "5"))
    agent_temperature: float = float(os.getenv("AGENT_TEMPERATURE", "0.7"))
    
    # Google Meet/Calendar Configuration
    google_credentials_file: Optional[str] = os.getenv("GOOGLE_CREDENTIALS_FILE")
    google_token_file: Optional[str] = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
    google_scopes: List[str] = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    google_meeting_lookback_days: int = int(os.getenv("GOOGLE_MEETING_LOOKBACK_DAYS", "7"))
    
    # Jira/Atlassian Configuration
    jira_server: str = os.getenv("JIRA_SERVER", "")
    jira_username: str = os.getenv("JIRA_USERNAME", "")
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")
    jira_project_key: str = os.getenv("JIRA_PROJECT_KEY", "")
    
    # Atlassian MCP Configuration
    mcp_server_url: str = os.getenv("MCP_SERVER_URL", "http://mcp-atlassian:9000")
    atlassian_oauth_token: Optional[str] = os.getenv("ATLASSIAN_OAUTH_TOKEN")
    atlassian_oauth_client_id: Optional[str] = os.getenv("ATLASSIAN_OAUTH_CLIENT_ID")
    atlassian_oauth_client_secret: Optional[str] = os.getenv("ATLASSIAN_OAUTH_CLIENT_SECRET")
    atlassian_cloud_id: Optional[str] = os.getenv("ATLASSIAN_CLOUD_ID")
    
    # Application Configuration
    port: int = int(os.getenv("PORT", "3000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings() 