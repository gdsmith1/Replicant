import boto3
import os
import time
import json
import shutil
from elevenlabs.client import ElevenLabs
from datetime import datetime

def upload_file_to_s3(bucket_name, file_path, s3_key):
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket_name, s3_key)
    print(f"Uploaded {file_path} to s3://{bucket_name}/{s3_key}")

def download_files_from_s3(bucket_name, local_directory, downloaded_files):
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    files_with_size = []
    MAX_SIZE_BYTES = 9.9 * 1024 * 1024  # 9.9MB in bytes (must be under 10MB for ElevenLabs)
    MAX_FILES = 25  # Maximum number of files to upload

    # Collect all eligible files with their sizes
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            key = obj['Key']
            size = obj['Size']

            if key.endswith('.wav') and key not in downloaded_files:
                if size > MAX_SIZE_BYTES:
                    print(f"Skipping {key}: File size {size/1024/1024:.2f}MB exceeds limit of 9.9MB")
                    continue

                files_with_size.append((key, size))

    # Sort files by size in descending order and take top 25
    files_with_size.sort(key=lambda x: x[1], reverse=True)
    selected_files = files_with_size[:MAX_FILES]

    new_files = []
    # Download only the selected files
    for key, size in selected_files:
        local_path = os.path.join(local_directory, os.path.basename(key))
        s3.download_file(bucket_name, key, local_path)
        print(f"Downloaded {key} ({size/1024/1024:.2f}MB) to {local_path}")
        downloaded_files.add(key)
        new_files.append(local_path)

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

    # Wait for the transcription file to be available
    TIME_LIMIT = int(os.getenv('TIME_LIMIT', '600'))
    print("Waiting for audio files to be available...")
    time.sleep(TIME_LIMIT + 120)  # Wait for the transcription to finish to start looking

    # Create audio directory if it doesn't exist
    if not os.path.exists('audio'):
        os.makedirs('audio')

    # Call the function to download files
    downloaded_files = set()
    audio_files = download_files_from_s3('replicant-s3-bucket', 'audio', downloaded_files)

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
            f.write(result['voice_id'])

        # Upload the file to S3
        upload_file_to_s3('replicant-s3-bucket', 'tts-id.txt', 'tts-id.txt')
    finally:
        # Make sure to close all file objects
        for file_obj in file_objects:
            file_obj.close()
