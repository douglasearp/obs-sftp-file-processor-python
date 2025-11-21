#!/bin/bash
# Build script for Portainer Docker image with Oracle Instant Client included

set -e

echo "=========================================="
echo "Building Docker Image for Portainer"
echo "=========================================="

# Check if Oracle Instant Client exists
if [ ! -d "oracle/instantclient_23_3" ]; then
    echo "ERROR: Oracle Instant Client not found at oracle/instantclient_23_3"
    echo "Please ensure Oracle Instant Client is extracted in the oracle/ directory"
    exit 1
fi

# Verify Oracle libraries exist
if [ ! -f "oracle/instantclient_23_3/libclntsh.so" ]; then
    echo "ERROR: Oracle library libclntsh.so not found"
    echo "Please verify Oracle Instant Client is correctly extracted"
    exit 1
fi

echo "✓ Oracle Instant Client found"

# Build the Docker image
echo ""
echo "Building Docker image..."
docker build --platform linux/amd64 -t obs-sftp-file-processor:portainer-v2 .

if [ $? -ne 0 ]; then
    echo "ERROR: Docker build failed"
    exit 1
fi

echo "✓ Docker image built successfully"

# Verify Oracle is in the image
echo ""
echo "Verifying Oracle Instant Client in image..."
docker run --rm obs-sftp-file-processor:portainer-v2 ls -la /opt/oracle/instantclient_23_3/libclntsh.so* > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Oracle Instant Client verified in image"
else
    echo "WARNING: Could not verify Oracle Instant Client in image"
fi

# Export the image
echo ""
echo "Exporting Docker image to tar file..."
OUTPUT_FILE="obs-sftp-file-processor-portainer-v2.tar"
docker save obs-sftp-file-processor:portainer-v2 -o "$OUTPUT_FILE"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to export image"
    exit 1
fi

# Get file size
FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
echo "✓ Image exported to $OUTPUT_FILE ($FILE_SIZE)"

echo ""
echo "=========================================="
echo "Build Complete!"
echo "=========================================="
echo ""
echo "Image: obs-sftp-file-processor:portainer-v2"
echo "File:  $OUTPUT_FILE"
echo ""
echo "Next steps:"
echo "1. Upload $OUTPUT_FILE to Portainer"
echo "2. Import it in Portainer UI (Images → Import image from file)"
echo "3. Deploy container using the imported image"
echo "4. Set environment variables (ORACLE_HOME, ORACLE_HOST, etc.)"
echo "5. NO bind mount needed - Oracle is in the image!"
echo ""


