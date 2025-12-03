#!/bin/bash

# Build and export Docker images for offline installation
# Usage: ./docker-build.sh

set -e

IMAGE_TAG="gpu-portal"
OUTPUT_DIR="./docker-export"
TAR_FILE="gpu-portal-docker.tar"

echo "=== GPU Portal Docker Build Script ==="
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Build images using docker-compose
echo "[1/4] Building Docker images..."
docker-compose build

# Tag images with consistent names
echo "[2/4] Tagging images..."
docker tag haidianrobot-backend:latest ${IMAGE_TAG}-backend:latest
docker tag haidianrobot-frontend:latest ${IMAGE_TAG}-frontend:latest

# Save images to tar file
echo "[3/4] Exporting images to ${OUTPUT_DIR}/${TAR_FILE}..."
docker save -o "${OUTPUT_DIR}/${TAR_FILE}" \
    ${IMAGE_TAG}-backend:latest \
    ${IMAGE_TAG}-frontend:latest

# Copy docker-compose file and create install script
echo "[4/4] Creating installation package..."

cat > "${OUTPUT_DIR}/docker-compose.yml" << 'COMPOSE'
version: '3.8'

services:
  backend:
    image: gpu-portal-backend:latest
    container_name: gpu-portal-backend
    environment:
      - DATABASE_PATH=/data/portal.db
    volumes:
      - ./data:/data
    ports:
      - "8000:8000"
    restart: unless-stopped

  frontend:
    image: gpu-portal-frontend:latest
    container_name: gpu-portal-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
COMPOSE

cat > "${OUTPUT_DIR}/install.sh" << 'INSTALL'
#!/bin/bash

# GPU Portal Installation Script
# Run this on the target machine to install from offline package

set -e

echo "=== GPU Portal Installation ==="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Load images
echo "[1/3] Loading Docker images..."
docker load -i gpu-portal-docker.tar

# Create data directory
echo "[2/3] Creating data directory..."
mkdir -p ./data

# Start services
echo "[3/3] Starting services..."
docker-compose up -d

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Frontend: http://localhost"
echo "Backend API: http://localhost:8000"
echo ""
echo "Default admin login:"
echo "  Phone: 13800000000"
echo "  Password: DongSheng2025#"
echo ""
echo "Commands:"
echo "  Start:   docker-compose up -d"
echo "  Stop:    docker-compose down"
echo "  Logs:    docker-compose logs -f"
echo "  Status:  docker-compose ps"
INSTALL

chmod +x "${OUTPUT_DIR}/install.sh"

# Create README
cat > "${OUTPUT_DIR}/README.txt" << 'README'
GPU Portal - Offline Installation Package
==========================================

Contents:
- gpu-portal-docker.tar  : Docker images
- docker-compose.yml     : Service configuration
- install.sh            : Installation script

Requirements:
- Docker
- docker-compose

Installation:
1. Copy this folder to target machine
2. Run: ./install.sh

Manual Installation:
1. docker load -i gpu-portal-docker.tar
2. mkdir -p ./data
3. docker-compose up -d

Access:
- Web UI: http://localhost
- API: http://localhost:8000

Default Admin:
- Phone: 13800000000
- Password: DongSheng2025#

Data Persistence:
- Database is stored in ./data/portal.db
- Backup ./data folder to preserve data
README

# Calculate size
TAR_SIZE=$(du -h "${OUTPUT_DIR}/${TAR_FILE}" | cut -f1)

echo ""
echo "=== Build Complete ==="
echo ""
echo "Output directory: ${OUTPUT_DIR}"
echo "Image archive: ${TAR_FILE} (${TAR_SIZE})"
echo ""
echo "To install on another machine:"
echo "  1. Copy the '${OUTPUT_DIR}' folder to target machine"
echo "  2. Run: cd ${OUTPUT_DIR} && ./install.sh"
