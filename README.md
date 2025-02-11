# Replicant


## Requirements
AWS access keys: create the keys in AWS and use `aws configure` to enter them to be able to use them with terragrunt.  For continuity's sake, all infra is written for _us-east-1_.

Discord Bot: create a discord bot from the developer portal and add it to your discord server.  I used administrator permissions to develop, but this is not a recommended approach for security.

Discord Server: Ensure that the users in your server will not disconnect the bot while it is running!

Create a `.env` file with the following contents:
* DISCORD_BOT_TOKEN: A discord bot token with administrator access (can be more fine-grained, but I haven't tested the minimum requirements)
* VOICE_CHANNEL_ID: The discord voice channel you wish to observe
* TARGET_USER_ID: The discord user you wish to observe
* AWS

## File Structure
```
.
├── .github
│   └── workflows
│       └── main.yaml
├── .gitignore
├── LICENSE
├── README.md
├── bootstrap
│   └── README.md
├── prod
│   ├── applications
│   │   ├── discord
│   │   │   ├── clockwatch
│   │   │   │   ├── README.md
│   │   │   │   └── argo-application.yaml
│   │   │   └── collector-bot
│   │   │       ├── app
│   │   │       │   ├── Dockerfile
│   │   │       │   ├── README.md
│   │   │       │   ├── audio
│   │   │       │   │   └── README.md
│   │   │       │   ├── index.js
│   │   │       │   ├── package-lock.json
│   │   │       │   └── package.json
│   │   │       ├── argo-application.yaml
│   │   │       └── manifests
│   │   │           └── README.md
│   │   └── machine-learning
│   │       ├── llm
│   │       │   ├── app
│   │       │   │   └── README.md
│   │       │   ├── argo-application.yaml
│   │       │   └── manifests
│   │       │       └── README.md
│   │       └── tts
│   │           ├── app
│   │           │   └── README.md
│   │           ├── argo-application.yaml
│   │           └── manifests
│   │               └── README.md
│   └── infra
│       ├── argocd
│       │   └── README.md
│       ├── eks
│       │   └── README.md
│       ├── s3
│       │   ├── README.md
│       │   ├── main.tf
│       │   ├── outputs.tf
│       │   └── variables.tf
│       └── vpc
│           └── README.md
└── terragrunt.hcl

24 directories, 29 files
```
