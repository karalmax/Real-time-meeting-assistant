import chromadb
import uuid
import logging

logger = logging.getLogger(__name__)

class MeetingVectorStore:
    def __init__(self, persist_directory="./.chroma_db"):
        """
        Initializes the ChromaDB client.
        Clears old meeting data on startup to prevent context mixing and hallucinations.
        """
        try:
            # Initialize persistent local database
            self.client = chromadb.PersistentClient(path=persist_directory)
            
            # --- THE FIX: Clean up stale data from previous sessions ---
            try:
                self.client.delete_collection(name="meeting_transcripts")
                logger.info("Cleared stale meeting data from Vector DB.")
            except Exception:
                # Collection doesn't exist yet (e.g., first time running), athu normal thaan
                pass 
                
            # Create a completely fresh collection for the current meeting
            self.collection = self.client.create_collection(name="meeting_transcripts")
            logger.info("ChromaDB initialized with a fresh 'meeting_transcripts' collection.")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")

    def add_transcript(self, text: str, timestamp: float):
        """
        Converts the transcript text into embeddings and stores it in the vector DB.
        """
        if not text.strip():
            return
            
        try:
            # Generate a unique ID for this specific text chunk
            chunk_id = str(uuid.uuid4())
            
            # Store the text, along with metadata (like when it was spoken)
            self.collection.add(
                documents=[text],
                metadatas=[{"timestamp": timestamp}],
                ids=[chunk_id]
            )
            logger.info(f"Stored transcript in Vector DB: '{text[:30]}...'")
        except Exception as e:
            logger.error(f"Error adding transcript to ChromaDB: {e}")

    def query_context(self, question: str, n_results: int = 3) -> list:
        """
        Retrieves the most semantically relevant transcript chunks for a given question.
        Used for the Live Q&A (RAG) feature.
        """
        try:
            results = self.collection.query(
                query_texts=[question],
                n_results=n_results
            )
            
            # Extract and return just the flat list of text documents
            if results and results['documents']:
                return results['documents'][0]
            return []
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return []