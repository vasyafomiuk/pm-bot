#!/bin/bash

# Docker Compose Runner for PM Bot
# Usage: ./docker_compose_run.sh [COMMAND]

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

COMMAND="${1:-up}"

show_help() {
    echo -e "${BLUE}PM Bot Docker Compose Runner${NC}"
    echo ""
    echo "Usage: ./docker_compose_run.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  up          - Start services (default)"
    echo "  down        - Stop and remove services"
    echo "  build       - Build images"
    echo "  rebuild     - Rebuild images without cache"
    echo "  logs        - Show logs"
    echo "  status      - Show service status"
    echo "  restart     - Restart services"
    echo "  help        - Show this help"
    echo ""
    echo "Examples:"
    echo "  ./docker_compose_run.sh up"
    echo "  ./docker_compose_run.sh logs"
    echo "  ./docker_compose_run.sh down"
    echo ""
}

check_env() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Creating .env from template...${NC}"
        if [ -f "environment.template.txt" ]; then
            cp environment.template.txt .env
            echo -e "${YELLOW}Please edit .env file with your credentials${NC}"
            exit 1
        else
            echo -e "${RED}No environment template found${NC}"
            exit 1
        fi
    fi
    
    # Check if MCP Atlassian credentials are configured
    if [ -f ".env" ]; then
        source .env 2>/dev/null || true
        if [ -z "$JIRA_SERVER" ] || [ -z "$JIRA_API_TOKEN" ]; then
            echo -e "${YELLOW}⚠️  MCP Atlassian service requires Jira credentials${NC}"
            echo -e "${YELLOW}   Configure JIRA_SERVER and JIRA_API_TOKEN in .env${NC}"
            echo -e "${YELLOW}   Or the PM Bot will run in minimal mode${NC}"
            echo ""
        else
            echo -e "${GREEN}✅ MCP Atlassian credentials found${NC}"
        fi
    fi
}

case $COMMAND in
    up)
        check_env
        echo -e "${BLUE}Starting PM Bot with docker-compose...${NC}"
        echo -e "${BLUE}Services: PM Bot + MCP Atlassian Server${NC}"
        echo ""
        docker-compose up -d
        echo ""
        echo -e "${GREEN}Services started${NC}"
        echo ""
        echo -e "${BLUE}Service Status:${NC}"
        docker-compose ps
        echo ""
        echo -e "${BLUE}🔗 Service URLs:${NC}"
        echo "  PM Bot:        http://localhost:3000"
        echo "  MCP Atlassian: http://localhost:9000"
        echo ""
        echo -e "${BLUE}📊 To monitor services:${NC}"
        echo "  ./docker_compose_run.sh logs"
        echo "  ./docker_compose_run.sh status"
        ;;
    down)
        echo -e "${BLUE}Stopping PM Bot services...${NC}"
        docker-compose down
        echo -e "${GREEN}Services stopped${NC}"
        ;;
    build)
        check_env
        echo -e "${BLUE}Building PM Bot images...${NC}"
        docker-compose build
        echo -e "${GREEN}Images built${NC}"
        ;;
    rebuild)
        check_env
        echo -e "${BLUE}Rebuilding PM Bot images (no cache)...${NC}"
        docker-compose build --no-cache
        echo -e "${GREEN}Images rebuilt${NC}"
        ;;
    logs)
        echo -e "${BLUE}Showing PM Bot logs...${NC}"
        docker-compose logs -f
        ;;
    status|ps)
        echo -e "${BLUE}Service Status:${NC}"
        docker-compose ps
        ;;
    restart)
        echo -e "${BLUE}Restarting PM Bot services...${NC}"
        docker-compose restart
        echo -e "${GREEN}Services restarted${NC}"
        docker-compose ps
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac 