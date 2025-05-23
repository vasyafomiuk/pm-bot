# Docker Deployment Guide 🐳

This guide provides comprehensive instructions for deploying the Project Management Bot using Docker.

## Quick Start

1. **Clone and configure:**
   ```bash
   git clone <repository-url>
   cd pm-bot
   cp env.example .env
   # Edit .env with your configuration
   ```

2. **Build and run:**
   ```bash
   ./docker-run.sh build
   ./docker-run.sh run
   ```

3. **View logs:**
   ```bash
   ./docker-run.sh logs
   ```

## Docker Architecture

### Container Components

- **Base Image**: Python 3.11-slim (optimized for production)
- **User Security**: Non-root user `pmbot` for enhanced security
- **Health Checks**: Automated health monitoring
- **Log Management**: Persistent log storage via volume mounts
- **Resource Limits**: CPU and memory constraints for production use

## Deployment Options

### Option 1: Management Script (Recommended)

```bash
./docker-run.sh build    # Build the image
./docker-run.sh run      # Run the container
./docker-run.sh status   # Check status
./docker-run.sh logs     # View logs
./docker-run.sh restart  # Restart container
./docker-run.sh clean    # Clean up
```

### Option 2: Docker Compose

```bash
./docker-run.sh compose  # Start with compose
./docker-run.sh down     # Stop services
```

### Option 3: Manual Docker Commands

```bash
docker build -t pm-bot .
docker run -d --name project-management-bot --env-file .env -v $(pwd)/logs:/app/logs:rw pm-bot
```

## Environment Configuration

Required variables in `.env`:

```env
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret
SLACK_APP_TOKEN=xapp-your-token
OPENAI_API_KEY=your-api-key
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ
```

## Troubleshooting

```bash
# Check container status
./docker-run.sh status

# View logs
./docker-run.sh logs

# Test configuration
./docker-run.sh test

# Access container shell
./docker-run.sh shell
```

For detailed Docker information, see the main README.md file. 