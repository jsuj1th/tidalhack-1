# main.tf
# Terraform configuration for AWS infrastructure deployment

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "hackathon-feedback"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "hackathon_id" {
  description = "Hackathon identifier"
  type        = string
  default     = "HACK2024"
}

# Local values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# DynamoDB Table
resource "aws_dynamodb_table" "feedback_table" {
  name           = "${local.name_prefix}-feedback"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "feedback_id"

  attribute {
    name = "feedback_id"
    type = "S"
  }

  attribute {
    name = "hackathon_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  global_secondary_index {
    name     = "hackathon-timestamp-index"
    hash_key = "hackathon_id"
    range_key = "timestamp"
    projection_type = "ALL"
  }

  tags = local.common_tags
}

# S3 Bucket for data backup
resource "aws_s3_bucket" "feedback_backup" {
  bucket = "${local.name_prefix}-data-backup"
  
  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "feedback_backup_versioning" {
  bucket = aws_s3_bucket.feedback_backup.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "feedback_backup_encryption" {
  bucket = aws_s3_bucket.feedback_backup.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${local.name_prefix}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${local.name_prefix}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = [
          aws_dynamodb_table.feedback_table.arn,
          "${aws_dynamodb_table.feedback_table.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.feedback_backup.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda Function
resource "aws_lambda_function" "feedback_processor" {
  filename         = "lambda_deployment.zip"
  function_name    = "${local.name_prefix}-processor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME    = aws_dynamodb_table.feedback_table.name
      S3_BUCKET_NAME         = aws_s3_bucket.feedback_backup.bucket
      CLOUDWATCH_NAMESPACE   = "HackathonFeedback"
      ENVIRONMENT           = var.environment
      HACKATHON_ID          = var.hackathon_id
    }
  }

  tags = local.common_tags
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.feedback_processor.function_name}"
  retention_in_days = 14

  tags = local.common_tags
}

# API Gateway (Optional - for HTTP access)
resource "aws_api_gateway_rest_api" "feedback_api" {
  name        = "${local.name_prefix}-api"
  description = "API for hackathon feedback system"

  tags = local.common_tags
}

resource "aws_api_gateway_resource" "feedback_resource" {
  rest_api_id = aws_api_gateway_rest_api.feedback_api.id
  parent_id   = aws_api_gateway_rest_api.feedback_api.root_resource_id
  path_part   = "feedback"
}

resource "aws_api_gateway_method" "feedback_post" {
  rest_api_id   = aws_api_gateway_rest_api.feedback_api.id
  resource_id   = aws_api_gateway_resource.feedback_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "feedback_integration" {
  rest_api_id = aws_api_gateway_rest_api.feedback_api.id
  resource_id = aws_api_gateway_resource.feedback_resource.id
  http_method = aws_api_gateway_method.feedback_post.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.feedback_processor.invoke_arn
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.feedback_processor.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.feedback_api.execution_arn}/*/*"
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "feedback_deployment" {
  depends_on = [
    aws_api_gateway_method.feedback_post,
    aws_api_gateway_integration.feedback_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.feedback_api.id
  stage_name  = var.environment
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "feedback_dashboard" {
  dashboard_name = "${local.name_prefix}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["HackathonFeedback", "FeedbackSubmitted"]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Feedback Submissions Over Time"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["HackathonFeedback", "FeedbackBySentiment", "Sentiment", "positive"],
            [".", ".", ".", "negative"],
            [".", ".", ".", "neutral"]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Feedback by Sentiment"
        }
      }
    ]
  })
}

# Outputs
output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.feedback_table.name
}

output "s3_bucket_name" {
  description = "Name of the S3 backup bucket"
  value       = aws_s3_bucket.feedback_backup.bucket
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.feedback_processor.function_name
}

output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = "${aws_api_gateway_deployment.feedback_deployment.invoke_url}/feedback"
}

output "cloudwatch_dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.feedback_dashboard.dashboard_name}"
}