import os
import dashscope
from dashscope import Generation, MultiModalConversation
from http import HTTPStatus
from dotenv import load_dotenv

load_dotenv()
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

def test_generation(model_name):
    print(f"Testing Generation.call with model: {model_name}")
    try:
        response = Generation.call(
            model=model_name,
            messages=[{'role': 'user', 'content': 'Hello, are you there?'}],
            result_format='message'
        )
        if response.status_code == HTTPStatus.OK:
            print(f"Generation Success! {response.output.choices[0].message.content}")
        else:
            print(f"Generation Failed! Code: {response.code}, Message: {response.message}")
    except Exception as e:
        print(f"Generation Exception: {e}")

def test_multimodal(model_name):
    print(f"Testing MultiModalConversation.call with model: {model_name}")
    try:
        response = MultiModalConversation.call(
            model=model_name,
            messages=[{'role': 'user', 'content': [{'text': 'Hello, are you there?'}]}]
        )
        if response.status_code == HTTPStatus.OK:
            print(f"MultiModal Success! {response.output.choices[0].message.content}")
        else:
            print(f"MultiModal Failed! Code: {response.code}, Message: {response.message}")
    except Exception as e:
        print(f"MultiModal Exception: {e}")

if __name__ == "__main__":
    test_generation("qwen3.5-flash")
    test_multimodal("qwen3.5-flash")
    test_generation("qwen-plus")
