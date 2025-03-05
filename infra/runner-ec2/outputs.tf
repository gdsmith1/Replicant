output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.runner.id
}

output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.runner.public_ip
}

output "ssh-key-location" {
  description = "The directory where Terragrunt was run"
  value       = var.terragrunt_dir
}