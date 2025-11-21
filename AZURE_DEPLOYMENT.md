# Azure Container Registry Deployment Guide

## Overview

This guide explains how to build and deploy the `obs-sftp-file-processor` Docker image to Azure Container Registry (ACR).

## Prerequisites

1. **Azure CLI installed** and logged in:
   ```bash
   az login
   ```

2. **Docker installed** and running

3. **Oracle Instant Client** extracted in `oracle/instantclient_23_3/` directory

## Azure Container Registry Details

- **Registry:** `fastapiobs.azurecr.io`
- **Username:** `fastapiobs`
- **Image Name:** `obs-sftp-file-processor`
- **Default Tag:** `latest`

## Quick Start

### Option 1: Use Build Script (Recommended)

```bash
# Build image for Azure
./build-azure.sh

# Or with custom tag
./build-azure.sh v1.0.0
```

### Option 2: Manual Build

```bash
# Build the image
docker build --platform linux/amd64 \
  -t fastapiobs.azurecr.io/obs-sftp-file-processor:latest .

# Verify the image
docker images fastapiobs.azurecr.io/obs-sftp-file-processor:latest
```

## Push to Azure Container Registry

### Step 1: Login to Azure Container Registry

**Using Azure CLI (Recommended):**
```bash
az acr login --name fastapiobs
```

**Using Docker directly:**
```bash
# Get ACR password (if using admin credentials)
az acr credential show --name fastapiobs --query "passwords[0].value" -o tsv

# Login with Docker
docker login fastapiobs.azurecr.io -u fastapiobs -p <password>
```

**Using Service Principal (Production):**
```bash
# Set environment variables
export AZURE_CLIENT_ID="<service-principal-id>"
export AZURE_CLIENT_SECRET="<service-principal-secret>"
export AZURE_TENANT_ID="<tenant-id>"

# Login
az login --service-principal -u $AZURE_CLIENT_ID -p $AZURE_CLIENT_SECRET --tenant $AZURE_TENANT_ID
az acr login --name fastapiobs
```

### Step 2: Push the Image

```bash
# Push latest tag
docker push fastapiobs.azurecr.io/obs-sftp-file-processor:latest

# Or push with specific tag
docker push fastapiobs.azurecr.io/obs-sftp-file-processor:v1.0.0
```

### Step 3: Verify in Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Container Registry: `fastapiobs`
3. Go to **Repositories** → `obs-sftp-file-processor`
4. Verify the image appears with the correct tag

## Image Details

**Image Name:** `fastapiobs.azurecr.io/obs-sftp-file-processor:latest`

**Includes:**
- ✅ Oracle Instant Client (thick mode support)
- ✅ All Python dependencies
- ✅ FastAPI application
- ✅ Startup Oracle connection test
- ✅ SFTP archived folder creation

**Environment Variables Required:**
- `ORACLE_HOME=/opt/oracle/instantclient_23_3` (already set in image)
- `ORACLE_HOST` - Oracle database host
- `ORACLE_PORT` - Oracle database port (default: 1521)
- `ORACLE_SERVICE_NAME` - Oracle service name
- `ORACLE_USERNAME` - Oracle username
- `ORACLE_PASSWORD` - Oracle password
- `ORACLE_SCHEMA` - Oracle schema (default: ACHOWNER)
- `SFTP_HOST` - SFTP server host
- `SFTP_PORT` - SFTP server port
- `SFTP_USERNAME` - SFTP username
- `SFTP_PASSWORD` - SFTP password

## Deploy to Azure Container Instances (ACI)

### Using Azure CLI

```bash
az container create \
  --resource-group <your-resource-group> \
  --name obs-sftp-file-processor \
  --image fastapiobs.azurecr.io/obs-sftp-file-processor:latest \
  --registry-login-server fastapiobs.azurecr.io \
  --registry-username fastapiobs \
  --registry-password <acr-password> \
  --dns-name-label obs-sftp-processor \
  --ports 8000 \
  --environment-variables \
    ORACLE_HOST=10.1.0.111 \
    ORACLE_PORT=1521 \
    ORACLE_SERVICE_NAME=PDB_ACHDEV01.privatesubnet1.obsnetwork1.oraclevcn.com \
    ORACLE_USERNAME=achowner \
    ORACLE_PASSWORD=<password> \
    ORACLE_SCHEMA=ACHOWNER \
    SFTP_HOST=10.1.3.123 \
    SFTP_PORT=2022 \
    SFTP_USERNAME=6001_obstest \
    SFTP_PASSWORD=<password>
```

## Deploy to Azure App Service

### Using Azure CLI

