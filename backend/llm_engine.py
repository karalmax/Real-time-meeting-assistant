import logging
import os
from dotenv import load_dotenv
from google import genai

# Load environment variables from .env
load_dotenv()

logger = logging.getLogger(__name__)

class MeetingIntelligence:
    def __init__(self, vector_store, *args, **kwargs):
        """
        Initializes the new Google GenAI SDK for RAG and Summarization.
        """
        self.vector_store = vector_store
        
        # API Key is now fetched from the .env file
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        logger.info("Intelligence Layer Switched to Google GenAI SDK (Cloud).")

    def generate_answer(self, question: str) -> str:
        try:
            context_chunks = self.vector_store.query_context(question, n_results=3)
            
            if not context_chunks:
                return "The current meeting context doesn't contain information about this."

            context_text = " ".join(context_chunks)
            
            prompt = f"""You are a smart AI secretary assisting with a technical meeting.
            Answer the user's question using ONLY the context provided below. 
            
            IMPORTANT STRICT RULE: You MUST reply STRICTLY in Tanglish (Tamil language written in English alphabets). 
            Example: "Intha meeting la budget pathi discuss pannanga."
            Do NOT use Tamil letters (தமிழ்). If you don't know the answer, say "Enakku intha detail theriyaathu".
            
            CONTEXT:
            {context_text}
            
            QUESTION: {question}
            """

            # Migrated to current GenAI model: gemini-3.5-flash
            response = self.client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt
            )
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini API Q&A Error: {e}")
            return "Failed to generate answer. Check API Key or network connection."

    def generate_summary(self) -> str:
        try:
            context_chunks = self.vector_store.query_context("key decisions, action items, and overview", n_results=50)
            
            if not context_chunks:
                return "No meeting data available to summarize."

            context_text = " ".join(context_chunks)
            
            prompt = f"""You are a highly precise executive assistant. 
            Analyze the meeting context and extract the summary. You MUST match the exact names to their specific tasks.
            
            IMPORTANT STRICT RULE: You MUST write the ENTIRE summary STRICTLY in Tanglish (Tamil language written in English alphabets). 
            Do NOT use Tamil letters (தமிழ்).
            
            Include:
            1. 📌 Overview: 2-sentence summary in Tanglish.
            2. 🎯 Key Decisions: Finalized items and tech stack in Tanglish.
            3. 🚀 Action Items: Strictly use the format "• [Name]: [Exact Task] (by [Deadline])" in Tanglish.
            
            CONTEXT:
            {context_text}
            """

            # Inga iruntha 2.0 bug-ah fix panni 3.5-kku maathiyachu
            response = self.client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt
            )
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini API Summary Error: {e}")
            return "Failed to generate meeting summary."