from app.services.stt import STTService
from pydub.utils import mediainfo



def get_audio_info(file_path):
    info = mediainfo(file_path)
    print(f"Sample rate: {info['sample_rate']}")
    print(f"Channels: {info['channels']}")
    print(f"Duration: {info['duration']} seconds")

def test_stt_service():
    # Instantiate the service
    stt_service = STTService()

    # Load an OGG audio file
    with open("test_audio.wav", "rb") as audio_file:
        audio_bytes = audio_file.read()

    # Call the transcribe function
    transcript = stt_service.transcribe_audio(audio_bytes)

    print("Transcription Result:", transcript)

if __name__ == "__main__":
    # test_stt_service()
    
    # Test with your .ogg file
    # get_audio_info("stt.ogg")
    get_audio_info("test_audio.wav")


