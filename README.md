# Replicant

[![Build and Publish Docker Images](https://github.com/gdsmith1/Replicant/actions/workflows/docker.yaml/badge.svg)](https://github.com/gdsmith1/Replicant/actions/workflows/docker.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Requirements

### Local Tooling
To run a Replicant session, you will need all of the following tools installed: (Makefile coming soonTM)
* AWS CLI
* Terraform
* Terragrunt

### API Resources
[__AWS Access Keys__](https://us-east-1.console.aws.amazon.com/console/home): create the keys in AWS and use `aws configure` to enter them to be able to use them with terragrunt.  For continuity's sake, all infra is written for _us-east-1_.

[__Discord Bot__](https://discord.com/developers/applications): create a discord bot from the developer portal and add it to your discord server.  I used administrator permissions to develop, but this is not a recommended approach for security.

[__Discord Server__](https://discord.com): Ensure that the users in your server will not disconnect the bot while it is running!

[__Open AI API Key__](https://platform.openai.com/docs/overview): create a key on OpenAI API to be used for the LLM generation and usage.  You have to put money into the account to be able to use the API.  I put $5 in and never got close to that limit, but YMMV.

[__Eleven Labs API Key__](https://elevenlabs.io/app/home): create a key on Eleven Labs API to be used for the text-to-speech generation and usage.  You will need at least the Starter Plan ($5 monthly) to be able to use Instant Voice Cloning.  I used the Creator Plan to be safe.

### Environment
Create a `.env` file with the following contents:
* DISCORD_BOT_TOKEN: A discord bot token with administrator access (can be more fine-grained, but I haven't tested the minimum requirements)
* VOICE_CHANNEL_ID: The discord voice channel you wish to observe
* TARGET_USER_ID: The discord user you wish to observe
* TIME_LIMIT: The amount of time (in seconds) you want the collector bot to run.  More time means more voicelines recorded, and a more detailed model generated.  Defaults to 10 minutes.  (For dev purposes, I usually run for only about 2 minutes.  For a full session, I run it for a full day, to try and cover the target user's full time online.)
* SPEAKING_LIMIT: The amount of time (in seconds) each 'sentence' will be recorded for.  This is dependent on how the actual user tends to speak, and took some rough estimation to get a decent value.  Defaults to 5 seconds.  (I found the best results are usually between 7.5 and 10 seconds)
* AWS_ACCESS_KEY_ID: Access key ID for your AWS account (Likely needs to have a card attached.)
* AWS_SECRET_ACCESS_KEY: Secret access key for your AWS account
* OPENAI_API_KEY: Open AI API key to a funded account (any amount of money is fine).
* ELEVENLABS_API_KEY: Eleven Labs API key to an account with a Starter Plan minimum.

## File Structure
```
.
├── .github
│   └── workflows
│       ├── docker.yaml
│       └── readme.yaml
├── .gitignore
├── LICENSE
├── Makefile
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
│       ├── Dockerfile
│       ├── audio
│       ├── main.py
│       └── requirements.md
├── docker-compose.yaml
├── infra
│   ├── artifact-s3
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   ├── terragrunt.hcl
│   │   └── variables.tf
│   └── runner-ec2
│       ├── main.tf
│       ├── outputs.tf
│       ├── terragrunt.hcl
│       └── variables.tf
└── root.hcl

14 directories, 28 files
```
