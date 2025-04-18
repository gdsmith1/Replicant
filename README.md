# Replicant

[![Build and Publish Docker Images](https://github.com/gdsmith1/Replicant/actions/workflows/docker.yaml/badge.svg)](https://github.com/gdsmith1/Replicant/actions/workflows/docker.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Clone your friends with AI!
Replicant is a collection of modular Docker containers that allows you to collect voice samples from a desired user, and use them to generate fine-tuned Text-to-Speech and Language Models from them, completely autonomously.

## Getting Started
To use Replicant, you will need to have the all of the required tools and set up your environment file in the Requirements section.  You can also find several ways to customize your Replicant setup in the environment file.

To run the default configuration, simply run `make` in the root of the project.  You can also use `make status` to see the status of the containers, `make stop` to stop the containers, or `make clean` to stop everything and take down the infrastructure.

At any point after starting Replicant, you can use `make download` to download the contents of the artifact bucket.

You can run Replicant locally by running the docker compose file in the root of the project with `docker compose up`.

Because of its modular design, you can also add or remove any docker containers from the compose file to customize your setup.  For example, you may want to run the collector bot multiple times to get much more data, but you only want to run the AI training containers once.  You can simply comment the unnecessary containers out, and add them back when you're ready.  You can also add other containers, such as [clockwatch](https://github.com/gdsmith1/clockwatch), which is used to make Replicant seem less suspicious to an unsuspecting user.


## Requirements

### Tooling for Remote Hosting
To run a remotely hosted Replicant session, you will need all of the following tools installed:
* AWS CLI
* Terraform
* Terragrunt
* Make
Mac users with Homebrew can install these with `brew bundle` from the root of the project.

### Tooling for Local Hosting
The following additional tools are required to run Replicant locally:
* Docker
* Docker Compose

Currently, Replicant depends on the existance of the S3 artifact storage bucket, so it must be built for any of these programs to run properly.

### API Resources
[__AWS Access Keys__](https://us-east-1.console.aws.amazon.com/console/home): create the keys in AWS and use `aws configure` to enter them to be able to use them with terragrunt.  For continuity's sake, all infra is written for _us-east-1_.

[__Discord Bot__](https://discord.com/developers/applications): create a discord bot from the developer portal and add it to your discord server.  I used administrator permissions to develop, but this is not a recommended approach for security.  If you would like to use a second bot for the final app, you can make a separate bot with similar permissions and configure it in the `.env` file.

[__Discord Server__](https://discord.com): Ensure that the users in your server will not disconnect the bot while it is running!

[__Open AI API Key__](https://platform.openai.com/docs/overview): create a key on OpenAI API to be used for the LLM generation and usage.  You have to put money into the account to be able to use the API.  I put $5 in and never got close to that limit, but YMMV.

[__Eleven Labs API Key__](https://elevenlabs.io/app/home): create a key on Eleven Labs API to be used for the text-to-speech generation and usage.  You will need at least the Starter Plan ($5 monthly) to be able to use Instant Voice Cloning.  I used the Creator Plan to be safe.

### Environment
Create a `.env` file with the following contents:
* __DISCORD_BOT_TOKEN__: A discord bot token with administrator access (can be more fine-grained, but I haven't tested the minimum requirements) for the collector bot to run.
* __VOICE_CHANNEL_ID__: The discord voice channel you wish to observe
* __TARGET_USER_ID__: The discord user you wish to observe
* __TIME_LIMIT__: The amount of time (in seconds) you want the collector bot to run.  More time means more voicelines recorded, and a more detailed model generated.  Defaults to 10 minutes.  (For dev purposes, I usually run for only about 2 minutes.  For a full session, I run it for a full day, to try and cover the target user's full time online.)
* __SPEAKING_LIMIT__: The amount of time (in seconds) each 'sentence' will be recorded for.  This is dependent on how the actual user tends to speak, and took some rough estimation to get a decent value.  Defaults to 5 seconds.  (I found the best results for my case are usually between 7.5 and 10 seconds)
* __AWS_ACCESS_KEY_ID__: Access key ID for your AWS account (Likely needs to have a card attached.)
* __AWS_SECRET_ACCESS_KEY__: Secret access key for your AWS account
* __OPENAI_API_KEY__: Open AI API key to a funded account (any amount of money is fine).
* __ELEVENLABS_API_KEY__: Eleven Labs API key to an account with a Starter Plan minimum.
* __REPLICANT_BOT_TOKEN__: The bot token for the replicant bot.  If you would like, you can use the same token as the collector bot.  Needs permissions to send messages, files, and join and speak in voice channels.
* __CENSOR_LLM_TRAINING__: Will censor the LLM training data to remove any potentially offensive content. Defaults to true.
* __LLM_TRAINING_PROMPT__: The prompt to use for the LLM training data. This is where you can specify any specifics or assumptions about the user you are training off of, such as what they are doing, how they may react to certain situations, or what their background is.
There is already a file in the repo to help you get started!

## File Structure
```
.
├── .github
│   └── workflows
│       ├── docker.yaml
│       └── readme.yaml
├── .gitignore
├── Brewfile
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
│   ├── replicant-bot
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
├── example.env
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

15 directories, 33 files
```