```bash
# Create App Service plan (if not exists)
az appservice plan create \
  --name obs-sftp-plan \
  --resource-group <your-resource-group> \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group <your-resource-group> \
  --plan obs-sftp-plan \
  --name obs-sftp-file-processor \
  --deployment-container-image-name fastapiobs.azurecr.io/obs-sftp-file-processor:latest

# Configure ACR credentials
az webapp config container set \
  --name obs-sftp-file-processor \
  --resource-group <your-resource-group> \
  --docker-custom-image-name fastapiobs.azurecr.io/obs-sftp-file-processor:latest \
  --docker-registry-server-url https://fastapiobs.azurecr.io \
  --docker-registry-server-user fastapiobs \
  --docker-registry-server-password <acr-password>

# Set environment variables
az webapp config appsettings set \
  --resource-group <your-resource-group> \
  --name obs-sftp-file-processor \
  --settings \
    ORACLE_HOST=10.1.0.111 \
    ORACLE_PORT=1521 \
    ORACLE_SERVICE_NAME=PDB_ACHDEV01.privatesubnet1.obsnetwork1.oraclevcn.com \
    ORACLE_USERNAME=achowner \
    ORACLE_PASSWORD=<password> \
    ORACLE_SCHEMA=ACHOWNER \
    SFTP_HOST=10.1.3.123 \
    SFTP_PORT=2022 \
    SFTP_USERNAME=6001_obstest \
    SFTP_PASSWORD=<password>
```

## Deploy to Azure Kubernetes Service (AKS)

### Create Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: obs-sftp-file-processor
spec:
  replicas: 1
  selector:
    matchLabels:
      app: obs-sftp-file-processor
  template:
    metadata:
      labels:
        app: obs-sftp-file-processor
    spec:
      containers:
      - name: obs-sftp-file-processor
        image: fastapiobs.azurecr.io/obs-sftp-file-processor:latest
        ports:
        - containerPort: 8000
        env:
        - name: ORACLE_HOST
          value: "10.1.0.111"
        - name: ORACLE_PORT
          value: "1521"
        - name: ORACLE_SERVICE_NAME
          value: "PDB_ACHDEV01.privatesubnet1.obsnetwork1.oraclevcn.com"
        - name: ORACLE_USERNAME
          valueFrom:
            secretKeyRef:
              name: oracle-secrets
              key: username
        - name: ORACLE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: oracle-secrets
              key: password
        - name: ORACLE_SCHEMA
          value: "ACHOWNER"
        - name: SFTP_HOST
          value: "10.1.3.123"
        - name: SFTP_PORT
          value: "2022"
        - name: SFTP_USERNAME
          value: "6001_obstest"
        - name: SFTP_PASSWORD
          valueFrom:
            secretKeyRef:
              name: sftp-secrets
              key: password
      imagePullSecrets:
      - name: acr-secret
---
apiVersion: v1
kind: Service
metadata:
  name: obs-sftp-file-processor-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: obs-sftp-file-processor
```

### Deploy to AKS

```bash
# Create ACR pull secret
kubectl create secret docker-registry acr-secret \
  --docker-server=fastapiobs.azurecr.io \
  --docker-username=fastapiobs \
  --docker-password=<acr-password> \
  --docker-email=<your-email>

# Create secrets for Oracle and SFTP
kubectl create secret generic oracle-secrets \
  --from-literal=username=achowner \
  --from-literal=password=<oracle-password>

kubectl create secret generic sftp-secrets \
  --from-literal=password=<sftp-password>

# Apply deployment
kubectl apply -f deployment.yaml
```

## Troubleshooting

### Image Push Fails

**Error:** `unauthorized: authentication required`

**Solution:**
```bash
# Re-login to ACR
az acr login --name fastapiobs
```

### Cannot Pull Image

**Error:** `pull access denied`

**Solution:**
- Ensure ACR credentials are configured in your deployment
- For AKS, create image pull secret:
  ```bash
  kubectl create secret docker-registry acr-secret \
    --docker-server=fastapiobs.azurecr.io \
    --docker-username=fastapiobs \
    --docker-password=<password>
  ```

### Oracle Connection Issues

- Verify `ORACLE_HOME` is set (already in image)
- Check network connectivity to Oracle database
- Verify Oracle credentials are correct
- Check Oracle service name format

## Best Practices

1. **Use specific tags** instead of `latest` for production:
   ```bash
   ./build-azure.sh v1.0.0
   docker push fastapiobs.azurecr.io/obs-sftp-file-processor:v1.0.0
   ```

2. **Use Azure Key Vault** for sensitive credentials:
   ```bash
   az keyvault secret set --vault-name <vault-name> --name oracle-password --value <password>
   ```

3. **Enable ACR authentication** with managed identity for AKS:
   ```bash
   az aks update -n <aks-cluster> -g <resource-group> --attach-acr fastapiobs
   ```

4. **Monitor logs** in Azure:
   ```bash
   az container logs --resource-group <rg> --name obs-sftp-file-processor
   ```

## References

- [Azure Container Registry Documentation](https://docs.microsoft.com/azure/container-registry/)
- [Azure Container Instances](https://docs.microsoft.com/azure/container-instances/)
- [Azure App Service for Containers](https://docs.microsoft.com/azure/app-service/containers/)
- [Azure Kubernetes Service](https://docs.microsoft.com/azure/aks/)

