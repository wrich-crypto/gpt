import openai

def gpt_content(api_key, prompt):
    try:
        openai.api_key = api_key
        response = openai.Completion.create(model="text-davinci-003",
                                            prompt=prompt,
                                            temperature=0.5,
                                            max_tokens=2048)
        return response.choices[0]
    except Exception as e:
        return None
