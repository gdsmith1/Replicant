from openai import OpenAI
import jsonlines
from datetime import datetime
import re
import requests
import boto3
import os
import time

def download_file_from_s3(bucket_name, s3_key, local_path):
    s3 = boto3.client('s3')
    s3.download_file(bucket_name, s3_key, local_path)
    print(f"Downloaded {s3_key} to {local_path}")

def upload_file_to_s3(bucket_name, file_path, s3_key):
    try:
        s3 = boto3.client('s3')
        s3.upload_file(file_path, bucket_name, s3_key)
        print(f"Uploaded {file_path} to s3://{bucket_name}/{s3_key}")
    except Exception as e:
        print(f"Error uploading file to S3: {e}")

def fetch_inappropriate_words(url):
    response = requests.get(url)
    return response.text.splitlines()

def process_transcription(file_path, inappropriate_words):
    with open(file_path, "r") as file:
        transcription = file.read()

    chunks = transcription.split('\n')
    censored_chunks = [re.sub(r'\b{}\b'.format(word), "[CENSORED]", chunk, flags=re.IGNORECASE) for chunk in chunks for word in inappropriate_words]

    dataset = []
    previous_chunk = None
    for chunk in censored_chunks:
        if chunk == previous_chunk:
            continue
        previous_chunk = chunk
        prompt = f"Assuming both users are gamers talking on Discord, what would one of them have said to get this response?  {chunk}  Give a likely quote in a simple, two-sentence max format that would cause this response, with no other feedback."
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        user_content = response.choices[0].message.content
        print("USER:", user_content, "AI:", chunk)
        dataset.append({
            "messages": [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": chunk}
            ]
        })

    with jsonlines.open("fine_tune_dataset.jsonl", mode='w') as writer:
        writer.write_all(dataset)

def upload_dataset(client, file_path):
    return client.files.create(
        file=open(file_path, "rb"),
        purpose="fine-tune"
    )

def create_fine_tuning_job(client, file_id, model, suffix):
    return client.fine_tuning.jobs.create(
        training_file=file_id,
        model=model,
        suffix=suffix
    )

if __name__ == "__main__":
    client = OpenAI()

    # Wait for the transcription file to be available
    TIME_LIMIT = int(os.getenv('TIME_LIMIT', '600'))
    print("Waiting for transcription file to be available...")
    time.sleep(TIME_LIMIT + 120)  # Wait for the transcription to finish to start looking

    # Download the transcription file
    while not os.path.exists('transcription.txt'):
        try:
            download_file_from_s3('replicant-s3-bucket', 'transcription.txt', 'transcription.txt')
        except Exception as e:
            print(f"Error downloading file: {e}. Retrying in 10 seconds...")
            time.sleep(10)

    # Process the transcription
    inappropriate_words = fetch_inappropriate_words("https://raw.githubusercontent.com/Hesham-Elbadawi/list-of-banned-words/refs/heads/master/en")
    process_transcription("transcription.txt", inappropriate_words)

    # Upload the dataset to OpenAI
    fileresponse = upload_dataset(client, "fine_tune_dataset.jsonl")

    # Create a fine-tuning job
    customsuffix = datetime.now().strftime("%Y%m%d%H%M%S")
    modelresponse = create_fine_tuning_job(client, fileresponse.id, "gpt-3.5-turbo", customsuffix)
    print("Fine-tuned model created:", modelresponse)

    # Upload the fine-tuning dataset to S3
    dataset_s3_key = f'fine_tune_dataset_{customsuffix}.jsonl'
    upload_file_to_s3('replicant-s3-bucket', 'fine_tune_dataset.jsonl', dataset_s3_key)
