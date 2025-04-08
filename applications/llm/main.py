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

def process_transcription(file_path, inappropriate_words, should_censor=True):
    with open(file_path, "r") as file:
        transcription = file.read()

    # Split the transcription into chunks by newline
    chunks = transcription.split('\n')

    # Filter out empty chunks and censor inappropriate words in each chunk if needed
    processed_chunks = []
    for chunk in chunks:
        if not chunk.strip():  # Skip empty lines
            continue

        processed_chunk = chunk
        if should_censor:
            # Apply censoring to this chunk
            for word in inappropriate_words:
                processed_chunk = re.sub(r'\b{}\b'.format(re.escape(word)), "[CENSORED]", processed_chunk, flags=re.IGNORECASE)

            print(f"Censoring enabled: Original: '{chunk}' → Censored: '{processed_chunk}'")
        else:
            print(f"Censoring disabled: Using original text: '{processed_chunk}'")

        processed_chunks.append(processed_chunk)

    # Create dataset using the processed chunks
    dataset = []
    previous_chunk = None
    for chunk in processed_chunks:
        if chunk == previous_chunk or not chunk.strip():
            continue
        previous_chunk = chunk

        prompt = f"Assuming both users are users talking on Discord, what would one of them have said to get this response? {chunk} Assume that the users could be playing a competitive game like Rainbow Six Siege, Counter-Strike: Global Offensive, or War Thunder, watching YouTube videos, or just chatting with each other and playing Minecraft. Give a likely quote in a simple, two-sentence max format that would cause this response, with no other feedback."

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

def check_fine_tuning_status(client, job_id):
    while True:
        response = client.fine_tuning.jobs.retrieve(job_id)
        status = response.status

        print(f"Fine-tuning status: {status}")

        if status == "succeeded":
            print(f"Fine-tuning completed successfully! Model ID: {response.fine_tuned_model}")
            return response.fine_tuned_model
        elif status in ["failed", "cancelled"]:
            raise Exception(f"Fine-tuning failed with status: {status}")

        # Wait 120 seconds before checking again
        time.sleep(120)

if __name__ == "__main__":
    client = OpenAI()

    # Wait for the transcription file to be available
    TIME_LIMIT = int(os.getenv('TIME_LIMIT', '600'))
    print("Waiting for transcription file to be available...")
    time.sleep(TIME_LIMIT + 120)  # Wait for the transcription to finish to start looking

    # Check if censoring should be applied
    should_censor = os.getenv('CENSOR_LLM_TRAINING', 'true').lower() == 'true'
    print(f"Censoring {'enabled' if should_censor else 'disabled'} based on CENSOR_LLM_TRAINING environment variable")

    # Download the transcription file
    while not os.path.exists('transcription.txt'):
        try:
            download_file_from_s3('replicant-s3-bucket', 'transcription.txt', 'transcription.txt')
        except Exception as e:
            print(f"Error downloading file: {e}. Retrying in 10 seconds...")
            time.sleep(10)

    # Process the transcription
    inappropriate_words = []
    if should_censor:
        inappropriate_words = fetch_inappropriate_words("https://raw.githubusercontent.com/Hesham-Elbadawi/list-of-banned-words/refs/heads/master/en")
        print(f"Loaded {len(inappropriate_words)} inappropriate words for censoring")

    process_transcription("transcription.txt", inappropriate_words, should_censor)

    # Upload the dataset to OpenAI
    fileresponse = upload_dataset(client, "fine_tune_dataset.jsonl")

    # Create a fine-tuning job
    customsuffix = datetime.now().strftime("%Y%m%d%H%M%S")
    modelresponse = create_fine_tuning_job(client, fileresponse.id, "gpt-3.5-turbo", customsuffix)
    print("Fine-tuned model created:", modelresponse)

    try:
        fine_tuned_model = check_fine_tuning_status(client, modelresponse.id)
        print(f"Fine-tuning completed. Model ID: {fine_tuned_model}")
        # Save the model ID to a file
        with open('llm-id.txt', 'w') as f:
            f.write(fine_tuned_model)
        # Upload the model ID file to S3
        upload_file_to_s3('replicant-s3-bucket', 'llm-id.txt', 'llm-id.txt')
    except Exception as e:
        print(f"Fine-tuning failed: {e}")

    # Upload the fine-tuning dataset to S3
    dataset_s3_key = f'fine_tune_dataset_{customsuffix}.jsonl'
    upload_file_to_s3('replicant-s3-bucket', 'fine_tune_dataset.jsonl', dataset_s3_key)
