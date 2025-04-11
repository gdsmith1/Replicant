locals {
  env_content = file("${path.module}/../../../../../.env")

  # Extract AWS_ACCESS_KEY_ID from the .env file using regex
  aws_access_key_pattern = "AWS_ACCESS_KEY_ID=([A-Z0-9]+)"
  aws_access_key_matches = regexall(local.aws_access_key_pattern, local.env_content)
  aws_access_key         = length(local.aws_access_key_matches) > 0 ? local.aws_access_key_matches[0][0] : "default"

  # Extract a portion of the key for the bucket name suffix
  access_key_suffix = lower(substr(local.aws_access_key, 0, 8))

  # Combine prefix with access key suffix
  bucket_name = "${var.bucket_name_prefix}-${local.access_key_suffix}"
}

resource "aws_s3_bucket" "s3_bucket" {
  bucket        = local.bucket_name
  tags          = var.tags
  force_destroy = true
}

resource "aws_s3_bucket_ownership_controls" "s3_bucket" {
  bucket = aws_s3_bucket.s3_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }

  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_s3_bucket_acl" "s3_bucket" {
  depends_on = [aws_s3_bucket_ownership_controls.s3_bucket]
  bucket     = aws_s3_bucket.s3_bucket.id
  acl        = "private"
}
