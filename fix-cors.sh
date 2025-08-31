#!/bin/bash

# Configuration
AWS_REGION="us-east-1"
API_ID="gr9ivpz244"
RESOURCE_ID="l2kley"

echo "🔧 Fixing CORS configuration in API Gateway..."

# Get the resource ID for the proxy resource
echo "📝 Getting resource ID..."
RESOURCE_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region $AWS_REGION \
    --query 'items[?path==`/{proxy+}`].id' --output text)

echo "✅ Resource ID: $RESOURCE_ID"

# Add OPTIONS method for CORS
echo "🔧 Adding OPTIONS method..."
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --authorization-type NONE \
    --region $AWS_REGION

# Set up OPTIONS integration (mock response)
echo "🔗 Setting up OPTIONS integration..."
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --type MOCK \
    --request-templates '{"application/json":"{\"statusCode\": 200}"}' \
    --region $AWS_REGION

# Add method response for OPTIONS
echo "📤 Adding method response for OPTIONS..."
aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Origin":true,"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true}' \
    --region $AWS_REGION

# Add integration response for OPTIONS
echo "📥 Adding integration response for OPTIONS..."
aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method OPTIONS \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'\''*'\''","method.response.header.Access-Control-Allow-Headers":"'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''","method.response.header.Access-Control-Allow-Methods":"'\''GET,POST,PUT,DELETE,OPTIONS'\''"}' \
    --region $AWS_REGION

# Update ANY method response to include CORS headers
echo "🔧 Updating ANY method response..."
aws apigateway put-method-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method ANY \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Origin":true,"method.response.header.Access-Control-Allow-Headers":true,"method.response.header.Access-Control-Allow-Methods":true}' \
    --region $AWS_REGION

# Update integration response for ANY method
echo "📥 Updating integration response for ANY method..."
aws apigateway put-integration-response \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method ANY \
    --status-code 200 \
    --response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'\''*'\''","method.response.header.Access-Control-Allow-Headers":"'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''","method.response.header.Access-Control-Allow-Methods":"'\''GET,POST,PUT,DELETE,OPTIONS'\''"}' \
    --region $AWS_REGION

# Deploy the API
echo "🚀 Deploying updated API..."
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region $AWS_REGION

echo "✅ CORS configuration updated!"
echo "🔗 Your API URL: https://$API_ID.execute-api.$AWS_REGION.amazonaws.com/prod/"
echo ""
echo "📋 Test with:"
echo "curl -X OPTIONS https://$API_ID.execute-api.$AWS_REGION.amazonaws.com/prod/api/stats"
