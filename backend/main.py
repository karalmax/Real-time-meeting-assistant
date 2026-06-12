import threading
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

from backend.transcriber import AudioTranscriber
from backend.vector_store import MeetingVectorStore
from backend.llm_engine import MeetingIntelligence

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ml_models = {}

class QuestionRequest(BaseModel):
    question: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Gemini Cloud STT Engine (30s Buffer)...")
    ml_models["stt_engine"] = AudioTranscriber()
    
    logger.info("Initializing ChromaDB Vector Store...")
    vector_db = MeetingVectorStore()
    ml_models["vector_db"] = vector_db
    
    logger.info("Initializing Intelligence Layer...")
    ml_models["llm_engine"] = MeetingIntelligence(vector_store=vector_db)
    
    logger.info("Server is ready.")
    yield
    ml_models.clear()

app = FastAPI(title="Real-Time Meeting Assistant API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/audio")
async def audio_stream_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established with client.")
    
    stt_engine = ml_models.get("stt_engine")
    vector_db = ml_models.get("vector_db")
    
    if not stt_engine or not vector_db:
        await websocket.close(code=1011, reason="Core Engines not initialized.")
        return

    # 30-Second Buffer
    BUFFER_SIZE_LIMIT = 960000
    audio_buffer = bytearray()

    try:
        while True:
            audio_chunk = await websocket.receive_bytes()
            audio_buffer.extend(audio_chunk)
            
            if len(audio_buffer) >= BUFFER_SIZE_LIMIT:
                # 30s portion ah mattum edukkurom
                process_bytes = bytes(audio_buffer[:BUFFER_SIZE_LIMIT])
                # Process panna portion ah mattum delete pandrom (Data loss thadukka)
                del audio_buffer[:BUFFER_SIZE_LIMIT]
                
                # --- THE PIPE OVERFLOW FIX 💓 ---
                cancel_event = threading.Event()
                transcription_task = asyncio.create_task(
                    asyncio.to_thread(stt_engine.process_audio_chunk, process_bytes, cancel_event)
                )
                
                # UI-kku udane Loading signal anupprom
                try:
                    await websocket.send_json({"status": "processing", "text": " "})
                except Exception:
                    pass

                last_ping_time = time.time()

                # Google-kaga wait pandra gap-la microphone audio-va receive pandrom (Non-blocking mode)
                while not transcription_task.done():
                    try:
                        # 1 second wait panni audio receive pannu (Pipe burst aagama irukka)
                        extra_chunk = await asyncio.wait_for(websocket.receive_bytes(), timeout=1.0)
                        audio_buffer.extend(extra_chunk)
                        
                        # 4 seconds kku oru thadava ping anuppu
                        if time.time() - last_ping_time > 4.0:
                            await websocket.send_json({"status": "processing", "text": " "})
                            last_ping_time = time.time()
                            
                    except asyncio.TimeoutError:
                        # Audio varalanaalum 4s kku oru thadava heartbeat ping
                        if time.time() - last_ping_time > 4.0:
                            try:
                                await websocket.send_json({"status": "processing", "text": " "})
                                last_ping_time = time.time()
                            except Exception:
                                cancel_event.set()
                                transcription_task.cancel()
                                return
                    except WebSocketDisconnect:
                        cancel_event.set()
                        transcription_task.cancel()
                        logger.warning("Client disconnected. Kill Switch fired.")
                        return
                        
                # Process aagi vantha result
                transcription = transcription_task.result()
                # ------------------------------------------------------
                
                if transcription and transcription.strip():
                    logger.info(f"Transcribed: {transcription}")
                    
                    current_time = time.time()
                    await asyncio.to_thread(
                        vector_db.add_transcript,
                        transcription,
                        current_time
                    )
                    
                    await websocket.send_json({
                        "status": "success", 
                        "text": transcription
                    })
                
    except WebSocketDisconnect:
        logger.warning("WebSocket client disconnected normally.")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket stream: {e}")

@app.post("/api/ask")
async def ask_question(request: QuestionRequest):
    llm_engine = ml_models.get("llm_engine")
    if not llm_engine:
        return {"error": "Intelligence Engine not initialized."}
    answer = await asyncio.to_thread(llm_engine.generate_answer, request.question)
    return {"question": request.question, "answer": answer}

@app.get("/api/summary")
async def get_meeting_summary():
    llm_engine = ml_models.get("llm_engine")
    if not llm_engine:
        return {"error": "Intelligence Engine not initialized."}
    summary = await asyncio.to_thread(llm_engine.generate_summary)
    return {"summary": summary}