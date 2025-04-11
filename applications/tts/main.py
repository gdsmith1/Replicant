import boto3
import os
import time
import json
import shutil
from elevenlabs.client import ElevenLabs
from datetime import datetime
from pydub import AudioSegment

def get_bucket_name():
    # Get AWS_ACCESS_KEY_ID from environment
    aws_key = os.getenv('AWS_ACCESS_KEY_ID', '')

    # Take first 8 characters and convert to lowercase
    key_prefix = aws_key[:8].lower() if aws_key else ''

    # Form bucket name
    bucket_name = f"replicant-s3-{key_prefix}"
    print(f"Using S3 bucket name: {bucket_name}")

    return bucket_name

def upload_file_to_s3(bucket_name, file_path, s3_key):
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket_name, s3_key)
    print(f"Uploaded {file_path} to s3://{bucket_name}/{s3_key}")

def download_files_from_s3(bucket_name, local_directory, downloaded_files):
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    files_with_duration = []
    MAX_DURATION_SEC = 30  # Maximum duration in seconds
    MIN_DURATION_SEC = 4.6   # Minimum duration in seconds
    MAX_FILES = 25         # Maximum number of files to upload

    # First download eligible wav files to check their duration
    temp_dir = os.path.join(local_directory, 'temp')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Collect all potential wav files
    wav_files = []
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.endswith('.wav') and key not in downloaded_files:
                wav_files.append(key)

    # Download and check durations
    for key in wav_files:
        temp_path = os.path.join(temp_dir, os.path.basename(key))
        try:
            s3.download_file(bucket_name, key, temp_path)
            # Check actual duration using pydub
            audio = AudioSegment.from_wav(temp_path)
            duration_sec = len(audio) / 1000  # Convert milliseconds to seconds

            if duration_sec > MAX_DURATION_SEC:
                print(f"Skipping {key}: Duration {duration_sec:.2f}s exceeds limit of {MAX_DURATION_SEC}s")
                os.remove(temp_path)  # Clean up temp file
                continue
            if duration_sec < MIN_DURATION_SEC:
                print(f"Skipping {key}: Duration {duration_sec:.2f}s is below minimum of {MIN_DURATION_SEC}s")
                os.remove(temp_path)  # Clean up temp file
                continue

            files_with_duration.append((key, temp_path, duration_sec))
            print(f"Found valid file {key} with duration {duration_sec:.2f}s")

        except Exception as e:
            print(f"Error processing {key}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # Sort files by duration in descending order and take top MAX_FILES
    files_with_duration.sort(key=lambda x: x[2], reverse=True)
    selected_files = files_with_duration[:MAX_FILES]

    if not selected_files:
        raise Exception(f"No suitable audio files found (must be between {MIN_DURATION_SEC} and {MAX_DURATION_SEC} seconds)")

    new_files = []
    # Move selected files to final location
    for key, temp_path, duration in selected_files:
        final_path = os.path.join(local_directory, os.path.basename(key))
        shutil.move(temp_path, final_path)
        print(f"Selected {key} ({duration:.2f}s) -> {final_path}")
        downloaded_files.add(key)
        new_files.append(final_path)

    # Clean up temp directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    return new_files

def rename_files_sequentially(file_paths, directory):
    """Rename files to sequential numbers with unix timestamp and return new paths."""
    new_paths = []
    timestamp = int(time.time())
    for i, old_path in enumerate(file_paths, 1):
        new_filename = f"{timestamp}_{i}.wav"
        new_path = os.path.join(directory, new_filename)
        shutil.move(old_path, new_path)
        print(f"Renamed {old_path} to {new_path}")
        new_paths.append(new_path)
    return new_paths

if __name__ == "__main__":
    client = ElevenLabs(
      api_key=os.getenv('ELEVENLABS_API_KEY'),
    )

    # Get the dynamic bucket name
    bucket_name = get_bucket_name()

    # Wait for the transcription file to be available
    TIME_LIMIT = int(os.getenv('TIME_LIMIT', '600'))
    print("Waiting for audio files to be available...")
    time.sleep(TIME_LIMIT + 120)  # Wait for the transcription to finish to start looking

    # Create audio directory if it doesn't exist
    if not os.path.exists('audio'):
        os.makedirs('audio')

    # Call the function to download files
    downloaded_files = set()
    audio_files = download_files_from_s3(bucket_name, 'audio', downloaded_files)

    # Open files in binary mode
    file_objects = [open(file_path, 'rb') for file_path in audio_files]

    # Print the files we're going to upload
    print(f"Attempting to upload {len(audio_files)} files:", audio_files)
    customsuffix = datetime.now().strftime("%Y%m%d%H%M%S")
    try:
        result = client.voices.add(
            name=f"replicant-{customsuffix}",
            files=file_objects,  # Pass the list of file objects
            remove_background_noise=True,
            description="Recorded autonomously via Replicant"
        )
        print(result)
        # Save voice_id to file
        with open('tts-id.txt', 'w') as f:
            f.write(result.voice_id)

        # Upload the file to S3
        upload_file_to_s3(bucket_name, 'tts-id.txt', 'tts-id.txt')
    finally:
        # Make sure to close all file objects
        for file_obj in file_objects:
            file_obj.close()
