# Project Management Bot 🤖

A powerful Slack bot that acts as an AI-powered project manager for agile teams. This bot automatically creates Jira epics and user stories using OpenAI's GPT models and integrates with Atlassian's ecosystem through the Jira API.

## Features ✨

- **Intelligent Epic Creation**: Create comprehensive epics in Jira with AI-generated features
- **Automated User Story Generation**: Generate detailed user stories with acceptance criteria
- **Meeting Notes Processing**: Fetch Google Meet notes and automatically create structured Confluence pages
- **Slack Integration**: Easy-to-use slash commands and natural language interaction
- **Atlassian MCP Integration**: Uses the [mcp-atlassian](https://github.com/sooperset/mcp-atlassian) server for robust Jira/Confluence integration
- **AI-Powered**: Uses AI agents with OpenAI/Azure OpenAI for intelligent feature and story generation
- **Google Calendar Integration**: Access Google Meet recordings, transcripts, and meeting notes
- **Confluence Documentation**: Automatically generate professional meeting documentation
- **Flexible Input**: Supports both structured and natural language inputs
- **Multi-User Support**: Supports OAuth 2.0 and Personal Access Token authentication

## Architecture 🏗️

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Slack Bot     │    │ Project Manager │    │ Atlassian MCP   │
│                 │────│                 │────│     Server      │
│ - Commands      │    │ - Orchestration │    │                 │
│ - Messages      │    │ - Workflow      │    │ - Jira Tools    │
│ - Formatting    │    │ - Validation    │    │ - Confluence    │
└─────────────────┘    └─────────────────┘    │ - Authentication│
         │                       │            └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Agents     │    │   Data Models   │    │ Atlassian APIs  │
│                 │    │                 │    │                 │
│ - Feature Gen   │    │ - Epic          │    │ - Jira Cloud    │
│ - Story Gen     │    │ - UserStory     │    │ - Jira Server   │
│ - Meeting Notes │    │ - MeetingNote   │    │ - Confluence    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       
         │              ┌─────────────────┐              
         │              │ Google Meet API │              
         │              │                 │              
         ▼              │ - Calendar      │              
┌─────────────────┐     │ - Drive Files   │              
│ OpenAI/Azure AI │     │ - Transcripts   │              
│                 │     │ - Recordings    │              
│ - GPT Models    │     └─────────────────┘              
│ - Multi-Agent   │                                      
│ - Async Proc    │                                      
└─────────────────┘                                      
```

## Quick Start 🚀

### Prerequisites

- Python 3.8+
- Slack workspace with bot permissions
- Jira Cloud instance with API access
- OpenAI API key

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd pm-bot
   ```

2. **Install uv (if not already installed):**
   ```bash
   # On macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Or with pip
   pip install uv
   ```

3. **Install dependencies with uv:**
   ```bash
   # Create virtual environment and install dependencies
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   
   # Or install directly from pyproject.toml
   uv pip install -e .
   ```

4. **Configure environment variables:**
   ```bash
   cp environment.template.txt .env
   # Edit .env with your configuration
   ```

5. **Set up Slack Bot:**
   - Create a new Slack app at https://api.slack.com/apps
   - Enable Socket Mode
   - Add the following OAuth scopes:
     - `app_mentions:read`
     - `chat:write`
     - `commands`
   - Create a slash command: `/create-epic`
   - Install the app to your workspace

6. **Configure Jira:**
   - Generate an API token in Jira
   - Note your Jira server URL and project key

7. **Run the bot:**
   ```bash
   python main.py
   ```

## Docker Deployment 🐳

### Quick Start with Docker

**🚀 Super Quick Start (Recommended):**
```bash
# One-command setup and run (builds image, validates config, starts bot)
./quick_docker_start.sh
```

**Advanced Options:**
```bash
# Run with advanced options
./run_docker.sh --mode minimal --build

# Use docker-compose for service management
./docker_compose_run.sh up
```

### Available Docker Scripts

#### 1. Quick Docker Start 
```bash
./quick_docker_start.sh
```
- **Best for**: First-time setup and testing
- **Features**: Automatic environment setup, credential validation, build and run
- **Mode**: Minimal (Slack + OpenAI only)

#### 2. Advanced Docker Runner
```bash
./run_docker.sh [OPTIONS]
```
**Options:**
- `--mode minimal` - Run with Slack + OpenAI only (default)
- `--mode full` - Run with all services (requires Jira credentials)
- `--mode test` - Run epic creation test
- `--build` - Build image before running
- `--rebuild` - Force rebuild (no cache)
- `--logs` - Show container logs
- `--stop` - Stop running container
- `--help` - Show help

**Examples:**
```bash
# Run in minimal mode with fresh build
./run_docker.sh --mode minimal --build

# View logs
./run_docker.sh --logs

# Stop the bot
./run_docker.sh --stop
```

#### 3. Docker Compose Runner
```bash
./docker_compose_run.sh [COMMAND]
```
**Commands:**
- `up` - Start services (default)
- `down` - Stop and remove services
- `build` - Build images
- `logs` - Show logs
- `status` - Show service status

**Examples:**
```bash
# Start with docker-compose
./docker_compose_run.sh up

# View logs
./docker_compose_run.sh logs

# Stop services
./docker_compose_run.sh down
```

### 📚 Comprehensive Docker Guide

For detailed Docker instructions, troubleshooting, and advanced configurations, see:

**[🐳 DOCKER_GUIDE.md](DOCKER_GUIDE.md)** - Complete Docker reference

**[🔗 MCP_ATLASSIAN_SSE_SETUP.md](MCP_ATLASSIAN_SSE_SETUP.md)** - MCP Atlassian SSE integration guide

The guides cover:
- ✅ All running methods (quick start, advanced, compose, manual)
- ✅ MCP Atlassian Server-Sent Events (SSE) integration
- ✅ Configuration and environment setup
- ✅ Monitoring and management
- ✅ Troubleshooting common issues
- ✅ Production deployment
- ✅ Volume mounts and persistence

### Docker Environment

The Docker setup includes:

- **UV package manager** for 10x faster builds
- **Multi-stage build** for optimized image size
- **Non-root user** for security
- **Volume mounts** for persistent logs
- **Environment file support** for easy configuration
- **Automatic restarts** on failure
- **Minimal and full modes** for different use cases

## Configuration ⚙️

### 📚 Detailed Setup Instructions

For comprehensive guides on generating credentials for each service, see the **[instructions/](instructions/)** folder:

- **[🚀 Quick Start Guide](instructions/README.md)** - Overview and setup order
- **[💬 Slack Credentials](instructions/slack-credentials.md)** - Bot setup and tokens
- **[🎯 Jira Credentials](instructions/jira-credentials.md)** - API tokens and permissions
- **[🤖 Azure OpenAI Credentials](instructions/azure-openai-credentials.md)** - Enterprise AI setup
- **[📅 Google Credentials](instructions/google-credentials.md)** - Calendar and Drive access

### Environment Setup

1. **Copy the environment template:**
   ```bash
   cp environment.template.txt .env
   ```

2. **Edit the `.env` file** with your actual credentials and configuration values.

### Required Environment Variables

The following variables are required for basic functionality:

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
SLACK_APP_TOKEN=xapp-your-slack-app-token

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4

# Jira Configuration
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=PROJ
```

### Optional Environment Variables

```env
# Azure OpenAI Configuration (alternative to OpenAI)
USE_AZURE_OPENAI=false
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=your-deployment-name

# AI Agent Configuration
AGENT_MAX_ITERATIONS=5
AGENT_TEMPERATURE=0.7

# Confluence Configuration
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki

# Atlassian OAuth Configuration (for multi-user setups)
ATLASSIAN_OAUTH_CLIENT_ID=your-oauth-client-id
ATLASSIAN_OAUTH_CLIENT_SECRET=your-oauth-client-secret
ATLASSIAN_OAUTH_TOKEN=your-oauth-token
ATLASSIAN_CLOUD_ID=your-cloud-id

# Google Meet Integration
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
GOOGLE_MEETING_LOOKBACK_DAYS=7

# Application Configuration
PORT=3000
LOG_LEVEL=INFO
MCP_LOG_LEVEL=INFO
```

### Docker Environment

The Docker Compose setup automatically uses the `.env` file. Just ensure your `.env` file is properly configured before running:

```bash
docker-compose up -d
```

For a complete list of all available environment variables with descriptions, see the `environment.template.txt` file.

## Atlassian MCP Integration 🔗

This bot uses the [mcp-atlassian](https://github.com/sooperset/mcp-atlassian) server for robust integration with Jira and Confluence. The MCP server provides:

- **Server-Sent Events (SSE)**: Real-time communication via streamable-HTTP transport
- **Multiple Authentication Methods**: API tokens, OAuth 2.0, Personal Access Tokens
- **Comprehensive Jira Tools**: Create issues, search, update, transitions, linking
- **Confluence Support**: Create and update pages, search content
- **Multi-User Support**: Each user can authenticate independently
- **Cloud & Server Support**: Works with Atlassian Cloud and Server/Data Center
- **Docker Integration**: Automatic service discovery and health monitoring

### Docker Compose Integration

The PM Bot includes full MCP Atlassian integration with docker-compose:

```bash
# Start both PM Bot and MCP Atlassian services
./docker_compose_run.sh up

# Services automatically configured:
# - PM Bot: http://localhost:3000
# - MCP Atlassian: http://localhost:9000 (SSE mode)
# - Health checks and service dependencies
```

**See [MCP_ATLASSIAN_SSE_SETUP.md](MCP_ATLASSIAN_SSE_SETUP.md) for complete setup instructions.**

### Authentication Options

**Option 1: API Token (Recommended for Cloud)**
- Use your Jira API token in `JIRA_API_TOKEN`
- Works with Atlassian Cloud instances
- Simplest setup for single-user scenarios

**Option 2: OAuth 2.0 (Multi-User)**
- Set up OAuth app in Atlassian Developer Console
- Configure `ATLASSIAN_OAUTH_*` variables
- Users authenticate individually
- Best for team environments

**Option 3: Personal Access Token (Server/Data Center)**
- Use PAT for Atlassian Server/Data Center
- Set in `JIRA_API_TOKEN`
- Good for on-premise installations

### Setting Up OAuth 2.0 (Optional)

For multi-user scenarios with OAuth authentication:

1. **Create OAuth App in Atlassian**:
   - Go to [Atlassian Developer Console](https://developer.atlassian.com/)
   - Create a new OAuth 2.0 app
   - Set redirect URI: `http://localhost:8080/callback`
   - Add required scopes: `read:jira-work write:jira-work`

2. **Configure Environment**:
   ```env
   ATLASSIAN_OAUTH_CLIENT_ID=your_client_id
   ATLASSIAN_OAUTH_CLIENT_SECRET=your_client_secret
   ATLASSIAN_CLOUD_ID=your_cloud_id
   ```

3. **Run OAuth Setup**:
   ```bash
   # Start MCP server for OAuth setup
   docker run --rm -i -p 8080:8080 \
     -v "${HOME}/.mcp-atlassian:/home/app/.mcp-atlassian" \
     ghcr.io/sooperset/mcp-atlassian:latest --oauth-setup -v
   ```

4. **Users authenticate individually** by providing their OAuth tokens in Slack commands.

### Azure OpenAI Setup (Optional)

To use Azure OpenAI instead of standard OpenAI:

1. **Create Azure OpenAI Resource**:
   - Go to [Azure Portal](https://portal.azure.com/)
   - Create an Azure OpenAI resource
   - Deploy a model (e.g., GPT-4, GPT-3.5-turbo)

2. **Configure Environment**:
   ```env
   USE_AZURE_OPENAI=true
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-azure-openai-api-key
   AZURE_OPENAI_DEPLOYMENT=your-deployment-name
   ```

3. **Benefits of Azure OpenAI**:
   - Enterprise-grade security and compliance
   - Data residency and privacy controls
   - Integration with Azure services
   - Dedicated capacity options

### Google Meet Integration Setup (Optional)

To enable meeting notes processing from Google Calendar/Meet:

1. **Create Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Calendar API and Google Drive API

2. **Create Service Account Credentials**:
   - Go to "Credentials" in the Google Cloud Console
   - Create credentials → Service account key
   - Download the JSON file as `credentials.json`

3. **Configure OAuth (for user access)**:
   - Create OAuth 2.0 credentials for desktop application
   - Download the JSON file as `credentials.json`
   - Add scopes: `https://www.googleapis.com/auth/calendar.readonly`, `https://www.googleapis.com/auth/drive.readonly`

4. **Set up Environment**:
   ```env
   GOOGLE_CREDENTIALS_FILE=credentials.json
   GOOGLE_TOKEN_FILE=token.json
   GOOGLE_MEETING_LOOKBACK_DAYS=7
   ```

5. **First Run Authentication**:
   - The first time you use meeting commands, you'll need to authenticate
   - The bot will guide you through OAuth flow
   - Token will be saved for future use

6. **Required Permissions**:
   - Google Calendar: Read access to calendar events
   - Google Drive: Read access to meeting recordings and transcripts

## Usage 📖

### Creating an Epic

Use the `/create-epic` slash command in Slack:

```
/create-epic
Title: User Authentication System
Description: Implement a comprehensive user authentication system with login, registration, and password reset functionality
Features: user registration, login/logout, password reset, two-factor authentication
Priority: High
Labels: security, authentication
```

### Processing Meeting Notes

Use the `/process-meetings` command to automatically process recent Google Meet notes:

```
/process-meetings space=PROJ
```

This will:
1. Fetch recent meetings from Google Calendar
2. Extract notes, transcripts, and recordings
3. Process content with AI to create structured documentation
4. Create Confluence pages with professional formatting
5. Include action items, decisions, and next steps

### Searching Specific Meetings

Use the `/search-meetings` command to find and process specific meetings:

```
/search-meetings sprint space=PROJ days=14
/search-meetings "project review" space=DEV
/search-meetings standup
```

### Epic Creation Workflow

1. **Input Processing**: The bot parses your epic request
2. **Feature Generation**: If features aren't specified, AI generates relevant features
3. **Epic Creation**: Creates the epic in Jira with proper metadata
4. **Story Generation**: AI generates detailed user stories for each feature
5. **Story Creation**: Creates and links user stories to the epic in Jira
6. **Notification**: Sends formatted results back to Slack

### Meeting Notes Workflow

1. **Meeting Discovery**: Fetches meetings from Google Calendar
2. **Content Extraction**: Retrieves notes, transcripts, recordings
3. **AI Processing**: Structures content into professional documentation
4. **Confluence Creation**: Creates formatted pages with action items
5. **Notification**: Reports successful processing to Slack

### Supported Commands

- `/create-epic` - Create a new epic with user stories
- `/process-meetings space=SPACE_KEY` - Process recent meeting notes to Confluence
- `/search-meetings keyword [space=SPACE_KEY] [days=30]` - Search and process specific meetings
- `@bot help` - Show help information
- `@bot create epic` - Get epic creation help

## API Structure 📋

### Core Models

#### Epic
```python
class Epic(BaseModel):
    key: Optional[str]           # Jira epic key
    title: str                   # Epic title
    description: str             # Epic description
    status: Optional[str]        # Epic status
    priority: str               # Epic priority
    features: Optional[List[str]] # Generated features
```

#### UserStory
```python
class UserStory(BaseModel):
    key: Optional[str]                    # Jira story key
    title: str                           # Story title
    description: str                     # Story description
    epic_key: Optional[str]              # Parent epic key
    story_points: Optional[int]          # Story points
    acceptance_criteria: Optional[List[AcceptanceCriteria]]
```

### Services

- **OpenAIService**: Manages AI agents for intelligent content generation
- **JiraService**: Manages Atlassian MCP integration for Jira operations
- **SlackService**: Handles Slack bot interactions and message formatting

### AI Agents Architecture

The bot uses specialized AI agents for different tasks:

- **FeatureGeneratorAgent**: Analyzes epics and generates comprehensive feature lists
- **UserStoryGeneratorAgent**: Creates detailed user stories with acceptance criteria
- **MultiAgentSystem**: Coordinates multiple agents and manages conversation history

**Agent Features:**
- Async execution for better performance
- Memory management for context retention
- Support for both OpenAI and Azure OpenAI
- Concurrent story generation for faster processing
- Specialized prompts for each agent type

### MCP Tools Used

The bot leverages these MCP tools from the Atlassian server:

- `jira_create_issue`: Create epics and user stories
- `jira_search`: Search for issues using JQL
- `jira_get_issue`: Retrieve issue details
- `jira_link_to_epic`: Link stories to epics
- `jira_transition_issue`: Update issue status
- `jira_get_transitions`: Get available status transitions

## Development 👨‍💻

### Project Structure

```
pm-bot/
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration management
├── models/
│   ├── __init__.py
│   ├── epic.py             # Epic data models
│   └── user_story.py       # User story data models
├── services/
│   ├── __init__.py
│   ├── openai_service.py   # OpenAI integration
│   ├── jira_service.py     # Jira integration
│   └── slack_service.py    # Slack integration
├── core/
│   ├── __init__.py
│   └── project_manager.py  # Main orchestration
├── utils/
│   ├── __init__.py
│   └── text_parser.py      # Text processing utilities
├── main.py                 # Application entry point
├── requirements.txt        # Dependencies
└── README.md              # This file
```

### Testing

Run in test mode to verify configuration:

```bash
python main.py test
```

### Adding New Features

1. **Add new models** in the `models/` directory
2. **Extend services** for new integrations
3. **Update the ProjectManager** for new workflows
4. **Add Slack handlers** for new commands

## Customization 🎨

### Custom Prompts

Modify the prompts in `OpenAIService` to customize AI behavior:

- `_build_features_prompt()` - Feature generation
- `_build_user_story_prompt()` - User story generation

### Jira Field Mapping

Update field mappings in `JiraService` for your Jira configuration:

- Custom fields for story points, epic names, etc.
- Issue type configurations
- Workflow transitions

### Slack Message Formatting

Customize message formatting in `SlackService`:

- Response templates
- Progress messages
- Error handling

## Troubleshooting 🔧

### Common Issues

1. **Authentication Errors**
   - Verify API tokens and credentials
   - Check OAuth scopes for Slack bot
   - Ensure Atlassian permissions are correct
   - Test MCP server connectivity: `curl http://localhost:9000/healthz`

2. **Connection Issues**
   - Verify network connectivity between containers
   - Check if MCP server is running: `docker logs mcp-atlassian`
   - Validate service URLs and ports
   - Ensure Docker network configuration

3. **Epic/Story Creation Fails**
   - Check Jira project configuration
   - Verify issue types exist (Epic, Story)
   - Test MCP tools directly for debugging
   - Check MCP server logs for detailed errors

4. **Docker Issues**
   - Check container status: `./docker-run.sh status`
   - View container logs: `./docker-run.sh logs`
   - Test configuration: `./docker-run.sh test`
   - Verify .env file exists and is configured properly

### Logs

**Local deployment:**
```bash
tail -f pm_bot.log
```

**Docker deployment:**
```bash
./docker-run.sh logs
# or
docker logs -f project-management-bot
```

**Docker logs location:**
Logs are mounted to `./logs/pm_bot.log` on the host system.

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Support 💬

For issues and questions:

1. Check the troubleshooting section
2. Review logs for error details
3. Open an issue on GitHub
4. Contact the development team

---

**Made with ❤️ for agile teams everywhere** 