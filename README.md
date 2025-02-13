# Replicant

## Requirements
### Tooling
__Required tools to run__:
* AWS CLI
* Terraform
* Terragrunt

__Additional Tools for Development__:
* Docker
* Kubectl (and k9s)


### Resources
__AWS access keys__: create the keys in AWS and use `aws configure` to enter them to be able to use them with terragrunt.  For continuity's sake, all infra is written for _us-east-1_.

__Discord Bot__: create a discord bot from the developer portal and add it to your discord server.  I used administrator permissions to develop, but this is not a recommended approach for security.

__Discord Server__: Ensure that the users in your server will not disconnect the bot while it is running!

### Environment
Create a `.env` file with the following contents:
* DISCORD_BOT_TOKEN: A discord bot token with administrator access (can be more fine-grained, but I haven't tested the minimum requirements)
* VOICE_CHANNEL_ID: The discord voice channel you wish to observe
* TARGET_USER_ID: The discord user you wish to observe
* AWS_ACCESS_KEY_ID: Access key ID for your AWS account
* AWS_SECRET_ACCESS_KEY: Secret access key for your AWS account

## File Structure
```
.
├── .github
│   └── workflows
│       └── main.yaml
├── .gitignore
├── LICENSE
├── README.md
├── applications
│   ├── discord
│   │   ├── clockwatch
│   │   │   ├── README.md
│   │   │   └── argo-application.yaml
│   │   └── collector-bot
│   │       ├── app
│   │       │   ├── Dockerfile
│   │       │   ├── README.md
│   │       │   ├── audio
│   │       │   │   └── README.md
│   │       │   ├── index.js
│   │       │   ├── package-lock.json
│   │       │   └── package.json
│   │       ├── argo-application.yaml
│   │       └── manifests
│   │           └── README.md
│   └── machine-learning
│       ├── llm
│       │   ├── app
│       │   │   └── README.md
│       │   ├── argo-application.yaml
│       │   └── manifests
│       │       └── README.md
│       ├── transcribe
│       │   ├── app
│       │   │   ├── README.md
│       │   │   ├── audio
│       │   │   │   └── README.md
│       │   │   ├── main.py
│       │   │   └── requirements.txt
│       │   ├── argo-application.yaml
│       │   └── manifests
│       │       └── README.md
│       └── tts
│           ├── app
│           │   ├── README.md
│           │   └── audio
│           │       └── README.md
│           ├── argo-application.yaml
│           └── manifests
│               └── README.md
├── bootstrap
│   └── README.md
├── infra
│   ├── argocd
│   │   └── README.md
│   ├── eks
│   │   └── README.md
│   ├── s3
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   ├── terragrunt.hcl
│   │   └── variables.tf
│   └── vpc
│       └── README.md
└── terragrunt.hcl

28 directories, 36 files
```
