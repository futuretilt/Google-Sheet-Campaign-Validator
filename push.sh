#!/bin/bash

# ECR Configuration
ECR_REGISTRY="992382592846.dkr.ecr.us-east-2.amazonaws.com"
ECR_REPOSITORY="trello-lambda-test"
IMAGE_TAG="latest"
AWS_REGION="us-east-2"

echo "========================================="
echo "Deploying Lambda Function to ECR"
echo "========================================="

# Step 1: Authenticate Docker to ECR
echo ""
echo "Step 1: Authenticating with ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

if [ $? -ne 0 ]; then
    echo "❌ Failed to authenticate with ECR"
    exit 1
fi
echo "Successfully authenticated with ECR"

# Step 2: Build Docker image
echo ""
echo "Step 2: Building Docker image..."
docker build -t $ECR_REPOSITORY:$IMAGE_TAG .

if [ $? -ne 0 ]; then
    echo "❌ Failed to build Docker image"
    exit 1
fi
echo "Docker image built successfully"

# Step 3: Tag the image for ECR
echo ""
echo "Step 3: Tagging image for ECR..."
docker tag $ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

if [ $? -ne 0 ]; then
    echo "❌ Failed to tag Docker image"
    exit 1
fi
echo "Image tagged successfully"

# Step 4: Push to ECR
echo ""
echo "Step 4: Pushing image to ECR..."
docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

if [ $? -ne 0 ]; then
    echo "❌ Failed to push image to ECR"
    exit 1
fi
echo "Image pushed successfully to ECR"

# Step 5: Get the image digest
echo ""
echo "Step 5: Getting image details..."
IMAGE_DIGEST=$(aws ecr describe-images --repository-name $ECR_REPOSITORY --region $AWS_REGION --image-ids imageTag=$IMAGE_TAG --query 'imageDetails[0].imageDigest' --output text)

echo ""
echo "========================================="
echo "DEPLOYMENT SUCCESSFUL!"
echo "========================================="
echo "Repository: $ECR_REGISTRY/$ECR_REPOSITORY"
echo "Tag: $IMAGE_TAG"
echo "Digest: $IMAGE_DIGEST"
echo "Full URI: $ECR_REGISTRY/$ECR_REPOSITORY@$IMAGE_DIGEST"
echo ""
echo "To update your Lambda function with this image:"
echo "aws lambda update-function-code --function-name YOUR_FUNCTION_NAME --image-uri $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG --region $AWS_REGION"
echo "========================================="