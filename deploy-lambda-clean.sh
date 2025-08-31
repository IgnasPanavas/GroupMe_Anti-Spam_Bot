#!/bin/bash

# Configuration
AWS_REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPOSITORY_NAME="spamshield-api"
IMAGE_TAG="latest"

echo "🚀 Deploying SpamShield API to AWS Lambda Container Images..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon not running. Please start Docker first."
    exit 1
fi

# Create ECR repository if it doesn't exist
echo "📦 Creating ECR repository..."
aws ecr describe-repositories --repository-names $REPOSITORY_NAME --region $AWS_REGION 2>/dev/null || \
aws ecr create-repository --repository-name $REPOSITORY_NAME --region $AWS_REGION

# Get ECR login token
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build the Docker image for single platform only
echo "🏗️ Building Docker image for linux/amd64 only..."
if ! docker buildx build --platform linux/amd64 --load -f api/Dockerfile.lambda -t $REPOSITORY_NAME:$IMAGE_TAG .; then
    echo "❌ Docker build failed!"
    exit 1
fi

# Tag the image for ECR
echo "🏷️ Tagging image for ECR..."
if ! docker tag $REPOSITORY_NAME:$IMAGE_TAG $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:$IMAGE_TAG; then
    echo "❌ Docker tag failed!"
    exit 1
fi

# Push the image to ECR
echo "📤 Pushing image to ECR..."
if ! docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:$IMAGE_TAG; then
    echo "❌ Docker push failed!"
    exit 1
fi

# Wait a moment for ECR to process the image
echo "⏳ Waiting for ECR to process the image..."
sleep 20

# Create Lambda function
FUNCTION_NAME="spamshield-api"
echo "🔧 Creating Lambda function..."

# Delete existing function if it exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $AWS_REGION &> /dev/null; then
    echo "🗑️ Deleting existing Lambda function..."
    aws lambda delete-function --function-name $FUNCTION_NAME --region $AWS_REGION
    sleep 10
fi

echo "🆕 Creating new Lambda function..."
aws lambda create-function \
    --function-name $FUNCTION_NAME \
    --package-type Image \
    --code ImageUri=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPOSITORY_NAME:$IMAGE_TAG \
    --role arn:aws:iam::$ACCOUNT_ID:role/lambda-execution-role \
    --timeout 30 \
    --memory-size 1024 \
    --region $AWS_REGION \
    --architectures x86_64

echo "✅ Deployment complete!"
echo "🔗 Lambda Function: $FUNCTION_NAME"
echo "🔗 ECR Repository: $REPOSITORY_NAME"
echo ""
echo "📋 Next steps:"
echo "1. Set up API Gateway integration"
echo "2. Test the Lambda function"
echo "3. Update your frontend's REACT_APP_API_URL"
