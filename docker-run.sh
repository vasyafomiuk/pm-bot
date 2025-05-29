#!/bin/bash

# Legacy Docker Runner - Redirects to New Scripts
# This script has been replaced with improved Docker management tools

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔄 docker-run.sh has been upgraded!${NC}"
echo ""
echo -e "${BLUE}New Docker Scripts Available:${NC}"
echo ""
echo -e "${GREEN}For Quick Start:${NC}"
echo "  ./quick_docker_start.sh          # One-command setup and run"
echo ""
echo -e "${GREEN}For Advanced Control:${NC}"
echo "  ./run_docker.sh --help           # Advanced Docker management"
echo "  ./run_docker.sh --mode minimal --build"
echo ""
echo -e "${GREEN}For Docker Compose:${NC}"
echo "  ./docker_compose_run.sh up       # Service management"
echo ""
echo -e "${BLUE}Legacy Command Mapping:${NC}"

case "${1:-help}" in
    build)
        echo "Legacy: ./docker-run.sh build"
        echo "New:    ./run_docker.sh --build --mode minimal"
        echo ""
        echo "Running new command..."
        exec ./run_docker.sh --build --mode minimal
        ;;
    run)
        echo "Legacy: ./docker-run.sh run"
        echo "New:    ./run_docker.sh --mode minimal"
        echo ""
        echo "Running new command..."
        exec ./run_docker.sh --mode minimal
        ;;
    compose)
        echo "Legacy: ./docker-run.sh compose"
        echo "New:    ./docker_compose_run.sh up"
        echo ""
        echo "Running new command..."
        exec ./docker_compose_run.sh up
        ;;
    down)
        echo "Legacy: ./docker-run.sh down"
        echo "New:    ./docker_compose_run.sh down"
        echo ""
        echo "Running new command..."
        exec ./docker_compose_run.sh down
        ;;
    test)
        echo "Legacy: ./docker-run.sh test"
        echo "New:    ./run_docker.sh --mode test"
        echo ""
        echo "Running new command..."
        exec ./run_docker.sh --mode test
        ;;
    logs)
        echo "Legacy: ./docker-run.sh logs"
        echo "New:    ./run_docker.sh --logs"
        echo ""
        echo "Running new command..."
        exec ./run_docker.sh --logs
        ;;
    status)
        echo "Legacy: ./docker-run.sh status"
        echo "New:    docker ps --filter name=pm-bot"
        echo ""
        echo "Running new command..."
        docker ps --filter name=pm-bot
        ;;
    stop)
        echo "Legacy: ./docker-run.sh stop"
        echo "New:    ./run_docker.sh --stop"
        echo ""
        echo "Running new command..."
        exec ./run_docker.sh --stop
        ;;
    restart)
        echo "Legacy: ./docker-run.sh restart"
        echo "New:    ./run_docker.sh --stop && ./run_docker.sh --mode minimal"
        echo ""
        echo "Running new commands..."
        ./run_docker.sh --stop
        exec ./run_docker.sh --mode minimal
        ;;
    shell)
        echo "Legacy: ./docker-run.sh shell"
        echo "New:    docker exec -it pm-bot /bin/bash"
        echo ""
        echo "Running new command..."
        exec docker exec -it pm-bot /bin/bash
        ;;
    clean)
        echo "Legacy: ./docker-run.sh clean"
        echo "New:    ./run_docker.sh --stop && docker rmi pm-bot:latest"
        echo ""
        echo "Running new commands..."
        ./run_docker.sh --stop
        docker rmi pm-bot:latest 2>/dev/null || echo "Image not found"
        ;;
    help|--help|-h|*)
        echo ""
        echo -e "${BLUE}📚 Recommended Usage:${NC}"
        echo ""
        echo -e "${GREEN}Quick Start (Recommended):${NC}"
        echo "  ./quick_docker_start.sh"
        echo ""
        echo -e "${GREEN}Development:${NC}"
        echo "  ./run_docker.sh --mode minimal --build"
        echo "  ./run_docker.sh --logs"
        echo "  ./run_docker.sh --stop"
        echo ""
        echo -e "${GREEN}Production:${NC}"
        echo "  ./docker_compose_run.sh up"
        echo "  ./docker_compose_run.sh logs"
        echo "  ./docker_compose_run.sh down"
        echo ""
        echo -e "${BLUE}For detailed Docker instructions:${NC}"
        echo "  See DOCKER_GUIDE.md"
        echo ""
        ;;
esac 