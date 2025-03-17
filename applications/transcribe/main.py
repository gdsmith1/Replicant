import os
import time
import boto3
import speech_recognition as sr
from pydub import AudioSegment

def delete_file(bucket_name, s3_key, local_path):
    try:
        # Delete from S3
        s3 = boto3.client('s3')
        s3.delete_object(Bucket=bucket_name, Key=s3_key)
        print(f"Deleted {s3_key} from bucket {bucket_name}")

        # Delete local file
        if os.path.exists(local_path):
            os.remove(local_path)
            print(f"Deleted local file: {local_path}")

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

def combine_audio_files(successful_files, output_path="combined_audio.wav"): # Not used by tts, but useful artifact for debugging
    if not successful_files:
        return None

    print(f"Combining {len(successful_files)} audio files:")
    for file in successful_files:
        print(f"- {file}")

    # Load the first file
    combined = AudioSegment.from_wav(successful_files[0])
    print(f"Initial audio length: {len(combined)} ms")

    # Append the rest of the files
    for audio_file in successful_files[1:]:
        sound = AudioSegment.from_wav(audio_file)
        print(f"Adding file of length: {len(sound)} ms")
        combined = combined + sound

    print(f"Final combined audio length: {len(combined)} ms")

    # Export the combined audio
    combined.export(output_path, format="wav")
    print(f"Created combined audio file: {output_path}")
    return output_path

def transcribe_audio(files):
    print("Initialized...")

    # Initialize recognizer
    recognizer = sr.Recognizer()
    print("Transcribing audio...")

    failed_files = []
    successful_files = []

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

                # Add to successful files list
                successful_files.append(file_path)

            except sr.UnknownValueError:
                print(f"Google Speech Recognition could not understand file {file_path}")
                failed_files.append((file_path, s3_key))
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service for file {file_path}; {e}")
                failed_files.append((file_path, s3_key))
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            failed_files.append((file_path, s3_key))

    # Clean up failed files from both S3 and local storage
    for local_path, s3_key in failed_files:
        delete_file('replicant-s3-bucket', s3_key, local_path)

    # Combine successful audio files
    if successful_files:
        combined_audio_path = combine_audio_files(successful_files)
        if combined_audio_path:
            upload_file_to_s3('replicant-s3-bucket', combined_audio_path, 'combined_audio.wav')

    return failed_files

if __name__ == "__main__":
    # Create necessary directories and files
    if not os.path.exists("audio"):
        os.makedirs("audio")
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

    # Upload final files to S3
    upload_file_to_s3('replicant-s3-bucket', 'transcription.txt', 'transcription.txt')
    print("Transcription uploaded.")
