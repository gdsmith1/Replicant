# needs ffmpeg installed
import os
import speech_recognition as sr
from pydub import AudioSegment

def transcribe_audio(file_path):
    print("Initialized...")

    # Initialize recognizer
    recognizer = sr.Recognizer()
    print("Transcribing audio...")

    # Load the audio file
    audio = AudioSegment.from_wav(file_path)
    chunk_length_ms = 30000  # 30 seconds
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

    # Create directory for audio chunks if it doesn't exist
    os.makedirs('chunks', exist_ok=True)

    full_transcription = ""

    for i, chunk in enumerate(chunks):
        chunk_file = f"audio/chunks/chunk{i}.wav"
        chunk.export(chunk_file, format="wav")

        with sr.AudioFile(chunk_file) as source:
            audio_data = recognizer.record(source)

        # Transcribe the audio chunk
        try:
            text = recognizer.recognize_google(audio_data)
            full_transcription += text + " "
            print(f"Chunk {i} Transcription: ", text)
        except sr.UnknownValueError:
            print(f"Google Speech Recognition could not understand chunk {i}")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service for chunk {i}; {e}")

    print("Full Transcription: ", full_transcription.strip())

    # Delete chunk files
    for i in range(len(chunks)):
        os.remove(f"chunks/chunk{i}.wav")

if __name__ == "__main__":
    transcribe_audio('audio/Trump.wav')