#!/bin/bash
# Build and deploy Portainer Docker image to deployment folder

set -e

TARGET_DIR="/Users/dougearp/Desktop/Deploy OBS"
IMAGE_NAME="obs-sftp-file-processor:portainer-v3"
TAR_FILE="obs-sftp-file-processor-portainer-v3.tar"

echo "=========================================="
echo "Building and Deploying Portainer Image"
echo "=========================================="

# Check Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "ERROR: Docker daemon is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Run the build script
echo ""
echo "Step 1: Building Docker image..."
./build-portainer-image.sh

# Check if build was successful
if [ ! -f "$TAR_FILE" ]; then
    echo "ERROR: Build failed - $TAR_FILE not found"
    exit 1
fi

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Copy file to target directory
echo ""
echo "Step 2: Copying image to deployment folder..."
cp "$TAR_FILE" "$TARGET_DIR/"

if [ $? -eq 0 ]; then
    FILE_SIZE=$(du -h "$TARGET_DIR/$TAR_FILE" | cut -f1)
    echo "✓ Image copied successfully"
    echo ""
    echo "=========================================="
    echo "✓ Task Complete!"
    echo "=========================================="
    echo "Image file location:"
    echo "  $TARGET_DIR/$TAR_FILE"
    echo ""
    echo "File size: $FILE_SIZE"
    echo ""
    echo "Includes latest changes:"
    echo "  - .DAT file format support (Watertown format)"
    echo "  - ORA-04036 fix for ACH_FILES_BLOBS creation"
    echo "  - Optional 'user' parameter for UPDATED_BY_USER"
    echo "  - Optional 'processing_status' parameter"
    echo "  - SFTP auto-reconnect fixes"
    echo "  - Oracle Instant Client included"
    echo ""
    echo "Ready for Portainer deployment!"
else
    echo "ERROR: Failed to copy image file"
    exit 1
fi

