start:
	@echo "Standing up infrastructure..."
	terragrunt run-all apply --non-interactive
	@echo "Adding server to known_hosts..."
	if ! grep -q "$$(cat ./infra/runner-ec2/runner-ip.txt)" ~/.ssh/known_hosts; then \
		echo "Waiting for instance to be ready..."; \
		sleep 60; \
		echo "IP $$(cat ./infra/runner-ec2/runner-ip.txt) not found in known_hosts, adding it..."; \
		ssh-keyscan -H "$$(cat ./infra/runner-ec2/runner-ip.txt)" >> ~/.ssh/known_hosts && \
		echo "Added host to known_hosts"; \
	else \
		echo "Host $$(cat ./infra/runner-ec2/runner-ip.txt) already exists in known_hosts"; \
		grep -q "$$(cat ./infra/runner-ec2/runner-ip.txt)" ~/.ssh/known_hosts; \
	fi
	@echo "Uploading .env and docker-compose.yaml to EC2 instance..."
	scp -i infra/runner-ec2/generated-key.pem ./.env ubuntu@$$(cat ./infra/runner-ec2/runner-ip.txt):/home/ubuntu/
	scp -i infra/runner-ec2/generated-key.pem ./docker-compose.yaml ubuntu@$$(cat ./infra/runner-ec2/runner-ip.txt):/home/ubuntu/
	@echo "Pulling docker images..."
	ssh -i infra/runner-ec2/generated-key.pem ubuntu@$$(cat ./infra/runner-ec2/runner-ip.txt) 'cd /home/ubuntu && sudo docker compose pull'
	@echo "Running docker-compose up on EC2 instance..."
	ssh -i infra/runner-ec2/generated-key.pem ubuntu@$$(cat ./infra/runner-ec2/runner-ip.txt) 'cd /home/ubuntu && sudo docker compose up -d'

status:
	@echo "Checking status of docker-compose on EC2 instance..."
	ssh -i infra/runner-ec2/generated-key.pem ubuntu@$$(cat ./infra/runner-ec2/runner-ip.txt) 'cd /home/ubuntu && sudo docker compose ps'

stop:
	@echo "Stopping docker-compose on EC2 instance..."
	ssh -i infra/runner-ec2/generated-key.pem ubuntu@$$(cat ./infra/runner-ec2/runner-ip.txt) 'cd /home/ubuntu && sudo docker compose down'

download:
	@echo "Downloading logs from EC2 instance..."
	@echo "TODO - Download all contents of artifact s3 bucket"

clean:
	@echo "Stopping docker-compose on EC2 instance..."
	ssh -i infra/runner-ec2/generated-key.pem ubuntu@$$(cat ./infra/runner-ec2/runner-ip.txt) 'cd /home/ubuntu && sudo docker compose down' || true
	@echo "Removing EC2 instance from known_hosts..."
	ssh-keygen -R "$$(cat ./infra/runner-ec2/runner-ip.txt)" || true
	@echo "Destroying infrastructure..."
	terragrunt run-all destroy --non-interactive
