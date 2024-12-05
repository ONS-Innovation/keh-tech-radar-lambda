terraform {
  backend "s3" {
    # Backend is selected using terraform init -backend-config=path/to/backend-<env>.tfbackend
    # bucket         = "sdp-dev-tf-state"
    # key            = "sdp-dev-tech-audit-tool-api-lambda/terraform.tfstate"
    # region         = "eu-west-2"
    # dynamodb_table = "terraform-state-lock"
  }

}

# 1. First create the IAM role
resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.domain}-${var.service_subdomain}-lambda-role"

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
}

# 2. Attach basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  depends_on = [aws_iam_role.lambda_execution_role]
}

# 3. Add ECR policy
resource "aws_iam_role_policy" "lambda_ecr_policy" {
  name = "${var.domain}-${var.service_subdomain}-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetAuthorizationToken"
        ]
        Resource = [
          "arn:aws:ecr:${var.region}:${var.aws_account_id}:repository/${var.ecr_repository_name}",
          "arn:aws:ecr:${var.region}:${var.aws_account_id}:repository/${var.ecr_repository_name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      }
    ]
  })
  depends_on = [aws_iam_role.lambda_execution_role]
}

# 4. Add S3 access policy
resource "aws_iam_role_policy" "lambda_s3_access" {
  name = "${var.domain}-${var.service_subdomain}-lambda-s3-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.source_bucket}",
          "arn:aws:s3:::${var.source_bucket}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.destination_bucket}",
          "arn:aws:s3:::${var.destination_bucket}/*"
        ]
      }
    ]
  })
  depends_on = [aws_iam_role.lambda_execution_role]
}

# 5. Add additional permissions
resource "aws_iam_role_policy" "lambda_additional_permissions" {
  name = "${var.domain}-${var.service_subdomain}-policy-2"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup"
        ]
        Resource = "arn:aws:logs:${var.region}:${var.aws_account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:${var.region}:${var.aws_account_id}:log-group:/aws/lambda/${var.domain}-${var.service_subdomain}-lambda:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "execute-api:Invoke",
          "execute-api:ManageConnections"
        ]
        Resource = "arn:aws:execute-api:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:*",
          "s3-object-lambda:*"
        ]
        Resource = "*"
      }
    ]
  })
  depends_on = [aws_iam_role.lambda_execution_role]
}

# 6. Create the Lambda function
resource "aws_lambda_function" "tech_audit_lambda" {
  function_name = "${var.domain}-${var.service_subdomain}-lambda"
  package_type  = "Image"
  image_uri     = "${var.aws_account_id}.dkr.ecr.${var.region}.amazonaws.com/${var.ecr_repository}:${var.container_ver}"
  
  role = aws_iam_role.lambda_execution_role.arn

  memory_size = 128
  timeout     = 30

  environment {
    variables = {
      SOURCE_BUCKET      = var.source_bucket
      SOURCE_KEY         = var.source_key
      DESTINATION_BUCKET = var.destination_bucket
      DESTINATION_KEY    = var.destination_key
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_ecr_policy,
    aws_iam_role_policy.lambda_s3_access,
    aws_iam_role_policy.lambda_additional_permissions,
    aws_iam_role_policy_attachment.lambda_basic_execution
  ]
}

# 7. Add ECR policy after the lambda function is created
resource "aws_ecr_repository_policy" "lambda_ecr_access" {
  repository = var.ecr_repository_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "LambdaECRAccess"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
          AWS = aws_iam_role.lambda_execution_role.arn
        }
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer"
        ]
      }
    ]
  })

  depends_on = [aws_iam_role.lambda_execution_role]
}

# Add EventBridge (CloudWatch Events) rule for daily trigger
resource "aws_cloudwatch_event_rule" "daily_trigger" {
  name                = "${var.domain}-${var.service_subdomain}-daily-trigger"
  description         = "Triggers tech radar lambda daily"
  schedule_expression = "cron(0 11 * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_trigger.name
  target_id = "${var.domain}-${var.service_subdomain}-lambda"
  arn       = aws_lambda_function.tech_audit_lambda.arn
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.tech_audit_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_trigger.arn
} 