terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS Region hosting Bedrock foundation models"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Deployment environment"
}

provider "aws" {
  region = var.aws_region
}

# Least-privilege IAM Role for LegacyLens AI ECS / EKS Task
resource "aws_iam_role" "legacylens_execution_role" {
  name = "legacylens-ai-execution-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "bedrock_access" {
  name        = "legacylens-bedrock-access-${var.environment}"
  description = "Least privilege access to Amazon Bedrock models for LegacyLens AI"
  policy      = file("${path.module}/../bedrock-iam-policy.json")
}

resource "aws_iam_role_policy_attachment" "attach_bedrock" {
  role       = aws_iam_role.legacylens_execution_role.name
  policy_arn = aws_iam_policy.bedrock_access.arn
}

output "execution_role_arn" {
  value       = aws_iam_role.legacylens_execution_role.arn
  description = "ARN of the IAM role configured with Bedrock access"
}
