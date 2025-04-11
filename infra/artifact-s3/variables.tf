variable "bucket_name_prefix" {
  description = "Prefix for the S3 bucket name. Will be combined with AWS access key ID."
  type        = string
  default     = "replicant-s3"
}

variable "tags" {
  description = "Tags to set on the bucket."
  type        = map(string)
  default = {
    Terraform = "true"
  }
}
