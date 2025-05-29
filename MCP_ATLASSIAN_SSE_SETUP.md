# 🔗 MCP Atlassian SSE Integration

**PM Bot now includes full MCP Atlassian integration with Server-Sent Events (SSE) support!**

## 🚀 What's Configured

### ✅ Official MCP Atlassian Server
- **Image**: `ghcr.io/sooperset/mcp-atlassian:latest` (official from [sooperset/mcp-atlassian](https://github.com/sooperset/mcp-atlassian))
- **Transport**: Streamable-HTTP (SSE mode) for real-time communication
- **Port**: 9000 (accessible at `http://localhost:9000`)
- **Health checks**: Automatic health monitoring with startup dependencies

### ✅ Service Integration
- **PM Bot** waits for MCP Atlassian to be healthy before starting
- **Automatic service discovery** via Docker network
- **Shared environment configuration** from `.env` file
- **Persistent logging** and restart policies

## 🔧 Configuration

### Required Environment Variables
```bash
# Jira Configuration (Required for MCP Atlassian)
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=YOUR_PROJECT_KEY

# Confluence Configuration (Optional)
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki

# MCP Server Configuration
MCP_SERVER_URL=http://mcp-atlassian:9000  # Auto-configured in docker-compose
MCP_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Authentication Methods

The MCP Atlassian server supports multiple authentication methods as described in the [official repository](https://github.com/sooperset/mcp-atlassian):

#### 1. API Token (Recommended for Cloud)
```bash
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
```

#### 2. OAuth 2.0 (Multi-User Support)
```bash
ATLASSIAN_OAUTH_CLIENT_ID=your_oauth_app_client_id
ATLASSIAN_OAUTH_CLIENT_SECRET=your_oauth_app_client_secret
ATLASSIAN_OAUTH_REDIRECT_URI=http://localhost:8080/callback
ATLASSIAN_OAUTH_SCOPE=read:jira-work write:jira-work read:confluence-content.all write:confluence-content offline_access
ATLASSIAN_OAUTH_CLOUD_ID=your_cloud_id
```

#### 3. Personal Access Token (Server/Data Center)
```bash
JIRA_SERVER=https://your-jira-server.com
JIRA_API_TOKEN=your_personal_access_token
```

## 🏃‍♂️ Running with Docker Compose

### Quick Start
```bash
# Start both services (PM Bot + MCP Atlassian)
./docker_compose_run.sh up

# Monitor logs
./docker_compose_run.sh logs

# Check service status
./docker_compose_run.sh status

# Stop services
./docker_compose_run.sh down
```

### Service URLs
- **PM Bot**: http://localhost:3000
- **MCP Atlassian**: http://localhost:9000
- **MCP Health Check**: http://localhost:9000/healthz

## 🔍 MCP Tools Available

The MCP Atlassian server provides these tools for the PM Bot:

### Jira Tools
- `jira_create_issue` - Create epics and user stories
- `jira_search` - Search issues using JQL
- `jira_get_issue` - Get issue details
- `jira_update_issue` - Update existing issues
- `jira_transition_issue` - Change issue status
- `jira_link_to_epic` - Link stories to epics
- `jira_add_comment` - Add comments to issues

### Confluence Tools  
- `confluence_create_page` - Create documentation pages
- `confluence_update_page` - Update existing pages
- `confluence_search` - Search Confluence content
- `confluence_get_page` - Retrieve page content

## 📊 Service Architecture

```
┌─────────────────┐    HTTP/SSE     ┌─────────────────┐    REST API    ┌─────────────────┐
│   PM Bot        │ ──────────────► │ MCP Atlassian   │ ─────────────► │  Atlassian      │
│   (Port 3000)   │                 │  Server         │                │ - Jira          │
│                 │                 │  (Port 9000)    │                │ - Confluence    │
│ - Slack Bot     │                 │ - Tool Routing  │                │                 │
│ - AI Agents     │                 │ - Authentication│                │                 │
│ - Workflows     │                 │ - Error Handling│                │                 │
└─────────────────┘                 └─────────────────┘                └─────────────────┘
```

## 🚨 Troubleshooting

### Common Issues

**MCP Service Won't Start**
```bash
# Check MCP Atlassian logs
docker logs mcp-atlassian

# Verify credentials
grep -E "(JIRA_|CONFLUENCE_)" .env

# Test connectivity
curl http://localhost:9000/healthz
```

**PM Bot Can't Connect to MCP**
```bash
# Check if MCP service is healthy
docker inspect mcp-atlassian | grep Health

# Verify network connectivity
docker exec pm-bot ping mcp-atlassian

# Check MCP_SERVER_URL setting
docker exec pm-bot env | grep MCP_SERVER_URL
```

**Authentication Failures**
```bash
# For Cloud: Verify API token (not password)
# For Server: Verify Personal Access Token
# Check permissions in Atlassian admin panel
```

### Debug Mode
Enable verbose logging for troubleshooting:
```bash
# In .env file
MCP_LOG_LEVEL=DEBUG

# Restart services
./docker_compose_run.sh restart
./docker_compose_run.sh logs
```

## 🔐 Security Considerations

### API Token Security
- Use API tokens, not passwords
- Limit token permissions to required scopes
- Rotate tokens regularly
- Keep `.env` file secure and out of version control

### Network Security
- Services communicate within Docker network
- Only necessary ports exposed to host
- Health checks ensure service availability

## 🎯 Benefits of SSE Mode

### Real-time Communication
- ✅ **Lower latency** - Direct HTTP/SSE connection
- ✅ **Better error handling** - Immediate feedback on failures
- ✅ **Connection persistence** - Maintains connection for faster operations
- ✅ **Streaming support** - Can handle large responses efficiently

### Enhanced Integration
- ✅ **Service discovery** - Automatic connection via Docker network
- ✅ **Health monitoring** - Built-in health checks and dependencies
- ✅ **Scalability** - Easy to scale both services independently
- ✅ **Reliability** - Automatic restarts and failure recovery

## 📚 Additional Resources

- **[MCP Atlassian GitHub](https://github.com/sooperset/mcp-atlassian)** - Official repository
- **[Docker Compose Guide](DOCKER_GUIDE.md)** - Complete Docker setup
- **[Jira Credentials Setup](instructions/jira_credentials.md)** - Credential configuration
- **[Atlassian OAuth Setup](https://developer.atlassian.com/)** - OAuth configuration

---

**Your PM Bot now has enterprise-grade Atlassian integration with SSE support!** 🚀🔗 