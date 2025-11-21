#!/bin/bash
# Build and push Docker image to Azure Container Registry

set -e

REGISTRY="fastapiobs.azurecr.io"
IMAGE_NAME="obs-sftp-file-processor"
IMAGE_TAG="${1:-latest}"
FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "=========================================="
echo "Building Docker Image for Azure ACR"
echo "=========================================="
echo ""
echo "Registry: ${REGISTRY}"
echo "Image: ${FULL_IMAGE_NAME}"
echo ""

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
echo ""

# Build the Docker image
echo "Building Docker image..."
docker build --platform linux/amd64 -t "${FULL_IMAGE_NAME}" .

if [ $? -ne 0 ]; then
    echo "ERROR: Docker build failed"
    exit 1
fi

echo "✓ Docker image built successfully"
echo ""

# Verify Oracle is in the image
echo "Verifying Oracle Instant Client in image..."
docker run --rm "${FULL_IMAGE_NAME}" sh -c 'ls -la /opt/oracle/instantclient_23_3/libclntsh.so*' > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✓ Oracle Instant Client verified in image"
else
    echo "WARNING: Could not verify Oracle Instant Client in image"
fi

echo ""
echo "=========================================="
echo "Build Complete!"
echo "=========================================="
echo ""
echo "Image: ${FULL_IMAGE_NAME}"
echo "Size: $(docker images ${FULL_IMAGE_NAME} --format '{{.Size}}')"
echo ""
echo "Next steps to push to Azure Container Registry:"
echo ""
echo "1. Login to Azure Container Registry:"
echo "   az acr login --name fastapiobs"
echo ""
echo "   OR using Docker:"
echo "   docker login ${REGISTRY} -u fastapiobs"
echo ""
echo "2. Push the image:"
echo "   docker push ${FULL_IMAGE_NAME}"
echo ""
echo "3. Verify in Azure Portal:"
echo "   https://portal.azure.com → fastapiobs → Repositories → ${IMAGE_NAME}"
echo ""

