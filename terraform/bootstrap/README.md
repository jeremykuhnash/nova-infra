# Terraform Backend Bootstrap

This bootstrap configuration creates the necessary S3 bucket and DynamoDB table for Terraform remote state management. It works in ANY AWS account with AdministratorAccess.

## Features

- ✅ **Account-agnostic**: Automatically detects account ID and region
- ✅ **Unique naming**: Generates unique bucket names using account ID
- ✅ **Security**: Enables encryption, versioning, and blocks public access
- ✅ **State locking**: Creates DynamoDB table for concurrent access protection
- ✅ **Zero manual steps**: Everything is created via Terraform

## Usage

### Step 1: Create Backend Resources

```bash
cd bootstrap
terraform init
terraform apply

# Note the outputs - they contain your backend configuration
```

### Step 2: Configure Main Terraform

The bootstrap will output the exact backend configuration to use. Copy it to your main `backend.tf` file.

### Step 3: Initialize Main Terraform

```bash
cd ..
terraform init
```

## What Gets Created

1. **S3 Bucket**: `nova-infra-{ACCOUNT_ID}-{REGION}-tfstate`
   - Versioning enabled for state history
   - Server-side encryption (AES256)
   - All public access blocked

2. **DynamoDB Table**: `nova-infra-terraform-lock`
   - Pay-per-request billing (no capacity planning needed)
   - Used for state locking during concurrent operations

## Customization

You can override defaults using variables:

```bash
terraform apply -var="prefix=mycompany" -var="aws_region=eu-west-1"
```

Or create a `terraform.tfvars` file:

```hcl
prefix     = "mycompany"
aws_region = "eu-west-1"
state_key  = "prod/terraform.tfstate"
```

## Clean Up

To destroy the backend resources (WARNING: This will delete your state!):

```bash
terraform destroy
```

## Notes

- The bucket name includes the AWS account ID to ensure global uniqueness
- This bootstrap configuration uses local state (no chicken-and-egg problem)
- Works in any AWS account with AdministratorAccess
- No hardcoded account IDs or manual AWS CLI commands needed
