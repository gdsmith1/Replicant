resource "aws_s3_bucket" "s3_bucket" {
  bucket = var.bucket_name
  tags = var.tags
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
  depends_on = [ aws_s3_bucket_ownership_controls.s3_bucket ]
  bucket = aws_s3_bucket.s3_bucket.id
  acl = "private"
}