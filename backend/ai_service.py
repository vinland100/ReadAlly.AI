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

        here are a few examples:
        example 1:
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

        example 2:
        [
          {{
            "text": "He",
            "type": "normal",
            "definition": "他",
            "context_meaning": "指代句中的男性主体",
            "group_id": null
          }},
          {{
            "text": "gave",
            "type": "attention",
            "definition": "放弃（give up）",
            "context_meaning": "表示停止尝试或不再坚持某事",
            "group_id": 1
          }},
          {{
            "text": "up",
            "type": "attention",
            "definition": "",
            "context_meaning": "",
            "group_id": 1
          }},
          {{
            "text": "the",
            "type": "normal",
            "definition": "这个",
            "context_meaning": "特指后面的计划",
            "group_id": null
          }},
          {{
            "text": "plan",
            "type": "normal",
            "definition": "计划",
            "context_meaning": "指原本打算执行的方案",
            "group_id": null
          }},
          {{
            "text": "after",
            "type": "normal",
            "definition": "在……之后",
            "context_meaning": "表示时间顺序",
            "group_id": null
          }},
          {{
            "text": "running",
            "type": "attention",
            "definition": "耗尽（run out of）",
            "context_meaning": "表示资源被完全用完",
            "group_id": 2
          }},
          {{
            "text": "out",
            "type": "attention",
            "definition": "",
            "context_meaning": "",
            "group_id": 2
          }},
          {{
            "text": "of",
            "type": "attention",
            "definition": "",
            "context_meaning": "",
            "group_id": 2
          }},
          {{
            "text": "time",
            "type": "normal",
            "definition": "时间",
            "context_meaning": "指可用的时间资源",
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

        example 3:
        [
          {{
            "text": "They",
            "type": "normal",
            "definition": "他们",
            "context_meaning": "指代做决定的一方",
            "group_id": null
          }},
          {{
            "text": "took",
            "type": "attention",
            "definition": "考虑到；把……纳入考虑（take ... into account）",
            "context_meaning": "表示在决策时综合考虑因素",
            "group_id": 2
          }},
          {{
            "text": "all",
            "type": "normal",
            "definition": "所有的",
            "context_meaning": "强调数量完整",
            "group_id": null
          }},
          {{
            "text": "the",
            "type": "normal",
            "definition": "这些",
            "context_meaning": "限定后面的因素",
            "group_id": null
          }},
          {{
            "text": "possible",
            "type": "attention",
            "definition": "可能的",
            "context_meaning": "表示不确定但存在的情况",
            "group_id": null
          }},
          {{
            "text": "risks",
            "type": "attention",
            "definition": "风险",
            "context_meaning": "可能带来负面结果的因素",
            "group_id": null
          }},
          {{
            "text": "into",
            "type": "attention",
            "definition": "",
            "context_meaning": "",
            "group_id": 2
          }},
          {{
            "text": "serious",
            "type": "normal",
            "definition": "严肃的",
            "context_meaning": "强调态度",
            "group_id": null
          }},
          {{
            "text": "account",
            "type": "attention",
            "definition": "",
            "context_meaning": "",
            "group_id": 2
          }},
          {{
            "text": "before",
            "type": "normal",
            "definition": "在……之前",
            "context_meaning": "表示时间顺序",
            "group_id": null
          }},
          {{
            "text": "deciding",
            "type": "normal",
            "definition": "决定",
            "context_meaning": "指做出选择",
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


        this is the target text:
        {text}

        JSON about the target text:
        """

        try:
            response = Generation.call(
                model="qwen3-coder-plus",
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
        Translate the following English paragraph into fluent, formal Chinese.
        Output MUST be a valid JSON object with the following structure:
        {{
            "translation": "formal chinese translation",
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
