provider "aws" {
  region = "us-east-1"
}

resource "tls_private_key" "ssh-key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = element(var.public_subnet_cidrs, count.index)
  map_public_ip_on_launch = true
  availability_zone       = element(var.availability_zones, count.index)
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_route_table_association" "public" {
  count          = length(var.public_subnet_cidrs)
  subnet_id      = element(aws_subnet.public.*.id, count.index)
  route_table_id = aws_route_table.public.id
}

resource "aws_key_pair" "generated_key" {
  key_name   = "generated-key"
  public_key = tls_private_key.ssh-key.public_key_openssh
}

resource "aws_security_group" "runner_sg" {
  name        = "runner-sg"
  description = "Allow SSH and HTTP traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "runner" {
  ami                    = "ami-0007a29926925d0db" # Ubuntu 22.04 Minimal
  instance_type          = "t2.micro"
  key_name               = aws_key_pair.generated_key.key_name
  vpc_security_group_ids = [aws_security_group.runner_sg.id]
  subnet_id              = element(aws_subnet.public.*.id, 0)

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              cd /home/ubuntu
              for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do apt-get remove -y $pkg; done
              apt-get update
              apt-get install -y ca-certificates curl
              install -m 0755 -d /etc/apt/keyrings
              curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
              chmod a+r /etc/apt/keyrings/docker.asc
              echo \
                "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
                $(. /etc/os-release && echo "$${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
                tee /etc/apt/sources.list.d/docker.list > /dev/null
              apt-get update
              apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
              EOF
}

resource "local_file" "private_key" {
  content         = tls_private_key.ssh-key.private_key_pem
  filename        = "${var.terragrunt_dir}/generated-key.pem"
  file_permission = "0600"
}

resource "local_file" "runner_ip" {
  content         = aws_instance.runner.public_ip
  filename        = "${var.terragrunt_dir}/runner-ip.txt"
  file_permission = "0644"
}
