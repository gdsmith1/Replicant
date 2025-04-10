import discord
from discord.ext import commands
import os
import openai
import time
from elevenlabs.client import ElevenLabs
import asyncio
import boto3
import io

# Wait for the tts file to be available
TIME_LIMIT = int(os.getenv('TIME_LIMIT', '600'))
print("Waiting for tts/llm file to be available...")
time.sleep(TIME_LIMIT + 120)

# Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# API Clients
openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
elevenlabs_client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))

def generate_audio(text):
    """Helper function to generate audio using ElevenLabs"""
    audio_stream = elevenlabs_client.text_to_speech.convert_as_stream(
        voice_id=VOICE_ID,
        output_format="mp3_44100_128",
        text=text,
        model_id="eleven_multilingual_v2",
    )

    # Convert stream to bytes
    audio_bytes = io.BytesIO()
    for chunk in audio_stream:
        audio_bytes.write(chunk)
    audio_bytes.seek(0)
    return audio_bytes

def download_file_from_s3(bucket_name, s3_key, local_path):
    """Download a file from S3 bucket"""
    s3 = boto3.client('s3')
    s3.download_file(bucket_name, s3_key, local_path)
    print(f"Downloaded {s3_key} to {local_path}")

# Load model and voice IDs from S3
try:
    # Download files from S3
    bucket_name = 'replicant-s3-bucket'
    for file_info in [('llm-id.txt', 'llm-id.txt'), ('tts-id.txt', 'tts-id.txt')]:
        s3_key, local_path = file_info
        retry_count = 0
        max_retries = 5

        while retry_count < max_retries:
            try:
                download_file_from_s3(bucket_name, s3_key, local_path)
                break
            except Exception as e:
                retry_count += 1
                print(f"Error downloading {s3_key}: {e}. Retry {retry_count}/{max_retries}...")
                asyncio.sleep(10)

        if retry_count == max_retries:
            raise Exception(f"Failed to download {s3_key} after {max_retries} attempts")

    # Read the model and voice IDs
    with open('llm-id.txt', 'r') as f:
        MODEL_ID = f.read().strip()
    with open('tts-id.txt', 'r') as f:
        VOICE_ID = f.read().strip()
except Exception as e:
    print(f"Error loading model/voice IDs: {e}")
    exit(1)

# Global variables
is_voice_active = False
voice_client = None

async def play_audio(ctx, audio_bytes):
    """Plays audio in voice channel if voice is active"""
    global voice_client
    if not is_voice_active:
        return

    if voice_client and voice_client.is_connected():
        if voice_client.is_playing():
            voice_client.stop()

        temp_file = "temp_audio.mp3"
        with open(temp_file, "wb") as f:
            f.write(audio_bytes.getvalue())

        voice_client.play(discord.FFmpegPCMAudio(temp_file))

        while voice_client.is_playing():
            await asyncio.sleep(0.1)
        os.remove(temp_file)

@bot.command(name='activate')
async def activate(ctx):
    """Activates the bot and joins your voice channel"""
    global is_voice_active, voice_client
    try:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            voice_client = await channel.connect()
            is_voice_active = True

            audio_bytes = generate_audio("Logan Link AI Online")
            await ctx.send(file=discord.File(audio_bytes, "activation.mp3"))
            await play_audio(ctx, audio_bytes)
            await ctx.send("Voice activation successful. Connected to voice channel.")
        else:
            await ctx.send("You need to be in a voice channel to activate voice features.")
    except Exception as e:
        await ctx.send(f"Error during voice activation: {str(e)}")

@bot.command(name='deactivate')
async def deactivate(ctx):
    """Disconnects the bot from voice channel"""
    global is_voice_active, voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        is_voice_active = False
        await ctx.send("Voice deactivated and disconnected from voice channel.")
    else:
        await ctx.send("I'm not currently in a voice channel.")

@bot.command(name='say')
async def say(ctx, *, text):
    """Generates audio from text and sends it (plays in voice if activated)"""
    try:
        async with ctx.typing():
            # Generate audio from text
            audio_bytes = generate_audio(text)

            # Send both text and audio file
            await ctx.send(f"📝 Text: {text}")
            await ctx.send(file=discord.File(audio_bytes, "speech.mp3"))

            # Only attempt to play in voice if voice is active
            if is_voice_active:
                await play_audio(ctx, audio_bytes)
            else:
                await ctx.send("Note: Voice playback is not active. Use !activate to enable voice channel features.")

    except Exception as e:
        await ctx.send(f"Error generating audio: {str(e)}")

@bot.command(name='talk')
async def talk(ctx, *, question):
    """Chat with the AI using text and voice (if activated)"""
    try:
        async with ctx.typing():
            # Get response from OpenAI
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant. Keep responses clear and concise."},
                {"role": "user", "content": question}
            ]

            response = openai_client.chat.completions.create(
                model=MODEL_ID,
                messages=messages
            )

            ai_response = response.choices[0].message.content
            audio_bytes = generate_audio(ai_response)

            # Send text and audio file
            await ctx.send(ai_response)
            await ctx.send(file=discord.File(audio_bytes, "response.mp3"))

            # Only attempt to play in voice if voice is active
            if is_voice_active:
                await play_audio(ctx, audio_bytes)
            else:
                await ctx.send("Note: Voice playback is not active. Use !activate to enable voice channel features.")

    except Exception as e:
        await ctx.send(f"Error processing question: {str(e)}")

@bot.command(name='chat')
async def chat(ctx, *, message):
    """Chat with the AI using text only"""
    try:
        async with ctx.typing():
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": message}
            ]

            response = openai_client.chat.completions.create(
                model=MODEL_ID,
                messages=messages
            )

            ai_response = response.choices[0].message.content
            await ctx.send(ai_response)

    except Exception as e:
        await ctx.send(f"Error during chat: {str(e)}")

@bot.command(name='repeat')
async def repeat(ctx):
    """Converts an uploaded audio file to speech using the bot's voice"""
    try:
        # Check if a file was attached to the message
        if not ctx.message.attachments:
            await ctx.send("Please attach an audio file (MP3) with your command!")
            return

        attachment = ctx.message.attachments[0]

        # Verify it's an audio file
        if not attachment.filename.lower().endswith('.mp3'):
            await ctx.send("Please provide an MP3 file!")
            return

        async with ctx.typing():
            # Download the attached audio file
            audio_data = await attachment.read()

            # Save temporary input file
            input_file = io.BytesIO(audio_data)

            # Convert speech to speech using ElevenLabs
            try:
                audio_stream = elevenlabs_client.speech_to_speech.convert_as_stream(
                    voice_id=VOICE_ID,
                    audio=input_file,
                    output_format="mp3_44100_128",
                    model_id="eleven_multilingual_sts_v2"
                )

                # Convert stream to bytes
                audio_bytes = io.BytesIO()
                for chunk in audio_stream:
                    audio_bytes.write(chunk)
                audio_bytes.seek(0)

                # Send the converted audio file
                await ctx.send("Here's your audio repeated in my voice:")
                await ctx.send(file=discord.File(audio_bytes, "repeated_audio.mp3"))

                # Play in voice channel if active
                if is_voice_active:
                    await play_audio(ctx, audio_bytes)
                else:
                    await ctx.send("Note: Voice playback is not active. Use !activate to enable voice channel features.")

            except Exception as e:
                await ctx.send(f"Error converting audio: {str(e)}")

    except Exception as e:
        await ctx.send(f"Error processing audio: {str(e)}")

# Run the bot
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
