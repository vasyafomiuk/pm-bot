#!/bin/bash

# Docker entrypoint script for Project Management Bot
set -e

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ENTRYPOINT] $1"
}

# Function to check if a required environment variable is set
check_env_var() {
    local var_name=$1
    local var_value=${!var_name}
    
    if [ -z "$var_value" ]; then
        log "ERROR: Required environment variable $var_name is not set"
        return 1
    fi
    return 0
}

# Create logs directory if it doesn't exist
mkdir -p /app/logs

log "Starting Project Management Bot..."

# Validate required environment variables
log "Validating environment configuration..."

required_vars=(
    "SLACK_BOT_TOKEN"
    "SLACK_SIGNING_SECRET" 
    "SLACK_APP_TOKEN"
    "OPENAI_API_KEY"
    "JIRA_SERVER"
    "JIRA_USERNAME"
    "JIRA_API_TOKEN"
    "JIRA_PROJECT_KEY"
)

all_vars_present=true
for var in "${required_vars[@]}"; do
    if ! check_env_var "$var"; then
        all_vars_present=false
    fi
done

if [ "$all_vars_present" = false ]; then
    log "ERROR: Missing required environment variables. Please check your configuration."
    exit 1
fi

log "Environment validation passed"

# Set default values for optional variables
export OPENAI_MODEL=${OPENAI_MODEL:-"gpt-4"}
export PORT=${PORT:-"3000"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

log "Configuration:"
log "  OpenAI Model: $OPENAI_MODEL"
log "  Port: $PORT"
log "  Log Level: $LOG_LEVEL"
log "  Jira Server: $JIRA_SERVER"
log "  Jira Project: $JIRA_PROJECT_KEY"

# Test mode handling
if [ "$1" = "test" ]; then
    log "Running in test mode..."
    exec python main.py test
fi

# Health check mode
if [ "$1" = "health" ]; then
    python -c "
import sys
import asyncio
try:
    from config import settings
    from core import ProjectManager
    
    async def health_check():
        pm = ProjectManager()
        validation = await pm.validate_services()
        if all(validation.values()):
            print('Health check passed')
            return 0
        else:
            print('Health check failed:', validation)
            return 1
    
    exit_code = asyncio.run(health_check())
    sys.exit(exit_code)
except Exception as e:
    print('Health check error:', str(e))
    sys.exit(1)
"
    exit $?
fi

# Run the main application
log "Starting Project Management Bot application..."
exec python main.py "$@" 