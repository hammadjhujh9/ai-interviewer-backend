import boto3
from dotenv import load_dotenv
import os
import base64

load_dotenv(".env", override=True)

class TTSService:
    def __init__(self):
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        
        if not all([aws_access_key, aws_secret_key]):
            raise ValueError("AWS credentials not found in environment variables")
        
        try:
            self.client = boto3.client(
                'polly',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Polly client: {str(e)}")
    
    def synthesize_speech(self, text: str, language_code: str = "en-US", gender="MALE"):
        """
        Synthesize speech from text using Amazon Polly.
        
        Args:
            text (str): The text to convert to speech
            language_code (str): The language code (default: en-US)
            gender (str): Voice gender preference ("MALE", "FEMALE", "NEUTRAL")
            
        Returns:
            dict: Dictionary containing base64 encoded audio and content type
                {
                    'audio_base64': str,  # Base64 encoded audio data
                    'content_type': str   # MIME type of the audio
                }
        """
        try:
            voice_mapping = {
                "NEUTRAL": "Ivy",
                "MALE": "Matthew",
                "FEMALE": "Joanna"
            }
            
            voice_id = voice_mapping.get(gender.upper(), "Ivy")
            
            response = self.client.synthesize_speech(
                Engine='standard',
                LanguageCode=language_code,
                OutputFormat='ogg_vorbis',
                Text=text,
                VoiceId=voice_id
            )
            
            if "AudioStream" in response:
                with response["AudioStream"] as stream:
                    audio_content = stream.read()
                
                # Convert to base64
                audio_base64 = base64.b64encode(audio_content).decode('utf-8')
                
                return {
                    'audio_base64': audio_base64,
                    'content_type': 'audio/ogg'
                }
            else:
                raise ValueError("No AudioStream in response")
                
        except Exception as e:
            raise ValueError(f"Speech synthesis failed: {str(e)}")
    
    def get_voices(self, language_code: str = "en-US"):
        try:
            response = self.client.describe_voices(
                Engine='standard',
                LanguageCode=language_code
            )
            return response.get('Voices', [])
        except Exception as e:
            raise ValueError(f"Failed to list voices: {str(e)}")