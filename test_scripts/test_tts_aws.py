from app.services.tts import TTSService
from dotenv import load_dotenv
import os

def test_tts_service():
    """
    Test the Amazon Polly TTS service functionality
    """
    try:
        print("Initializing TTS Service...")
        tts_service = TTSService()
        
        # Test text
        test_text = "Hello! This is a test of the Amazon Polly text to speech service."
        
        print("\nTesting speech synthesis...")
        print(f"Input text: {test_text}")
        
        # Test with different genders
        for gender in ["NEUTRAL", "MALE", "FEMALE"]:
            print(f"\nTesting with {gender} voice...")
            
            # Synthesize speech
            audio_content = tts_service.synthesize_speech(
                text=test_text,
                language_code="en-US",
                gender=gender
            )
            
            # Save the audio file
            output_filename = f"test_output_{gender.lower()}.ogg"
            with open(output_filename, "wb") as audio_file:
                audio_file.write(audio_content)
            
            print(f"Audio file saved as: {output_filename}")
            print(f"Audio size: {len(audio_content)} bytes")
        
        print("\nTest completed successfully!")
        return True
        
    except Exception as e:
        print("\nTest Failed!")
        print("-" * 50)
        print(f"Error: {str(e)}")
        print("-" * 50)
        return False

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    print("Starting TTS Service Test")
    print("=" * 50)
    
    # Check if AWS credentials are set
    required_env_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        print("\nPlease set these variables in your .env file")
    else:
        success = test_tts_service()
        print("\nTest Summary:")
        print("=" * 50)
        print(f"Test {'Passed' if success else 'Failed'}")