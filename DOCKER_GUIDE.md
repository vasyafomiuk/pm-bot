# 🐳 Docker Guide for PM Bot

This guide explains how to run the Project Management Bot using Docker with different methods and configurations.

## 🚀 Quick Start (Recommended)

The fastest way to get started:

```bash
# 1. Quick setup with automatic environment creation
./quick_docker_start.sh
```

This script will:
- ✅ Check if Docker is running
- ✅ Create `.env` from template if needed
- ✅ Validate essential credentials
- ✅ Build the Docker image
- ✅ Start the bot in minimal mode

## 🛠️ Available Scripts

### 1. Quick Docker Start
```bash
./quick_docker_start.sh
```
**Best for**: First-time setup and testing

**Features:**
- Automatic environment setup
- Credential validation
- One-command build and run
- Minimal mode (Slack + OpenAI only)

### 2. Advanced Docker Runner
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

# Run with all services (requires full configuration)
./run_docker.sh --mode full

# View logs
./run_docker.sh --logs

# Stop the bot
./run_docker.sh --stop
```

### 3. Docker Compose Runner
```bash
./docker_compose_run.sh [COMMAND]
```

**Commands:**
- `up` - Start services (default)
- `down` - Stop and remove services
- `build` - Build images
- `rebuild` - Rebuild without cache
- `logs` - Show logs
- `status` - Show service status
- `restart` - Restart services

**Examples:**
```bash
# Start with docker-compose
./docker_compose_run.sh up

# View logs
./docker_compose_run.sh logs

# Stop services
./docker_compose_run.sh down
```

## 📋 Prerequisites

### Required
- Docker installed and running
- Docker Compose (for compose method)

### Credentials Needed
**Minimal Mode (Slack + OpenAI):**
- `SLACK_BOT_TOKEN`
- `SLACK_SIGNING_SECRET`
- `SLACK_APP_TOKEN`
- `OPENAI_API_KEY`

**Full Mode (All Services):**
- All minimal credentials plus:
- `JIRA_SERVER`
- `JIRA_USERNAME`
- `JIRA_API_TOKEN`
- `JIRA_PROJECT_KEY`

## 🔧 Configuration

### Environment Setup
```bash
# Create .env file from template
cp environment.template.txt .env

# Edit with your credentials
nano .env
```

### Essential Environment Variables
```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4

# Optional: Jira Configuration (for full mode)
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@domain.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=YOUR_PROJECT_KEY
```

## 🏃‍♂️ Running Methods

### Method 1: Quick Start (Simplest)
```bash
./quick_docker_start.sh
```

### Method 2: Docker Run Script (Flexible)
```bash
# Minimal mode (recommended for testing)
./run_docker.sh --mode minimal --build

# Full mode (production)
./run_docker.sh --mode full --build
```

### Method 3: Docker Compose (Service Management)
```bash
# Start services
./docker_compose_run.sh up

# Follow logs
./docker_compose_run.sh logs
```

### Method 4: Manual Docker Commands
```bash
# Build image
docker build -t pm-bot:latest .

# Run container (minimal mode)
docker run -d \
  --name pm-bot \
  --env-file .env \
  -p 3000:3000 \
  -v "$(pwd)/logs:/app/logs" \
  pm-bot:latest \
  python3 main.py --skip-validation

# View logs
docker logs -f pm-bot

# Stop container
docker stop pm-bot && docker rm pm-bot
```

## 📊 Monitoring and Management

### View Logs
```bash
# Using scripts
./run_docker.sh --logs
./docker_compose_run.sh logs

# Direct Docker commands
docker logs -f pm-bot
```

### Check Status
```bash
# Container status
docker ps --filter name=pm-bot

# Service status (compose)
./docker_compose_run.sh status
```

### Access Container Shell
```bash
# Get shell access
docker exec -it pm-bot /bin/bash

# Run commands inside container
docker exec pm-bot python3 main.py test
```

## 🗂️ Volume Mounts

The bot uses these volume mounts:

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./logs` | `/app/logs` | Log files persistence |
| `./.env` | `/app/.env` | Environment configuration |

## 🔄 Common Operations

### Update and Restart
```bash
# Pull latest code changes
git pull

# Rebuild and restart
./run_docker.sh --rebuild --mode minimal
```

### Clean Up
```bash
# Stop and remove container
./run_docker.sh --stop

# Remove Docker image
docker rmi pm-bot:latest

# Clean up unused Docker resources
docker system prune
```

### Debugging
```bash
# View recent logs
docker logs --tail 100 pm-bot

# Check container resources
docker stats pm-bot

# Inspect container details
docker inspect pm-bot
```

## 🚨 Troubleshooting

### Common Issues

**"Docker is not running"**
```bash
# Start Docker Desktop or Docker daemon
# On macOS: Open Docker Desktop app
# On Linux: sudo systemctl start docker
```

**"Permission denied" on scripts**
```bash
# Make scripts executable
chmod +x *.sh
```

**"Missing credentials" error**
```bash
# Check .env file exists and has correct values
cat .env | grep -E "(SLACK_|OPENAI_)"
```

**Container keeps restarting**
```bash
# Check logs for errors
./run_docker.sh --logs

# Common fix: Invalid credentials in .env
```

**Port already in use**
```bash
# Find what's using port 3000
lsof -i :3000

# Stop conflicting service or change port in .env
PORT=3001
```

## 🎯 Production Deployment

### Recommended Production Setup
```bash
# 1. Use docker-compose for service management
./docker_compose_run.sh build

# 2. Run in full mode with all services
# Edit docker-compose.yml to change command:
# command: python3 main.py  # (removes --skip-validation)

# 3. Start services
./docker_compose_run.sh up
```

### Health Monitoring
```bash
# Check if container is healthy
docker inspect pm-bot | grep Health

# Set up monitoring (example with crontab)
*/5 * * * * docker ps | grep pm-bot || ./run_docker.sh --mode minimal
```

## 📚 Additional Resources

- [Setup Instructions](instructions/README.md) - Credential setup guides
- [Quick Start UV](QUICK_START_UV.md) - Local development setup
- [Quick Start Minimal](QUICK_START_MINIMAL.md) - Minimal local setup

---

## 🎯 Summary

**For Quick Testing:**
```bash
./quick_docker_start.sh
```

**For Development:**
```bash
./run_docker.sh --mode minimal --build
```

**For Production:**
```bash
./docker_compose_run.sh up
```

Your PM Bot is now ready to run in any environment! 🚀🤖 