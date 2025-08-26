#!/bin/bash
# Example script with Google docstring-style annotations

# SERVICE_NAME (str): Name of the service to deploy
# ENVIRONMENT (choice[dev, staging, prod]): Target deployment environment
# VERSION (str): Version tag to deploy. Default: latest
# DRY_RUN (bool): Perform a dry run without making changes. Default: false
# REPLICAS (int): Number of replicas to deploy. Default: 3
# TIMEOUT (float): Deployment timeout in seconds. Default: 30.5

echo "🚀 Deployment Configuration:"
echo "  Service: $SERVICE_NAME"
echo "  Environment: $ENVIRONMENT"
echo "  Version: ${VERSION}"
echo "  Replicas: ${REPLICAS}"
echo "  Timeout: ${TIMEOUT}s"

if [ "$DRY_RUN" = "true" ]; then
    echo ""
    echo "🔍 DRY RUN MODE - No actual deployment will occur"
    echo ""
fi

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    echo "❌ Error: Invalid environment. Must be one of: dev, staging, prod" >&2
    exit 1
fi

echo ""
echo "📦 Deploying $SERVICE_NAME:$VERSION to $ENVIRONMENT environment..."

if [ "$DRY_RUN" != "true" ]; then
    # Simulate deployment with timeout
    echo "  - Starting deployment (timeout: ${TIMEOUT}s)..."
    sleep 1
    echo "  - Scaling to $REPLICAS replicas..."
    sleep 1
    echo ""
    echo "✅ Deployment completed successfully!"
else
    echo ""
    echo "✅ Dry run completed - no changes made"
fi