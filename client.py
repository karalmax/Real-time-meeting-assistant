import asyncio
import websockets
import pyaudio
import json

# Audio Configuration (Optimized for Whisper)
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # 16kHz sample rate
CHUNK = 4096  # Send audio in chunks

async def record_and_send(websocket, stream):
    """Captures microphone audio and streams it to the WebSocket server."""
    print("🎤 Microphone ON. Start speaking...")
    try:
        while True:
            # Read audio data from mic
            data = stream.read(CHUNK, exception_on_overflow=False)
            
            # Send raw bytes to WebSocket
            await websocket.send(data)
            
            # Brief sleep to yield control to the event loop
            await asyncio.sleep(0.01) 
    except Exception as e:
        print(f"Error sending audio: {e}")

async def receive_transcripts(websocket):
    """Listens for transcribed text from the server and prints it."""
    try:
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("status") == "success":
                print(f"📝 Transcribed: {data.get('text')}")
    except websockets.exceptions.ConnectionClosed:
        print("Server connection closed.")
    except Exception as e:
        print(f"Error receiving data: {e}")

async def main():
    # FastAPI WebSocket URL
    uri = "ws://127.0.0.1:8000/ws/audio"
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to Meeting Assistant Server")
            
            # Run both streaming and receiving concurrently
            await asyncio.gather(
                record_and_send(websocket, stream),
                receive_transcripts(websocket)
            )
    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        # Resource cleanup
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    asyncio.run(main())