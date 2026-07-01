# =============================================================================
# bbws-auth-layer — GitHub Actions OIDC Role (CI/CD)
# =============================================================================

data "aws_caller_identity" "ci" {}
data "aws_region" "ci" {}

data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_role" "github_actions_ci" {
  name = "bbws-auth-layer-${var.environment}-github-actions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = data.aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:BigBeardWebSolutions/2_bbws_auth_layer:*"
          }
        }
      }
    ]
  })

  tags = {
    Name = "bbws-auth-layer-${var.environment}-github-actions-role"
  }
}

resource "aws_iam_role_policy" "github_actions_ci" {
  name = "bbws-auth-layer-${var.environment}-ci-policy"
  role = aws_iam_role.github_actions_ci.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TerraformStateBucket"
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = [
          "arn:aws:s3:::bbws-terraform-state-${var.environment}",
          "arn:aws:s3:::bbws-terraform-state-${var.environment}/*",
        ]
      },
      {
        Sid    = "TerraformStateLock"
        Effect = "Allow"
        Action = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem"]
        Resource = "arn:aws:dynamodb:${data.aws_region.ci.name}:${data.aws_caller_identity.ci.account_id}:table/bbws-terraform-locks-${var.environment}"
      },
      {
        Sid    = "LambdaLayerManage"
        Effect = "Allow"
        Action = [
          "lambda:PublishLayerVersion",
          "lambda:DeleteLayerVersion",
          "lambda:GetLayerVersion",
          "lambda:ListLayerVersions",
          "lambda:AddLayerVersionPermission",
          "lambda:RemoveLayerVersionPermission",
          "lambda:GetLayerVersionPolicy",
        ]
        Resource = [
          "arn:aws:lambda:${data.aws_region.ci.name}:${data.aws_caller_identity.ci.account_id}:layer:bbws-auth-${var.environment}",
          "arn:aws:lambda:${data.aws_region.ci.name}:${data.aws_caller_identity.ci.account_id}:layer:bbws-auth-${var.environment}:*",
        ]
      },
      {
        Sid    = "SSMParameter"
        Effect = "Allow"
        Action = [
          "ssm:PutParameter",
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:DescribeParameters",
          "ssm:DeleteParameter",
          "ssm:AddTagsToResource",
          "ssm:ListTagsForResource",
        ]
        Resource = "arn:aws:ssm:${data.aws_region.ci.name}:${data.aws_caller_identity.ci.account_id}:parameter/kimmy-ai/${var.environment}/bbws-auth/*"
      },
      {
        Sid    = "IAMOIDCRead"
        Effect = "Allow"
        Action = [
          "iam:GetRole",
          "iam:GetRolePolicy",
          "iam:ListRolePolicies",
          "iam:ListAttachedRolePolicies",
          "iam:GetOpenIDConnectProvider",
          "iam:ListOpenIDConnectProviders",
        ]
        Resource = "*"
      },
    ]
  })
}

output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions OIDC role — set as AWS_ROLE_ARN in the GitHub dev environment secret"
  value       = aws_iam_role.github_actions_ci.arn
}
