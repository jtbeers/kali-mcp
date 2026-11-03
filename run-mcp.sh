#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="kali-mcp"
IMAGE_NAME="kali-mcp:latest"
WORKSPACE_DIR="$DIR/workspace"

mkdir -p "$WORKSPACE_DIR"

# Ensure image exists
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo "[kali-mcp] Image $IMAGE_NAME not found. Building image from Dockerfile..." >&2
    docker build -t "$IMAGE_NAME" "$DIR" >&2
fi

# Ephemeral mode if requested via argument
if [ "$1" = "--ephemeral" ]; then
    exec docker run -i --rm \
        --cap-add=NET_RAW \
        --cap-add=NET_ADMIN \
        -v "$WORKSPACE_DIR:/workspace" \
        -w /workspace \
        "$IMAGE_NAME" \
        python3 /app/server.py
fi

# Persistent container mode (default)
# Check if container is already running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    # If container exists but stopped, start it
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        docker start "$CONTAINER_NAME" >/dev/null 2>&1
    else
        # Create and start persistent container running in the background
        docker run -d \
            --name "$CONTAINER_NAME" \
            --restart unless-stopped \
            --cap-add=NET_RAW \
            --cap-add=NET_ADMIN \
            -v "$WORKSPACE_DIR:/workspace" \
            -w /workspace \
            "$IMAGE_NAME" \
            tail -f /dev/null >/dev/null 2>&1
    fi
fi

# Connect MCP server over stdio inside the running container
exec docker exec -i "$CONTAINER_NAME" python3 /app/server.py
