#!/bin/bash

# PM Bot Docker Runner Script
# Usage: ./run_docker.sh [OPTIONS]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
MODE="minimal"
BUILD=false
REBUILD=false
LOGS=false
STOP=false
HELP=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --build)
            BUILD=true
            shift
            ;;
        --rebuild)
            REBUILD=true
            shift
            ;;
        --logs)
            LOGS=true
            shift
            ;;
        --stop)
            STOP=true
            shift
            ;;
        --help|-h)
            HELP=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Help function
show_help() {
    echo -e "${BLUE}PM Bot Docker Runner${NC}"
    echo ""
    echo "Usage: ./run_docker.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --mode MODE        Run mode: minimal, full, test (default: minimal)"
    echo "  --build           Build Docker image before running"
    echo "  --rebuild         Force rebuild Docker image (no cache)"
    echo "  --logs            Show container logs and exit"
    echo "  --stop            Stop running container"
    echo "  --help, -h        Show this help message"
    echo ""
    echo "Modes:"
    echo "  minimal   - Run with minimal validation (Slack + OpenAI only)"
    echo "  full      - Run with full validation (requires all credentials)"
    echo "  test      - Run epic creation test"
    echo ""
    echo "Examples:"
    echo "  ./run_docker.sh --mode minimal --build"
    echo "  ./run_docker.sh --mode full"
    echo "  ./run_docker.sh --stop"
    echo "  ./run_docker.sh --logs"
    echo ""
}

# Show help if requested
if [ "$HELP" = true ]; then
    show_help
    exit 0
fi

# Container and image names
CONTAINER_NAME="pm-bot"
IMAGE_NAME="pm-bot:latest"
DOCKERFILE="Dockerfile"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    if [ -f "environment.template.txt" ]; then
        echo -e "${BLUE}Creating .env from template...${NC}"
        cp environment.template.txt .env
        echo -e "${YELLOW}Please edit .env file with your credentials before running${NC}"
        exit 1
    else
        echo -e "${RED}Error: No environment template found${NC}"
        exit 1
    fi
fi

# Stop container if requested
if [ "$STOP" = true ]; then
    echo -e "${BLUE}Stopping PM Bot container...${NC}"
    docker stop $CONTAINER_NAME 2>/dev/null || echo -e "${YELLOW}Container not running${NC}"
    docker rm $CONTAINER_NAME 2>/dev/null || echo -e "${YELLOW}Container not found${NC}"
    echo -e "${GREEN}Container stopped and removed${NC}"
    exit 0
fi

# Show logs if requested
if [ "$LOGS" = true ]; then
    echo -e "${BLUE}Showing PM Bot container logs...${NC}"
    docker logs -f $CONTAINER_NAME 2>/dev/null || echo -e "${RED}Container not found or not running${NC}"
    exit 0
fi

# Build image if requested
if [ "$BUILD" = true ] || [ "$REBUILD" = true ]; then
    echo -e "${BLUE}Building PM Bot Docker image...${NC}"
    
    BUILD_ARGS=""
    if [ "$REBUILD" = true ]; then
        BUILD_ARGS="--no-cache"
    fi
    
    docker build $BUILD_ARGS -t $IMAGE_NAME -f $DOCKERFILE .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Docker image built successfully${NC}"
    else
        echo -e "${RED}Failed to build Docker image${NC}"
        exit 1
    fi
fi

# Check if image exists
if ! docker image inspect $IMAGE_NAME >/dev/null 2>&1; then
    echo -e "${YELLOW}Docker image not found. Building...${NC}"
    docker build -t $IMAGE_NAME -f $DOCKERFILE .
fi

# Stop existing container if running
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Determine run command based on mode
case $MODE in
    minimal)
        CMD_ARGS="--skip-validation"
        echo -e "${BLUE}Running PM Bot in minimal mode (Slack + OpenAI only)${NC}"
        ;;
    full)
        CMD_ARGS=""
        echo -e "${BLUE}Running PM Bot in full mode (all services)${NC}"
        ;;
    test)
        CMD_ARGS="test"
        echo -e "${BLUE}Running PM Bot in test mode${NC}"
        ;;
    *)
        echo -e "${RED}Invalid mode: $MODE${NC}"
        echo "Valid modes: minimal, full, test"
        exit 1
        ;;
esac

# Run the container
echo -e "${BLUE}Starting PM Bot container...${NC}"

# Docker run command with environment file
docker run -d \
    --name $CONTAINER_NAME \
    --env-file .env \
    -p 3000:3000 \
    -v "$(pwd)/logs:/app/logs" \
    --restart unless-stopped \
    $IMAGE_NAME \
    python3 main.py $CMD_ARGS

if [ $? -eq 0 ]; then
    echo -e "${GREEN}PM Bot container started successfully${NC}"
    echo ""
    echo -e "${BLUE}Container Status:${NC}"
    docker ps --filter name=$CONTAINER_NAME --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo "  View logs:    docker logs -f $CONTAINER_NAME"
    echo "  Stop bot:     ./run_docker.sh --stop"
    echo "  View status:  docker ps"
    echo "  Shell access: docker exec -it $CONTAINER_NAME /bin/bash"
    echo ""
    echo -e "${BLUE}To view live logs:${NC}"
    echo "  ./run_docker.sh --logs"
else
    echo -e "${RED}Failed to start PM Bot container${NC}"
    exit 1
fi 