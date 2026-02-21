from google.cloud import texttospeech
from google.oauth2 import service_account
import os
from dotenv import load_dotenv

load_dotenv(".env", override=True)
class TTSServiceG:
    def __init__(self):
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        
        try:
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = texttospeech.TextToSpeechClient(credentials=credentials)

        except Exception as e:
            raise ValueError(f"Failed to initialize Speech client: {str(e)}")
   
    def synthesize_speech(self, text: str, language_code: str = "en-US", gender=texttospeech.SsmlVoiceGender.NEUTRAL):
        input_text = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=gender,
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.OGG_OPUS)
        try:
            response = self.client.synthesize_speech(
                input=input_text, voice=voice, audio_config=audio_config
            )
            return response.audio_content
        except Exception as e:
            raise ValueError(f"Speech synthesis failed: {str(e)}")

