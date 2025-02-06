# Replicant


## Requirements
Create a `.env` file with the following contents:
* A discord bot token with administrator access (can be more fine-grained, but I haven't tested the minimum requirements)

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
