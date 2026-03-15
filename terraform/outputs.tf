output "layer_arn" {
  description = "ARN of the bbws-auth Lambda Layer (includes version)"
  value       = aws_lambda_layer_version.bbws_auth.arn
}

output "layer_version" {
  description = "Version number of the bbws-auth Lambda Layer"
  value       = aws_lambda_layer_version.bbws_auth.version
}

output "layer_name" {
  description = "Layer name"
  value       = aws_lambda_layer_version.bbws_auth.layer_name
}
