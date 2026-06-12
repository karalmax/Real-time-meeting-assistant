from faster_whisper import WhisperModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_load():
    logger.info("Starting isolated Faster-Whisper load...")
    try:
        # Added cpu_threads=4 to prevent Windows thread deadlock
        model = WhisperModel(
            "tiny", 
            device="cpu", 
            compute_type="int8",
            cpu_threads=4 
        )
        logger.info("✅ SUCCESS: Model loaded perfectly!")
    except Exception as e:
        logger.error(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_load()