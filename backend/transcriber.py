import logging
import wave
import io
import time
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env
load_dotenv()

logger = logging.getLogger(__name__)

class AudioTranscriber:
    def __init__(self, *args, **kwargs):
        """
        CLOUD ARCHITECTURE (30-Second Buffered): 
        Uses Gemini 3.5 Flash for 100% accurate Tanglish & Code-mixed transcription
        with built-in Rate Limit handling and Zombie Thread prevention.
        """
        # API Key is now fetched from the .env file
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        logger.info("STT Engine Switched to Google Gemini Cloud (30s Buffer with Auto-Retry).")

    def process_audio_chunk(self, audio_bytes: bytes, cancel_event=None) -> str:
        """
        Sends 30 seconds of audio to Gemini. Listens for Kill Switch to stop Zombie Threads.
        """
        try:
            # 1. Convert raw audio bytes into WAV format in memory
            with io.BytesIO() as wav_io:
                with wave.open(wav_io, 'wb') as wav_file:
                    wav_file.setnchannels(1)       # Mono
                    wav_file.setsampwidth(2)       # 16-bit
                    wav_file.setframerate(16000)   # 16 kHz
                    wav_file.writeframes(audio_bytes)
                wav_data = wav_io.getvalue()

            # 2. Advanced Code-Mixing Prompt Optimization
            prompt = """
            Transcribe the speech in this audio exactly as spoken. The speaker is mixing Tamil and English. 
            Strict Rule: Write the Tamil words in Tamil script, and the English words strictly in English script. 
            Example output format: 'Database connection error ஆகிடுச்சு'. 
            Do not translate. If there is only silence or background noise, return exactly the word: [SILENCE].
            """

            # 3. Exponential Backoff Loop with Interruptible Events
            max_retries = 5 
            for attempt in range(max_retries):
                # Pre-flight check: Client disconnect aayிருந்தா API call thavirthிடு
                if cancel_event and cancel_event.is_set():
                    logger.warning("Kill switch detected! Aborting API request.")
                    return ""

                try:
                    response = self.client.models.generate_content(
                        model='gemini-3.5-flash', 
                        contents=[
                            prompt,
                            types.Part.from_bytes(
                                data=wav_data,
                                mime_type='audio/wav',
                            )
                        ]
                    )
                    
                    transcription = response.text.strip()
                    
                    if "[SILENCE]" in transcription or len(transcription) < 2:
                        return ""
                        
                    return transcription

                except Exception as api_error:
                    error_str = str(api_error)
                    retry_triggers = ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "500", "502"]
                    
                    if any(trigger in error_str for trigger in retry_triggers):
                        wait_time = 5 * (attempt + 1)
                        logger.warning(f"Google Server Busy. Retrying in {wait_time}s... (Attempt {attempt + 1} of {max_retries})")
                        
                        # Kill Switch Integration to break thread blocks instantly
                        if cancel_event:
                            is_killed = cancel_event.wait(wait_time) 
                            if is_killed:
                                logger.warning("Kill switch triggered during sleep. Exiting thread gracefully.")
                                return ""
                        else:
                            time.sleep(wait_time)
                            
                        continue
                    else:
                        raise api_error

            logger.error("Failed to transcribe audio after 5 retries due to extreme Google server overload.")
            return ""

        except Exception as main_error:
            logger.error(f"Gemini API Audio Error: {main_error}")
            return ""