#!/bin/bash
# Initialize Terraform Backend Resources
# This script creates the S3 bucket and DynamoDB table needed for Terraform state management

set -e

echo "==================================="
echo "Terraform Backend Initialization"
echo "==================================="

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "❌ Error: Unable to get AWS account ID. Please configure AWS credentials."
    echo "Run: aws configure"
    exit 1
fi

# Bucket and table names
BUCKET_NAME="nova-infra-${AWS_ACCOUNT_ID}-${AWS_REGION}-tfstate"
DYNAMODB_TABLE="nova-infra-terraform-state-lock"

echo ""
echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo "S3 Bucket: $BUCKET_NAME"
echo "DynamoDB Table: $DYNAMODB_TABLE"
echo ""

# Check if S3 bucket exists
echo "Checking S3 bucket..."
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "✅ S3 bucket already exists: $BUCKET_NAME"
else
    echo "Creating S3 bucket: $BUCKET_NAME"

    # Create bucket with proper settings based on region
    if [ "$AWS_REGION" = "us-east-1" ]; then
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$AWS_REGION"
    else
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$AWS_REGION" \
            --create-bucket-configuration LocationConstraint="$AWS_REGION"
    fi

    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "$BUCKET_NAME" \
        --versioning-configuration Status=Enabled

    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket "$BUCKET_NAME" \
        --server-side-encryption-configuration '{
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }'

    # Block public access
    aws s3api put-public-access-block \
        --bucket "$BUCKET_NAME" \
        --public-access-block-configuration \
            "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

    echo "✅ S3 bucket created successfully"
fi

# Check if DynamoDB table exists
echo ""
echo "Checking DynamoDB table..."
if aws dynamodb describe-table --table-name "$DYNAMODB_TABLE" --region "$AWS_REGION" 2>/dev/null > /dev/null; then
    echo "✅ DynamoDB table already exists: $DYNAMODB_TABLE"
else
    echo "Creating DynamoDB table: $DYNAMODB_TABLE"

    aws dynamodb create-table \
        --table-name "$DYNAMODB_TABLE" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$AWS_REGION"

    # Wait for table to be active
    echo "Waiting for DynamoDB table to be active..."
    aws dynamodb wait table-exists --table-name "$DYNAMODB_TABLE" --region "$AWS_REGION"

    echo "✅ DynamoDB table created successfully"
fi

# Create backend.tf file if it doesn't exist
BACKEND_FILE="backend.tf"
if [ ! -f "$BACKEND_FILE" ]; then
    echo ""
    echo "Creating backend.tf configuration..."
    cat > "$BACKEND_FILE" <<EOB
terraform {
  backend "s3" {
    bucket         = "$BUCKET_NAME"
    key            = "tf-visualizer/terraform.tfstate"
    region         = "$AWS_REGION"
    dynamodb_table = "$DYNAMODB_TABLE"
    encrypt        = true
  }
}
EOB
    echo "✅ Created backend.tf"
else
    echo ""
    echo "✅ backend.tf already exists"
fi

echo ""
echo "==================================="
echo "✅ Backend initialization complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Run: terraform init"
echo "2. Run: terraform plan"
echo "3. Run: terraform apply"
echo ""
echo "To use this backend in CI/CD, set:"
echo "  TF_STATE_BUCKET=$BUCKET_NAME"
echo "  TF_STATE_DYNAMODB_TABLE=$DYNAMODB_TABLE"
