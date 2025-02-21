from openai import OpenAI
import jsonlines
from datetime import datetime
import re
import requests

# Load your API key from an environment variable or secret management service
client = OpenAI()

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

# Prepare the dataset in chat format
dataset = []
for chunk in censored_chunks:
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

# Save the dataset to a JSONL file
with jsonlines.open("fine_tune_dataset.jsonl", mode='w') as writer:
    writer.write_all(dataset)

# Upload the dataset to OpenAI
fileresponse = client.files.create(
    file=open("fine_tune_dataset.jsonl", "rb"),
    purpose="fine-tune"
)

# Generate a suffix with the current date and time
customsuffix = datetime.now().strftime("%Y%m%d%H%M%S")

# Create a fine-tuning job
modelresponse = client.fine_tuning.jobs.create(
    training_file=fileresponse.id,
    model="gpt-3.5-turbo", # Use the GPT-3.5-turbo model to avoid unexplained censoring blocking training
    suffix=customsuffix
)

print("Fine-tuned model created:", modelresponse)