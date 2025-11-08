#!/bin/bash

# Flask Task Manager - AWS Deployment Script
# This script automates the deployment of the Flask application infrastructure

set -e

echo "🚀 Starting Flask Task Manager Deployment..."

# Configuration 
STACK_NAME="flask-task-manager-stack"
REGION="ap-south-1"
KEY_PAIR="your-keypair-name"
DB_PASSWORD="your-secure-db-password"  

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📋 Deployment Configuration:${NC}"
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "Key Pair: $KEY_PAIR"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if CloudFormation template exists
if [ ! -f "cloudformation-template.yaml" ]; then
    echo -e "${RED}❌ CloudFormation template not found!${NC}"
    exit 1
fi

echo -e "${YELLOW}🔍 Validating CloudFormation template...${NC}"
aws cloudformation validate-template \
    --template-body file://cloudformation-template.yaml \
    --region $REGION

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Template validation successful!${NC}"
else
    echo -e "${RED}❌ Template validation failed!${NC}"
    exit 1
fi

echo -e "${YELLOW}🏗️ Deploying CloudFormation stack...${NC}"
aws cloudformation deploy \
    --template-file cloudformation-template.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        KeyPairName=$KEY_PAIR \
        DBPassword=$DB_PASSWORD \
    --capabilities CAPABILITY_IAM \
    --region $REGION

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Stack deployment successful!${NC}"
    
    echo -e "${YELLOW}📊 Getting stack outputs...${NC}"
    aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --region $REGION \
        --query 'Stacks[0].Outputs'
else
    echo -e "${RED}❌ Stack deployment failed!${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Launch EC2 instances in the created subnets"
echo "2. Create RDS database in private subnets"
echo "3. Configure Application Load Balancer"
echo "4. Deploy Flask application code"
echo ""
echo -e "${GREEN}🌐 Your infrastructure is ready!${NC}"
