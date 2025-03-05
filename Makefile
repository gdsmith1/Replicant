start:
	@echo "Standing up infrastructure..."
	terragrunt run-all apply --non-interactive
	@echo "Adding server to known_hosts..."
	@echo "TODO - check if server exists in known_hosts, if not add it"
	@echo "Uploading .env and docker-compose.yaml to EC2 instance..."
	@echo scp -i infra/runner-ec2/generated-key.pem .env ubuntu@$(terraform output -raw instance_public_ip):/home/ubuntu/
	@echo scp -i infra/runner-ec2/generated-key.pem docker-compose.yaml ubuntu@$(terraform output -raw instance_public_ip):/home/ubuntu/
	@echo "Running docker-compose up on EC2 instance..."
	@echo ssh -i infra/runner-ec2/generated-key.pem ubuntu@$(terraform output -raw instance_public_ip) 'cd /home/ubuntu && docker-compose up'

stop:
	@echo "Stopping docker-compose on EC2 instance..."
	@echo "TODO - depends on known_hosts"

download:
	@echo "Downloading logs from EC2 instance..."
	@echo "TODO - Download all contents of artifact s3 bucket"

clean:
	@echo "Stopping docker-compose on EC2 instance..."
	@echo "TODO - depends on known_hosts"
	@echo "Destroying infrastructure..."
	terragrunt run-all destroy --non-interactive
