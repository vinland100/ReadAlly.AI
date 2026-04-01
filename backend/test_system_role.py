import os
import dashscope
from dashscope import MultiModalConversation
from http import HTTPStatus
from dotenv import load_dotenv

load_dotenv()
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

def test_system_role(model_name):
    print(f"Testing MultiModalConversation.call WITH SYSTEM ROLE and model: {model_name}")
    try:
        response = MultiModalConversation.call(
            model=model_name,
            messages=[
                {'role': 'system', 'content': [{'text': 'You are a helpful assistant.'}]},
                {'role': 'user', 'content': [{'text': 'Hello, are you there?'}]}
            ]
        )
        if response.status_code == HTTPStatus.OK:
            print(f"Success! {response.output.choices[0].message.content[0]['text']}")
        else:
            print(f"Failed! Code: {response.code}, Message: {response.message}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_system_role("qwen3.5-flash")
