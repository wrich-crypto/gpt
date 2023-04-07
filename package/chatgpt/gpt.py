import openai

def gpt_content(api_key, prompt):
    openai.api_key = api_key
    response = openai.Completion.create(model="text-davinci-003",
                                        prompt=prompt,
                                        temperature=0.5,
                                        max_tokens=1024)
    return response