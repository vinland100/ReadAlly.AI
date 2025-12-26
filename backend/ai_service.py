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
        if level == DifficultyLevel.INITIAL.value:
            level_instruction = "Target: High School level (CEFR B1)."
        elif level == DifficultyLevel.INTERMEDIATE.value:
             level_instruction = "Target: CET-4 level (CEFR B2)."
        elif level == DifficultyLevel.UPPER_INTERMEDIATE.value:
             level_instruction = "Target: CET-6 / Graduate Entrance Exam level (CEFR C1)."
        elif level == DifficultyLevel.ADVANCED.value:
             level_instruction = "Target: IELTS 7+ / TOEFL / Professional level (CEFR C1/C2)."
        else:
             level_instruction = "Target: General English learner."

        prompt = f"""
        Role: Expert linguist and English tutor.

        Goal:
        Analyze the following text using the vocabulary and comprehension standards of a learner currently studying at {level_instruction}.


        TASK:
        1. Tokenize the entire text into a linear sequence of tokens (words + punctuation), preserving order.
        2. For each token, output an object with:
           - text
           - type: "normal" | "attention" | "punctuation"
           - definition (Chinese)
           - context_meaning (Chinese, sentence-specific)
           - group_id (integer or null)

        TYPE RULES:
        - "normal": easy/common words or expressions for this level.
        - "attention": difficult, new, or key words or expressions for this level.
        - "punctuation": punctuation symbols only.

        PUNCTUATION RULE:
        - If type == "punctuation":
          - definition = ""
          - context_meaning = ""
          - group_id = null

        GROUPING RULES (CRITICAL):
        - If a word or expression is a multi-word phrase (phrasal verb, idiom, fixed expression etc...):
          - Assign a UNIQUE integer group_id to ALL tokens in that phrase.
          - ALL tokens in the same group MUST share EXACTLY the SAME type:
            - either ALL "normal" or ALL "attention"
            - mixing "normal" and "attention" within a group is STRICTLY FORBIDDEN
        - SPARSE DATA RULE (CRITICAL):
          - Exactly the FIRST token of the group may carry semantic content.
          - The definition and context_meaning on the FIRST token of the group MUST represent the FULL meaning of the ENTIRE group.
          - ALL remaining tokens in the same group MUST be:
            - definition = ""
            - context_meaning = ""


        OUTPUT RULES:
        - Include EVERY token from the source text.
        - Preserve original token order.
        - Output MUST be STRICTLY valid JSON.
        - Output ONLY the JSON array, no explanations.

        An example:
        [
          {{
            "text": "She",
            "type": "normal",
            "definition": "她",
            "context_meaning": "指代句中的女性主体",
            "group_id": null
          }},
          {{
            "text": "not",
            "type": "attention",
            "definition": "不仅……而且……（not only ... but also ...）",
            "context_meaning": "构成强调并列结构的一部分",
            "group_id": 1
          }},
          {{
            "text": "only",
            "type": "attention",
            "definition": "",
            "context_meaning": "",
            "group_id": 1
          }},
          {{
            "text": "quickly",
            "type": "normal",
            "definition": "迅速地",
            "context_meaning": "修饰动作发生的速度",
            "group_id": null
          }},
          {{
            "text": "turned",
            "type": "attention",
            "definition": "拒绝（turn ... down）",
            "context_meaning": "表示拒绝某个提议",
            "group_id": 2
          }},
          {{
            "text": "the",
            "type": "normal",
            "definition": "这个",
            "context_meaning": "特指下文提到的提议",
            "group_id": null
          }},
          {{
            "text": "offer",
            "type": "normal",
            "definition": "提议；报价",
            "context_meaning": "指被拒绝的提议",
            "group_id": null
          }},
          {{
            "text": "down",
            "type": "attention",
            "definition": "",
            "context_meaning": "",
            "group_id": 2
          }},
          {{
            "text": ",",
            "type": "punctuation",
            "definition": "",
            "context_meaning": "",
            "group_id": null
          }},
          {{
            "text": "but",
            "type": "attention",
            "definition": "",
            "context_meaning": "",
            "group_id": 1
          }},
          {{
            "text": "also",
            "type": "attention",
            "definition": "",
            "context_meaning": "",
            "group_id": 1
          }},
          {{
            "text": "flat",
            "type": "attention",
            "definition": "断然地；毫不留情地（flat out）",
            "context_meaning": "强调拒绝的坚决程度",
            "group_id": 3
          }},
          {{
            "text": "out",
            "type": "attention",
            "definition": "",
            "context_meaning": "",
            "group_id": 3
          }},
          {{
            "text": "refused",
            "type": "attention",
            "definition": "拒绝",
            "context_meaning": "明确表示不愿意做某事",
            "group_id": null
          }},
          {{
            "text": "to",
            "type": "normal",
            "definition": "去；做（不定式标记）",
            "context_meaning": "引出后续动作",
            "group_id": null
          }},
          {{
            "text": "explain",
            "type": "normal",
            "definition": "解释",
            "context_meaning": "说明原因或细节",
            "group_id": null
          }},
          {{
            "text": "why",
            "type": "normal",
            "definition": "为什么",
            "context_meaning": "引导原因从句",
            "group_id": null
          }},
          {{
            "text": ".",
            "type": "punctuation",
            "definition": "",
            "context_meaning": "",
            "group_id": null
          }}
        ]

        Target Text:
        {text}

        JSON about the text:
        """

        try:
            response = Generation.call(
                model="qwen3-next-80b-a3b-instruct",
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
                model="qwen3-next-80b-a3b-instruct",
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
                model="qwen3-next-80b-a3b-instruct",
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
            response = dashscope.MultiModalConversation.call(
                model='qwen3-tts-flash',
                text=text,
                voice='Jennifer',
                api_key=os.getenv("DASHSCOPE_API_KEY") ,
                language_type="English"
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
