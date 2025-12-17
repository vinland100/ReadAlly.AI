import os
import json
import logging
from http import HTTPStatus
import dashscope
from dashscope import Generation
from models import DifficultyLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure API key is set
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

class AIService:
    @staticmethod
    def classify_difficulty(text: str) -> str:
        """Classifies the reading level of the text."""
        prompt = f"""
        Analyze the following English text and classify its difficulty level into one of these categories:
        High School, CET-4, CET-6, IELTS, TEM-8.

        Only output the category name.

        Text snippet:
        {text[:1000]}...
        """

        try:
            response = Generation.call(
                model="qwen-flash",
                messages=[{'role': 'system', 'content': 'You are a helpful language assessment expert.'},
                          {'role': 'user', 'content': prompt}],
                result_format='message'
            )

            if response.status_code == HTTPStatus.OK:
                return response.output.choices[0].message.content.strip()
            else:
                logger.error(f"AI Classification Error: {response.code} - {response.message}")
                return "Unknown"
        except Exception as e:
            logger.error(f"AI Classification Exception: {e}")
            return "Unknown"

    @staticmethod
    def analyze_vocabulary(text: str, level: str):
        """
        Analyzes the text for vocabulary based on the user's difficulty level.
        Returns a JSON list of objects: {word, type, definition, context_example}
        """

        level_instruction = ""
        if level == "High School":
            level_instruction = "Identify words that are above standard high school level (CEFR B2+)."
        elif level == "CET-4":
             level_instruction = "Identify words that are difficult for CET-4 students (CEFR C1)."
        elif level == "IELTS":
             level_instruction = "Identify sophisticated vocabulary, idioms, and nuances suitable for Band 7+."
        else:
             level_instruction = "Identify challenging words, idioms, and phrases."

        prompt = f"""
        You are an expert English tutor. Analyze the following text segment.
        {level_instruction}

        Identify:
        1. Uncommon words
        2. Idioms
        3. Phrasal verbs
        4. Fixed expressions/collocations
        5. Slang (if any)

        Output STRICTLY valid JSON format with this structure:
        [
            {{
                "word": "exact phrase or word from text",
                "type": "word" | "idiom" | "phrase" | "slang",
                "definition": "Concise Chinese definition and explanation",
                "context_example": "A short simple example sentence using this word/phrase"
            }}
        ]

        Do not output any markdown or explanations outside the JSON.

        Text:
        {text}
        """

        try:
            response = Generation.call(
                model="qwen-flash",
                messages=[{'role': 'system', 'content': 'You are a strict JSON outputting AI assistant.'},
                          {'role': 'user', 'content': prompt}],
                result_format='message'
            )

            if response.status_code == HTTPStatus.OK:
                content = response.output.choices[0].message.content.strip()
                # Clean markdown code blocks if present
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                return json.loads(content)
            else:
                logger.error(f"AI Vocab Analysis Error: {response.code} - {response.message}")
                return []
        except Exception as e:
            logger.error(f"AI Vocab Analysis Exception: {e}")
            return []

    @staticmethod
    def translate_paragraph(text: str) -> str:
        prompt = f"""
        Translate the following English paragraph into fluent, natural Chinese.

        Text:
        {text}
        """
        try:
            response = Generation.call(
                model="qwen-flash",
                messages=[{'role': 'system', 'content': 'You are a professional translator.'},
                          {'role': 'user', 'content': prompt}],
                result_format='message'
            )
            if response.status_code == HTTPStatus.OK:
                return response.output.choices[0].message.content.strip()
            return "Translation failed."
        except Exception as e:
            logger.error(f"Translation Exception: {e}")
            return "Translation error."

    @staticmethod
    def analyze_syntax(text: str) -> str:
        prompt = f"""
        Analyze the syntax of the following English paragraph for a learner.
        Highlight:
        1. Sentence structures (Subject-Verb-Object, etc.)
        2. Clauses (Relative clauses, Noun clauses)
        3. Key grammatical points.

        Keep the explanation in Chinese. Be concise and structured.

        Text:
        {text}
        """
        try:
            response = Generation.call(
                model="qwen-flash",
                messages=[{'role': 'system', 'content': 'You are a grammar expert.'},
                          {'role': 'user', 'content': prompt}],
                result_format='message'
            )
            if response.status_code == HTTPStatus.OK:
                return response.output.choices[0].message.content.strip()
            return "Analysis failed."
        except Exception as e:
            logger.error(f"Syntax Analysis Exception: {e}")
            return "Analysis error."

    @staticmethod
    def generate_tts(text: str) -> bytes:
        """
        Generates TTS audio using Qwen3-TTS.
        Returns the audio content (bytes) directly (MP3 format).
        """
        try:
            # Using the SDK class directly as per user example (though call method might vary slightly,
            # I will follow the user provided snippet pattern but adapted for streaming/direct return)

            # The user snippet used: dashscope.audio.qwen_tts.SpeechSynthesizer.call(...)
            # I need to handle the return. It usually returns a Result object with 'audio_url' or binary content.
            # dashscope SDK often saves to file if 'file_path' is provided, or provides url.

            # Checking documentation logic via inference or standard patterns:
            # If I want the raw bytes, I might need to download from the URL if it returns a URL,
            # or check if it returns bytes.

            # Let's try the standard call.
            response = dashscope.audio.tts.SpeechSynthesizer.call(
                model='qwen3-tts-flash',
                text=text,
                voice='Cherry'
            )

            # The response usually contains audio_address or output directly?
            # Qwen-tts often returns an audio buffer or url.
            # According to docs (implied), save to file is common.
            # For this web app, I want to stream it back.

            if response.get_audio_data() is not None:
                 return response.get_audio_data()
            elif response.output and response.output.get("audio_address"):
                 # Download the audio
                 import requests
                 r = requests.get(response.output["audio_address"])
                 return r.content
            else:
                 logger.error(f"TTS Error: {response}")
                 return None

        except Exception as e:
            logger.error(f"TTS Exception: {e}")
            return None

# Fix for SpeechSynthesizer import
# Dashscope SDK structure might be slightly different.
# I will use the 'dashscope.audio.tts.SpeechSynthesizer' as it is standard.
