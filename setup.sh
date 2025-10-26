#!/bin/bash
# Quick setup script for XR ECG Twin project

echo "XR ECG Twin - Quick Setup"
echo "=============================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "WARNING: Please edit .env file and change default passwords!"
    echo ""
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not found. Please install Docker first."
    echo "Install with: sudo apt install docker.io"
    exit 1
fi

echo "Docker found"
echo ""

# Check for docker-compose (old style) or docker compose (new plugin)
COMPOSE_CMD=""
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "ERROR: Docker Compose not found."
    echo ""
    echo "Install with one of:"
    echo "  sudo apt install docker-compose"
    echo "  OR"
    echo "  sudo apt install docker-compose-plugin"
    echo ""
    exit 1
fi

echo "Using: $COMPOSE_CMD"
echo ""

echo "Building Docker images..."
$COMPOSE_CMD build

echo ""
echo "Starting services..."
$COMPOSE_CMD up -d

echo ""
echo "Waiting for services to be ready..."
sleep 15

echo ""
echo "Running database migrations..."
$COMPOSE_CMD exec -T gateway python manage.py migrate 2>/dev/null || echo "Gateway migrations will run on first start"
$COMPOSE_CMD exec -T ecg-service python manage.py migrate 2>/dev/null || echo "ECG service migrations will run on first start"
$COMPOSE_CMD exec -T iot-service python manage.py migrate 2>/dev/null || echo "IoT service migrations will run on first start"

echo ""
echo "Setup complete!"
echo ""
echo "Services are running:"
echo "  - API Gateway:  http://localhost:8000"
echo "  - ECG Service:  http://localhost:8001"
echo "  - IoT Service:  http://localhost:8002"
echo "  - Frontend:     http://localhost:3000"
echo "  - MQTT Broker:  mqtt://localhost:1883"
echo ""
echo "Check health:"
echo "  curl http://localhost:8000/health/"
echo ""
echo "View logs:"
echo "  $COMPOSE_CMD logs -f"
echo ""
echo "Stop services:"
echo "  $COMPOSE_CMD down"
echo ""
