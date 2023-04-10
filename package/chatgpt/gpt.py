import openai
import requests
from init import hot_config


def gpt_content(prompt, max_try=1):
    current_try = 0

    while current_try < max_try:
        proxy = hot_config.get_next_proxy()
        api_key = hot_config.get_next_api_key()

        try:
            openai.api_key = api_key

            session = requests.Session()
            session.proxies = {'https': proxy}

            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0.5,
                max_tokens=2048,
                session=session
            )
            current_try = current_try + 1
            return response.choices[0]

        except Exception as e:
            print(f"Error occurred: {e}")
            current_try = current_try + 1
            continue
