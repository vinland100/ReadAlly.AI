import os
import dashscope
from dashscope import Generation
from http import HTTPStatus
from dotenv import load_dotenv

load_dotenv()
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

def test_model(model_name):
    print(f"Testing model: {model_name}")
    try:
        response = Generation.call(
            model=model_name,
            messages=[{'role': 'user', 'content': 'Hello, are you there?'}],
            result_format='message'
        )
        if response.status_code == HTTPStatus.OK:
            print(f"Success! Model {model_name} responded.")
            print(response.output.choices[0].message.content)
        else:
            print(f"Failed! Code: {response.code}, Message: {response.message}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_model("qwen3.5-flash")
    test_model("qwen-turbo")
