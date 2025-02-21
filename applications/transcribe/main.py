# needs ffmpeg installed
import os
import boto3
import speech_recognition as sr

def download_files_from_s3(bucket_name, local_directory):
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.endswith('.wav'):
                local_path = os.path.join(local_directory, os.path.basename(key))
                s3.download_file(bucket_name, key, local_path)
                print(f"Downloaded {key} to {local_path}")

def upload_file_to_s3(bucket_name, file_path, s3_key):
    s3 = boto3.client('s3')
    s3.upload_file(file_path, bucket_name, s3_key)
    print(f"Uploaded {file_path} to s3://{bucket_name}/{s3_key}")

def transcribe_audio(directory_path):
    print("Initialized...")

    # Initialize recognizer
    recognizer = sr.Recognizer()
    print("Transcribing audio...")

    full_transcription = ""

    # Iterate over all .wav files in the directory
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".wav"):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")

                with sr.AudioFile(file_path) as source:
                    audio_data = recognizer.record(source)

                # Transcribe the audio file
                try:
                    text = recognizer.recognize_google(audio_data)
                    full_transcription += text + ".\n"
                except sr.UnknownValueError:
                    print(f"Google Speech Recognition could not understand file {file}")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service for file {file}; {e}")

    # Write the full transcription to a file
    with open("transcription.txt", "w") as f:
        f.write(full_transcription.strip())

if __name__ == "__main__":
    download_files_from_s3('replicant-s3-bucket', 'audio')
    transcribe_audio('audio')
    upload_file_to_s3('replicant-s3-bucket', 'transcription.txt', 'transcription.txt')