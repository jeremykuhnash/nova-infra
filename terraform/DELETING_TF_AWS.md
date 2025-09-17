# Terraform AWS Resource Deletion Issues & Fixes

## Overview

This document captures issues encountered during AWS resource deletion and outlines necessary Terraform configuration improvements.

## Deletion Issues Encountered

### 1. ECR Repository with Images

**Problem:** ECR repository deletion failed because it contained Docker images

```
Error: ECR Repository (nova-infra) not empty, consider using force_delete
```

**Manual Fix Applied:**

```bash
aws ecr delete-repository --repository-name nova-infra --force --region us-east-1
```

**Terraform Fix Required:**

- Add `force_delete = true` to ECR repository resource in `modules/ecr/main.tf`
- This allows Terraform to delete repositories even when they contain images

### 2. Classic Load Balancer Not Managed by Terraform

**Problem:** A Classic ELB was created by Kubernetes but not tracked in Terraform state

- ELB Name: `a12da48c8c381420992c2d2cee14c638`
- Created by: `k8s-elb-a12da48c8c381420992c2d2cee14c638` security group

**Manual Fix Applied:**

```bash
aws elb delete-load-balancer --load-balancer-name a12da48c8c381420992c2d2cee14c638
```

**Terraform Fix Required:**

- Consider using AWS Load Balancer Controller with proper annotations
- Add lifecycle rules to prevent orphaned resources
- Document that K8s-created resources need manual cleanup

### 3. VPC Deletion Blocked by Hidden Dependencies

**Problem:** VPC couldn't be deleted due to remaining route tables that weren't properly cleaned up

**Dependencies Found:**

- 3 non-main route tables still attached:
  - rtb-06aa02c7cf523253c (nova-infra-dev-private-rt-1)
  - rtb-008a4690169aa7c11 (nova-infra-dev-public-rt)
  - rtb-0b0f560029f8eafb8 (nova-infra-dev-private-rt-2)
- Security groups: k8s-elb-a12da48c8c381420992c2d2cee14c638

**Manual Fix Applied:**

```bash
# Delete route tables
for rt in rtb-06aa02c7cf523253c rtb-008a4690169aa7c11 rtb-0b0f560029f8eafb8; do
  aws ec2 delete-route-table --route-table-id $rt
done

# Delete security groups
aws ec2 delete-security-group --group-id sg-02863e66b5a7c5a66
aws ec2 delete-security-group --group-id sg-075dce3fa13a1a678
```

**Terraform Fix Required:**

- Ensure explicit dependencies between VPC and route tables
- Add proper cleanup order in destroy provisioners
- Consider using `depends_on` for explicit ordering

### 4. Long Deletion Times

**Problem:** EKS node group deletion took 8+ minutes

**Observation:**

- Node group deletion is the longest operation in the destroy process
- No timeout or status feedback in Terraform

**Terraform Fix Required:**

- Add timeouts configuration for EKS resources
- Consider implementing status checks or notifications for long-running operations

## Recommended Terraform Improvements

### 1. Update ECR Module (`modules/ecr/main.tf`)

```hcl
resource "aws_ecr_repository" "main" {
  name                 = var.repository_name
  force_delete         = true  # Add this line
  image_tag_mutability = var.image_tag_mutability

  image_scanning_configuration {
    scan_on_push = var.scan_on_push
  }
}
```

### 2. Add Destroy-Time Provisioners

Consider adding local-exec provisioners to handle K8s-created resources:

```hcl
resource "aws_eks_cluster" "main" {
  # ... existing configuration ...

  provisioner "local-exec" {
    when    = destroy
    command = "kubectl delete svc --all -n default || true"
  }
}
```

### 3. Implement Proper Dependency Chain

```hcl
# In modules/vpc/main.tf
resource "aws_route_table" "private" {
  # ... existing configuration ...

  depends_on = [
    aws_vpc.main
  ]
}

resource "aws_vpc" "main" {
  # ... existing configuration ...

  # Ensure route tables are destroyed first
  lifecycle {
    create_before_destroy = false
  }
}
```

### 4. Add Timeout Configurations

```hcl
resource "aws_eks_node_group" "main" {
  # ... existing configuration ...

  timeouts {
    create = "30m"
    update = "30m"
    delete = "30m"
  }
}
```

### 5. Document Manual Cleanup Requirements

Add to README.md:

```markdown
## Cleanup Notes

- Kubernetes may create AWS resources (ELBs, Security Groups) not managed by Terraform
- Before running `terraform destroy`, ensure all K8s services of type LoadBalancer are deleted
- Check for orphaned resources after destroy:
  - Classic/Application Load Balancers
  - Security Groups with prefix "k8s-"
  - Elastic IPs
```

## Deletion Order for Clean Destroy

The correct order for destroying resources (as discovered):

1. Kubernetes services (to remove load balancers)
2. EKS Node Groups (longest operation, ~8-10 minutes)
3. EKS Cluster
4. ECR Repositories (with force_delete)
5. NAT Gateways
6. Internet Gateway (after NAT gateways)
7. Subnets
8. Route Tables (non-main)
9. Security Groups (non-default)
10. VPC

## Script for Complete Cleanup

```bash
#!/bin/bash
# cleanup_aws_resources.sh

echo "Starting complete AWS resource cleanup..."

# 1. Delete any K8s-created load balancers
for lb in $(aws elb describe-load-balancers --query 'LoadBalancerDescriptions[?starts_with(LoadBalancerName, `a`) || starts_with(LoadBalancerName, `k`)].LoadBalancerName' --output text); do
  echo "Deleting ELB: $lb"
  aws elb delete-load-balancer --load-balancer-name "$lb"
done

# 2. Run Terraform destroy
terraform destroy -auto-approve

# 3. Clean up any remaining resources
# ... (add specific cleanup commands as needed)

echo "Cleanup complete!"
```

## Testing Recommendations

1. **Test destroy in dev environment** before production
2. **Create destroy checklist** for operators
3. **Implement monitoring** for orphaned resources
4. **Add cost alerts** for resources that might be left behind

## Summary

The main issues stem from:

- Resources created by Kubernetes outside of Terraform's control
- Missing `force_delete` flags for resources with content
- Implicit dependencies not properly declared
- No cleanup hooks for K8s-created resources

Implementing the fixes above will ensure cleaner, more reliable resource deletion and prevent orphaned resources that continue to incur costs.
