import openai

def gpt_content(api_key):
    openai.api_key = api_key
    response = openai.Completion.create(model="text-davinci-003",
                                        prompt="Say this is a test",
                                        temperature=0,
                                        max_tokens=7)
    return response