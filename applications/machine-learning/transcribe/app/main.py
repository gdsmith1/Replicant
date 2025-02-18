# needs ffmpeg installed
import os
import speech_recognition as sr
from pydub import AudioSegment
import nltk

def transcribe_audio(directory_path):
    print("Initialized...")

    # Initialize recognizer
    recognizer = sr.Recognizer()
    print("Transcribing audio...")

    full_transcription = ""

    # Iterate over all .wav files in the directory, excluding audio/chunks
    for root, dirs, files in os.walk(directory_path):
        if 'chunks' in dirs:
            dirs.remove('chunks')  # Ignore the 'chunks' directory

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
    transcribe_audio('audio')