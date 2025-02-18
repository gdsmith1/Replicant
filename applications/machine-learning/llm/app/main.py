from openai import OpenAI
import jsonlines
from datetime import datetime
import re
import requests

# Load your API key from an environment variable or secret management service
# client = OpenAI()

# Fetch the list of inappropriate words from the URL
response = requests.get("https://raw.githubusercontent.com/Hesham-Elbadawi/list-of-banned-words/refs/heads/master/en")
inappropriate_words = response.text.splitlines()

# Function to censor inappropriate content
def censor_content(content):
    for word in inappropriate_words:
        content = re.sub(r'\b{}\b'.format(word), "[CENSORED]", content, flags=re.IGNORECASE)
    return content

# Read the transcription file
with open("transcription.txt", "r") as file:
    transcription = file.read()

# Split the transcription into smaller chunks (for example, by sentences or paragraphs)
chunks = transcription.split('\n')  # Splitting by new lines for simplicity

# Censor inappropriate chunks
censored_chunks = [censor_content(chunk) for chunk in chunks]

# TODO: Create the user prompt for the training with a cheap prompt response
# i.e. Assuming both users are gamers, what would one of them have said to get this response? $chunk

# Prepare the dataset in chat format
dataset = [{"messages": [
    {"role": "system", "content": "Transcription:"},
    {"role": "user", "content": ""},
    {"role": "assistant", "content": chunk}
]} for chunk in censored_chunks]

# Save the dataset to a JSONL file
with jsonlines.open("fine_tune_dataset.jsonl", mode='w') as writer:
    writer.write_all(dataset)

# Upload the dataset to OpenAI
# fileresponse = client.files.create(
#     file=open("fine_tune_dataset.jsonl", "rb"),
#     purpose="fine-tune"
# )

# Generate a suffix with the current date and time
customsuffix = datetime.now().strftime("%Y%m%d%H%M%S")

# Create a fine-tuning job
# modelresponse = client.fine_tuning.jobs.create(
#     training_file=fileresponse.id,
#     model="gpt-3.5-turbo",
#     suffix=customsuffix
# )

# print("Fine-tuned model created:", modelresponse)