# LegacyLens Infrastructure & Deployment

This directory contains cloud provisioning infrastructure for production deployment on AWS.

## Contents

- `bedrock-iam-policy.json`: Least-privilege IAM policy granting access strictly to authorized Amazon Bedrock models (`anthropic.claude-3-sonnet`, `anthropic.claude-3-haiku`).
- `terraform/main.tf`: Terraform configuration provisioning the ECS task execution role and attaching the Bedrock policy.

## Deployment Steps

```bash
cd infra/terraform
terraform init
terraform plan -var="aws_region=us-east-1"
terraform apply
```
