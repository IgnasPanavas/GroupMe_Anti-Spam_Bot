#!/bin/bash

echo "🚀 Deploying SpamShield to AWS S3..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Please run this script from the spamshield-frontend directory"
    exit 1
fi

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first:"
    echo "   https://aws.amazon.com/cli/"
    exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run:"
    echo "   aws configure"
    exit 1
fi

# Build the React app
echo "📦 Building React app..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful!"

# S3 bucket name (you'll need to create this)
BUCKET_NAME="spamshield-ignaspanavas-com"

# Create S3 bucket if it doesn't exist
echo "🪣 Creating S3 bucket..."
aws s3 mb s3://$BUCKET_NAME --region us-east-1

# Upload files to S3
echo "📤 Uploading files to S3..."
aws s3 sync build/ s3://$BUCKET_NAME --delete

# Configure bucket for static website hosting
echo "🌐 Configuring static website hosting..."
aws s3 website s3://$BUCKET_NAME --index-document index.html --error-document index.html

# Set bucket policy for public read access
echo "🔓 Setting bucket policy..."
cat > bucket-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
        }
    ]
}
EOF

aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://bucket-policy.json

# Clean up
rm bucket-policy.json

echo ""
echo "🎉 Deployment successful!"
echo ""
echo "📋 Next steps:"
echo "1. Set up CloudFront distribution (optional, for HTTPS)"
echo "2. Configure Route 53 for spamshield.ignaspanavas.com"
echo "3. Point DNS to S3 bucket or CloudFront distribution"
echo ""
echo "🔗 Your site URL: http://$BUCKET_NAME.s3-website-us-east-1.amazonaws.com"
echo ""
echo "💡 For production, consider:"
echo "   - Setting up CloudFront for HTTPS"
echo "   - Using Route 53 for DNS management"
echo "   - Setting up CI/CD pipeline"
