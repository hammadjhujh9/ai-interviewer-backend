import base64
from app.services.stt import STTService
from pydub import AudioSegment
from pydub.utils import mediainfo


def get_audio_info(file_path):
    info = mediainfo(file_path)
    print(f"Sample rate: {info['sample_rate']}")
    print(f"Channels: {info['channels']}")
    print(f"Duration: {info['duration']} seconds")


def test_stt_service():
    # Instantiate the service
    stt_service = STTService()

    # Load an audio file using pydub
    audio = AudioSegment.from_wav("test_audio.wav")  # Change the format based on your audio file
    sample_rate = audio.frame_rate  # Get the sample rate of the audio
    print(f"Extracted sample rate: {sample_rate} Hz")

    # Convert the audio to raw bytes and then encode to base64
    with open("test_audio.wav", "rb") as audio_file:
        audio_bytes = audio_file.read()
    
    # Ensure the audio size is reasonable (debugging)
    print(f"Audio file size: {len(audio_bytes)} bytes")
    
    # Base64 encode the audio bytes
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    # Call the transcribe function with base64 audio and sample rate
    try:
        transcript = stt_service.transcribe_audio(audio_base64, sample_rate_hertz=sample_rate)
        print("Transcription Result:", transcript)
    except Exception as e:
        print(f"Error during transcription: {e}")


if __name__ == "__main__":
    # test_stt_service()

    # Optionally test audio info with .ogg file (if needed)
    get_audio_info("test_audio.wav")
