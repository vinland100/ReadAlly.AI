import os
from dotenv import load_dotenv

load_dotenv()
import json
import logging
from http import HTTPStatus
import dashscope
from dashscope import Generation
from models import DifficultyLevel
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure API key is set
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

class AIService:


    @staticmethod
    def analyze_vocabulary(text: str, level: str):
        """
        Analyzes the text for vocabulary based on the user's difficulty level.
        Returns a JSON list of objects representing the full text tokenization.
        """

        level_instruction = ""
        if level == "High School":
            level_instruction = "Target: High School level (CEFR B2+)."
        elif level == "CET-4":
             level_instruction = "Target: CET-4 level (CEFR C1)."
        elif level == "IELTS":
             level_instruction = "Target: IELTS Band 7+."
        else:
             level_instruction = "Target: Advanced learner."

        prompt = f"""
        You are an expert linguist and English tutor.
        Goal: Analyze the following text {level_instruction}

        Task:
        1. Tokenize the entire text into a linear list of tokens (words and punctuation).
        2. Assign a 'type' to each token:
           - 'normal': clearly understood, simple words/Phrase/phrases/idioms/fixed expressions for this level.
           - 'attention': difficult, new, or important words/Phrase/phrases/idioms/fixed expressions for this level (Target Items).
           - 'punctuation': Punctuation marks (.,?! ")""——"etc).
        3. For 'normal' AND 'attention' tokens:
           - Provide a concise Chinese definition (`definition`).
           - Provide the `context_meaning` (meaning in this specific sentence).
        4. For 'punctuation' tokens:
           - Set `definition` and `context_meaning` to empty.
        5. Grouping (Crucial) and Group Consistency Rule (CRITICAL):
           - If a 'normal' OR 'attention' item consists of multiple words (e.g. "turn on", "rip open"), assign a UNIQUE integer `group_id` to ALL tokens in that phrase.
           - **SPARSE DATA RULE**: 
             - Provide the full `definition` and `context_meaning` ONLY for the **FIRST** token of the group.
             - For **ALL SUBSEQUENT** tokens in the same group, set `definition` and `context_meaning` to **empty string ""**.
           - The meaning provided in the first token MUST describe the **WHOLE PHRASE**.
             - Example: "rip open". 
               - Token 1 "rip": type="attention", group_id=1, definition="迅速撕开", context_meaning="喻指..."
               - Token 2 "open": type="attention", group_id=1, definition="", context_meaning=""
        6. Output Requirement:
           - Ensure every token from the source text is included in order.
        
        Output STRICTLY valid JSON format:
        [
            {{
                "text": "The",
                "type": "normal",
                "definition": "定冠词",
                "context_meaning": "特指前文提过的",
                "group_id": null
            }},
            {{
                "text": "teacher",
                "type": "normal",
                "definition": "老师",
                "context_meaning": "指代该教育者",
                "group_id": null
            }},
            {{
                "text": "turned",
                "type": "attention",
                "definition": "打开 (turn on)",
                "context_meaning": "启动电源",
                "group_id": 1
            }},
            {{
                "text": "the",
                "type": "normal",
                "definition": "定冠词",
                "context_meaning": null,
                "group_id": null
            }},
            {{
                "text": "computer",
                "type": "normal",
                "definition": "电脑",
                "context_meaning": "指代那台机器",
                "group_id": null
            }},
            {{
                "text": "on",
                "type": "attention",
                "definition": "打开 (turn on)",
                "context_meaning": "启动电源",
                "group_id": 1
            }},
            {{
                "text": ".",
                "type": "punctuation",
                "definition": "",
                "context_meaning": "",
                "group_id": null
            }}
        ]
        
        Text:
        {text}
        
        JSON about the text:
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
    def translate_paragraph(text: str):
        prompt = f"""
        Translate the following English paragraph into fluent, natural Chinese.
        Output MUST be a valid JSON object with the following structure:
        {{
            "translation": "natural chinese translation",
            "style": "description of the writing style (e.g. academic, conversational, poetic)",
            "key_phrases": [
                {{"en": "phrase", "cn": "chinese equivalent"}}
            ]
        }}
        Do not output markdown or explanations outside the JSON.

        Text:
        {text}
        """
        try:
            response = Generation.call(
                model="qwen-flash",
                messages=[{'role': 'system', 'content': 'You are a professional translator. Output only JSON.'},
                          {'role': 'user', 'content': prompt}],
                result_format='message'
            )
            if response.status_code == HTTPStatus.OK:
                content = response.output.choices[0].message.content.strip()
                if content.startswith("```json"): content = content[7:]
                if content.endswith("```"): content = content[:-3]
                return json.loads(content)
            return {"translation": "Translation failed."}
        except Exception as e:
            logger.error(f"Translation Exception: {e}")
            return {"translation": "Translation error."}

    @staticmethod
    def analyze_syntax(text: str):
        prompt = f"""
        Analyze the syntax of the following English paragraph for an English learner.
        Output MUST be a valid JSON object with the following structure:
        {{
            "structures": [
                {{"pattern": "S-V-VO (主谓宾)", "content": "example from text", "explanation": "chinese explanation"}}
            ],
            "clauses": [
                {{"type": "Relative clause (定语从句)", "content": "...", "explanation": "..."}}
            ],
            "grammar_points": [
                {{"point": "Present Perfect", "point_cn": "现在完成时", "explanation": "Explain how it IS USED in this specific text. DO NOT include if not present."}}
            ]
        }}
        
        CRITICAL RULES:
        1. ONLY include grammar_points that are ACTUALLY USED in the provided text.
        2. If a grammar point is not clearly present, DO NOT include it.
        3. The "explanation" must refer to the specific instance in the text.
        4. Do not output markdown or explanations outside the JSON.

        Text:
        {text}
        """
        try:
            response = Generation.call(
                model="qwen-flash",
                messages=[{'role': 'system', 'content': 'You are a grammar expert. Output only JSON.'},
                          {'role': 'user', 'content': prompt}],
                result_format='message'
            )
            if response.status_code == HTTPStatus.OK:
                content = response.output.choices[0].message.content.strip()
                if content.startswith("```json"): content = content[7:]
                if content.endswith("```"): content = content[:-3]
                return json.loads(content)
            return {"error": "Analysis failed."}
        except Exception as e:
            logger.error(f"Syntax Analysis Exception: {e}")
            return {"error": "Analysis error."}

    @staticmethod
    def generate_tts(text: str) -> bytes:
        """
        Generates TTS audio using Qwen3-TTS.
        Returns the audio content (bytes) directly (MP3 format).
        """
        try:
            # Using the correct SDK class as per user instructions
            response = dashscope.audio.qwen_tts.SpeechSynthesizer.call(
                model='qwen3-tts-flash',
                text=text,
                voice='Jennifer',
                api_key=os.getenv("DASHSCOPE_API_KEY") 
            )

            # Check successful response
            if response.status_code == HTTPStatus.OK:
                # Structure: response.output['audio']['url']
                if hasattr(response, 'output') and response.output and 'audio' in response.output and 'url' in response.output['audio']:
                    audio_url = response.output['audio']['url']
                    # Download the audio
                    r = requests.get(audio_url)
                    if r.status_code == 200:
                        return r.content
                    else:
                        logger.error(f"TTS Download Error: {r.status_code}")
                        return None
                else:
                    logger.error(f"TTS Response missing audio url: {response}")
                    return None
            else:
                logger.error(f"TTS API Error: {response.code} - {response.message}")
                return None

        except Exception as e:
            logger.error(f"TTS Exception: {e}")
            return None

# Fix for SpeechSynthesizer import
# Dashscope SDK structure might be slightly different.
# I will use the 'dashscope.audio.tts.SpeechSynthesizer' as it is standard.
