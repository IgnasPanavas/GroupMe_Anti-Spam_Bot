#!/bin/bash

# Configuration
AWS_REGION="us-east-1"
API_NAME="spamshield-api-gateway"
FUNCTION_NAME="spamshield-api"

echo "🌐 Setting up API Gateway for Lambda function..."

# Create REST API
echo "📦 Creating REST API..."
API_ID=$(aws apigateway create-rest-api \
    --name $API_NAME \
    --description "SpamShield API Gateway" \
    --region $AWS_REGION \
    --query 'id' --output text)

echo "✅ API Gateway created with ID: $API_ID"

# Get the root resource ID
echo "🔍 Getting root resource ID..."
ROOT_RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region $AWS_REGION \
    --query 'items[?path==`/`].id' --output text)

echo "✅ Root resource ID: $ROOT_RESOURCE_ID"

# Create API resource
echo "📝 Creating API resource..."
RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_RESOURCE_ID \
    --path-part "{proxy+}" \
    --region $AWS_REGION \
    --query 'id' --output text)

echo "✅ Resource created with ID: $RESOURCE_ID"

# Create ANY method
echo "🔧 Creating ANY method..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method ANY \
    --authorization-type NONE \
    --region $AWS_REGION

# Set up Lambda integration
echo "🔗 Setting up Lambda integration..."
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method ANY \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:$AWS_REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):function:$FUNCTION_NAME/invocations \
    --region $AWS_REGION

# Add Lambda permission for API Gateway
echo "🔐 Adding Lambda permission..."
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id apigateway-access \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/*/*" \
    --region $AWS_REGION

# Deploy the API
echo "🚀 Deploying API..."
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region $AWS_REGION

echo "✅ API Gateway setup complete!"
echo "🔗 Your API URL: https://$API_ID.execute-api.$AWS_REGION.amazonaws.com/prod/"
echo ""
echo "📋 Next steps:"
echo "1. Test the API endpoint"
echo "2. Update your frontend's REACT_APP_API_URL"
echo "3. Configure CORS if needed"
