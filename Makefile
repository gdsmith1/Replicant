start:
	@echo "Standing up infrastructure..."
	terragrunt run-all apply --non-interactive
	@echo "Adding server to known_hosts..."
	@echo "Waiting for instance to be ready to accept SSH connections..."
	@IP="$$(cat ./infra/runner-ec2/runner-ip.txt)"; \
	MAX_ATTEMPTS=30; \
	ATTEMPT=1; \
	until nc -z -w 5 $$IP 22 || [ $$ATTEMPT -gt $$MAX_ATTEMPTS ]; do \
		echo "Attempt $$ATTEMPT/$$MAX_ATTEMPTS: Instance not ready yet, waiting..."; \
		sleep 10; \
		ATTEMPT=$$((ATTEMPT+1)); \
	done; \
	if [ $$ATTEMPT -gt $$MAX_ATTEMPTS ]; then \
		echo "Instance did not become ready within the timeout period"; \
		exit 1; \
	fi; \
	if ! grep -q "$$IP" ~/.ssh/known_hosts; then \
		echo "IP $$IP not found in known_hosts, adding it..."; \
		ssh-keyscan -H "$$IP" >> ~/.ssh/known_hosts && \
		echo "Added host to known_hosts"; \
	else \
		echo "Host $$IP already exists in known_hosts"; \
		grep -q "$$IP" ~/.ssh/known_hosts; \
	fi
	@echo "Waiting for Docker daemon to be fully operational..."
	@IP="$$(cat ./infra/runner-ec2/runner-ip.txt)"; \
	MAX_ATTEMPTS=30; \
	ATTEMPT=1; \
	until ssh -i infra/runner-ec2/generated-key.pem -o ConnectTimeout=5 ubuntu@$$IP 'sudo docker info' 2>/dev/null || [ $$ATTEMPT -gt $$MAX_ATTEMPTS ]; do \
		echo "Attempt $$ATTEMPT/$$MAX_ATTEMPTS: Docker daemon not ready yet, waiting..."; \
		sleep 10; \
		ATTEMPT=$$((ATTEMPT+1)); \
	done; \
	if [ $$ATTEMPT -gt $$MAX_ATTEMPTS ]; then \
		echo "Docker daemon did not become operational within the timeout period"; \
		exit 1; \
	else \
		echo "Docker daemon is operational!"; \
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
	@echo "Determining S3 bucket name..."
	@AWS_KEY=$$(grep 'AWS_ACCESS_KEY_ID=' .env | cut -d'=' -f2); \
	KEY_PREFIX=$$(echo $$AWS_KEY | cut -c1-8 | tr '[:upper:]' '[:lower:]'); \
	BUCKET_NAME="replicant-s3-$$KEY_PREFIX"; \
	echo "Using bucket name: $$BUCKET_NAME"; \
	echo "Downloading logs from EC2 instance..."; \
	chmod +x ./download.sh; \
	./download.sh $$BUCKET_NAME; \
	echo "Download complete. Contents are in bucket_contents.zip"

clean:
	@echo "Removing EC2 instance from known_hosts..."
	ssh-keygen -R "$$(cat ./infra/runner-ec2/runner-ip.txt)" || true
	@echo "Destroying infrastructure..."
	terragrunt run-all destroy --non-interactive
