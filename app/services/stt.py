from groq import Groq
import os
import io
import base64
from dotenv import load_dotenv
import tempfile
import shutil

load_dotenv(".env", override=True)

class STTService:
    def __init__(self):
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        try:
            print("Initializing Groq client...")
            self.client = Groq(api_key=groq_api_key)
            print("Groq client initialized successfully.")
        except Exception as e:
            print(f"Error during client initialization: {str(e)}")
            raise ValueError(f"Failed to initialize Groq client: {str(e)}")

    def decode_base64_to_bytes(self, base64_str: str) -> bytes:
        """Decodes a base64 string back to bytes."""
        return base64.b64decode(base64_str)
    
    def transcribe_audio(self, audio_base64: str, language_code: str = "en-US"):
        """
        Transcribes audio using Groq's API.
        
        Args:
            audio_base64 (str): Base64 encoded audio string
            language_code (str): Language code (note: Groq may handle language detection automatically)
        
        Returns:
            str: Transcribed text
        """
        audio_bytes = self.decode_base64_to_bytes(audio_base64)
        print(f"Received audio of size: {len(audio_bytes)} bytes")
        
        # Create temporary directory instead of just a file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, "temp_audio.wav")
        
        try:
            # Write audio data to temporary file
            with open(temp_file_path, 'wb') as temp_audio_file:
                temp_audio_file.write(audio_bytes)
            
            print(f"Processing audio file: {temp_file_path}")
            
            # Read and process the file
            with open(temp_file_path, 'rb') as file:
                file_content = file.read()  # Read content first
                response = self.client.audio.transcriptions.create(
                    file=(temp_file_path, file_content),
                    model="whisper-large-v3-turbo",
                    response_format="verbose_json",
                )
            
            if not response or not response.text:
                print("No transcription returned from the service.")
                return ""
            
            transcript = response.text
            print(f"Final transcript: {transcript}")
            return transcript
                
        except Exception as e:
            print(f"Error during transcription: {str(e)}")
            raise ValueError(f"Speech recognition failed: {str(e)}")
        finally:
            # Clean up temporary directory and its contents
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Could not clean up temporary files: {str(e)}")