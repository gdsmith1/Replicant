# Replicant

## Requirements
### Tooling
* AWS CLI
* Terraform
* Terragrunt
* Docker


### Resources
[__AWS Access Keys__](https://us-east-1.console.aws.amazon.com/console/home): create the keys in AWS and use `aws configure` to enter them to be able to use them with terragrunt.  For continuity's sake, all infra is written for _us-east-1_.

[__Discord Bot__](https://discord.com/developers/applications): create a discord bot from the developer portal and add it to your discord server.  I used administrator permissions to develop, but this is not a recommended approach for security. 

[__Discord Server__](https://discord.com): Ensure that the users in your server will not disconnect the bot while it is running!

[__Open AI API Key__](https://platform.openai.com/docs/overview): create a key on OpenAI API to be used for the LLM generation and usage.

### Environment
Create a `.env` file with the following contents:
* DISCORD_BOT_TOKEN: A discord bot token with administrator access (can be more fine-grained, but I haven't tested the minimum requirements)
* VOICE_CHANNEL_ID: The discord voice channel you wish to observe
* TARGET_USER_ID: The discord user you wish to observe
* AWS_ACCESS_KEY_ID: Access key ID for your AWS account (Likely needs to have a card attached.)
* AWS_SECRET_ACCESS_KEY: Secret access key for your AWS account
* OPENAI_API_KEY: Open AI API key to a funded account.  (Average pricing TBD.)

## File Structure
```
.
├── .github
│   └── workflows
│       ├── docker.yaml
│       └── readme.yaml
├── .gitignore
├── LICENSE
├── applications
│   ├── collector-bot
│   │   ├── Dockerfile
│   │   ├── audio
│   │   ├── index.js
│   │   ├── package-lock.json
│   │   └── package.json
│   ├── llm
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.md
│   ├── transcribe
│   │   ├── Dockerfile
│   │   ├── audio
│   │   ├── main.py
│   │   └── requirements.md
│   └── tts
│       └── audio
├── infra
│   └── artifact-s3
│       ├── main.tf
│       ├── outputs.tf
│       ├── terragrunt.hcl
│       └── variables.tf
└── terragrunt.hcl

13 directories, 19 files
```
