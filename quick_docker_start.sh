#!/bin/bash

# Quick Docker Start Script for PM Bot
# This script will build and run the PM Bot with minimal configuration

set -e

echo "🤖 PM Bot Quick Docker Start"
echo "=============================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists, create from template if not
if [ ! -f ".env" ]; then
    echo "📄 Creating .env file from template..."
    if [ -f "environment.template.txt" ]; then
        cp environment.template.txt .env
        echo "✅ .env file created from template"
        echo ""
        echo "⚠️  IMPORTANT: Edit .env file with your credentials:"
        echo "   - SLACK_BOT_TOKEN"
        echo "   - SLACK_SIGNING_SECRET" 
        echo "   - SLACK_APP_TOKEN"
        echo "   - OPENAI_API_KEY"
        echo ""
        echo "Then run this script again: ./quick_docker_start.sh"
        exit 1
    else
        echo "❌ No environment template found!"
        exit 1
    fi
fi

# Check if essential credentials are configured
echo "🔍 Checking essential credentials..."
source .env 2>/dev/null || true

missing_creds=()
[ -z "$SLACK_BOT_TOKEN" ] && missing_creds+=("SLACK_BOT_TOKEN")
[ -z "$SLACK_SIGNING_SECRET" ] && missing_creds+=("SLACK_SIGNING_SECRET")
[ -z "$SLACK_APP_TOKEN" ] && missing_creds+=("SLACK_APP_TOKEN")
[ -z "$OPENAI_API_KEY" ] && missing_creds+=("OPENAI_API_KEY")

if [ ${#missing_creds[@]} -gt 0 ]; then
    echo "❌ Missing essential credentials in .env file:"
    for cred in "${missing_creds[@]}"; do
        echo "   - $cred"
    done
    echo ""
    echo "Please edit .env file and add these credentials, then run again."
    exit 1
fi

echo "✅ Essential credentials found"

# Build and run
echo ""
echo "🏗️  Building PM Bot Docker image..."
docker build -t pm-bot:latest .

echo ""
echo "🚀 Starting PM Bot in minimal mode..."
./run_docker.sh --mode minimal

echo ""
echo "🎉 PM Bot is starting up!"
echo ""
echo "📊 To view logs:"
echo "   ./run_docker.sh --logs"
echo ""
echo "🛑 To stop:"
echo "   ./run_docker.sh --stop"
echo ""
echo "📋 Container status:"
docker ps --filter name=pm-bot --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 