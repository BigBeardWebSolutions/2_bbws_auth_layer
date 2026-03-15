terraform {
  required_version = ">= 1.5.0"

  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      Project     = "kimmy-ai"
      ManagedBy   = "terraform"
      Repository  = "2_bbws_auth_layer"
    }
  }
}

data "aws_caller_identity" "current" {}
