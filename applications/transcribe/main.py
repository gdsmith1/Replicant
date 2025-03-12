# needs ffmpeg installed
import os
import time
import boto3
import speech_recognition as sr

def delete_file_from_s3(bucket_name, s3_key):
    """Delete a specific file from S3 bucket"""
    try:
        s3 = boto3.client('s3')
        s3.delete_object(Bucket=bucket_name, Key=s3_key)
        print(f"Deleted {s3_key} from bucket {bucket_name}")
        return True
    except Exception as e:
        print(f"Error deleting {s3_key}: {str(e)}")
        return False

def download_files_from_s3(bucket_name, local_directory, downloaded_files):
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    new_files = []
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.endswith('.wav') and key not in downloaded_files:
                local_path = os.path.join(local_directory, os.path.basename(key))
                s3.download_file(bucket_name, key, local_path)
                print(f"Downloaded {key} to {local_path}")
                downloaded_files.add(key)
                new_files.append((local_path, key))  # Store both local path and S3 key
    print("List of downloaded files:", downloaded_files)
    return new_files

def upload_file_to_s3(bucket_name, file_path, s3_key):
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket_name, s3_key)
    print(f"Uploaded {file_path} to s3://{bucket_name}/{s3_key}")

def transcribe_audio(files):
    print("Initialized...")

    # Initialize recognizer
    recognizer = sr.Recognizer()
    print("Transcribing audio...")

    failed_files = []

    # Iterate over all .wav files in the list
    for file_path, s3_key in files:
        print(f"Processing file: {file_path}")

        try:
            with sr.AudioFile(file_path) as source:
                audio_data = recognizer.record(source)

            # Transcribe the audio file
            try:
                text = recognizer.recognize_google(audio_data)
                print(f"Transcribed text: {text}")

                # Append the transcription to the file instead of storing in memory
                with open("transcription.txt", "a") as f:
                    f.write(f"{text}\n")

            except sr.UnknownValueError:
                print(f"Google Speech Recognition could not understand file {file_path}")
                failed_files.append((file_path, s3_key))
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service for file {file_path}; {e}")
                failed_files.append((file_path, s3_key))
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            failed_files.append((file_path, s3_key))

    # Clean up failed files from S3
    for _, s3_key in failed_files:
        delete_file_from_s3('replicant-s3-bucket', s3_key)

    return failed_files

if __name__ == "__main__":
    if not os.path.exists("transcription.txt"):
            open("transcription.txt", "w").close()
    TIME_LIMIT = int(os.getenv('TIME_LIMIT', '600'))
    end_time = time.time() + TIME_LIMIT + 120  # Add 2 minutes as a buffer for late uploads

    downloaded_files = set()

    while time.time() < end_time:
        new_files = download_files_from_s3('replicant-s3-bucket', 'audio', downloaded_files)
        if new_files:
            failed_files = transcribe_audio(new_files)
        print("Waiting for new files...")
        time.sleep(15)  # Wait for 15 seconds before checking for new files

    upload_file_to_s3('replicant-s3-bucket', 'transcription.txt', 'transcription.txt')
    print("Transcription uploaded.")
