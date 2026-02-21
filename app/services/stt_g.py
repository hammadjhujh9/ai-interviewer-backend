from google.cloud import speech
from google.oauth2 import service_account
import os
import io
from dotenv import load_dotenv
import base64

load_dotenv(".env", override=True)



class STTServiceG:
    def __init__(self):
        # Debugging: Check the path to the credentials file
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        print(f"GOOGLE_APPLICATION_CREDENTIALS path: {credentials_path}")

        if not credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        
        try:
            # Debugging: Attempt to load the credentials
            print("Attempting to load credentials from service account file...")
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = speech.SpeechClient(credentials=credentials)
            print("Speech client initialized successfully.")
        except Exception as e:
            print(f"Error during client initialization: {str(e)}")
            raise ValueError(f"Failed to initialize Speech client: {str(e)}")

    def decode_base64_to_bytes(self,base64_str: str) -> bytes:
        """Decodes a base64 string back to bytes."""
        return base64.b64decode(base64_str)
    
    def transcribe_audio(self, audio_base64: str, language_code: str = "en-US"):
        # Debugging: Check the audio byte size
        audio_bytes = self.decode_base64_to_bytes(audio_base64)
        print(f"Received audio of size: {len(audio_bytes)} bytes")
        
        audio = speech.RecognitionAudio(content=audio_bytes)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code=language_code,
        )
        try:
            # Debugging: Log the configuration settings
            print(f"Recognizing audio with config: {config}")
            response = self.client.recognize(config=config, audio=audio)
            print("Speech recognition response received.")
        except Exception as e:
            print(f"Error during recognition: {str(e)}")
            raise ValueError(f"Speech recognition failed: {str(e)}")
        
        transcript = ""
        # Debugging: Check if the response contains results
        if not response.results:
            print("No results returned from the speech recognition service.")
        
        for result in response.results:
            print(f"Processing result: {result}")
            transcript += result.alternatives[0].transcript
        
        # Debugging: Final transcript result
        print(f"Final transcript: {transcript}")
        return transcript
