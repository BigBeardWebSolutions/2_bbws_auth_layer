resource "aws_lambda_layer_version" "bbws_auth" {
  layer_name          = "bbws-auth-${var.environment}"
  description         = "Shared authorization library for Kimmy AI platform"
  filename            = "${path.module}/../bbws-auth-layer.zip"
  source_code_hash    = filebase64sha256("${path.module}/../bbws-auth-layer.zip")
  compatible_runtimes = ["python3.12"]

  compatible_architectures = ["arm64", "x86_64"]
}

resource "aws_ssm_parameter" "layer_arn" {
  name        = "/kimmy-ai/${var.environment}/bbws-auth/layer-arn"
  description = "ARN of the bbws-auth Lambda Layer (latest version)"
  type        = "String"
  value       = aws_lambda_layer_version.bbws_auth.arn
  overwrite   = true
}
