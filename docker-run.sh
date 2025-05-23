#!/bin/bash

# Docker management script for Project Management Bot
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="pm-bot"
CONTAINER_NAME="project-management-bot"
ENV_FILE=".env"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}==== $1 ====${NC}"
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        print_error ".env file not found. Please create one from env.example"
        print_status "Running: cp env.example .env"
        cp env.example .env
        print_warning "Please edit .env file with your configuration before running the bot"
        exit 1
    fi
}

# Function to build the Docker image
build() {
    print_header "Building Docker Image"
    docker build -t $IMAGE_NAME .
    print_status "Build completed successfully"
}

# Function to run the container
run() {
    print_header "Starting Project Management Bot"
    check_env_file
    
    # Stop existing container if running
    if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
        print_status "Stopping existing container..."
        docker stop $CONTAINER_NAME
    fi
    
    # Remove existing container if exists
    if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
        print_status "Removing existing container..."
        docker rm $CONTAINER_NAME
    fi
    
    # Create logs directory
    mkdir -p logs
    
    # Run new container
    docker run -d \
        --name $CONTAINER_NAME \
        --env-file $ENV_FILE \
        -v "$(pwd)/logs:/app/logs:rw" \
        --restart unless-stopped \
        $IMAGE_NAME
    
    print_status "Container started successfully"
    print_status "Container name: $CONTAINER_NAME"
    print_status "View logs with: $0 logs"
}

# Function to run with docker-compose
compose_up() {
    print_header "Starting with Docker Compose"
    check_env_file
    docker-compose up -d
    print_status "Services started with docker-compose"
}

# Function to stop with docker-compose
compose_down() {
    print_header "Stopping Docker Compose Services"
    docker-compose down
    print_status "Services stopped"
}

# Function to run in test mode
test() {
    print_header "Running in Test Mode"
    check_env_file
    
    docker run --rm \
        --env-file $ENV_FILE \
        -v "$(pwd)/logs:/app/logs:rw" \
        $IMAGE_NAME test
}

# Function to show logs
logs() {
    if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
        docker logs -f $CONTAINER_NAME
    else
        print_error "Container $CONTAINER_NAME is not running"
        exit 1
    fi
}

# Function to show container status
status() {
    print_header "Container Status"
    
    if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
        print_status "Container is running"
        docker ps -f name=$CONTAINER_NAME
        echo ""
        print_status "Container health:"
        docker exec $CONTAINER_NAME ./docker-entrypoint.sh health
    elif [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
        print_warning "Container exists but is not running"
        docker ps -a -f name=$CONTAINER_NAME
    else
        print_warning "Container does not exist"
    fi
}

# Function to stop the container
stop() {
    print_header "Stopping Container"
    
    if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
        docker stop $CONTAINER_NAME
        print_status "Container stopped"
    else
        print_warning "Container is not running"
    fi
}

# Function to restart the container
restart() {
    print_header "Restarting Container"
    stop
    sleep 2
    run
}

# Function to enter the container shell
shell() {
    if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
        docker exec -it $CONTAINER_NAME /bin/bash
    else
        print_error "Container $CONTAINER_NAME is not running"
        exit 1
    fi
}

# Function to clean up
clean() {
    print_header "Cleaning Up"
    
    # Stop and remove container
    if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
        docker stop $CONTAINER_NAME
    fi
    
    if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
        docker rm $CONTAINER_NAME
    fi
    
    # Remove image
    if [ "$(docker images -q $IMAGE_NAME)" ]; then
        print_status "Removing Docker image..."
        docker rmi $IMAGE_NAME
    fi
    
    print_status "Cleanup completed"
}

# Function to show help
help() {
    echo "Project Management Bot - Docker Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build      Build the Docker image"
    echo "  run        Run the container"
    echo "  compose    Start with docker-compose"
    echo "  down       Stop docker-compose services"
    echo "  test       Run in test mode"
    echo "  logs       Show container logs"
    echo "  status     Show container status"
    echo "  stop       Stop the container"
    echo "  restart    Restart the container"
    echo "  shell      Enter container shell"
    echo "  clean      Remove container and image"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build && $0 run    # Build and run"
    echo "  $0 logs               # Follow logs"
    echo "  $0 test               # Test configuration"
    echo ""
}

# Main script logic
case "${1:-help}" in
    build)
        build
        ;;
    run)
        run
        ;;
    compose)
        compose_up
        ;;
    down)
        compose_down
        ;;
    test)
        test
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    shell)
        shell
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        help
        ;;
    *)
        print_error "Unknown command: $1"
        help
        exit 1
        ;;
esac 